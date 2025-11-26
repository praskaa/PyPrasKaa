# Dokumentasi Skrip Sinkronisasi Visibilitas Grid

## Deskripsi
Skrip Python ini dirancang untuk digunakan dalam lingkungan pyRevit pada Autodesk Revit. Skrip ini menyalin status visibilitas grid dari satu view sumber ke satu atau lebih view target. Berguna untuk menyamakan tampilan grid di berbagai view dalam proyek, seperti plan, section, dan elevation.

## Persyaratan Sistem
- **Autodesk Revit**: Versi yang kompatibel dengan pyRevit (disarankan 2018 atau lebih baru).
- **pyRevit**: Ekstensi Python untuk Revit.
- **Python**: IronPython (versi yang disertakan dengan pyRevit).
- **Modul**: `pyrevit`, `Autodesk.Revit.DB`, `System.Collections.Generic`.

## Cara Kerja Skrip
1. **Pengumpulan View Kandidat**: Mengumpulkan view non-template dengan tipe FloorPlan, EngineeringPlan, CeilingPlan, Section, Elevation, atau AreaPlan.
2. **Pemilihan View Sumber**: Menampilkan dialog untuk memilih satu view sebagai acuan visibilitas grid.
3. **Pemilihan View Target**: Menampilkan dialog multiselect untuk memilih view yang akan disinkronkan.
4. **Perhitungan Visibilitas**:
   - Mengumpulkan ID grid yang visible di view sumber menggunakan FilteredElementCollector.
   - Untuk setiap view target, hitung grid yang perlu di-show atau di-hide.
5. **Penerapan Perubahan**: Menggunakan transaksi untuk:
   - Unhide grid yang visible di sumber tapi hidden di target.
   - Hide grid yang hidden di sumber tapi visible di target.
   - Memastikan kategori Grid tidak disembunyikan jika perlu.
6. **Notifikasi**: Menampilkan toast per view target dengan jumlah show/hide, dan ringkasan akhir.

## Penggunaan
1. Jalankan skrip melalui pushbutton pyRevit.
2. Pilih view sumber dari daftar yang muncul.
3. Pilih satu atau lebih view target.
4. Skrip akan menyinkronkan visibilitas dan memberikan feedback.

### Contoh Penggunaan
- **Sumber**: Floor Plan Level 1, di mana grid A, B, C visible.
- **Target**: Section A-A dan Elevation North.
- Hasil: Di Section A-A dan Elevation North, grid A, B, C akan dibuat visible, dan grid lain disembunyikan jika diperlukan.

## Struktur Kode
- **Fungsi `candidate_views()`**: Mengumpulkan view kandidat.
- **Fungsi `get_visible_grids_in_view(view)`**: Mengembalikan set ID grid visible di view.
- **Fungsi `ensure_grid_category_visible(view)`**: Memastikan kategori Grid tidak hidden.
- **Fungsi `hide_in_view(view, ids_iter)` dan `unhide_in_view(view, ids_iter)`**: Mengelola visibilitas grid.
- **Proses Utama**: Pemilihan view dan penerapan sinkronisasi dalam transaksi.

## Penanganan Error dan Batasan
- Jika tidak ada view kandidat, skrip keluar dengan alert.
- Menggunakan try-except untuk operasi hide/unhide.
- Hanya berlaku untuk view tipe tertentu; template view dikecualikan.
- Transaksi dibatalkan jika error terjadi.

## Tips dan Best Practices
- Pilih view sumber yang representatif untuk visibilitas grid yang diinginkan.
- Jalankan secara bertahap untuk proyek besar.
- Periksa hasil di view target setelah sinkronisasi.

## Lisensi dan Kontribusi
Skrip ini untuk keperluan pribadi. Modifikasi harus mempertimbangkan kompatibilitas versi.

---
*Dokumentasi ini untuk skrip `script.py` di folder `CopyStateViewGrid.pushbutton`.*