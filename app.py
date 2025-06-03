# app.py

import os
import sys
from pathlib import Path
import logging

import numpy as np
import pandas as pd # Hanya jika feature_extractor Anda membutuhkannya untuk input
from flask import Flask, request, render_template_string, jsonify # Tambahkan jsonify

# --- 1. Pengaturan Path dan Impor Modul Internal ---
# Tambahkan root proyek ke sys.path agar bisa mengimpor dari 'src'
# Asumsi app.py ada di root proyek (sejajar dengan folder 'src')
project_root_path = Path(__file__).resolve().parent
if str(project_root_path) not in sys.path:
    sys.path.append(str(project_root_path))
    print(f"Path proyek ditambahkan: {project_root_path}")

try:
    from src.utils.logger import setup_logging, get_logger
    # Panggil setup_logging sekali saat aplikasi dimulai
    # Cek apakah root logger sudah punya handler untuk menghindari konfigurasi ganda
    if not logging.getLogger().hasHandlers():
        setup_logging(log_level=logging.INFO, console_output=True, file_output=True)
    logger = get_logger('flask_app') # Beri nama spesifik untuk logger aplikasi Flask
    logger.info("Logger untuk Flask app berhasil di-setup.")
except ImportError as e_logger:
    # Fallback ke basic config jika modul logger kustom tidak ditemukan
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('flask_app_fallback')
    logger.warning(f"Modul logger kustom (src.utils.logger) tidak ditemukan atau error: {e_logger}. Menggunakan basicConfig.")
except Exception as e_setup:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('flask_app_fallback_error')
    logger.error(f"Error saat setup logger kustom: {e_setup}. Menggunakan basicConfig.", exc_info=True)


try:
    from src.features.feature_extractor import extract_features # Fungsi Anda
    logger.info("Fungsi 'extract_features' berhasil diimpor.")
except ImportError as e_fe:
    logger.critical(f"GAGAL mengimpor 'extract_features': {e_fe}. Aplikasi tidak akan berfungsi dengan benar.", exc_info=True)
    # Definisikan fungsi placeholder agar aplikasi bisa start, tapi beri warning keras
    def extract_features(url_string: str) -> list:
        logger.error("!!! MENGGUNAKAN FUNGSI 'extract_features' PLACEHOLDER !!!")
        # Ganti 20 dengan jumlah fitur yang diharapkan model Anda
        return list(np.random.rand(20)) if url_string else []


# --- 2. Inisialisasi Aplikasi Flask ---
app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True # Untuk debugging error di Flask dengan lebih baik


# --- 3. Memuat Model Keras dan Preprocessor (jika ada) ---
# Variabel global untuk model dan preprocessor
loaded_model = None
preprocessor = None # Akan tetap None jika tidak ada file preprocessor yang valid

# Tentukan path ke model Anda
MODEL_PATH_RELATIVE_TO_SRC = Path("models") / "model_checkpoints_recall_focused" / "best_recall_model.keras"
SAVED_MODEL_PATH = project_root_path / "src" / MODEL_PATH_RELATIVE_TO_SRC

# TODO: Sesuaikan path ini jika Anda memiliki file preprocessor terpisah (misal, scaler.joblib)
# PREPROCESSOR_PATH_RELATIVE_TO_SRC = Path("models") / "nama_preprocessor.joblib"
# SAVED_PREPROCESSOR_PATH = project_root_path / "src" / PREPROCESSOR_PATH_RELATIVE_TO_SRC
SAVED_PREPROCESSOR_PATH = None # Set ke None jika tidak ada preprocessor terpisah

try:
    if SAVED_MODEL_PATH.exists():
        from tensorflow import keras # Impor di sini agar hanya jika path ada
        loaded_model = keras.models.load_model(SAVED_MODEL_PATH)
        logger.info(f"Model Keras berhasil dimuat dari: {SAVED_MODEL_PATH}")
        # loaded_model.summary(print_fn=logger.info) # Cetak summary ke log
    else:
        logger.error(f"File model TIDAK DITEMUKAN di: {SAVED_MODEL_PATH}")
except Exception as e:
    logger.error(f"Error saat memuat model Keras: {e}", exc_info=True)

if SAVED_PREPROCESSOR_PATH and SAVED_PREPROCESSOR_PATH.exists():
    try:
        import joblib
        preprocessor = joblib.load(SAVED_PREPROCESSOR_PATH)
        logger.info(f"Preprocessor berhasil dimuat dari: {SAVED_PREPROCESSOR_PATH}")
    except Exception as e:
        logger.error(f"Error saat memuat preprocessor: {e}", exc_info=True)
elif SAVED_PREPROCESSOR_PATH:
    logger.warning(f"File preprocessor TIDAK DITEMUKAN di: {SAVED_PREPROCESSOR_PATH}")
else:
    logger.info("Tidak ada preprocessor terpisah yang dikonfigurasi untuk dimuat.")


