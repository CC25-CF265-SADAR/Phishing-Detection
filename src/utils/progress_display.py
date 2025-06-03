# src/utils/progress_display.py

import logging
from tqdm import tqdm
from typing import Iterable, Optional, Any

# Impor logger dari modul logger.py Anda
# Menggunakan impor relatif karena diasumsikan progress_display.py dan logger.py
# berada dalam paket utils yang sama.
try:
    from .logger import get_logger
except ImportError:
    # Fallback jika dijalankan sebagai skrip atau struktur berbeda
    # Ini akan menggunakan basicConfig jika logger kustom tidak terjangkau
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger_fallback = logging.getLogger(__name__)
    logger_fallback.warning(
        "Tidak dapat mengimpor get_logger dari .logger. Menggunakan fallback logger dasar untuk progress_display."
    )
    # Definisikan fungsi get_logger dummy jika impor gagal agar kode di bawah tetap jalan
    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

# Dapatkan logger untuk modul ini
logger = get_logger(__name__)

def track_progress(
    iterable: Iterable,
    description: str = "Memproses",
    total: Optional[int] = None,
    unit: str = "it",
    log_level: int = logging.INFO,
    log_start_end: bool = True,
    **tqdm_kwargs: Any
) -> Iterable:
    """
    Membungkus sebuah iterable dengan tqdm untuk menampilkan bilah progres
    dan secara opsional mencatat pesan awal dan akhir proses menggunakan logger.

    Args:
        iterable (Iterable): Objek yang bisa diiterasi (misalnya, list, range).
        description (str): Deskripsi yang akan ditampilkan pada bilah progres.
        total (Optional[int]): Jumlah total item. Jika None, tqdm akan mencoba menentukannya.
        unit (str): Satuan untuk setiap item (misalnya, "item", "file", "baris").
        log_level (int): Level logging untuk pesan awal/akhir (misalnya, logging.INFO, logging.DEBUG).
        log_start_end (bool): Jika True, catat pesan di awal dan akhir iterasi.
        **tqdm_kwargs: Argumen tambahan yang akan diteruskan ke tqdm (misalnya, ncols, leave).

    Returns:
        Iterable: Iterable yang sama, tetapi sekarang dengan bilah progres saat diiterasi.
    """
    if total is None:
        try:
            total = len(iterable) # type: ignore
        except (TypeError, AttributeError):
            # tqdm akan menangani ini jika total adalah None (tidak akan ada persentase/waktu sisa)
            logger.debug(f"Tidak dapat menentukan jumlah total untuk tqdm: '{description}'.")
            pass # Biarkan total tetap None

    if log_start_end:
        logger.log(log_level, f"Mulai: {description} (Total item: {total if total is not None else 'tidak diketahui'})")

    processed_count = 0
    try:
        # Atur default leave=True jika tidak disediakan, agar progress bar tidak hilang setelah selesai
        if 'leave' not in tqdm_kwargs:
            tqdm_kwargs['leave'] = True
            
        for item in tqdm(iterable, desc=description, total=total, unit=unit, **tqdm_kwargs):
            yield item
            processed_count += 1
    except Exception as e:
        logger.error(f"Error terjadi selama '{description}' setelah {processed_count} {unit} diproses: {e}", exc_info=True)
        raise # Lemparkan kembali error setelah dicatat
    finally:
        if log_start_end:
            logger.log(log_level, f"Selesai: {description}. Total {processed_count} {unit} berhasil diproses.")

# # --- Contoh Penggunaan (bisa dihapus atau dikomentari di file produksi) ---
# if __name__ == "__main__":
#     # Untuk menjalankan contoh ini, Anda mungkin perlu setup logger utama jika belum
#     # Ini hanya untuk demonstrasi jika file ini dijalankan langsung
#     try:
#         from .logger import setup_logging # Coba impor setup_logging
#         if not logging.getLogger().hasHandlers():
#              setup_logging(log_level=logging.DEBUG)
#     except ImportError:
#         logger.info("Menjalankan contoh progress_display.py tanpa setup logger kustom.")
#         # logger sudah menggunakan basicConfig dari fallback di atas jika impor gagal

#     import time

#     my_list = range(30)
#     logger.info("Memulai contoh iterasi dengan track_progress...")
#     results = []
#     for i in track_progress(my_list, description="Mengolah Angka", unit="angka", ncols=80):
#         results.append(i * i)
#         time.sleep(0.05) # Simulasi pekerjaan
#     logger.info(f"Hasil contoh: {results[:5]}")

#     logger.info("\nMemulai contoh iterasi lain tanpa info total...")
#     def my_generator():
#         for i in range(15):
#             yield i
#             time.sleep(0.1)

#     results_gen = []
#     for x in track_progress(my_generator(), description="Proses Generator", unit="gen", log_level=logging.DEBUG):
#         results_gen.append(x + 1)
#     logger.info(f"Hasil generator: {results_gen[:5]}")

#     logger.info("\nContoh dengan error:")
#     error_list = [1, 2, 3, 'bad_value', 5]
#     try:
#         for item in track_progress(error_list, description="Proses dengan Potensi Error"):
#             if not isinstance(item, int):
#                 raise TypeError(f"Item {item} bukan integer!")
#             time.sleep(0.1)
#     except TypeError:
#         logger.info("Contoh error berhasil ditangkap dan dicatat oleh track_progress.")