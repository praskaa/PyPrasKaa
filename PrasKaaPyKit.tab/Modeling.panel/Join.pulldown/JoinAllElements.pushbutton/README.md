# Join All Elements

Skrip PyRevit untuk menggabungkan elemen struktur secara manual yang tidak dapat digabungkan secara otomatis selama proses Matching Dimension.

## Deskripsi

Skrip ini menyediakan fungsionalitas gabungan manual untuk elemen struktur yang tidak secara otomatis tergabung selama proses Matching Dimension. Ini memungkinkan pengguna untuk secara selektif menggabungkan elemen untuk melengkapi model mereka setelah menonaktifkan auto-joins untuk mencegah crash.

## Fitur

- Gabung elemen terpilih (dengan seleksi interaktif jika tidak ada yang dipilih)
- Gabung elemen berdasarkan kategori (balok, kolom, lantai, fondasi, dinding)
- Pemrosesan batch untuk mencegah crash
- Pelaporan progress
- Filter seleksi untuk kategori struktur saja
- Dukungan mode dual: elemen terpilih atau semua elemen struktur
- Progress bar untuk feedback pengguna
- Manajemen memori dengan garbage collection
- Toast notification untuk penyelesaian

## Kategori Elemen yang Didukung

- Structural Framing (balok, penyangga)
- Structural Columns (kolom struktur)
- Floors (lantai)
- Structural Foundation (fondasi struktur)
- Walls (dinding)

## Penjelasan Kode Detail

### Import dan Setup
```python
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    ElementId,
    JoinGeometryUtils,
    Transaction,
    TransactionStatus,
    BoundingBoxIntersectsFilter,
    Outline,
    XYZ,
    ExclusionFilter,
    ElementIsElementTypeFilter
)
from Autodesk.Revit.UI.Selection import ISelectionFilter
from System.Collections.Generic import List

from pyrevit import revit, forms, script
```

### Konfigurasi
```python
# Configuration
ENABLE_PROGRESS_DETAIL = True  # Show detailed progress

# Structural categories that can be joined
STRUCTURAL_CATEGORIES = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_Walls
]
```

### Filter Seleksi Struktur
```python
class StructuralElementFilter(ISelectionFilter):
    """Selection filter to allow only structural elements."""

    def AllowElement(self, element):
        if element and element.Category:
            return element.Category.BuiltInCategory in STRUCTURAL_CATEGORIES
        return False

    def AllowReference(self, reference, position):
        # Not used for element selection
        return False
```

### Mode Seleksi
```python
def select_join_mode():
    """
    Let user select the join mode.

    Returns:
        str: Selected mode ('selection' or 'all_structural')
    """
    join_modes = [
        {'name': 'Elemen Terpilih', 'value': 'selection'},
        {'name': 'Semua Elemen', 'value': 'all_structural'}
    ]

    selected_mode_name = forms.SelectFromList.show(
        [mode['name'] for mode in join_modes],
        title='Pilih Mode Gabungan',
        button_name='Pilih Mode',
        multiselect=False
    )
```

### Proses Gabungan Elemen
```python
def process_join_elements(elements):
    """
    Process all elements and join them with intersecting structural elements.
    Follows the pattern from "Join Walls to Structure" script.

    Args:
        elements (list): List of elements to process

    Returns:
        tuple: (total_processed, successful_joins, failed_joins, error_messages)
    """
```

## Penggunaan

1. Jalankan skrip dari toolbar PyRevit
2. Pilih mode gabungan:
   - **Elemen Terpilih**: Gabung elemen yang sudah dipilih atau prompt untuk seleksi manual
   - **Semua Elemen**: Gabung semua elemen struktur dalam model
3. Tunggu proses selesai dengan progress bar
4. Tinjau ringkasan hasil dan toast notification

## Persyaratan

- Revit 2021 atau yang lebih baru
- PyRevit 4.7.11 atau yang lebih baru

## Catatan

- Skrip menggunakan toleransi 1mm untuk mendeteksi elemen yang menyentuh
- Mendukung pemrosesan batch untuk mencegah crash pada model besar
- Progress bar memberikan feedback real-time selama pemrosesan
- Toast notification menampilkan ringkasan hasil akhir
- Garbage collection digunakan untuk mengelola memori
- Semua operasi dibungkus dalam transaksi untuk keamanan

## Kemungkinan Peningkatan

1. **Optimasi Performa**:
    - Tambahkan opsi untuk filter berdasarkan level atau zona
    - Implementasi pemrosesan paralel
    - Tambahkan spatial indexing untuk filtering yang lebih cepat

2. **Fitur Tambahan**:
    - Tambahkan opsi untuk exclude kategori tertentu
    - Sertakan konfigurasi toleransi yang dapat disesuaikan
    - Tambahkan mode preview untuk highlight gabungan potensial

3. **Antarmuka Pengguna**:
    - Tambahkan opsi untuk pause/resume pemrosesan
    - Buat dialog konfigurasi lanjutan
    - Tambahkan statistik detail selama pemrosesan

4. **Penanganan Error**:
    - Tambahkan retry mechanism untuk gabungan yang gagal
    - Sertakan logging detail untuk troubleshooting
    - Tambahkan opsi untuk skip elemen bermasalah

5. **Validasi**:
    - Tambahkan pre-check untuk validitas geometri
    - Verifikasi struktur model sebelum pemrosesan
    - Tambahkan validasi hasil gabungan