# --- 4. Fungsi Pembantu untuk Prediksi ---
def get_prediction_for_url(url_string: str, threshold: float = 0.5) -> Tuple[Optional[str], Optional[float], Optional[str]]:
    """
    Menerima URL, melakukan ekstraksi fitur, pra-pemrosesan, prediksi,
    dan mengembalikan hasil.
    """
    if not loaded_model:
        return "Error", None, "Model tidak berhasil dimuat."
    if not url_string:
        return None, None, "Input URL tidak boleh kosong."

    try:
        logger.info(f"Memproses URL untuk prediksi: {url_string}")
        
        # 1. Ekstraksi Fitur
        list_of_features = extract_features(url_string) # Menggunakan fungsi Anda
        if list_of_features is None:
            return "Error", None, "Gagal mengekstrak fitur dari URL."
        
        features_1d = np.array(list_of_features, dtype=np.float32)
        
        # Validasi jumlah fitur
        expected_features = loaded_model.input_shape[1]
        if features_1d.shape[0] != expected_features:
            msg = f"Jumlah fitur ({features_1d.shape[0]}) tidak sesuai dengan ekspektasi model ({expected_features})."
            logger.error(msg)
            return "Error", None, msg

        features_2d = features_1d.reshape(1, -1) # Reshape untuk model (1 sampel, N fitur)

        # 2. Pra-pemrosesan dengan preprocessor yang dimuat (jika ada)
        features_processed = features_2d
        if preprocessor:
            logger.debug("Menerapkan preprocessor pada fitur...")
            features_processed = preprocessor.transform(features_2d) # Harap transform, bukan fit_transform

        # 3. Membuat Prediksi
        logger.debug(f"Membuat prediksi dengan model pada fitur shape: {features_processed.shape}")
        prediction_proba = loaded_model.predict(features_processed)
        
        # Interpretasi output model
        # Asumsi model Anda (best_recall_model.keras) memiliki 1 output neuron dengan sigmoid
        if prediction_proba.shape[1] == 1: 
            prob_phishing = prediction_proba[0, 0]
            predicted_label_int = 1 if prob_phishing > threshold else 0
        # Atau jika model Anda memiliki 2 output neuron dengan softmax (sesuaikan jika perlu)
        # elif prediction_proba.shape[1] > 1: 
        #     predicted_label_int = np.argmax(prediction_proba, axis=1)[0]
        #     prob_phishing = prediction_proba[0, 1] # Asumsi kelas 1 (phishing) adalah indeks 1
        else:
            return "Error", None, "Format output prediksi model tidak dikenali."
        
        label_mapping = {0: 'Aman', 1: 'Phishing'} 
        predicted_type = label_mapping.get(predicted_label_int, f"Label Int Tidak Diketahui: {predicted_label_int}")
        
        logger.info(f"Prediksi untuk '{url_string}': Tipe='{predicted_type}', Prob_Phishing={prob_phishing:.4f}")
        return predicted_type, float(prob_phishing), None # Kirim probabilitas sebagai float standar

    except Exception as e:
        logger.error(f"Error saat memprediksi URL '{url_string}': {e}", exc_info=True)
        return "Error", None, f"Terjadi kesalahan internal: {str(e)}"


# --- 5. Definisi Rute Flask ---
@app.route('/', methods=['GET', 'POST'])
def index():
    prediction_result = None
    prediction_proba = None
    error_message = None
    input_url = ""

    if request.method == 'POST':
        input_url = request.form.get('url_input', '').strip()
        if input_url:
            predicted_type, proba, err = get_prediction_for_url(input_url)
            if err:
                error_message = err
            else:
                prediction_result = predicted_type
                prediction_proba = f"{proba:.4f}" if proba is not None else None
        else:
            error_message = "Silakan masukkan URL."
            
    # HTML Sederhana (inline)
    html_template = """
    <!doctype html>
    <html lang="id">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Deteksi URL Phishing</title>
        <style>
            body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
            .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            label { display: block; margin-bottom: 8px; font-weight: bold; }
            input[type="text"] { width: calc(100% - 22px); padding: 10px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 4px; }
            input[type="submit"] { background-color: #5cb85c; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            input[type="submit"]:hover { background-color: #4cae4c; }
            .result { margin-top: 20px; padding: 15px; border-radius: 4px; }
            .result.phishing { background-color: #f2dede; border: 1px solid #ebccd1; color: #a94442; }
            .result.aman { background-color: #dff0d8; border: 1px solid #d6e9c6; color: #3c763d; }
            .result.error { background-color: #fcf8e3; border: 1px solid #faebcc; color: #8a6d3b; }
            .probability { font-size: 0.9em; color: #555; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Deteksi URL Phishing</h1>
            <form method="post">
                <label for="url_input">Masukkan URL:</label>
                <input type="text" id="url_input" name="url_input" value="{{ input_url if input_url else '' }}" required>
                <input type="submit" value="Periksa URL">
            </form>

            {% if error_message %}
                <div class="result error">
                    <strong>Error:</strong> {{ error_message }}
                </div>
            {% elif prediction_result %}
                <div class="result {{ 'phishing' if prediction_result == 'Phishing' else 'aman' }}">
                    <strong>Hasil Deteksi:</strong> {{ prediction_result }}
                    {% if prediction_proba %}
                        <p class="probability">(Probabilitas Phishing: {{ prediction_proba }})</p>
                    {% endif %}
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, 
                                  prediction_result=prediction_result, 
                                  prediction_proba=prediction_proba,
                                  error_message=error_message,
                                  input_url=input_url)

# Endpoint JSON API (opsional)
@app.route('/api/predict', methods=['POST'])
def api_predict():
    if not request.is_json:
        return jsonify({"error": "Request harus berupa JSON"}), 400
    
    data = request.get_json()
    url_to_check = data.get('url')

    if not url_to_check:
        return jsonify({"error": "Parameter 'url' tidak ditemukan dalam JSON body"}), 400

    predicted_type, proba, err_msg = get_prediction_for_url(url_to_check)

    if err_msg:
        return jsonify({"error": err_msg, "url": url_to_check}), 400 # atau 500 tergantung jenis error
    
    return jsonify({
        "url": url_to_check,
        "predicted_type": predicted_type,
        "phishing_probability": proba
    })


# --- 6. Menjalankan Aplikasi Flask ---
if __name__ == '__main__':
    # Gunakan port yang berbeda jika 5000 sudah terpakai
    # debug=True hanya untuk development, jangan gunakan di produksi
    app.run(host='0.0.0.0', port=5000, debug=True)