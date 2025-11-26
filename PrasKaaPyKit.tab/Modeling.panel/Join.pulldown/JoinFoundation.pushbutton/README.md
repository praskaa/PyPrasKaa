# Join Foundation

Skrip PyRevit yang menggabungkan fondasi struktur dengan elemen struktur yang bersinggungan (framing, kolom, lantai) dan memungkinkan pengguna untuk mendefinisikan prioritas gabungan.

## Deskripsi

Skrip ini menggabungkan fondasi struktur dengan elemen struktur yang bersinggungan dan menggunakan sistem prioritas berbasis hierarki untuk memastikan urutan pemotongan yang benar. Fondasi dengan prioritas lebih tinggi akan memotong elemen dengan prioritas lebih rendah.

## Fitur

- Seleksi manual dengan filtering fondasi spesifik
- Sistem prioritas berbasis hierarki untuk urutan gabungan
- Eksklusi tipe fondasi tertentu (misalnya pile types)
- Konfigurasi prioritas kustom
- Penanganan error komprehensif dengan ID elemen
- Ringkasan hasil yang detail

## Hierarki Prioritas Gabungan

Urutan prioritas (dari tertinggi ke terendah):
1. **Floors** (Lantai) - Prioritas tertinggi
2. **Structural Foundation** (Fondasi Struktur)
3. **Structural Columns** (Kolom Struktur)
4. **Structural Framing** (Framing Struktur)
5. **Walls** (Dinding) - Prioritas terendah

Elemen dengan prioritas lebih tinggi akan memotong elemen dengan prioritas lebih rendah.

## Kategori Elemen yang Didukung

- Structural Framing (balok, penyangga)
- Structural Columns (kolom struktur)
- Floors (lantai)
- Structural Foundation (fondasi struktur)
- Walls (dinding)

## Penjelasan Kode Detail

### Import dan Setup
```python
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType
from System.Collections.Generic import List
from pyrevit import forms
from pyrevit import script
from pyrevit import revit
```

### Konfigurasi Prioritas
```python
# Define join priority: Floor > Foundation > Column > Framing > Wall
# Elements higher in this list should cut elements lower in this list
join_priority_categories = [
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_Walls
]
```

### Filter Seleksi Fondasi
```python
class FoundationSelectionFilter(ISelectionFilter):
    def AllowElement(self, elem):
        # Allow only Structural Foundations during selection
        if hasattr(elem, "Category") and elem.Category and \
           elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFoundation):
            return True
        return False

    def AllowReference(self, refer, point):
        return False
```

### Eksklusi Tipe Fondasi
```python
# Filter out "Foundation Pile - Rectangular" after initial selection
foundations_to_process = []
excluded_count = 0
for foundation in initial_selected_foundations:
    # Get the element type of the foundation
    foundation_type = doc.GetElement(foundation.GetTypeId())
    # Check if the type exists and has a Name property before accessing it
    if foundation_type and hasattr(foundation_type, "Name") and foundation_type.Name == "Foundation Pile - Rectangular":
        excluded_count += 1
    else:
        foundations_to_process.append(foundation)
```

### Logika Switching Prioritas
```python
# Determine the priority of the foundation and the joined element
foundation_priority_idx = join_priority_categories.index(BuiltInCategory.OST_StructuralFoundation) \
    if BuiltInCategory.OST_StructuralFoundation in join_priority_categories else -1
joined_element_priority_idx = join_priority_categories.index(joined_cat) \
    if joined_cat in join_priority_categories else -1

# Priority-based switching logic
if foundation_priority_idx != -1 and joined_element_priority_idx != -1:
    # If foundation has higher priority and is currently being cut
    if foundation_priority_idx < joined_element_priority_idx:
        if JoinGeometryUtils.IsCuttingElementInJoin(doc, joined_element, foundation):
            JoinGeometryUtils.SwitchJoinOrder(doc, foundation, joined_element)
```

## Penggunaan

1. Jalankan skrip dari toolbar PyRevit
2. Pilih fondasi struktur yang ingin diproses (hanya fondasi yang akan ditampilkan)
3. Skrip akan secara otomatis menggabungkan fondasi dengan elemen struktur yang bersinggungan
4. Urutan gabungan akan disesuaikan berdasarkan hierarki prioritas
5. Tinjau ringkasan hasil yang mencakup jumlah gabungan berhasil dan gagal

## Persyaratan

- Revit 2021 atau yang lebih baru
- PyRevit 4.7.11 atau yang lebih baru

## Catatan

- Skrip secara otomatis mengecualikan tipe fondasi "Foundation Pile - Rectangular"
- Menggunakan toleransi 1mm untuk mendeteksi elemen yang menyentuh
- Hierarki prioritas: Lantai > Fondasi > Kolom > Framing > Dinding
- Semua operasi dibungkus dalam transaksi untuk keamanan
- Error dilaporkan dengan ID elemen untuk troubleshooting

## Kemungkinan Peningkatan

1. **Optimasi Performa**:
    - Tambahkan opsi untuk filter berdasarkan level atau zona
    - Implementasi pemrosesan paralel untuk multiple foundations
    - Tambahkan spatial indexing untuk filtering yang lebih cepat

2. **Fitur Tambahan**:
    - Tambahkan konfigurasi prioritas yang dapat disesuaikan pengguna
    - Sertakan opsi untuk include/exclude kategori tertentu
    - Tambahkan mode preview untuk highlight gabungan potensial
    - Tambahkan dukungan untuk foundation types kustom

3. **Antarmuka Pengguna**:
    - Tambahkan progress bar untuk operasi besar
    - Buat dialog konfigurasi prioritas
    - Tambahkan opsi untuk batch processing
    - Sertakan statistik detail selama pemrosesan

4. **Penanganan Error**:
    - Tambahkan retry mechanism untuk gabungan yang gagal
    - Sertakan logging detail untuk troubleshooting
    - Tambahkan visual feedback untuk failed joins
    - Tambahkan opsi untuk skip elemen bermasalah

5. **Validasi**:
    - Tambahkan pre-check untuk validitas geometri fondasi
    - Verifikasi struktur model sebelum pemrosesan
    - Tambahkan validasi hasil gabungan
    - Periksa konsistensi tipe fondasi