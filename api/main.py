#main API

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from api import (
    call_fireworks,
    save_to_csv,
    translate,
    generate_image,
    create_product_from_trends,
    save_product_to_csv
)
import requests
import os
import logging
from langdetect import detect, LangDetectException
from dotenv import load_dotenv
import re
import json
from fastapi.staticfiles import StaticFiles
from inci_utils import check_ingredients_pipeline
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["http://localhost:5173"]  # o il tuo dominio React

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carica variabili ambiente
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# cartella dati
data_path = os.path.join(ROOT_DIR, "data")
if not os.path.exists(data_path):
    os.makedirs(data_path)

# monta static per servire immagini salvate
app.mount("/data", StaticFiles(directory=data_path), name="data")

def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        json_str = match.group(0)
        return json.loads(json_str)
    else:
        raise ValueError("Nessun JSON trovato nel testo")

def getenv_path(env_var: str, root_dir: str, default: str) -> str:
    val = os.getenv(env_var)
    if val:
        if not os.path.isabs(val):
            abs_path = os.path.abspath(os.path.join(root_dir, val))
            logging.info(f"📁 Path '{env_var}' risolto in '{abs_path}'")
            return abs_path
        else:
            logging.info(f"📁 Path assoluto da env '{env_var}': {val}")
            return val
    return default

CSV_PATH = getenv_path("CSV_PATH", ROOT_DIR, os.path.join(ROOT_DIR, "data", "qa_history_prompt.csv"))
RETRIEVER_URL = os.getenv("RETRIEVER_URL", "http://localhost:9000/search")

class QueryRequest(BaseModel):
    query: str
    platform: str  # twitter / instagram

class InciRequest(BaseModel):
    query: str

def lang_code_to_name(code: str) -> str:
    mapping = {
        "en": "English",
        "it": "Italian",
        "fr": "French",
        "es": "Spanish",
        "de": "German"
    }
    return mapping.get(code.lower(), "English")

