# Matching Dimension

## Deskripsi

Skrip PyRevit ini melakukan pencocokan balok antara model host dan model linked EXR (dari ETABS) berdasarkan volume geometri yang berintersect. Setelah menemukan pasangan balok terbaik, skrip mentransfer family type (dimensi) dari balok linked ke balok host, sehingga mensinkronkan dimensi balok antara model analitik (ETABS) dan model dokumentasi (Revit).

## Fitur Utama

- **Pencocokan Geometri Otomatis**: Mencari balok yang cocok berdasarkan volume intersection maksimal
- **Transfer Type Balok**: Mengubah family type balok host sesuai dengan linked
- **Opsi Transformasi Koordinat**: Mendukung model dengan origin berbeda (untuk enhancement future)
- **Progress Tracking**: Menampilkan progress pemrosesan dengan progress bar
- **Laporan Detail**: Tabel hasil transfer dan daftar balok yang tidak cocok
- **Error Handling**: Penanganan komprehensif untuk berbagai skenario error

## Cara Kerja

1. **Pilih Model Linked EXR**: Skrip meminta pengguna memilih model EXR dari ETABS yang di-link
2. **Opsi Transformasi**: Pilih apakah menggunakan transformasi koordinat (untuk model dengan origin berbeda)
3. **Kumpulkan Balok**: Mengumpulkan balok dari host (seleksi atau semua) dan linked
4. **Pencocokan Geometri**: Hitung volume intersection antara setiap balok host dengan semua balok linked
5. **Transfer Type**: Ubah family type balok host yang cocok sesuai balok linked
6. **Laporan**: Tampilkan hasil transfer, kegagalan, dan balok yang tidak cocok

## Algoritma Pencocokan

Skrip menggunakan algoritma intersection volume untuk mencocokkan balok:

- Ekstrak geometri solid dari setiap balok
- Hitung volume intersection antara solid host dan linked
- Pilih balok linked dengan volume intersection terbesar
- Jika volume > 0, anggap sebagai match

## Langkah Penggunaan

1. Jalankan skrip dari panel PyRevit
2. **Konfigurasi Output**: Pilih opsi tampilan output:
   - ✅ **Show old host type in results** (default: enabled) - Tampilkan type lama sebelum transfer
   - ⭕ **Show detailed unmatched beams list** (default: disabled) - Tampilkan semua balok unmatched
3. Pilih model linked EXR dari daftar yang tersedia
4. **Opsional**: Pilih balok host yang ingin diproses (jika tidak dipilih, semua balok akan diproses)
5. Klik OK untuk memulai proses otomatis pencocokan dan transfer type

## Output

Skrip menampilkan laporan komprehensif di panel output PyRevit:

- **Ringkasan Proses**: Jumlah balok yang diproses dan dicocokkan
- **Tabel Transfer Berhasil**: Daftar balok yang berhasil diubah typenya dengan detail:
  - Host Beam ID
  - **Old Host Type** (type sebelum transfer - jika diaktifkan)
  - New Host Type (type setelah transfer)
  - Matched Linked ID
  - Linked Type Name
  - Family Name
- **Tabel Transfer Gagal**: Daftar balok yang gagal diubah dengan alasan kegagalan
- **Balok Tidak Cocok**: Summary atau detail lengkap balok yang tidak menemukan pasangan

### Opsi Tampilan Output

- **Show old host type in results** (default: ✅ enabled)
  - Menampilkan kolom "Old Host Type" untuk melihat perubahan type
  - Membantu tracking perubahan yang terjadi

- **Show detailed unmatched beams list** (default: ❌ disabled)
  - **Disabled**: Menampilkan sample 10 beams + statistik type distribution
  - **Enabled**: Menampilkan semua unmatched beams (bisa sangat panjang)

## Persyaratan

- Model host harus memiliki balok Structural Framing
- Model linked EXR harus dimuat dan memiliki balok Structural Framing
- Family dan type balok yang akan ditransfer harus sudah ada di model host
- Model linked harus dari export ETABS (EXR) dengan geometri yang sesuai

## Penanganan Error

- **Model Linked Tidak Ditemukan**: Skrip akan keluar dengan pesan error
- **Tidak Ada Balok**: Error jika tidak ada balok di host atau linked
- **Type Tidak Ada**: Transfer dilewati jika family/type tidak ditemukan di host
- **Geometry Error**: Balok dengan geometri bermasalah akan dilewati
- **Intersection Gagal**: Menggunakan logging untuk melacak kegagalan boolean operations

## Contoh Penggunaan

### Skenario: Sinkronisasi Dimensi dari ETABS

1. Model Revit host memiliki balok dengan type yang salah/sementara
2. Model EXR dari ETABS di-link dengan dimensi balok yang benar
3. Jalankan skrip Matching Dimension
4. Pilih model linked EXR
5. Skrip otomatis mencocokkan balok berdasarkan geometri
6. Type balok host diubah sesuai dimensi dari ETABS
7. Balok yang tidak cocok akan dilaporkan untuk verifikasi manual

## Tips Penggunaan

- Pastikan geometri balok di EXR sudah akurat dan sesuai dengan kondisi konstruksi
- Jika hasil pencocokan tidak memuaskan, periksa skala dan posisi model linked
- Gunakan seleksi untuk memproses hanya area tertentu jika model terlalu besar
- Periksa tabel "Failed Transfers" untuk melihat type yang perlu ditambahkan ke model host
- Untuk model dengan koordinat berbeda, aktifkan opsi transformasi koordinat

## Transformasi Koordinat

Fitur transformasi koordinat saat ini dinonaktifkan dan akan diimplementasi di versi future untuk menangani:

- **Origin Berbeda**: Perbedaan titik origin antara model host dan EXR
- **Shared Coordinates**: Koordinat bersama yang tidak konsisten
- **Rotasi dan Translasi**: Transformasi kompleks dari instance linked

Untuk model dengan koordinat berbeda, pastikan model linked sudah dalam koordinat yang benar sebelum menggunakan skrip ini.

## Teknologi

- **Bahasa**: Python
- **Framework**: PyRevit
- **API**: Autodesk Revit API
- **Algoritma**: Pencocokan berdasarkan volume intersection geometri
- **Geometri**: Solid boolean operations untuk kalkulasi intersection

## Perbedaan dengan Skrip Lain

- **Transfer Mark**: Fokus pada parameter Mark (string), bukan type
- **Manual Selection**: Memerlukan pemilihan manual vs otomatis
- **Intersection vs Manual**: Berdasarkan geometri vs input user

## Troubleshooting

### Masalah: Tidak Ada Match Ditemukan
- Periksa geometri balok di EXR apakah sudah benar
- Verifikasi posisi dan rotasi model linked
- Coba aktifkan opsi transformasi koordinat

### Masalah: Type Tidak Ditemukan
- Pastikan family balok dari EXR sudah dimuat di model host
- Tambahkan family yang missing secara manual
- Periksa nama family dan type apakah sama persis

### Masalah: Performance Lambat
- Gunakan seleksi balok tertentu instead of semua balok
- Pastikan model tidak terlalu kompleks
- Tutup view lain untuk mengurangi beban memory

## Versi

- **Versi**: 1.0
- **Penulis**: Cline
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+, PyRevit

## Lisensi

Skrip ini adalah bagian dari PrasKaaPyKit extension untuk PyRevit.

## Future Enhancements

- Auto-loading missing families dari linked model
- Support untuk coordinate transformation penuh
- Batch processing untuk multiple linked models
- Advanced matching algorithms (centerline distance, etc.)
- Undo support untuk revert changes