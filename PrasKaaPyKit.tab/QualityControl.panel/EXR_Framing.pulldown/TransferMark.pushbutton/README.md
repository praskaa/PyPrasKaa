# Transfer Mark (Fixed Coordinates)

## Deskripsi

Skrip PyRevit ini melakukan transfer parameter Mark secara otomatis dari balok (beam) dalam model linked ke balok di model host berdasarkan kecocokan geometri dengan transformasi koordinat. Skrip mencari pasangan balok antara model host dan linked dengan mencari volume intersection terbesar, dengan memperhitungkan transformasi koordinat untuk menangani perbedaan origin internal dan koordinat bersama, kemudian mengekstrak nilai Mark dari parameter Type Name balok linked dan mentransfernya ke parameter Mark balok host.

## Fitur Utama

- **Transformasi Koordinat**: Menangani perbedaan origin internal antara model host dan linked
- **Pencocokan Otomatis**: Mencari balok yang cocok berdasarkan intersection volume geometri
- **Ekstraksi Otomatis**: Nilai Mark diekstrak dari parameter Type Name balok linked
- **Progress Bar**: Menampilkan progress pemrosesan
- **Laporan Detail**: Menampilkan tabel hasil transfer dan balok yang tidak cocok

## Cara Kerja

1. **Pilih Model Linked**: Skrip meminta pengguna memilih model linked sebagai sumber data
2. **Dapatkan Transformasi**: Mengambil matriks transformasi dari instance linked
3. **Tentukan Parameter Target**: Masukkan nama parameter target di balok host (default: "Mark")
4. **Kumpulkan Balok**:
   - Jika ada seleksi, gunakan balok yang dipilih
   - Jika tidak ada seleksi, gunakan semua balok Structural Framing di proyek
5. **Pencocokan Geometri**: Cari balok linked yang memiliki intersection volume terbesar dengan setiap balok host, dengan memperhitungkan transformasi koordinat
6. **Transfer Mark**: Ekstrak Mark dari Type Name dan transfer ke balok host

## Pola Ekstraksi Mark

Skrip menggunakan pola regex untuk mengekstrak angka dari parameter Type Name:

- `G9-99` → `99`
- `G5.99` → `99`
- `GA1-6-CJ` → `6`

Pola: Angka setelah "." atau "-" (opsional diikuti "-CI" atau "-CJ")

## Transformasi Koordinat

Versi ini menangani masalah koordinat yang kompleks dalam model Revit:

- **Origin Internal**: Perbedaan titik origin antara model host dan linked
- **Koordinat Bersama**: Shared coordinates yang mungkin berbeda
- **Transformasi Matriks**: Menerapkan transformasi penuh (translation, rotation, scaling) dari instance linked

## Langkah Penggunaan

1. Jalankan skrip dari panel PyRevit
2. Pilih model linked dari daftar yang tersedia
3. Masukkan nama parameter target (biasanya "Mark")
4. **Opsional**: Pilih balok host yang ingin diproses (jika tidak dipilih, semua balok akan diproses)
5. Klik OK untuk memulai proses otomatis dengan transformasi koordinat

## Output

Skrip menampilkan laporan detail di panel output PyRevit:

- **Konfirmasi Transformasi**: Menunjukkan bahwa transformasi koordinat telah diterapkan
- **Tabel Updated Beams**: Daftar balok yang berhasil diupdate dengan detail ID, Type, Mark yang diekstrak
- **Unmatched Beams**: Daftar balok host yang tidak dapat dicocokkan dengan balok linked
- **Statistik**: Jumlah balok yang berhasil diupdate dari total balok

## Persyaratan

- Model host harus memiliki balok Structural Framing
- Model linked harus dimuat dan memiliki balok Structural Framing
- Parameter Type Name di balok linked harus mengikuti pola yang dapat diekstrak
- Parameter target di balok host harus dapat diedit (tidak read-only)
- Instance linked harus memiliki transformasi yang valid

## Contoh Penggunaan

### Skenario: Transfer Mark dari Model ETABS dengan Koordinat Berbeda

1. Model Revit host dan model ETABS linked memiliki origin yang berbeda
2. Balok di kedua model memiliki geometri yang sama tetapi posisi koordinat berbeda
3. Jalankan skrip dan pilih model linked ETABS
4. Skrip otomatis menerapkan transformasi koordinat
5. Pencocokan geometri dilakukan dalam koordinat yang benar
6. Mark ditransfer berdasarkan kecocokan geometri yang akurat

## Tips

- Gunakan versi ini ketika model linked memiliki koordinat yang berbeda dari host
- Jika model menggunakan shared coordinates dengan benar, versi ini memberikan hasil yang lebih akurat
- Periksa log untuk informasi detail tentang matriks transformasi yang diterapkan
- Jika hasil masih tidak memuaskan, periksa pengaturan koordinat di model linked

## Teknologi

- **Bahasa**: Python
- **Framework**: PyRevit
- **API**: Autodesk Revit API
- **Transformasi**: Matriks transformasi koordinat 4x4
- **Algoritma**: Pencocokan berdasarkan volume intersection dengan transformasi
- **Pola Regex**: Ekstraksi nilai Mark dari string

## Perbedaan dengan Versi Lain

- **Transformasi Koordinat**: Versi ini memiliki transformasi koordinat, versi "with Override" tidak
- **Akurasi**: Lebih akurat untuk model dengan koordinat berbeda
- **Kompleksitas**: Menangani kasus koordinat yang lebih kompleks
- **Logging**: Menampilkan informasi detail tentang transformasi yang diterapkan

## Troubleshooting Koordinat

Jika pencocokan masih bermasalah:

1. Periksa apakah model linked menggunakan shared coordinates
2. Pastikan instance linked tidak memiliki rotasi atau scaling yang tidak diinginkan
3. Gunakan "Reload From" pada instance linked jika perlu
4. Periksa origin internal model melalui Manage > Inquiry > Project Base Point

## Versi

- **Versi**: 1.0
- **Penulis**: Cline
- **Tanggal**: 2024

## Lisensi

Skrip ini adalah bagian dari PrasKaaPyKit extension untuk PyRevit.