def get_context_from_query_http(query: str, index_type: str = "post") -> list:
    try:
        resp = requests.post(
            RETRIEVER_URL,
            json={"query": query, "index_type": index_type},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        logging.error(f"❌ Errore chiamando retriever: {e}")
        return []

def clean_generated_text(text: str, max_len: int = 280) -> str:
    text = re.sub(r"(?i)(here is the translation:?|let me know[^\n]*)", "", text).strip()
    lines = list(dict.fromkeys(text.split("\n")))  # deduplica righe
    cleaned = " ".join(lines).strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rsplit(" ", 1)[0] + "..."
    return cleaned

@app.get("/health")
async def healthcheck():
    return {"status": "ok"}

@app.post("/generate")
async def generate(data: QueryRequest):
    original_query = data.query.strip()
    platform = data.platform.strip().lower()
    logging.info(f"📥 Query ricevuta: {original_query} (platform={platform})")

    try:
        detected_lang = detect(original_query)
        logging.info(f"🌐 Lingua rilevata: {detected_lang}")
    except LangDetectException:
        detected_lang = "en"
        logging.warning("⚠️ Lingua non rilevata, default 'en'")

    query_en = original_query
    if detected_lang != "en":
        try:
            query_en = translate(original_query, target_language="English")
            logging.info(f"🈯 Query tradotta in inglese: {query_en}")
        except Exception as e:
            logging.error(f"❌ Errore traduzione query: {e}")
            query_en = original_query

    context_docs = get_context_from_query_http(query_en, index_type="post")
    context_str = "\n".join(doc["content"] for doc in context_docs)
    logging.info(f"📚 Contesto ricevuto ({sum(len(doc['content']) for doc in context_docs)} caratteri in {len(context_docs)} documenti)")

    try:
        answer_en = call_fireworks(query_en, context_str, platform.capitalize())
        answer_en = clean_generated_text(answer_en)

        image_url = None
        if platform == "instagram":
            image_path = generate_image(prompt=answer_en)  # es: .../data/images/post_123.png
            filename = os.path.basename(image_path)        # post_123.png
            subfolder = os.path.basename(os.path.dirname(image_path))  # images
            image_url = f"http://localhost:8000/data/{subfolder}/{filename}"
            logging.info(f"✅ Immagine disponibile a: {image_url}")

    except Exception as e:
        logging.error(f"❌ Errore generazione risposta: {e}")
        answer_en = "Sorry, I couldn't get an answer."
        image_url = None

    answer_final = answer_en
    if detected_lang != "en":
        try:
            answer_final = translate(answer_en, target_language=lang_code_to_name(detected_lang))
            logging.info("✅ Risposta tradotta nella lingua originale")
        except Exception as e:
            logging.error(f"❌ Errore traduzione risposta: {e}")

    try:
        save_to_csv(original_query, answer_final, CSV_PATH)
    except Exception as e:
        logging.error(f"❌ Errore salvataggio CSV: {e}")

    return {"answer": answer_final, "image_url": image_url}

@app.post("/check_inci")
async def check_inci(data: InciRequest):
    query = data.query.strip()
    result = check_ingredients_pipeline(query)
    return result

from inci_utils import append_to_csv, GREEN_CSV, RED_CSV

class IngredientRequest(BaseModel):
    ingredient: str

@app.post("/add_green")
async def add_green(data: IngredientRequest):
    ing = data.ingredient.strip().lower()
    if not ing:
        raise HTTPException(status_code=400, detail="Missing ingredient")
    try:
        append_to_csv(GREEN_CSV, ing)
        return {"status": "ok", "ingredient": ing, "list": "green"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore scrittura CSV: {e}")

@app.post("/add_red")
async def add_red(data: IngredientRequest):
    ing = data.ingredient.strip().lower()
    if not ing:
        raise HTTPException(status_code=400, detail="Missing ingredient")
    try:
        append_to_csv(RED_CSV, ing)
        return {"status": "ok", "ingredient": ing, "list": "red"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore scrittura CSV: {e}")

class ProductRequest(BaseModel):
    hint: str | None = None

@app.post("/create_product")
async def create_product(data: ProductRequest):
    hint = (data.hint or "").strip()
    logging.info(f"🧪 Richiesta creazione prodotto (hint={hint})")

    try:
        context_docs = get_context_from_query_http(hint or "trend skincare green", index_type="post")
        context_str = "\n".join(doc.get("content", "") for doc in context_docs)
        logging.info(f"📚 Contesto per create_product: {len(context_docs)} documenti")
    except Exception as e:
        logging.error(f"❌ Errore recupero contesto: {e}")
        raise HTTPException(status_code=500, detail="Errore recupero contesto")

    try:
        raw_output = create_product_from_trends(context_str, hint)
        logging.info(f"📝 Output LLM (grezzo): {raw_output}")

        if isinstance(raw_output, dict) and "nome_prodotto" in raw_output:
            product = raw_output
        else:
            if isinstance(raw_output, dict) and "raw_output" in raw_output:
                text_out = raw_output["raw_output"]
            else:
                text_out = str(raw_output)

            match = re.search(r"\{[\s\S]*\}", text_out)
            if not match:
                logging.error("⚠️ Nessun blocco JSON trovato nell'output")
                raise HTTPException(status_code=500, detail="Nessun JSON trovato nell'output")
            json_str = match.group(0)

            try:
                product = json.loads(json_str)
            except json.JSONDecodeError as e:
                logging.error(f"⚠️ Errore parsing JSON: {e}\n---STRINGA CHE HA FALLITO---\n{json_str}\n--------------------------")
                raise HTTPException(status_code=500, detail=f"Errore parsing JSON: {e}")

        if "image_prompt" in product and "image_url" not in product:
            try:
                from api import generate_image, ROOT_DIR
                image_path = generate_image(product["image_prompt"], output_dir="data/product_images")
                
                filename = os.path.basename(image_path)        
                subfolder = os.path.basename(os.path.dirname(image_path))  
                product["image_url"] = f"http://localhost:8000/data/{subfolder}/{filename}"

                logging.info(f"✅ Immagine disponibile a: {product['image_url']}")

            except Exception as e:
                logging.error(f"⚠️ Errore generazione immagine: {e}")

        try:
            save_product_to_csv(product)
        except Exception as e:
            logging.error(f"⚠️ Errore salvataggio CSV prodotto: {e}")

        return product

    except Exception as e:
        logging.error(f"❌ Errore creazione prodotto: {e}")
        raise HTTPException(status_code=500, detail=str(e))
