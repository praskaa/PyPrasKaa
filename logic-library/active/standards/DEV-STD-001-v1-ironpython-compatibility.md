# LOGIC LIBRARY: DEV-STD-001-v1

**Title:** Panduan Kompatibilitas IronPython 2.7 untuk pyRevit
**Version:** 1.0
**Status:** Active
**Author:** Kilo Code
**Date:** 2025-10-24
**Category:** Development Standards

---

## 1. Latar Belakang

Pengembangan untuk pyRevit mengharuskan kode ditulis dalam sintaks yang kompatibel dengan **IronPython 2.7**. Lingkungan ini tidak mendukung banyak fitur modern dari Python 3. Dokumen ini berfungsi sebagai referensi praktis untuk menghindari kesalahan umum dan memastikan semua kode, terutama di dalam `logic-library` dan `lib/`, dapat berjalan dengan andal.

## 2. Aturan Kompatibilitas Kunci

Berikut adalah daftar masalah umum yang ditemukan dan solusi yang harus diterapkan:

### 2.1. Manajemen Impor Modul Kustom (`sys.path`)

-   **Masalah:** Skrip di dalam direktori `.pushbutton` tidak dapat menemukan modul di folder `lib/` pada root ekstensi.
-   **Solusi Standar:** Tambahkan kode berikut di bagian atas setiap skrip yang membutuhkan akses ke `lib/`.

    ```python
    # -*- coding: utf-8 -*-
    import sys
    import os

    # Menambahkan root ekstensi ke Python path
    # Sesuaikan jumlah os.path.dirname() sesuai kedalaman folder skrip
    # Contoh ini untuk skrip di dalam .../pulldown/button.pushbutton/
    extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if extension_root not in sys.path:
        sys.path.insert(0, extension_root)

    # Sekarang impor dari lib/ dapat dilakukan
    from lib.parameters import ParameterSettingFramework
    ```

### 2.2. F-Strings (String Formatting)

-   **Masalah:** F-strings (`f"Halo, {nama}"`) tidak didukung dan akan menyebabkan `SyntaxError`.
-   **Solusi Standar:** Selalu gunakan metode `.format()`.

    ```python
    # SALAH:
    # raise ValueError(f"Nilai {nilai} tidak valid.")

    # BENAR:
    raise ValueError("Nilai {} tidak valid.".format(nilai))
    ```

### 2.3. Abstract Base Classes (ABC)

-   **Masalah:** `import ABC` dan pewarisan `class MojaKlasa(ABC):` tidak berfungsi.
-   **Solusi Standar:** Gunakan `ABCMeta` sebagai `__metaclass__`.

    ```python
    from abc import ABCMeta, abstractmethod

    class StrategiDasar(object):
        """Kelas abstrak dasar."""
        __metaclass__ = ABCMeta

        @abstractmethod
        def jalankan(self, data):
            pass
    ```

### 2.4. Panggilan `super()` pada Pewarisan

-   **Masalah:** Panggilan `super().__init__()` tanpa argumen akan menyebabkan `TypeError`.
-   **Solusi Standar:** Gunakan sintaks `super()` yang eksplisit dengan menyertakan nama kelas dan `self`.

    ```python
    class StrategiSpesifik(StrategiDasar):
        def __init__(self, doc, logger=None):
            # SALAH:
            # super().__init__(doc, logger)

            # BENAR:
            super(StrategiSpesifik, self).__init__(doc, logger)
            # ... sisa inisialisasi ...
    ```

## 3. Rekomendasi

-   **Validasi Awal:** Sebelum melakukan *commit* kode *library* baru, jalankan skrip sederhana yang mengimpor dan menginisialisasi kelas dari *library* tersebut di dalam lingkungan pyRevit untuk menangkap `ImportError` atau `SyntaxError` lebih awal.
-   **Konsistensi:** Terapkan semua aturan di atas secara konsisten di seluruh basis kode untuk menjaga kualitas dan kemudahan pemeliharaan.