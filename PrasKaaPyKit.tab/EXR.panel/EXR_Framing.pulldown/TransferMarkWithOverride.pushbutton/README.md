# Transfer Mark with Override

## Deskripsi

Skrip PyRevit ini melakukan transfer parameter Mark secara otomatis dari balok (beam) dalam model linked ke balok di model host berdasarkan kecocokan geometri. Skrip mencari pasangan balok antara model host dan linked dengan mencari volume intersection terbesar, kemudian mengekstrak nilai Mark dari parameter Type Name balok linked dan mentransfernya ke parameter Mark balok host.

## Fitur Utama

- **Pencocokan Otomatis**: Mencari balok yang cocok berdasarkan intersection volume geometri
- **Ekstraksi Otomatis**: Nilai Mark diekstrak dari parameter Type Name balok linked
- **Penanganan Error**: Balok yang tidak cocok atau gagal ekstraksi diberi tanda di parameter Comments
- **Progress Bar**: Menampilkan progress pemrosesan
- **Laporan Detail**: Menampilkan tabel hasil transfer dan balok yang tidak cocok

## Cara Kerja

1. **Pilih Model Linked**: Skrip meminta pengguna memilih model linked sebagai sumber data
2. **Tentukan Parameter Target**: Masukkan nama parameter target di balok host (default: "Mark")
3. **Kumpulkan Balok**: 
   - Jika ada seleksi, gunakan balok yang dipilih
   - Jika tidak ada seleksi, gunakan semua balok Structural Framing di proyek
4. **Pencocokan Geometri**: Cari balok linked yang memiliki intersection volume terbesar dengan setiap balok host
5. **Transfer Mark**: Ekstrak Mark dari Type Name dan transfer ke balok host
6. **Penanganan Error**: 
   - Jika ekstraksi gagal: Set Comments ke "Extract Fail"
   - Jika tidak ada kecocokan: Set Comments ke "Failed"

## Pola Ekstraksi Mark

Skrip menggunakan pola regex untuk mengekstrak angka dari parameter Type Name:

- `G9-99` → `99`
- `G5.99` → `99`
- `GA1-6-CJ` → `6`

Pola: Angka setelah "." atau "-" (opsional diikuti "-CI" atau "-CJ")

## Langkah Penggunaan

1. Jalankan skrip dari panel PyRevit
2. Pilih model linked dari daftar yang tersedia
3. Masukkan nama parameter target (biasanya "Mark")
4. **Opsional**: Pilih balok host yang ingin diproses (jika tidak dipilih, semua balok akan diproses)
5. Klik OK untuk memulai proses otomatis

## Output

Skrip menampilkan laporan detail di panel output PyRevit:

- **Tabel Updated Beams**: Daftar balok yang berhasil diupdate dengan detail ID, Type, Mark yang diekstrak
- **Unmatched Beams**: Daftar balok host yang tidak dapat dicocokkan dengan balok linked
- **Statistik**: Jumlah balok yang berhasil diupdate dari total balok

## Penanganan Error

- **Extract Fail**: Jika Type Name tidak mengikuti pola yang dapat diekstrak, parameter Comments di-set ke "Extract Fail"
- **Failed**: Jika balok host tidak dapat dicocokkan dengan balok linked manapun, parameter Comments di-set ke "Failed"
- **Read-only Parameter**: Jika parameter target tidak dapat diedit, balok tersebut dilewati

## Persyaratan

- Model host harus memiliki balok Structural Framing
- Model linked harus dimuat dan memiliki balok Structural Framing
- Parameter Type Name di balok linked harus mengikuti pola yang dapat diekstrak
- Parameter target di balok host harus dapat diedit (tidak read-only)
- Parameter Comments di balok host harus dapat diedit untuk penandaan error

## Contoh Penggunaan

### Skenario: Transfer Mark dari Model ETABS

1. Model Revit host berisi balok yang perlu diberi Mark
2. Model ETABS di-link dengan balok yang memiliki Type Name seperti "G9-15", "G12-22", dll.
3. Jalankan skrip dan pilih model linked ETABS
4. Skrip otomatis mencocokkan balok berdasarkan geometri
5. Nilai "15", "22", dll. ditransfer ke parameter Mark balok host yang cocok
6. Balok yang tidak cocok akan ditandai di Comments

## Tips

- Pastikan geometri balok di model host dan linked sudah akurat untuk pencocokan yang baik
- Jika hasil pencocokan tidak memuaskan, gunakan versi manual untuk kontrol lebih baik
- Periksa parameter Comments setelah proses untuk melihat balok yang bermasalah
- Gunakan seleksi untuk memproses hanya balok tertentu jika diperlukan

## Teknologi

- **Bahasa**: Python
- **Framework**: PyRevit
- **API**: Autodesk Revit API
- **Algoritma**: Pencocokan berdasarkan volume intersection geometri
- **Pola Regex**: Ekstraksi nilai Mark dari string

## Perbedaan dengan Versi Manual

- **Otomatis vs Manual**: Versi ini otomatis, sedangkan versi manual memerlukan pemilihan manual
- **Pencocokan**: Berdasarkan geometri vs pemilihan manual
- **Skala**: Dapat memproses banyak balok sekaligus vs satu per satu
- **Error Handling**: Menggunakan Comments untuk penandaan vs pesan dialog

## Versi

- **Versi**: 1.0
- **Penulis**: Cline
- **Tanggal**: 2024

## Lisensi

Skrip ini adalah bagian dari PrasKaaPyKit extension untuk PyRevit.