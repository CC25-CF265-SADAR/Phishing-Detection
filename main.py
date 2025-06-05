# main.py

import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Any, List, Dict # <--- TAMBAHKAN Dict DI SINI

import numpy as np

# import pandas as pd # Hanya jika 'extract_features' Anda membutuhkannya secara internal

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl # Untuk validasi URL input

# --- 1. Pengaturan Path dan Impor Modul Internal ---

# Asumsi main.py ada di root proyek (sejajar dengan folder 'src')
project_root_path = Path(__file__).resolve().parent
if str(project_root_path) not in sys.path:
    sys.path.append(str(project_root_path))  # <--- TAMBAHKAN INDENTASI (4 spasi)
    # Pesan ini akan muncul di konsol saat pertama kali server FastAPI/Uvicorn dimulai
    print(f"Path root proyek ditambahkan: {project_root_path}") # <--- TAMBAHKAN INDENTASI (4 spasi)


# Impor fungsi ekstraksi fitur
try:
    from src.features.feature_extractor import extract_features
    print("Fungsi 'extract_features' dari src.features.feature_extractor berhasil diimpor.")
except ImportError as e_fe:
    print(f"KRITIKAL: GAGAL mengimpor 'extract_features': {e_fe}. Aplikasi tidak akan dapat melakukan prediksi.")
    # Definisikan fungsi placeholder
    def extract_features(url_string: str) -> list: # type: ignore
        # Pesan error di dalam fungsi, hanya akan terlempar jika fungsi ini dipanggil
        print("!!! MENGGUNAKAN FUNGSI 'extract_features' PLACEHOLDER KARENA IMPOR GAGAL !!!")
        raise RuntimeError( # Ini adalah line 39 jika dihitung dari 'try'
            "Fungsi 'extract_features' yang valid tidak dapat dimuat. "
            "Periksa path dan file src/features/feature_extractor.py, serta dependensinya."
        )
except Exception as e_other_import_error: # Menangkap error lain saat impor
    print(f"KRITIKAL: Error tak terduga saat mengimpor 'extract_features': {e_other_import_error}.")
    def extract_features(url_string: str) -> list: # type: ignore
        print(f"!!! MENGGUNAKAN FUNGSI 'extract_features' PLACEHOLDER KARENA ERROR IMPOR: {e_other_import_error} !!!")
        raise RuntimeError(
            f"Error tak terduga saat impor extract_features: {e_other_import_error}"
        )
    
# --- 2. Inisialisasi Aplikasi FastAPI ---

# Inisialisasi Aplikasi FastAPI
app = FastAPI(
    title="Detektor URL Phishing API",
    description="API untuk mendeteksi apakah sebuah URL berpotensi phishing.",
    version="1.0.0"
)

# --- 3. Variabel Global untuk Model ---

# Kita akan menggunakan dictionary untuk menyimpan state aplikasi seperti model
# Ini lebih bersih daripada menggunakan banyak variabel global.
app_state: Dict[str, Any] = {}

# Path ke model Anda yang sudah dilatih
SAVED_MODEL_PATH = project_root_path / "models_trained" / "best_recall_model.h5"
# SAVED_PREPROCESSOR_PATH = None # Jika Anda punya preprocessor terpisah

