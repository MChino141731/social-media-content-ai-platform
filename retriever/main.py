import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import re
import numpy as np
import csv
import datetime
from scipy.spatial.distance import cosine

# =====================================
# LOGGING & ENV CONFIGURATION
# =====================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
load_dotenv()

# =====================================
# PATHS
# =====================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Cartella centralizzata per log e CSV
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

CONTEXT_LOG_PATH = os.path.join(LOG_DIR, "context_log.csv")
DEBUG_CHUNKS_PATH = os.path.join(LOG_DIR, "debug_chunks.txt")
SEARCH_LOG_PATH = os.path.join(LOG_DIR, "log.txt")

def getenv_path(env_var, root_dir, default):
    val = os.getenv(env_var)
    if val:
        return os.path.abspath(os.path.join(root_dir, val)) if not os.path.isabs(val) else val
    return default

INDEX_PATHS = {
    "post": getenv_path("INDEX_PATH_POST", ROOT_DIR, os.path.join(DATA_DIR, "faiss_index_post")),
}

FILE_METADATA_POST = {
    getenv_path("TWEETS_ESG", ROOT_DIR, os.path.join(DATA_DIR, "tweets_ESG.txt")): "tweet_ESG",
    getenv_path("TWEETS_GREEN", ROOT_DIR, os.path.join(DATA_DIR, "tweets_green.txt")): "tweet_green",
    getenv_path("BRAND_VOICE", ROOT_DIR, os.path.join(DATA_DIR, "linee_guida_brand_tone.txt")): "brand_voice",
    getenv_path("INCI_GREEN", ROOT_DIR, os.path.join(DATA_DIR, "inci_sostenibile.txt")): "inci_green",
    getenv_path("INCI_AVOID", ROOT_DIR, os.path.join(DATA_DIR, "inci_dannoso.txt")): "inci_avoid",
}

# =====================================
# DOCUMENT PARSING FUNCTIONS
# =====================================
def parse_tweet_blocks(file_path, category):
    if not os.path.isfile(file_path):
        logger.error(f"❌ File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"📄 Reading file: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        raw_text = f.read()

    blocks = raw_text.split('---')
    documents = []
    seen_ids = set()

    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue

        tweet_text = ""
        metadata = {"source": os.path.basename(file_path), "category": category}
        tweet_id = None

        for line in lines:
            line = line.strip()
            if line.startswith("ID:"):
                tweet_id = line[len("ID:"):].strip()
                metadata["id"] = tweet_id
            elif line.startswith("Text:"):
                tweet_text = line[len("Text:"):].strip()
            elif re.match(r"(?i)^Sentiment:", line):
                metadata["sentiment"] = line.split(":", 1)[1].strip()
            elif re.match(r"(?i)^Confidence:", line):
                try:
                    metadata["confidence"] = float(line.split(":", 1)[1].strip())
                except:
                    metadata["confidence"] = None

        if tweet_id and tweet_id in seen_ids:
            logger.debug(f"🔁 Duplicate document with ID {tweet_id}, skipped.")
            continue

        if tweet_text:
            documents.append(Document(page_content=tweet_text, metadata=metadata))
            if tweet_id:
                seen_ids.add(tweet_id)

    logger.info(f"📄 Parsed {len(documents)} tweet documents from {file_path}")
    return documents

def load_documents_from_files(files_map: dict) -> List[Document]:
    docs = []
    for filepath, metadata_key in files_map.items():
        if not os.path.isfile(filepath):
            logger.warning(f"⚠️ File not found, skipping: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read().strip()
        if not raw_text:
            logger.warning(f"⚠️ Empty file, skipping: {filepath}")
            continue

        logger.info(f"📂 Loading file {filepath} as {metadata_key}")

        if metadata_key in ["tweet_ESG", "tweet_green"]:
            parsed = parse_tweet_blocks(filepath, metadata_key)
            docs.extend(parsed)
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ".", "!", "?", " "]
            )
            chunks = splitter.split_text(raw_text)
            for chunk in chunks:
                docs.append(Document(page_content=chunk, metadata={"source": metadata_key, "category": metadata_key}))

    logger.info(f"📚 Total documents loaded: {len(docs)}")
    return docs

# =====================================
# VECTORSTORE
# =====================================
def get_vectorstore(docs: List[Document], index_path: str):
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if not os.path.exists(index_path):
        logger.info("🧐 Creating new FAISS index")
        vectorstore = FAISS.from_documents(docs, embedding)
        vectorstore.save_local(index_path)
        logger.info(f"💾 FAISS index saved at {index_path}")
    else:
        logger.info("📂 Loading existing FAISS index")
        vectorstore = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True)
        logger.info(f"✅ FAISS index loaded from {index_path}")
    return vectorstore

