# Join Walls to Structure

Skrip PyRevit yang secara otomatis menggabungkan dinding dengan elemen struktur dan memastikan urutan pemotongan yang benar.

## Deskripsi

Skrip ini mengotomatisasi proses penggabungan dinding dengan elemen struktur (kolom, balok, fondasi, dll.) dan memastikan bahwa elemen struktur memotong dinding dengan benar. Menggunakan pendekatan bounding box yang diperluas untuk menangkap elemen yang bersinggungan dan menyentuh.

## Fitur

- Menggabungkan dinding dengan berbagai jenis elemen struktur
- Menangani model group yang berisi elemen struktur
- Termasuk toleransi kecil untuk elemen yang menyentuh
- Secara otomatis mengatur urutan gabungan yang benar
- Memberikan ringkasan hasil yang jelas
- **Smart Selection**: Mendukung seleksi yang sudah ada atau prompt manual
- Kompatibilitas lintas versi Revit (2020-2026+)
- Penanganan error yang komprehensif dengan ID elemen

## Kategori Elemen yang Didukung

- Structural Framing (balok, penyangga)
- Structural Columns (kolom struktur)
- Floors (lantai)
- Structural Foundations (fondasi struktur)
- Structural Walls (dinding struktur)
- Model Groups (grup model)

## Penjelasan Kode Detail

### Import dan Setup
```python
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
from pyrevit import forms, script, revit

# Import smart selection utility
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logic-library', 'active', 'utilities', 'selection'))
from smart_selection import get_filtered_selection
```
Import penting untuk akses Revit API dan fungsionalitas PyRevit, termasuk utility smart selection.

### Konfigurasi
```python
structural_categories = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_Walls,
    BuiltInCategory.OST_IOSModelGroups
]
```
Mendefinisikan kategori elemen mana yang akan diproses untuk penggabungan.

### Seleksi Elemen Pintar
```python
# Get filtered walls using smart selection
walls_to_process = get_filtered_selection(
    doc=doc,
    uidoc=uidoc,
    category_filter_func=lambda elem: isinstance(elem, Wall),
    prompt_message="Select Walls to join with structure",
    no_selection_message="No walls selected. Please select walls to process.",
    filter_name="Wall Selection"
)
```
Menggunakan utility smart selection untuk mendapatkan dinding yang akan diproses, dengan dukungan pre-selection dan fallback manual.

### Koleksi Elemen
```python
wall_bb = wall.get_BoundingBox(None)
tolerance = 0.001  # 1mm tolerance
expanded_min = XYZ(wall_bb.Min.X - tolerance,
                  wall_bb.Min.Y - tolerance,
                  wall_bb.Min.Z - tolerance)
expanded_max = XYZ(wall_bb.Max.X + tolerance,
                  wall_bb.Max.Y + tolerance,
                  wall_bb.Max.Z + tolerance)
```
Membuat bounding box yang sedikit diperluas di sekitar setiap dinding untuk menangkap elemen yang bersinggungan dan menyentuh.

### Filtering Elemen
```python
bb_filter = BoundingBoxIntersectsFilter(outline)
ids_to_exclude = List[ElementId]([wall.Id])
exclude_self_filter = ExclusionFilter(ids_to_exclude)
not_element_type_filter = ElementIsElementTypeFilter(True)
```
Mengatur filter untuk:
- Mencari elemen dalam bounding box yang diperluas
- Mengecualikan dinding itu sendiri
- Memfilter element type (kita hanya ingin instance)

### Proses Gabungan
```python
if not JoinGeometryUtils.AreElementsJoined(doc, wall, intersecting_element):
    JoinGeometryUtils.JoinGeometry(doc, wall, intersecting_element)
```
Mencoba menggabungkan elemen yang belum tergabung.

### Manajemen Urutan Gabungan
```python
if JoinGeometryUtils.IsCuttingElementInJoin(doc, wall, joined_element):
    JoinGeometryUtils.SwitchJoinOrder(doc, wall, joined_element)
```
Memastikan elemen struktur memotong dinding dengan memeriksa dan menyesuaikan urutan gabungan.

## Kemungkinan Peningkatan

1. **Optimasi Performa**:
    - Tambahkan opsi untuk filter berdasarkan level atau zona
    - Implementasi pemrosesan paralel untuk multiple walls
    - Tambahkan spatial indexing untuk filtering elemen yang lebih cepat

2. **Fitur Tambahan**:
    - Tambahkan opsi untuk gabung dengan elemen non-struktur
    - Sertakan preferensi urutan gabungan per kategori
    - Tambahkan kemampuan undo/redo
    - Tambahkan mode preview untuk highlight gabungan potensial
    - Tambahkan dukungan untuk curtain walls dan panels

3. **Antarmuka Pengguna**:
    - Tambahkan progress bar untuk operasi besar
    - Tambahkan seleksi elemen interaktif
    - Buat dialog opsi untuk kustomisasi:
      - Penyesuaian toleransi
      - Seleksi kategori
      - Preferensi urutan gabungan

4. **Penanganan Error**:
    - Tambahkan mekanisme retry untuk gabungan yang gagal
    - Tambahkan opsi logging detail
    - Sertakan feedback visual untuk gabungan yang gagal
    - Tambahkan opsi untuk skip elemen bermasalah

5. **Validasi**:
    - Tambahkan pre-check untuk validitas elemen
    - Tambahkan validasi geometri sebelum penggabungan
    - Periksa nested groups/links
    - Verifikasi properti struktur

## Penggunaan

1. Pilih satu atau lebih dinding di Revit (atau biarkan kosong untuk prompt manual)
2. Jalankan skrip dari toolbar PyRevit
3. Tinjau ringkasan hasil

## Persyaratan

- Revit 2020 atau yang lebih baru
- PyRevit 4.7.11 atau yang lebih baru

## Catatan

- Skrip menggunakan toleransi 1mm untuk mendeteksi elemen yang menyentuh
- Elemen struktur akan selalu memotong dinding
- Model groups didukung tetapi mungkin memerlukan waktu pemrosesan tambahan
- Semua operasi dibungkus dalam satu transaksi untuk performa yang lebih baik
- Menggunakan utility smart selection untuk pengalaman pengguna yang lebih baik
