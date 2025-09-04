#api.py

import os
import json
import csv
import re
from datetime import datetime
import requests
import logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from PIL import Image
from io import BytesIO
from together import Together

# Carica variabili ambiente
load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY_MIA")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not FIREWORKS_API_KEY or not TOGETHER_API_KEY:
    raise ValueError("❌ FIREWORKS_API_KEY o TOGETHER_API_KEY non trovata")

client = Together(api_key=TOGETHER_API_KEY)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Traduzione ---
def translate(text: str, target_language: str) -> str:
    logging.info(f"🌐 Traduzione in {target_language}")
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {"Authorization": f"Bearer {FIREWORKS_API_KEY}", "Content-Type": "application/json"}
    
    # Prompt aggiornato per rispondere solo con il testo tradotto senza spiegazioni
    prompt = f"Translate the following text to {target_language}. Return ONLY the translated text, no explanations or introductory phrases:\n\n{text}"
    
    payload = {
        "model": "accounts/fireworks/models/llama4-scout-instruct-basic",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code == 200:
        return resp.json()['choices'][0]['message']['content'].strip()
    else:
        raise RuntimeError(f"API Fireworks error (translation): {resp.status_code}")

# --- Generazione contenuti ---
@retry(stop=stop_after_attempt(3), wait=wait_fixed(10), retry=retry_if_exception_type(RuntimeError))
def call_fireworks(question: str, context: str, platform: str = "Instagram") -> str:
    platform = platform.capitalize()  # Assicura che sia 'Instagram' o 'Twitter' con iniziale maiuscola
    logging.info(f"✍️ Generazione contenuto con Fireworks per piattaforma: {platform}")
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {"Authorization": f"Bearer {FIREWORKS_API_KEY}", "Content-Type": "application/json"}

    instagram_extra = """
For Instagram:
- Add engaging call-to-actions (e.g., "✨ Save this post!", "💬 Tell us your thoughts below!", "➡️ Swipe for more!")
- Use a visually descriptive tone to inspire image creation.
- Include a concise suggestion for the image prompt at the end in brackets, e.g., [Image prompt: ...].
""" if platform.lower() == "instagram" else ""

    twitter_extra = """
For Twitter:
- The entire tweet (including hashtags) MUST fit within 280 characters.
- Write in a short, fresh, engaging tone.
- Include 2–4 relevant hashtags at the end.
- Include any hashtags that appear in the provided context documents verbatim.
- Avoid long sentences or detailed descriptions.
- The post MUST NOT end with incomplete sentences or trailing ellipsis ("..."). If needed, shorten or rephrase to ensure a clean ending.
""" if platform.lower() == "twitter" else ""

    prompt = f"""
You are a professional AI assistant for social media content creation.

🧠 Brand Voice Guidelines:
- Use a consistent and engaging tone aligned with sustainability and real brand values.
- Avoid exaggerations or vague marketing phrases.

📄 Brand Materials and Context:
{context}

📌 User Request:
"{question}"

📎 Constraints:
- Base the post primarily on the information and language used in the context above.
- Include only hashtags found verbatim in the context documents if any exist.
- If no hashtags are found, you may add relevant and coherent hashtags related to the topic and brand.
- Do NOT invent or include unrelated or unsupported ideas or hashtags.
- Do NOT include any URLs, links, or references to websites in the post.
- Ensure the post is natural, human-like, and engaging.
- Please ensure the post ends with a complete sentence and NO trailing ellipsis ("...").
- Please do NOT end with ellipsis or incomplete sentences. End with a full, clear sentence.

🎯 Task:
Based on the materials and request above, generate a complete and engaging **social media post** tailored for **{platform}**.
{instagram_extra}{twitter_extra}

Your response should include:
- ✅ Only the final post (no titles, no explanations)
- ✅ Written as it would appear on the platform
- ✅ Keep it within the format and tone expected for {platform}

Return only the post text, nothing else.
"""

    max_tokens = 150 if platform == "Instagram" else 120
    temperature = 0.6 if platform == "Instagram" else 0.5

    payload = {
        "model": "accounts/fireworks/models/llama4-scout-instruct-basic",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
        # Se Fireworks supporta, prova a usare 'stop' per fermare generazione su '...' o newline
        "stop": ["...", "\n"]
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code == 200:
        text = resp.json()['choices'][0]['message']['content'].strip()

        # Pulizia finale: rimuovi eventuali puntini sospensivi alla fine
        while text.endswith("...") or text.endswith("…"):
            text = text[:-3].rstrip()

        # Assicura che il testo finisca con un punto, punto esclamativo o domanda
        if not text.endswith((".", "!", "?")):
            text += "."

        return text
    elif resp.status_code == 429:
        logging.warning("⚠️ Rate limit Fireworks raggiunto, retry in corso...")
        raise RuntimeError("Rate limit Fireworks")
    else:
        raise RuntimeError(f"API Fireworks error: {resp.status_code}")

# --- Generazione immagine ---
def generate_image(prompt: str, output_dir: str = "data/images", output_filename: str = None) -> str:
    logging.info(f"🖼️ Chiamata generate_image con prompt: {prompt}")
    abs_output_dir = os.path.join(ROOT_DIR, output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)

    if not output_filename:
        output_filename = f"generated_image_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.png"
    output_path = os.path.join(abs_output_dir, output_filename)

    response = client.images.generate(
        prompt=prompt,
        model="black-forest-labs/FLUX.1-schnell-Free",
        steps=3,
        n=1
    )

    if not response.data or not hasattr(response.data[0], 'url'):
        raise RuntimeError("Risposta API Together senza dati immagine")

    image_url = response.data[0].url
    image_resp = requests.get(image_url)
    if image_resp.status_code != 200:
        raise RuntimeError("Errore download immagine")

    image = Image.open(BytesIO(image_resp.content))
    image.save(output_path)
    logging.info(f"✅ Immagine salvata: {output_path}")
    return output_path

@retry(stop=stop_after_attempt(3), wait=wait_fixed(10), retry=retry_if_exception_type(RuntimeError))
def create_product_from_trends(context: str, hint: str = "") -> dict:
    logging.info("🧪 Creazione nuovo prodotto basato su trend...")

    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {"Authorization": f"Bearer {FIREWORKS_API_KEY}", "Content-Type": "application/json"}

    prompt = f"""
Sei un esperto sviluppatore di prodotti nel settore skincare.

Analizza i seguenti trend e opinioni recenti:
{context}

Suggerimento utente (opzionale): {hint}

🎯 Obiettivo:
- Proponi un prodotto innovativo e sostenibile basato su questi trend.
- Il prodotto deve appartenere a UNA di queste categorie:
  • Shampoo
  • Bagnoschiuma / Docciaschiuma
  • Crema solare
  • Crema viso o corpo
- Indica contenitore coerente (es: flacone per shampoo/doccia, tubetto per crema solare, vasetto per crema viso/corpo).
- Includi: nome prodotto, descrizione marketing breve, ingredienti chiave, aspetti sostenibilità.
- Testo in Italiano, realistico e specifico (non generico).
- Alla fine includi UN solo prompt per immagine frontale del prodotto (senza retro etichetta).

Formato risposta in JSON, ad esempio:
{{
  "nome_prodotto": "...",
  "descrizione": "...",
  "categoria": "shampoo | bagnoschiuma | crema solare | crema viso",
  "ingredienti": ["...", "..."],
  "note_sostenibilita": "...",
  "image_prompt": "prodotto visto frontalmente, dettagli realistici"
}}
"""

    payload = {
        "model": "accounts/fireworks/models/llama4-scout-instruct-basic",
        "max_tokens": 512,
        "temperature": 0.6,
        "messages": [{"role": "user", "content": prompt}]
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code != 200:
        raise RuntimeError(f"API Fireworks error: {resp.status_code}")

    content = resp.json()['choices'][0]['message']['content'].strip()
    logging.info(f"📝 Output LLM: {content}")

    try:
        product_data = json.loads(content)
    except Exception as e:
        logging.error(f"⚠️ Output non JSON: {e}")
        product_data = {"raw_output": content}
        return product_data

    # genera immagine frontale (unica immagine)
    if "image_prompt" in product_data:
        try:
            img_path = generate_image(product_data["image_prompt"], output_dir="data/product_images")
            product_data["image_url"] = "/" + os.path.relpath(img_path, ROOT_DIR).replace(os.sep, "/")
        except Exception as e:
            logging.error(f"⚠️ Errore generazione immagine: {e}")

    return product_data

PRODUCTS_CSV = os.path.join(ROOT_DIR, "data", "products_history.csv")

def save_product_to_csv(product: dict, csv_path: str = PRODUCTS_CSV):
    # Assicura cartella
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Normalizza i campi
    nome = product.get("nome_prodotto", "")
    descrizione = product.get("descrizione", "")
    ingredienti = ", ".join(product.get("ingredienti", []))
    sostenibilita = product.get("note_sostenibilita", "")
    image_url = product.get("image_url", "")
    timestamp = datetime.utcnow().isoformat()

    # Scrive o aggiunge al CSV
    write_header = not os.path.exists(csv_path)
    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp",
                "nome_prodotto",
                "descrizione",
                "ingredienti",
                "note_sostenibilita",
                "image_url"
            ])
        writer.writerow([
            timestamp,
            nome,
            descrizione,
            ingredienti,
            sostenibilita,
            image_url
        ])

    logging.info(f"💾 Prodotto salvato in CSV: {csv_path}")

# --- Controllo INCI ---
@retry(stop=stop_after_attempt(3), wait=wait_fixed(10), retry=retry_if_exception_type(RuntimeError))
def call_fireworks_for_ingredient(ingredient: str) -> str:
    logging.info(f"🔎 Verifica ingrediente con Fireworks: {ingredient}")
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {"Authorization": f"Bearer {FIREWORKS_API_KEY}", "Content-Type": "application/json"}

    prompt = f"""
You are an AI assistant specialized in cosmetic ingredient analysis.

Ingredient: "{ingredient}"

Question: Is this ingredient harmful, sustainable, or neutral in cosmetic products? Please answer briefly and clearly.
"""

    payload = {
        "model": "accounts/fireworks/models/llama4-scout-instruct-basic",
        "max_tokens": 50,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}]
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code == 200:
        return resp.json()['choices'][0]['message']['content'].strip().lower()
    else:
        raise RuntimeError(f"API Fireworks error: {resp.status_code}")

# --- Salvataggio CSV ---
def save_to_csv(question: str, answer: str, csv_path: str):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    current_id = 1
    if os.path.exists(csv_path):
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                ids = [int(row["id_q"]) for row in reader if row["id_q"].isdigit()]
                current_id = max(ids) + 1 if ids else 1
        except Exception:
            current_id = 1

    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if current_id == 1 and f.tell() == 0:
            writer.writerow(["id_q", "question", "answer"])
        writer.writerow([current_id, question, answer])


