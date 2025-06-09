# Detektor URL Phishing (Proyek CC25-CF265-SADAR)

![Deteksi Phishing](https://placehold.co/1200x300/2c3e50/ffffff?text=Phishing+URL+Detector&font=lato)

Aplikasi web dan API berbasis FastAPI yang memanfaatkan model *deep learning* (TensorFlow/Keras) untuk mengklasifikasikan sebuah URL sebagai "Aman" atau "Phishing". Proyek ini merupakan bagian dari program Coding Camp 2025, dengan fokus pada penerapan *machine learning* untuk keamanan siber.

## 📜 Daftar Isi

  - [Fitur Utama](#fitur-utama)
  - [Struktur Proyek](#struktur-proyek)
  - [Teknologi yang Digunakan](#teknologi-yang-digunakan)
  - [Setup dan Instalasi Lokal](#setup-dan-instalasi-lokal)
  - [Menjalankan Aplikasi](#menjalankan-aplikasi)
  - [Endpoint API](#endpoint-api)
  - [Alur Kerja Machine Learning](#alur-kerja-machine-learning)
  - [Deployment](#deployment)

## ✨ Fitur Utama

  - **Prediksi Real-time**: Menyediakan antarmuka web sederhana untuk analisis URL tunggal secara langsung.
  - **API Endpoint**: Endpoint RESTful (`/api/predict`) tersedia untuk integrasi dengan sistem atau aplikasi lain.
  - **Penanganan URL Shortener**: Mampu mengikuti pengalihan dari URL *shortener* untuk menganalisis URL tujuan yang sebenarnya, meningkatkan akurasi deteksi.
  - **Ekstraksi Fitur Komprehensif**: Menggunakan lebih dari 20 fitur yang diekstrak dari URL, termasuk fitur leksikal, berbasis domain, dan berbasis konten HTML.
  - **Siap Deployment**: Dikonfigurasi untuk deployment ke platform cloud modern seperti Vercel atau Railway menggunakan `Dockerfile`.
  - **Dokumentasi Otomatis**: Dilengkapi dokumentasi API interaktif yang dibuat secara otomatis oleh FastAPI (tersedia di `/docs`).

## 📁 Struktur Proyek

Proyek ini mengikuti struktur modular agar mudah dipelihara dan dikembangkan lebih lanjut.

```plaintext
Phishing-Detection/
├── data/                  # Dataset mentah, hasil preprocessing, dan notebook eksplorasi
├── models_trained/        # Model deep learning (.h5) yang sudah dilatih
├── notebooks/             # Jupyter Notebook untuk eksperimen dan analisis data
├── reports/               # Laporan, grafik evaluasi, dan dokumentasi visual
├── src/                   # Kode sumber utama
│   ├── etl/               # Pipeline ETL: ekstraksi, transformasi, dan pemuatan data
│   ├── features/          # Logika ekstraksi fitur dari URL (termasuk shortener)
│   ├── models/            # Skrip training, evaluasi, dan tuning model
│   ├── utils/             # Fungsi pembantu: konfigurasi, logging, validasi input
│   └── visualization/     # Pembuatan plot dan visualisasi
├── tests/                 # Unit test dan integrasi
├── main.py                # Entry point aplikasi FastAPI
├── requirements.txt       # Daftar dependensi Python
├── Dockerfile             # Konfigurasi Docker untuk containerization
└── vercel.json            # Konfigurasi deployment ke Vercel (opsional)
```
## 🚀 Teknologi yang Digunakan

Proyek ini memanfaatkan berbagai pustaka dan alat modern untuk mendukung pengembangan aplikasi deteksi phishing berbasis machine learning.

- **Bahasa Pemrograman**:
  - Python 3.11+

- **Framework & Server**:
  - FastAPI — untuk membangun REST API
  - Uvicorn / Gunicorn — server ASGI untuk menjalankan aplikasi

- **Machine Learning & Deep Learning**:
  - TensorFlow (Keras) — pelatihan dan inferensi model neural network
  - scikit-learn — preprocessing dan evaluasi
  - NumPy & Pandas — manipulasi data

- **Web Scraping & Analisis URL**:
  - `requests` — untuk mengambil konten HTML
  - `beautifulsoup4` — parsing HTML
  - `tldextract`, `urllib`, `socket` — untuk ekstraksi dan analisis struktur URL

- **Deployment**:
  - Docker — containerization untuk deployment lintas platform
  - Vercel — deployment serverless (opsional)
  - Railway — platform deployment berbasis Docker (opsional)

- **Tools Lain**:
  - Jupyter Notebook — eksplorasi data dan eksperimen model
  - Git — versi kontrol

## ⚙️ Setup dan Instalasi Lokal

Untuk menjalankan aplikasi ini di lingkungan lokal, ikuti langkah-langkah berikut:

### 1. Prasyarat

Pastikan Anda sudah menginstal perangkat lunak berikut di komputer Anda:

- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- (Opsional) [Docker Desktop](https://www.docker.com/products/docker-desktop) — untuk menjalankan aplikasi dalam container

### 2. Kloning Repositori

Langkah pertama adalah menyalin (clone) repositori ini ke komputer lokal Anda menggunakan Git.

```bash
git clone https://github.com/CC25-CF265-SADAR/Phishing-Detection.git
cd Phishing-Detection
```

### 3. Buat dan Aktifkan Virtual Environment

Disarankan untuk menggunakan virtual environment agar dependensi proyek terisolasi dari sistem utama.

```bash
# Membuat virtual environment
python -m venv venv

# Mengaktifkan virtual environment
# Jika Anda menggunakan Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Jika Anda menggunakan macOS/Linux
source venv/bin/activate
```

### 4. Instalasi Dependensi

Setelah virtual environment aktif, instal semua pustaka yang dibutuhkan oleh proyek:

```bash
pip install -r requirements.txt
```

## ▶️ Menjalankan Aplikasi

### Menjalankan Secara Lokal (Development)

Gunakan Uvicorn untuk menjalankan server FastAPI dari direktori root proyek:

```bash
uvicorn main:app --reload --port 8000
```

Penjelasan:

- `--reload`: Server akan otomatis me-restart setiap kali ada perubahan pada kode. Sangat berguna saat proses pengembangan.

Setelah server berjalan, Anda dapat mengakses aplikasi melalui browser:

- **Antarmuka Web**: [http://localhost:8000/](http://localhost:8000/)
- **Dokumentasi API (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)


### Menjalankan dengan Docker (Simulasi Produksi)

Jika Anda memiliki Docker Desktop, Anda dapat menjalankan aplikasi dalam container menggunakan langkah berikut:

1. **Bangun image Docker dari Dockerfile:**

```bash
docker build -t phishing-detector-app .
```

2. **Jalankan container dari image yang telah dibangun:**

```bash
docker run -p 8000:8000 --env PORT=8000 phishing-detector-app
```

Setelah container berjalan, aplikasi dapat diakses melalui:

- **Antarmuka Web**: [http://localhost:8000/](http://localhost:8000/)
- **Dokumentasi API (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🔌 Endpoint API

Aplikasi menyediakan endpoint utama untuk melakukan prediksi URL phishing melalui metode POST.

### 📍 Endpoint

- **URL**: `/api/predict`
- **Metode**: `POST`
- **Content-Type**: `application/json`

### 🔸 Contoh Request Body

```json
{
  "url": "https://contoh.com"
}
```

### 🔸 Contoh Permintaan menggunakan curl
```bash
curl -X POST "http://localhost:8000/api/predict" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://contoh.com"}'
```

### 🔸 Contoh Respons Berhasil
```json
{
  "url": "https://contoh.com",
  "predicted_type": "Aman",
  "phishing_probability": 0.0123,
  "error": null
}
```
> Catatan: Nilai phishing_probability menunjukkan kemungkinan bahwa URL tersebut adalah phishing (semakin mendekati 1, semakin berisiko).

## 🤖 Alur Kerja Machine Learning

Proses pengembangan model deteksi phishing dalam proyek ini mengikuti alur berikut:

1. **Pengumpulan Data**  
   Dataset URL phishing dan URL aman dikumpulkan dari berbagai sumber terpercaya, lalu disimpan dalam direktori `data/raw/`.

2. **Eksplorasi dan Pra-pemrosesan**  
   Data dianalisis dan dibersihkan menggunakan notebook di `notebooks/`, serta skrip ETL di `src/etl/`.

3. **Ekstraksi Fitur**  
   Setiap URL dianalisis menggunakan berbagai teknik untuk menghasilkan lebih dari 20 fitur. Ekstraksi dilakukan dengan modul di `src/features/`.

   Fitur-fitur yang digunakan dalam model antara lain:

   - `IP_Address`
   - `URL_Length`
   - `URL_Shortening`
   - `Double_Slash_Redirect_After_HTTPS`
   - `Hyphen_in_Domain_Name`
   - `Presence_of_Subdomain`
   - `Uses_HTTPS_Protocol`
   - `Favicon_Source_Consistency`
   - `Custom_Port_Usage`
   - `External_Resource_Ratio`
   - `External_Links_Ratio`
   - `External_CSS_and_JS_Resources`
   - `External_Form_Submission`
   - `Form_Submits_to_Email_Address`
   - `HTTP_Response_Status_Content`
   - `Number_of_Redirects`
   - `Mouseover_Link_Manipulation`
   - `Right_Click_Disabled`
   - `Popup_Window_Usage`
   - `Iframe_Usage`
   - `URL_Blacklist_Status`

4. **Pelatihan Model**  
   Model *deep learning* dibangun menggunakan TensorFlow/Keras dan dilatih melalui `src/models/train_model.py`.  
   Eksperimen dilakukan di `notebooks/models_playground.ipynb`.

5. **Evaluasi Model**  
   Model dievaluasi menggunakan metrik:
   - **Akurasi**
   - **Precision**
   - **Recall** (fokus utama untuk mengurangi false negatives)
   - **F1-score**

6. **Penyimpanan Model**  
   Model terbaik disimpan dalam format `.h5` di `models_trained/` dan di-load secara otomatis oleh aplikasi saat prediksi dilakukan melalui API.
## 🚀 Deployment

Aplikasi ini telah dikonfigurasi agar dapat dideploy ke berbagai platform modern menggunakan pendekatan container atau serverless.

### 🔧 Railway

- Aplikasi dapat dijalankan di [Railway](https://railway.app/) menggunakan Docker.
- Railway akan secara otomatis:
  - Mendeteksi `Dockerfile`
  - Membangun image
  - Menyediakan endpoint publik untuk aplikasi Anda

### ⚙️ Vercel (Opsional)

- Aplikasi juga dapat dijalankan di [Vercel](https://vercel.com/) dengan konfigurasi `vercel.json`.
- Pastikan Anda menggunakan `@vercel/python` sebagai builder untuk proyek FastAPI.
- File `vercel.json` telah disiapkan untuk memetakan handler ke `main.py`.

### 📁 Berkas yang Wajib Ada untuk Deployment

Pastikan semua berkas berikut tersedia di root repositori:

- `main.py`
- `requirements.txt`
- `Dockerfile` (untuk Railway)
- `vercel.json` (untuk Vercel, opsional)
- Folder `src/` (berisi seluruh kode sumber)
- Folder `models_trained/` (berisi model `.h5`)

---

Setelah deployment, aplikasi akan tersedia secara publik dengan endpoint seperti:
> https://phishing-detector-production.up.railway.app/

> https://phishing-detector.vercel.app/

(Alamat bergantung pada konfigurasi dan nama proyek Anda di platform terkait.)
