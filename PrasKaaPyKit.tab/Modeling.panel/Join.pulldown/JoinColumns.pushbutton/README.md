# Join Columns

Skrip PyRevit untuk menggabungkan kolom struktur dengan elemen sekitar (balok, lantai, fondasi, dinding) dan memastikan kolom menang dalam urutan gabungan.

## Deskripsi

Skrip ini secara otomatis menggabungkan kolom struktur yang dipilih dengan elemen struktur sekitar yang bersinggungan, dan memastikan kolom selalu menang dalam urutan gabungan (join order).

## Fitur

- Gabung kolom dengan elemen sekitar secara otomatis
- Mendukung balok, lantai, fondasi, dan dinding
- Pastikan kolom selalu menang dalam join order
- Seleksi otomatis: gunakan kolom terpilih atau prompt untuk memilih
- Proses silent tanpa output atau dialog

## Elemen yang Digabungkan

Kolom akan digabungkan dengan:
- Structural Framing (balok, penyangga)
- Floors (lantai)
- Structural Foundation (fondasi)
- Walls (dinding)

## Penggunaan

1. **Dengan kolom terpilih**: Pilih kolom struktur terlebih dahulu, lalu jalankan tool
2. **Tanpa seleksi**: Jalankan tool dan Anda akan diminta memilih kolom
3. Tool akan memproses semua kolom yang dipilih secara silent

## Persyaratan

- Revit 2018 atau yang lebih baru
- PyRevit extension
- Kolom struktur dalam model

## Teknis

- Menggunakan bounding box intersection untuk deteksi elemen sekitar
- Toleransi 1mm untuk menangkap elemen yang bersinggungan
- Semua operasi dalam transaction untuk keamanan
- Error handling silent - tool akan melanjutkan meski ada elemen yang tidak bisa digabungkan