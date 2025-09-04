# inci_utils.py

import os
import re
import csv
import logging
from datetime import datetime
from api import call_fireworks_for_ingredient
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Percorsi CSV presi dagli env, con fallback
GREEN_CSV = os.getenv("GREEN_CSV", os.path.join(ROOT_DIR, "data", "inci_green.csv"))
RED_CSV   = os.getenv("RED_CSV",   os.path.join(ROOT_DIR, "data", "inci_red.csv"))

# ✅ Funzione per caricare un CSV in un set
def load_csv_to_set(path):
    s = set()
    if not os.path.exists(path):
        return s
    with open(path, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip().lower() != "ingrediente":
                s.add(row[0].strip().lower())
    return s

# ✅ Funzione per aggiungere un ingrediente a un CSV
def append_to_csv(path, ingredient):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ingredient.strip().lower()])

# ✅ Salva risultati in CSV
def save_inci_check(ingredienti, risultati, csv_path=os.path.join(ROOT_DIR, "data", "inci_checks.csv")):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    timestamp = datetime.utcnow().isoformat()
    ingredienti_str = "; ".join(ingredienti)
    risultati_str = "; ".join([f"{r['ingrediente']}:{r['status']}" for r in risultati])
    file_exists = os.path.exists(csv_path)
    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "ingredienti", "risultati"])
        writer.writerow([timestamp, ingredienti_str, risultati_str])

# ✅ Pipeline principale con CSV e LLM
def check_ingredients_pipeline(query: str):
    # Carico i dizionari (ogni chiamata ricarica dai CSV per avere la lista aggiornata)
    SET_GREEN = load_csv_to_set(GREEN_CSV)
    SET_RED   = load_csv_to_set(RED_CSV)

    # Parsing ingredienti
    ingredients = [i.strip().lower() for i in re.split(r"[,\n;]+|\s{2,}", query) if i.strip()]
    if not ingredients:
        return {"error": "Empty ingredient list"}

    results = []
    llm_cache = {}

    for ing in ingredients:
        # ✅ Primo check sui CSV
        if ing in SET_GREEN:
            results.append({
                "ingrediente": ing,
                "status": "sustainable",
                "source": "dict"
            })
            continue
        if ing in SET_RED:
            results.append({
                "ingrediente": ing,
                "status": "harmful",
                "source": "dict"
            })
            continue

        # ✅ Nessun match locale → controlla cache LLM
        if ing in llm_cache:
            status = llm_cache[ing]
            results.append({
                "ingrediente": ing,
                "status": status,
                "source": "llm"
            })
            continue

        # ✅ Chiamata a LLM (Fireworks)
        try:
            llm_resp = call_fireworks_for_ingredient(ing).lower()
            if any(term in llm_resp for term in ["harmful", "avoid", "toxic"]):
                status = "harmful"
            elif any(term in llm_resp for term in ["sustainable", "natural", "green", "vegetable"]):
                status = "sustainable"
            else:
                status = "neutral"
        except Exception as e:
            logging.error(f"❌ LLM error '{ing}': {e}")
            status = "not_found"

        llm_cache[ing] = status
        results.append({
            "ingrediente": ing,
            "status": status,
            "source": "llm"
        })

    # ✅ Salvataggio CSV dei risultati
    try:
        save_inci_check(ingredients, results)
    except Exception as e:
        logging.error(f"❌ Errore salvataggio INCI: {e}")

    return {"results": results}
