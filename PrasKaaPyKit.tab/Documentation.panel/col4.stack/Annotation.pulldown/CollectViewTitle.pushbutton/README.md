# Dokumentasi Skrip Export View Revit ke CSV

## Deskripsi
Skrip Python ini dirancang untuk digunakan dalam lingkungan pyRevit pada Autodesk Revit. Skrip ini mengumpulkan data dari berbagai jenis view (Plan, Section, dan Schedule) dalam dokumen Revit aktif, kemudian mengekspor data tersebut ke dalam file CSV. File CSV akan disimpan di folder Documents pengguna dengan nama `Revit_ViewTitles.csv`.

Skrip ini berguna untuk mengaudit atau mengelola view dalam proyek Revit, memberikan informasi seperti nama view, deskripsi, subkategori, dan sheet yang mereferensikan view tersebut.

## Persyaratan Sistem
- **Autodesk Revit**: Versi yang kompatibel dengan pyRevit (disarankan versi 2018 atau lebih baru).
- **pyRevit**: Ekstensi Python untuk Revit yang diperlukan untuk menjalankan skrip ini.
- **Python**: IronPython (versi yang disertakan dengan pyRevit).
- **Modul Python**: `csv`, `os`, `codecs` (sudah tersedia di IronPython), dan modul dari `pyrevit` serta `Autodesk.Revit.DB`.

## Cara Kerja Skrip
Skrip ini bekerja melalui langkah-langkah berikut:

1. **Inisialisasi Dokumen**: Mendapatkan dokumen Revit aktif melalui `__revit__.ActiveUIDocument.Document`.

2. **Pengumpulan Data View**:
   - Menggunakan `FilteredElementCollector` untuk mengumpulkan view berdasarkan tipe:
     - `ViewPlan`: View plan (lantai).
     - `ViewSection`: View section (potongan).
     - `ViewSchedule`: View schedule (jadwal).
   - Untuk setiap view, skrip mengambil parameter berikut:
     - **Nama View**: Nama view dari properti `v.Name`.
     - **Deskripsi (Title on Sheet)**: Dari parameter `BuiltInParameter.VIEW_DESCRIPTION`.
     - **Subkategori (View Type Detail)**: Dari parameter `BuiltInParameter.VIEW_TYPE`.
     - **Sheet Referensi**: Dari parameter `BuiltInParameter.VIEW_REFERENCING_SHEET`.

3. **Penyimpanan Data**: Data dikumpulkan dalam list of tuples, kemudian digabungkan dari semua tipe view.

4. **Eksport ke CSV**:
   - Path file: `~/Documents/Revit_ViewTitles.csv` (diperluas menggunakan `os.path.expanduser("~")`).
   - Menggunakan `codecs.open` dengan encoding UTF-8 untuk menangani karakter non-ASCII.
   - Header CSV: `["View Type", "Name", "Title", "Sub Category", "Referencing Sheet"]`.
   - Setiap baris berisi data untuk satu view.

5. **Notifikasi Pengguna**: Menampilkan toast notification menggunakan `forms.toast` dari pyRevit, dengan opsi untuk membuka folder atau file CSV.

## Penggunaan
1. Pastikan pyRevit terinstal dan aktif di Revit.
2. Buka dokumen Revit yang ingin diekspor datanya.
3. Jalankan skrip `script.py` melalui pyRevit (biasanya melalui panel ekstensi atau command).
4. Skrip akan secara otomatis membuat file CSV dan menampilkan notifikasi.
5. Klik opsi di notifikasi untuk membuka lokasi file atau membuka file CSV langsung.

### Contoh Output CSV
Berikut adalah contoh isi file CSV yang dihasilkan:

```
View Type,Name,Title,Sub Category,Referencing Sheet
Plan,Floor Plan 1,Drawing of Level 1,Floor Plan,A101
Section,Section A-A,Vertical Section,Building Section,S201
Schedule,Door Schedule,List of Doors,Schedule,S102
```

## Struktur Kode
- **Import Modul**: Mengimpor modul yang diperlukan untuk operasi file, Revit API, dan UI pyRevit.
- **Fungsi `collect_views(viewtype, typename)`**: Fungsi utama untuk mengumpulkan data view. Mengembalikan list of tuples berisi data view.
- **Pengumpulan Data Utama**: Memanggil `collect_views` untuk setiap tipe view dan menggabungkan hasilnya.
- **Penulisan CSV**: Menggunakan `csv.writer` untuk menulis data ke file.
- **Notifikasi**: Menggunakan `forms.toast` untuk memberikan feedback kepada pengguna.

## Penanganan Error dan Batasan
- Skrip ini mengasumsikan bahwa parameter view tersedia dan memiliki nilai. Jika parameter kosong, nilai akan diisi dengan string kosong.
- Encoding UTF-8 digunakan untuk mendukung karakter internasional dalam nama view atau deskripsi.
- Jika file CSV sudah ada, skrip akan menimpanya tanpa konfirmasi.
- Skrip hanya mengumpulkan view yang terlihat dan aktif dalam dokumen; view yang dihapus atau disembunyikan tidak akan disertakan.

## Tips dan Best Practices
- Jalankan skrip setelah semua view telah dibuat dan diberi nama dengan benar untuk hasil yang akurat.
- Periksa file CSV setelah ekspor untuk memastikan data lengkap.
- Jika proyek besar, pertimbangkan untuk memfilter view tertentu jika diperlukan (modifikasi skrip dapat dilakukan).
- Backup file CSV sebelum menjalankan ulang jika data sebelumnya penting.

## Lisensi dan Kontribusi
Skrip ini dibuat untuk keperluan internal atau pribadi. Jika ingin berkontribusi atau memodifikasi, pastikan perubahan kompatibel dengan versi Revit dan pyRevit yang digunakan.

## Kontak
Untuk pertanyaan atau dukungan, silakan hubungi pengembang skrip atau komunitas pyRevit.

---
*Dokumentasi ini dibuat untuk memudahkan pemahaman dan penggunaan skrip `script.py`. Pastikan untuk mengikuti persyaratan sistem sebelum menjalankan skrip.*