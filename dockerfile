# Dockerfile

# 1. Gunakan image dasar Python resmi.
# Pilih versi Python yang sesuai dengan proyek Anda (misalnya, 3.10, 3.11).
# Versi -slim lebih kecil.
FROM python:3.11-slim

# 2. Tetapkan variabel lingkungan (opsional tapi praktik baik)
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

# 3. Buat direktori kerja di dalam image
WORKDIR ${APP_HOME}

# 4. Salin file requirements terlebih dahulu dan instal dependensi
# Ini memanfaatkan caching layer Docker: jika requirements.txt tidak berubah,
# layer ini tidak akan dibangun ulang, mempercepat build berikutnya.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 5. Salin seluruh kode aplikasi Anda ke direktori kerja
# Ini termasuk main.py, folder src/, folder models_trained/, dll.
COPY . .

# 6. Memberitahu Docker bahwa aplikasi akan berjalan di port yang ditentukan oleh Railway
# Railway akan menyuntikkan variabel $PORT. Uvicorn/Gunicorn akan menggunakan ini.
# EXPOSE 8000 # Port default Uvicorn jika $PORT tidak diset

# 7. Perintah untuk menjalankan aplikasi saat kontainer dimulai.
# Ini mirip dengan perintah di Procfile.
# Kita akan menggunakan Gunicorn untuk menjalankan worker Uvicorn.
# Railway akan menyediakan variabel $PORT.
CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind "0.0.0.0:${PORT:-8000}" --timeout 120