# =====================================
# CONTEXT SELECTION
# =====================================
def get_context_stratified(
    vectorstore,
    query: str,
    k: int = 5,
    search_k: int = 50,
    allowed_categories: list = None,
) -> dict:
    results = vectorstore.similarity_search(query, k=search_k)
    logger.info(f"🔍 Found {len(results)} initial documents for query: '{query}'")

    results.sort(key=lambda d: float(d.metadata.get("confidence") or 0), reverse=True)

    def filter_by_sentiment_confidence(sentiment: str, min_conf: float):
        return [
            doc for doc in results
            if doc.metadata.get("sentiment", "").lower() == sentiment.lower()
            and float(doc.metadata.get("confidence") or 0) >= min_conf
            and (allowed_categories is None or doc.metadata.get("category") in allowed_categories)
        ]

    positives = filter_by_sentiment_confidence("positive", 0.8)
    if len(positives) < 20:
        positives = filter_by_sentiment_confidence("positive", 0.6)

    def get_embedding(text):
        return vectorstore.embedding_function.embed_query(text)

    query_embedding = get_embedding(query)

    def similarity(doc):
        doc_embedding = get_embedding(doc.page_content)
        return 1 - cosine(query_embedding, doc_embedding)  # usa scipy cosine

    positives.sort(key=similarity, reverse=True)
    selected = positives[:k]

    if len(selected) < k:
        remaining = k - len(selected)
        neutrals = filter_by_sentiment_confidence("neutral", 0.5)
        neutrals.sort(key=similarity, reverse=True)
        selected += neutrals[:remaining]

    if len(selected) < k:
        remaining = k - len(selected)
        unknowns = [
            doc for doc in results
            if doc.metadata.get("sentiment", "").lower() not in ("positive", "neutral")
            and (allowed_categories is None or doc.metadata.get("category") in allowed_categories)
        ]
        unknowns.sort(key=similarity, reverse=True)
        selected += unknowns[:remaining]

    selected = selected[:k]

    final = []
    for doc in selected:
        final.append({
            "content": doc.page_content.strip(),
            "source": doc.metadata.get("source", "unknown"),
            "category": doc.metadata.get("category", "unknown"),
            "id": doc.metadata.get("id"),
            "sentiment": doc.metadata.get("sentiment", "unknown"),
            "confidence": float(doc.metadata.get("confidence") or 0),
        })

    logger.info(f"✅ Filtered and selected documents: {len(final)}")

    # 📁 Logging to CSV
    with open(CONTEXT_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "query", "id", "category", "sentiment", "confidence", "content"])
        if f.tell() == 0:
            writer.writeheader()
        for doc in final:
            writer.writerow({
                "timestamp": datetime.datetime.now().isoformat(),
                "query": query,
                "id": doc["id"],
                "category": doc["category"],
                "sentiment": doc["sentiment"],
                "confidence": doc["confidence"],
                "content": doc["content"]
            })

    return {"filtered": final}

# =====================================
# DOCUMENT LOADING & VECTORSTORE INIT
# =====================================
docs_post = load_documents_from_files(FILE_METADATA_POST)

with open(DEBUG_CHUNKS_PATH, "w", encoding="utf-8") as out:
    for i, doc in enumerate(docs_post):
        out.write(f"\n--- CHUNK #{i+1} ---\n")
        out.write(f"Content: {doc.page_content}\n")
        out.write("Metadata:\n")
        for k, v in doc.metadata.items():
            out.write(f"  {k}: {v}\n")

vs_post = get_vectorstore(docs_post, index_path=INDEX_PATHS["post"])
logger.info(f"✅ Vectorstore 'post/nuovo_prodotto' loaded with {len(docs_post)} documents.")

vectorstores = {
    "post": vs_post,
    "nuovo_prodotto": vs_post,
}

# =====================================
# FASTAPI SETUP
# =====================================
app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    index_type: str
    sentiment: str = "positive"
    categories: List[str] = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search")
def search(data: QueryRequest):
    logger.info(f"🔎 Received search request - query: '{data.query}', index_type: '{data.index_type}', categories: {data.categories}")
    
    if data.index_type not in vectorstores:
        error_msg = f"Index_type '{data.index_type}' is invalid. Use one of: {list(vectorstores.keys())}"
        logger.error(error_msg)
        return {"error": error_msg}

    vectorstore = vectorstores[data.index_type]

    # Detect intent to include brand voice
    query_lower = data.query.lower()
    auto_include_brand = any(keyword in query_lower for keyword in [
        "brand", "tone", "voice", "guidelines", "our", "promote"
    ])

    all_categories = {"tweet_ESG", "tweet_green", "brand_voice", "inci_green", "inci_avoid"}

    if data.categories:
        allowed_categories = data.categories.copy()
    else:
        allowed_categories = ["tweet_ESG", "tweet_green"]
        if auto_include_brand:
            allowed_categories.append("brand_voice")
            logger.info("📌 'brand_voice' automatically added based on query intent.")

    logger.info(f"Category filter applied: {allowed_categories}")

    result = get_context_stratified(
        vectorstore=vectorstore,
        query=data.query,
        allowed_categories=allowed_categories,
        k=5,
        search_k=20
    )

    filtered_contexts = result.get("filtered", [])
    logger.info(f"Filtered results: {len(filtered_contexts)} documents")

    with open(SEARCH_LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n=== New Search Request ===\n")
        f.write(f"Query: {data.query}\n")
        f.write(f"Index_type: {data.index_type}\n")
        f.write(f"Category filter: {allowed_categories}\n")
        f.write(f"Returned documents: {len(filtered_contexts)}\n")
        seen_ids = set()
        for ctx in filtered_contexts:
            doc_id = ctx.get('id')
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            f.write(f"ID: {doc_id}\n")
            f.write(f"Category: {ctx.get('category')}\n")
            f.write(f"Sentiment: {ctx.get('sentiment')}\n")
            f.write(f"Confidence: {ctx.get('confidence')}\n")
            f.write("Content:\n")
            f.write(ctx.get('content', '') + "\n")
            f.write("-" * 80 + "\n")
    
    return {"results": filtered_contexts}

# =====================================
# MAIN ENTRYPOINT
# =====================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True)
