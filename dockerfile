# Dockerfile

# 1. Gunakan image dasar Python resmi.
FROM python:3.11-slim

# 2. Tetapkan variabel lingkungan
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

# 3. Buat direktori kerja di dalam image
WORKDIR ${APP_HOME}

# 4. Salin file requirements terlebih dahulu dan instal dependensi
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 5. Salin seluruh kode aplikasi ke direktori kerja
# Ini termasuk main.py, folder src/, folder models_trained/, dll.
COPY . .


# 7. Perintah untuk menjalankan aplikasi saat kontainer dimulai.
CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind "0.0.0.0:${PORT:-8000}" --timeout 120