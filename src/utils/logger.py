# src/utils/logger.py

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Union # <--- TAMBAHKAN IMPORT INI

# Tentukan level logging default dan format pesan
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Tentukan path untuk file log
# Biasanya disimpan di folder 'logs' di root proyek
# Kita asumsikan logger.py ada di src/utils/, jadi kita naik dua level untuk root proyek
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE_PATH = LOGS_DIR / "project_activity.log"

# Konfigurasi untuk rotasi file log
LOG_FILE_MAX_BYTES = 1024 * 1024 * 5  # 5 MB (pastikan spasi standar)
LOG_FILE_BACKUP_COUNT = 5 # Simpan 5 file backup

# Pastikan direktori logs ada
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Penampung untuk memastikan logger hanya di-setup sekali
_logger_configured = False

def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    log_file: Union[str, Path] = LOG_FILE_PATH, # Union sudah diimpor
    console_output: bool = True,
    file_output: bool = True
) -> None:
    """
    Mengkonfigurasi root logger untuk proyek.
    Fungsi ini sebaiknya dipanggil sekali di awal aplikasi (misalnya, di main.py).

    Args:
        log_level (int): Level logging minimum (misalnya, logging.DEBUG, logging.INFO).
        log_format (str): Format string untuk pesan log.
        date_format (str): Format string untuk tanggal dan waktu dalam pesan log.
        log_file (Union[str, Path]): Path lengkap ke file log.
        console_output (bool): Jika True, log juga akan ditampilkan di konsol.
        file_output (bool): Jika True, log akan ditulis ke file.
    """
    global _logger_configured
    if _logger_configured:
        logging.getLogger(__name__).debug("Konfigurasi logging sudah dilakukan sebelumnya.")
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(log_format, datefmt=date_format)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if file_output:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=LOG_FILE_MAX_BYTES,
                backupCount=LOG_FILE_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.error(f"Gagal membuat file log handler di {log_file}: {e}", exc_info=True)

    _logger_configured = True
    root_logger.info("Konfigurasi logging selesai.")


def get_logger(name: str) -> logging.Logger:
    """
    Mendapatkan instance logger dengan nama tertentu.
    """
    return logging.getLogger(name)

# # --- Contoh Penggunaan (bisa dihapus atau dikomentari di file produksi) ---
# if __name__ == "__main__":
#     setup_logging(log_level=logging.DEBUG)

#     logger_contoh = get_logger(__name__)

#     logger_contoh.debug("Ini adalah pesan debug dari contoh logger.")
#     logger_contoh.info("Ini adalah pesan info dari contoh logger.")
#     logger_contoh.warning("Ini adalah pesan peringatan dari contoh logger.")
#     logger_contoh.error("Ini adalah pesan error dari contoh logger.")
#     logger_contoh.critical("Ini adalah pesan critical dari contoh logger.")

#     another_module_logger = get_logger("modul.lain.spesifik")
#     another_module_logger.info("Pesan dari logger modul lain.")

#     try:
#         x = 1 / 0
#     except ZeroDivisionError:
#         logger_contoh.error("Terjadi error pembagian dengan nol!", exc_info=True)

#     logger_contoh.info(f"File log disimpan di: {LOG_FILE_PATH}")