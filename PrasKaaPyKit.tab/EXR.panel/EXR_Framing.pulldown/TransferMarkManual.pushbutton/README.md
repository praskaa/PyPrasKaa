# Transfer Mark by Manual

## Deskripsi

Skrip PyRevit ini memungkinkan transfer parameter Mark secara manual dari balok (beam) dalam model linked ke balok di model host. Proses ini dilakukan dengan pemilihan balok secara berpasangan antara model host dan linked, di mana nilai Mark diekstrak dari parameter Type Name balok linked dan ditransfer ke parameter Mark balok host.

## Fitur Utama

- **Pemilihan Manual**: Pengguna memilih balok host dan balok linked secara manual satu per satu
- **Ekstraksi Otomatis**: Nilai Mark diekstrak secara otomatis dari parameter Type Name balok linked
- **Loop Kontinyu**: Proses pemilihan berlanjut hingga pengguna menekan ESC
- **Validasi**: Memastikan elemen yang dipilih adalah Structural Framing (balok)
- **Konfirmasi Transfer**: Pengguna diminta konfirmasi sebelum transfer dilakukan

## Cara Kerja

1. **Pilih Model Linked**: Skrip meminta pengguna memilih model linked sebagai sumber data
2. **Tentukan Parameter Target**: Masukkan nama parameter target di balok host (default: "Mark")
3. **Loop Pemilihan**:
   - Pilih balok host dari proyek Anda
   - Pilih balok linked dari model linked
   - Ekstrak nilai Mark dari Type Name balok linked
   - Konfirmasi transfer
   - Ulangi hingga ESC ditekan

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
4. Klik OK untuk memulai proses pemilihan
5. **Pilih balok host**: Klik pada balok di model host Anda
6. **Pilih balok linked**: Klik pada balok di model linked
7. Konfirmasi transfer dengan klik "Yes"
8. Ulangi langkah 5-7 untuk balok lainnya
9. Tekan **ESC** untuk mengakhiri proses

## Output

Skrip menampilkan informasi detail di panel output PyRevit:

- Informasi balok host yang dipilih (Type, Mark saat ini, ID)
- Informasi balok linked yang dipilih (Type, Mark saat ini, ID)
- Nilai Mark yang diekstrak
- Status transfer (berhasil/gagal)

## Persyaratan

- Model host harus memiliki balok Structural Framing
- Model linked harus dimuat dan memiliki balok Structural Framing
- Parameter Type Name di balok linked harus mengikuti pola yang dapat diekstrak
- Parameter target di balok host harus dapat diedit (tidak read-only)

## Error Handling

- Jika tidak ada model linked: Skrip akan keluar dengan pesan error
- Jika elemen yang dipilih bukan balok: Pesan peringatan dan lanjut ke pemilihan berikutnya
- Jika ekstraksi Mark gagal: Pesan peringatan dan lanjut ke pemilihan berikutnya
- Jika parameter target tidak dapat diedit: Pesan error dan lanjut ke pemilihan berikutnya

## Contoh Penggunaan

### Skenario: Transfer Mark dari Model ETABS

1. Model Revit host berisi balok dengan parameter Mark kosong
2. Model ETABS di-link dengan balok yang memiliki Type Name seperti "G9-15", "G12-22", dll.
3. Jalankan skrip dan pilih model linked ETABS
4. Pilih balok host, lalu balok linked yang sesuai
5. Nilai "15", "22", dll. akan ditransfer ke parameter Mark balok host

## Tips

- Pastikan model linked sudah dimuat sebelum menjalankan skrip
- Gunakan zoom dan orbit untuk memilih balok dengan jelas
- Jika Type Name tidak mengikuti pola standar, ekstraksi mungkin gagal
- ESC dapat digunakan kapan saja untuk menghentikan proses

## Teknologi

- **Bahasa**: Python
- **Framework**: PyRevit
- **API**: Autodesk Revit API
- **Pola Regex**: Ekstraksi nilai Mark dari string

## Versi

- **Versi**: 1.0
- **Penulis**: Cline
- **Tanggal**: 2024

## Lisensi

Skrip ini adalah bagian dari PrasKaaPyKit extension untuk PyRevit.