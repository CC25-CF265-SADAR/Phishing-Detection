# src/etl/data_validator.py

import pandas as pd
import numpy as np
import re
# Menggunakan logger yang sudah Anda siapkan dari src.utils.logger
# Asumsi setup_logging() sudah dipanggil di entry point aplikasi Anda (misal, main.py)
# sehingga logging.getLogger(__name__) akan mendapatkan logger yang terkonfigurasi.
import logging 
from typing import Dict, List, Any, Optional, Callable, Tuple, Union

# Dapatkan logger untuk modul ini
# Nama logger akan menjadi 'src.etl.data_validator' jika dipanggil dari sini
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Eksepsi kustom untuk error yang signifikan selama validasi data."""
    pass

class DataValidator:
    """
    Kelas komprehensif untuk melakukan berbagai validasi pada Pandas DataFrame
    berdasarkan skema yang ditentukan.
    """
    def __init__(self, schema: Dict[str, Dict[str, Any]]):
        """
        Inisialisasi validator dengan skema data.

        Args:
            schema (Dict[str, Dict[str, Any]]): Kamus yang mendefinisikan aturan validasi per kolom.
                Contoh skema untuk satu kolom:
                'nama_kolom': {
                    'dtype': type,                 # Tipe data Python yang diharapkan (str, int, float, bool, 'datetime')
                    'required': bool,              # Apakah kolom ini wajib ada (default: False)
                    'nullable': bool,              # Apakah nilai null/NaN diizinkan (default: True)
                    'unique': bool,                # Apakah semua nilai dalam kolom harus unik (default: False)
                    'min_value': Union[int, float],# Nilai minimum (untuk numerik/datetime)
                    'max_value': Union[int, float],# Nilai maksimum (untuk numerik/datetime)
                    'strict_min': bool,            # True jika > min_value, False jika >= min_value (default: False)
                    'strict_max': bool,            # True jika < max_value, False jika <= max_value (default: False)
                    'min_length': int,             # Panjang string minimum
                    'max_length': int,             # Panjang string maksimum
                    'allowed_values': List[Any],   # Daftar nilai yang diizinkan (untuk kategorikal)
                    'regex_pattern': str,          # Pola regex yang harus dicocokkan oleh string
                    'disallowed_regex_pattern': str, # Pola regex yang TIDAK boleh dicocokkan
                    'custom_function': Callable[[Any], bool], # Fungsi kustom yang mengembalikan True jika valid
                    'custom_function_series': Callable[[pd.Series], pd.Series], # Fungsi kustom yang mengembalikan Series boolean
                    'trim_whitespace': bool        # Jika True, pangkas spasi sebelum validasi string (default: False)
                }
        """
        if not isinstance(schema, dict):
            logger.error("Inisialisasi DataValidator gagal: Skema harus berupa dictionary.")
            raise ValueError("Skema harus berupa dictionary.")
        self.schema = schema
        self.validation_errors: List[Dict[str, Any]] = []
        logger.debug("DataValidator diinisialisasi dengan skema.")

    def _add_error(self, column: Optional[str], validation_type: str, message: str,
                   severity: str = "error", offending_sample: Optional[List[Any]] = None):
        """Mencatat error validasi ke list internal dan juga ke logger."""
        error_details = {
            "column": column if column else "DataFrame-Level",
            "validation_type": validation_type,
            "message": message,
            "severity": severity,
            "offending_sample": offending_sample if offending_sample else []
        }
        self.validation_errors.append(error_details)
        
        log_message = f"Validasi Gagal [{column if column else 'DataFrame'} - {validation_type}]: {message}"
        if offending_sample:
            log_message += f" Sampel bermasalah: {offending_sample[:3]}" # Log beberapa sampel
            
        if severity == "error":
            logger.error(log_message)
        elif severity == "warning":
            logger.warning(log_message)

    def _get_column_series(self, df: pd.DataFrame, col_name: str) -> Optional[pd.Series]:
        """Mengambil series kolom dan menangani jika tidak ada."""
        if col_name not in df.columns:
            if self.schema.get(col_name, {}).get('required', False):
                self._add_error(col_name, "Kolom Wajib", f"Kolom wajib '{col_name}' tidak ditemukan.")
            return None
        return df[col_name].copy() # Gunakan copy untuk operasi yang aman

    def _validate_required_columns(self, df: pd.DataFrame):
        """Memeriksa apakah semua kolom yang dibutuhkan ada."""
        logger.debug("Memulai validasi kolom wajib.")
        for col_name, col_config in self.schema.items():
            if col_config.get('required', False) and col_name not in df.columns:
                # Error sudah ditangani oleh _get_column_series, tapi ini untuk logging eksplisit
                logger.debug(f"Kolom wajib '{col_name}' tidak ditemukan saat pemeriksaan eksplisit.")
        logger.debug("Validasi kolom wajib selesai.")


    def _validate_data_types(self, df: pd.DataFrame):
        """Memeriksa tipe data kolom."""
        logger.debug("Memulai validasi tipe data.")
        type_mapping = {
            str: ['object', 'string'],
            int: ['int64', 'int32', 'int16', 'int8', 'Int64'],
            float: ['float64', 'float32'],
            bool: ['bool'],
            'datetime': ['datetime64[ns]']
        }
        for col_name, col_config in self.schema.items():
            series = self._get_column_series(df, col_name)
            if series is None: continue

            expected_py_type = col_config.get('dtype')
            if expected_py_type:
                expected_pandas_dtypes = type_mapping.get(expected_py_type)
                if not expected_pandas_dtypes:
                    self._add_error(col_name, "Tipe Data", f"Tipe Python '{expected_py_type}' tidak dikenali untuk skema.")
                    continue

                actual_dtype_str = str(series.dtype).lower()
                if actual_dtype_str not in [s.lower() for s in expected_pandas_dtypes]:
                    if actual_dtype_str == 'float64' and series.isnull().all() and expected_py_type in [str, int, bool]:
                        logger.debug(f"Kolom '{col_name}' adalah semua NaN, diterima sebagai tipe '{expected_py_type}' yang diharapkan.")
                    else:
                        self._add_error(col_name, "Tipe Data",
                                        f"Tipe data diharapkan salah satu dari {expected_pandas_dtypes} (untuk {expected_py_type}), ditemukan '{series.dtype}'.")
        logger.debug("Validasi tipe data selesai.")

    def _validate_nullable(self, df: pd.DataFrame):
        """Memeriksa nilai null/NaN."""
        logger.debug("Memulai validasi nilai null.")
        for col_name, col_config in self.schema.items():
            series = self._get_column_series(df, col_name)
            if series is None: continue

            if not col_config.get('nullable', True) and series.isnull().any():
                null_count = series.isnull().sum()
                percentage = null_count / len(series) if len(series) > 0 else 0
                self._add_error(col_name, "Nilai Null",
                                f"Tidak mengizinkan nilai null, tetapi ditemukan {null_count} ({percentage:.2%}) nilai null.")
        logger.debug("Validasi nilai null selesai.")

    def _validate_uniqueness(self, df: pd.DataFrame):
        """Memeriksa keunikan nilai dalam kolom."""
        logger.debug("Memulai validasi keunikan.")
        for col_name, col_config in self.schema.items():
            series = self._get_column_series(df, col_name)
            if series is None: continue

            if col_config.get('unique', False) and series.dropna().duplicated().any(): # Cek duplikat pada non-NaN
                duplicated_values = series.dropna()[series.dropna().duplicated(keep=False)].unique().tolist()
                self._add_error(col_name, "Keunikan",
                                f"Nilai harus unik, tetapi ditemukan duplikat. Contoh nilai duplikat: {duplicated_values[:5]}",
                                offending_sample=duplicated_values[:3])
        logger.debug("Validasi keunikan selesai.")

    def _validate_string_properties(self, df: pd.DataFrame):
        """Memeriksa properti string: panjang, pola regex."""
        logger.debug("Memulai validasi properti string.")
        for col_name, col_config in self.schema.items():
            series = self._get_column_series(df, col_name)
            if series is None: continue
            
            if col_config.get('dtype') not in [str, object, None]: # Hanya validasi jika tipe diharapkan string/object atau tidak dispesifik
                continue

            # Hanya validasi string pada nilai non-null
            # Pastikan series adalah string sebelum operasi string
            try:
                str_series_original = series.dropna()
                if str_series_original.empty: continue
                str_series = str_series_original.astype(str)
            except Exception as e:
                logger.warning(f"Gagal mengkonversi kolom '{col_name}' ke string untuk validasi properti: {e}")
                continue


            if col_config.get('trim_whitespace', False):
                str_series = str_series.str.strip()

            if 'min_length' in col_config and (str_series.str.len() < col_config['min_length']).any():
                offending = str_series[str_series.str.len() < col_config['min_length']].head(3).tolist()
                self._add_error(col_name, "Panjang String Min",
                                f"Panjang string kurang dari minimum {col_config['min_length']}.", offending_sample=offending)
            if 'max_length' in col_config and (str_series.str.len() > col_config['max_length']).any():
                offending = str_series[str_series.str.len() > col_config['max_length']].head(3).tolist()
                self._add_error(col_name, "Panjang String Max",
                                f"Panjang string melebihi maksimum {col_config['max_length']}.", offending_sample=offending)
            if 'regex_pattern' in col_config:
                pattern_str = col_config['regex_pattern']
                try:
                    pattern = re.compile(pattern_str)
                    # Cek jika ada yang tidak cocok
                    non_matching_mask = ~str_series.apply(lambda x: bool(pattern.fullmatch(str(x))))
                    if non_matching_mask.any():
                        offending = str_series[non_matching_mask].head(3).tolist()
                        self._add_error(col_name, "Pola Regex",
                                        f"Nilai tidak cocok dengan pola regex: {pattern_str}.", offending_sample=offending)
                except re.error as e:
                    self._add_error(col_name, "Pola Regex", f"Pola regex tidak valid: {pattern_str}. Error: {e}")

            if 'disallowed_regex_pattern' in col_config:
                pattern_str = col_config['disallowed_regex_pattern']
                try:
                    pattern = re.compile(pattern_str)
                    # Cek jika ada yang cocok (terlarang)
                    matching_mask = str_series.apply(lambda x: bool(pattern.search(str(x))))
                    if matching_mask.any():
                        offending = str_series[matching_mask].head(3).tolist()
                        self._add_error(col_name, "Pola Regex Terlarang",
                                        f"Nilai cocok dengan pola regex terlarang: {pattern_str}.", offending_sample=offending)
                except re.error as e:
                    self._add_error(col_name, "Pola Regex Terlarang", f"Pola regex terlarang tidak valid: {pattern_str}. Error: {e}")
        logger.debug("Validasi properti string selesai.")

    def _validate_numerical_constraints(self, df: pd.DataFrame):
        """Memeriksa batasan numerik: min_value, max_value."""
        logger.debug("Memulai validasi batasan numerik.")
        for col_name, col_config in self.schema.items():
            series = self._get_column_series(df, col_name)
            if series is None: continue

            if col_config.get('dtype') not in [int, float, 'datetime', None]:
                continue
            
            num_series = series.copy().dropna() # Bekerja dengan data non-null
            if num_series.empty: continue

            # Coba konversi ke tipe yang tepat jika perlu
            if col_config.get('dtype') in [int, float] and not pd.api.types.is_numeric_dtype(num_series):
                num_series = pd.to_numeric(num_series, errors='coerce').dropna()
            elif col_config.get('dtype') == 'datetime' and not pd.api.types.is_datetime64_any_dtype(num_series):
                num_series = pd.to_datetime(num_series, errors='coerce').dropna()
            
            if num_series.empty: continue # Jika konversi gagal semua

            if 'min_value' in col_config:
                min_val = col_config['min_value']
                op = np.greater if col_config.get('strict_min', False) else np.greater_equal
                comp_char = ">" if col_config.get('strict_min', False) else ">="
                if (~op(num_series, min_val)).any():
                    offending = num_series[~op(num_series, min_val)].head(3).tolist()
                    self._add_error(col_name, "Nilai Minimum",
                                    f"Nilai kurang dari {comp_char} {min_val}.", offending_sample=offending)
            if 'max_value' in col_config:
                max_val = col_config['max_value']
                op = np.less if col_config.get('strict_max', False) else np.less_equal
                comp_char = "<" if col_config.get('strict_max', False) else "<="
                if (~op(num_series, max_val)).any():
                    offending = num_series[~op(num_series, max_val)].head(3).tolist()
                    self._add_error(col_name, "Nilai Maksimum",
                                    f"Nilai lebih dari {comp_char} {max_val}.", offending_sample=offending)
        logger.debug("Validasi batasan numerik selesai.")

    def _validate_allowed_values(self, df: pd.DataFrame):
        """Memeriksa apakah nilai termasuk dalam daftar yang diizinkan."""
        logger.debug("Memulai validasi nilai yang diizinkan.")
        for col_name, col_config in self.schema.items():
            series = self._get_column_series(df, col_name)
            if series is None: continue

            if 'allowed_values' in col_config:
                allowed = set(col_config['allowed_values'])
                # Perlu perlakuan khusus jika tipe data adalah list atau set di dalam series
                # Untuk saat ini, kita asumsikan nilai adalah skalar atau bisa di-hash
                # dan bandingkan setelah dikonversi ke tipe yang sama jika memungkinkan
                try:
                    # Coba konversi elemen series ke tipe elemen pertama di allowed_values jika ada & seragam
                    # Ini membantu jika misal allowed_values adalah [0,1] tapi series adalah ['0','1']
                    if allowed and len(series.dropna()) > 0:
                        example_allowed_type = type(list(allowed)[0])
                        current_series_type = series.dropna().iloc[0]
                        if not isinstance(current_series_type, example_allowed_type):
                            # Coba konversi dengan hati-hati
                            series_to_check = series.dropna().astype(example_allowed_type)
                        else:
                            series_to_check = series.dropna()
                    else:
                        series_to_check = series.dropna()
                    
                    unique_values_in_series = set(series_to_check.unique())
                except Exception: # Jika konversi gagal, gunakan nilai asli
                    unique_values_in_series = set(series.dropna().unique())

                
                if not unique_values_in_series.issubset(allowed):
                    disallowed_found = list(unique_values_in_series - allowed)
                    self._add_error(col_name, "Nilai Diizinkan",
                                    f"Ditemukan nilai yang tidak diizinkan: {disallowed_found[:5]}. Diizinkan: {list(allowed)[:10]}.",
                                    offending_sample=disallowed_found[:3])
        logger.debug("Validasi nilai yang diizinkan selesai.")

    def _validate_custom_functions(self, df: pd.DataFrame):
        """Menjalankan fungsi validasi kustom."""
        logger.debug("Memulai validasi fungsi kustom.")
        for col_name, col_config in self.schema.items():
            series = self._get_column_series(df, col_name)
            if series is None: continue

            if 'custom_function' in col_config:
                custom_func = col_config['custom_function']
                try:
                    # Terapkan pada nilai non-null
                    non_null_series = series.dropna()
                    if not non_null_series.empty:
                        # Hasil dari apply harus boolean series
                        results = non_null_series.apply(custom_func)
                        if not results.all() and isinstance(results, pd.Series) and results.dtype == bool : # Pastikan semua True
                            offending = non_null_series[~results].head(3).tolist()
                            self._add_error(col_name, "Fungsi Kustom (per elemen)",
                                            f"Beberapa nilai gagal validasi fungsi kustom: {custom_func.__name__}.",
                                            offending_sample=offending)
                        elif not isinstance(results, pd.Series) or results.dtype != bool:
                             self._add_error(col_name, "Fungsi Kustom (per elemen)",
                                        f"Fungsi kustom '{custom_func.__name__}' tidak mengembalikan Pandas Series boolean untuk semua elemen.")
                except Exception as e:
                    self._add_error(col_name, "Fungsi Kustom (per elemen)", f"Error menjalankan fungsi kustom '{custom_func.__name__}': {e}")

            if 'custom_function_series' in col_config:
                custom_func_series = col_config['custom_function_series']
                try:
                    is_valid_series = custom_func_series(series.copy()) 
                    if not isinstance(is_valid_series, pd.Series) or is_valid_series.dtype != bool:
                        self._add_error(col_name, "Fungsi Kustom (per series)",
                                        f"Fungsi kustom '{custom_func_series.__name__}' harus mengembalikan Pandas Series boolean.")
                        continue
                    if (~is_valid_series & ~series.isnull()).any(): 
                        offending_indices = series.index[~is_valid_series & ~series.isnull()]
                        offending_values = series.loc[offending_indices].head(3).tolist()
                        self._add_error(col_name, "Fungsi Kustom (per series)",
                                        f"Validasi fungsi kustom series '{custom_func_series.__name__}' gagal.",
                                        offending_sample=offending_values)
                except Exception as e:
                    self._add_error(col_name, "Fungsi Kustom (per series)",
                                    f"Error saat menjalankan fungsi kustom series '{custom_func_series.__name__}': {e}")
        logger.debug("Validasi fungsi kustom selesai.")

    def _validate_duplicate_rows(self, df: pd.DataFrame):
        """Memeriksa baris duplikat keseluruhan DataFrame."""
        logger.debug("Memulai validasi baris duplikat.")
        if df.duplicated().any():
            num_duplicates = df.duplicated().sum()
            self._add_error(None, "Baris Duplikat",
                            f"Ditemukan {num_duplicates} baris duplikat dalam keseluruhan DataFrame.")
        logger.debug("Validasi baris duplikat selesai.")

    def validate_dataframe(self, df: pd.DataFrame, raise_exception_on_error: bool = False) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Menjalankan semua pemeriksaan validasi yang dikonfigurasi pada DataFrame.
        """
        if not isinstance(df, pd.DataFrame):
            logger.error("Input untuk validasi bukan Pandas DataFrame.")
            raise ValueError("Input harus berupa Pandas DataFrame.")

        self.validation_errors = [] 
        logger.info(f"Memulai validasi DataFrame dengan {len(df)} baris dan {len(df.columns)} kolom.")

        self._validate_required_columns(df)
        self._validate_data_types(df)    
        self._validate_nullable(df)      
        self._validate_uniqueness(df)
        self._validate_string_properties(df)
        self._validate_numerical_constraints(df)
        self._validate_allowed_values(df)
        self._validate_custom_functions(df)
        self._validate_duplicate_rows(df)

        has_critical_errors = any(err['severity'] == 'error' for err in self.validation_errors)
        is_overall_valid = not has_critical_errors

        if not is_overall_valid and raise_exception_on_error:
            critical_error_messages = [
                f"- Kolom '{err['column']}': [{err['validation_type']}] {err['message']}" + (f" (Sampel: {err['offending_sample']})" if err['offending_sample'] else "")
                for err in self.validation_errors if err['severity'] == 'error'
            ]
            error_summary = "\n".join(critical_error_messages)
            logger.critical(f"Validasi data gagal dengan error kritis. Memunculkan DataValidationError. Rincian:\n{error_summary}")
            raise DataValidationError(f"Validasi data gagal dengan error kritis:\n{error_summary}")
        
        if is_overall_valid and not self.validation_errors:
            logger.info("Validasi DataFrame berhasil tanpa error atau peringatan.")
        elif is_overall_valid and self.validation_errors:
             logger.info("Validasi DataFrame berhasil, tetapi dengan beberapa peringatan.")
        else: 
            logger.error("Validasi DataFrame gagal dengan error kritis.")
            
        return is_overall_valid, self.validation_errors
