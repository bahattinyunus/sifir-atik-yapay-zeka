# Sıfır Atık YZ - FastAPI Backend & Dashboard Konteyneri
FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları (OpenCV ve derleme araçları için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kur
COPY arayuz/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Proje kaynak kodlarını kopyala
COPY arayuz /app/arayuz
COPY yapay-zeka /app/yapay-zeka
COPY gomulu-yazilim /app/gomulu-yazilim

WORKDIR /app/arayuz/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