# --- BARU: Lifespan Event Handler ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(current_app: FastAPI):
    # Kode yang dijalankan saat startup
    print("--- Memulai Aplikasi: Memuat Model ---")
    model_to_load = None
    try:
        if SAVED_MODEL_PATH.exists():
            from tensorflow import keras # Impor di sini untuk menjaga scope
            model_to_load = keras.models.load_model(SAVED_MODEL_PATH)
            print(f"Model Keras berhasil dimuat dari: {SAVED_MODEL_PATH}")
            # model_to_load.summary() # Opsional
        else:
            print(f"ERROR KRITIKAL: File model TIDAK DITEMUKAN di: {SAVED_MODEL_PATH}. Aplikasi mungkin tidak berfungsi dengan benar.")
    except Exception as e:
        print(f"ERROR KRITIKAL saat memuat model Keras: {e}")
        # Anda bisa memutuskan untuk raise error di sini jika model adalah dependensi kritis
        # raise RuntimeError(f"Tidak dapat memuat model: {e}") from e
    
    app_state["loaded_model"] = model_to_load
    
    # Jika Anda punya preprocessor terpisah:
    # preprocessor_to_load = None
    # if SAVED_PREPROCESSOR_PATH and SAVED_PREPROCESSOR_PATH.exists():
    #     try:
    #         import joblib
    #         preprocessor_to_load = joblib.load(SAVED_PREPROCESSOR_PATH)
    #         print(f"Preprocessor berhasil dimuat dari: {SAVED_PREPROCESSOR_PATH}")
    #     except Exception as e:
    #         print(f"Error saat memuat preprocessor: {e}")
    # elif SAVED_PREPROCESSOR_PATH:
    #     print(f"PERINGATAN: File preprocessor TIDAK DITEMUKAN di: {SAVED_PREPROCESSOR_PATH}")
    # app_state["preprocessor"] = preprocessor_to_load

    print("--- Startup Aplikasi Selesai ---")
    yield # Ini adalah titik di mana aplikasi akan berjalan
    # Kode yang dijalankan saat shutdown (opsional)
    print("--- Aplikasi Berhenti ---")
    app_state.clear() # Bersihkan state jika perlu

# Terapkan lifespan handler ke aplikasi FastAPI Anda
app.router.lifespan_context = lifespan



# --- 4. Pydantic Models untuk Validasi Data API ---
class URLInput(BaseModel):
    url: HttpUrl # Pydantic akan memvalidasi bahwa ini adalah URL yang valid # <--- TAMBAHKAN INDENTASI

class PredictionResponse(BaseModel): # Pastikan ini juga di-indentasi dengan benar jika ada setelahnya
    url: str                             # <--- TAMBAHKAN INDENTASI
    predicted_type: str                  # <--- TAMBAHKAN INDENTASI
    phishing_probability: Optional[float] = None # <--- TAMBAHKAN INDENTASI
    error: Optional[str] = None          # <--- TAMBAHKAN INDENTASI

# --- 5. Fungsi Pembantu untuk Prediksi ---
# --- Fungsi Pembantu untuk Prediksi (get_prediction_for_url) ---
# Modifikasi sedikit untuk mengambil model dari app_state
def get_prediction_for_url(url_string: str, threshold: float = 0.5) -> Tuple[Optional[str], Optional[float], Optional[str]]:
    model = app_state.get("loaded_model")
    # preprocessor = app_state.get("preprocessor") # Jika Anda menggunakan preprocessor terpisah

    if not model: # Periksa model dari app_state
        return "Error", None, "Model tidak siap atau tidak berhasil dimuat."
 
    try:
        list_of_features = extract_features(url_string)
        if list_of_features is None:
            return "Error", None, "Gagal mengekstrak fitur dari URL."
        
        features_1d = np.array(list_of_features, dtype=np.float32)
        
        expected_features = model.input_shape[1]
        if features_1d.shape[0] != expected_features:
            msg = (
                f"Jumlah fitur ({features_1d.shape[0]}) tidak sesuai ({expected_features})."
            )
            return "Error", None, msg

        features_2d = features_1d.reshape(1, -1)
        
        # Jika Anda menggunakan preprocessor terpisah:
        # features_processed = features_2d
        # if preprocessor:
        #     features_processed = preprocessor.transform(features_2d)
        # else:
        #     features_processed = features_2d
        features_processed = features_2d # Karena kita asumsikan preprocessor tidak ada/sudah di feature_extractor

        prediction_proba = model.predict(features_processed)
        
        num_output_neurons = model.layers[-1].units
        activation_output_config = model.layers[-1].get_config()['activation']

        prob_phishing: Optional[float] = None
        predicted_label_int: Optional[int] = None

        if num_output_neurons == 1 and activation_output_config == 'sigmoid': 
            prob_phishing = float(prediction_proba[0, 0])
            predicted_label_int = 1 if prob_phishing > threshold else 0
        elif num_output_neurons > 1 and activation_output_config == 'softmax': 
            predicted_label_int = int(np.argmax(prediction_proba, axis=1)[0])
            prob_phishing = float(prediction_proba[0, 1]) 
        else:
            msg = (
                f"Struktur output model tidak dikenali "
                f"(neurons: {num_output_neurons}, activation: {activation_output_config})."
            )
            return "Error", None, msg
        
        label_mapping = {0: 'Aman', 1: 'Phishing'} 
        predicted_type = label_mapping.get(predicted_label_int, f"Label Int Tidak Diketahui: {predicted_label_int}")
        
        return predicted_type, prob_phishing, None

    except RuntimeError as r_err:
        print(f"RuntimeError saat prediksi: {r_err}")
        return "Error", None, str(r_err)
    except Exception as e:
        print(f"Error internal saat prediksi untuk URL '{url_string}': {e}")
        return "Error", None, "Terjadi kesalahan internal saat memproses permintaan Anda."


