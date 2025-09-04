# api/Dockerfile
FROM python:3.11

# Imposta la working directory
WORKDIR /app

# Evita warning di pip e disabilita cache
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

# Installa git (non serve build-essential perché nessuna libreria da compilare)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements per caching Docker
COPY requirements.txt .

# Aggiorna pip e installa dipendenze Python
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copia tutto il codice dell'API
COPY . .

# Espone porta API
EXPOSE 8000

# Comando per avviare l'API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

