# retriever/Dockerfile
FROM python:3.11

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

# Aggiorna apt e installa git
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements.txt
COPY requirements.txt .

# Installa pip, wheel e PyTorch CPU prima delle altre dipendenze
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir torch==2.3.1+cpu -f https://download.pytorch.org/whl/torch_stable.html \
    && pip install --no-cache-dir -r requirements.txt

# Copia tutto il codice dell'app
COPY . .

# Espone la porta dell'app
EXPOSE 9000

# Comando di avvio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]