# --- 6. Definisi Rute (Endpoints) FastAPI ---
# main.py
# ... (impor dan kode lainnya di atas tetap sama) ...

# --- 6. Definisi Rute (Endpoints) FastAPI ---

# # HTML untuk halaman input dan hasil (disimpan sebagai string untuk kesederhanaan)
# HTML_FORM_PAGE = """
# <!doctype html>
# <html lang="id">
# <head>
#     <meta charset="utf-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
#     <title>Detektor URL Phishing</title>
# </head>
# <body>
#     <div class="container">
#         <h1>Detektor URL Phishing</h1>
#         <form action="/predict" method="post">
#             <label for="url_input">Masukkan URL untuk diperiksa:</label>
#             <input type="text" id="url_input" name="url_input" value="{input_url_display}" placeholder="Contoh: http://example.com" required>
#             <input type="submit" value="Periksa URL">
#         </form>
#         <div class="result-container">
#             {result_content}
#         </div>
#         {back_link_content}
#         <div class="footer">Aplikasi Deteksi Phishing</div>
#     </div>
# </body>
# </html>
# """

# @app.get("/", response_class=HTMLResponse)
# async def read_root_form(request: Request):
#     # Cetak ini untuk memastikan HTML_FORM_PAGE yang benar digunakan
#     # print("--- Konten HTML_FORM_PAGE di read_root_form ---")
#     # print(HTML_FORM_PAGE[:500]) # Cetak 500 karakter pertama untuk verifikasi
#     # print("--- Akhir Konten HTML_FORM_PAGE ---")
#     return HTMLResponse(content=HTML_FORM_PAGE.format(input_url_display="", result_content="", back_link_content=""))

@app.post("/api/predict", response_model=PredictionResponse)
async def api_predict_url(item: URLInput):
    # BARIS-BARIS BERIKUTNYA HARUS DI-INDENTASI
    predicted_type, proba, err_msg = get_prediction_for_url(str(item.url)) # <--- TAMBAHKAN INDENTASI

    if err_msg:                                                               # <--- TAMBAHKAN INDENTASI (dst.)
        # Untuk API, lebih baik mengembalikan status error HTTP yang sesuai jika memungkinkan
        # raise HTTPException(status_code=400, detail=err_msg) # Contoh jika input buruk
        return PredictionResponse(url=str(item.url), predicted_type="Error", error=err_msg)

    return PredictionResponse(
        url=str(item.url),
        predicted_type=predicted_type,
        phishing_probability=proba
    )

# --- 7. Menjalankan Aplikasi dengan Uvicorn (untuk development lokal) ---

if __name__ == "__main__":
    import uvicorn
    # Port akan diambil dari variabel lingkungan PORT jika ada (digunakan oleh Railway)
    # Jika tidak, default ke 8000 untuk development lokal dengan Uvicorn
    app_port = int(os.environ.get('PORT', 8000))

    print(f"Menjalankan Uvicorn server di http://0.0.0.0:{app_port}")

    # --- reload akan memantau perubahan kode dan me-restart server (hanya untuk development)
    uvicorn.run("main:app", host="0.0.0.0", port=app_port, reload=True, log_level="info")

