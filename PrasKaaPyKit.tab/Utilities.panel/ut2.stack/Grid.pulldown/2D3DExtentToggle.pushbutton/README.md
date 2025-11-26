# Dokumentasi Skrip Toggle 2D/3D Extent Grid

## Deskripsi
Skrip Python ini dirancang untuk digunakan dalam lingkungan pyRevit pada Autodesk Revit. Skrip ini mengubah extent grid antara mode 2D (ViewSpecific) dan 3D (Model) di active view. Jika salah satu ujung grid sudah dalam mode 2D, akan diubah ke 3D, dan sebaliknya. Skrip bekerja pada grid yang dipilih pengguna, atau semua grid yang visible di active view jika tidak ada seleksi.

## Persyaratan Sistem
- **Autodesk Revit**: Versi yang kompatibel dengan pyRevit (disarankan 2018 atau lebih baru).
- **pyRevit**: Ekstensi Python untuk Revit.
- **Python**: IronPython (versi yang disertakan dengan pyRevit).
- **Modul**: `pyrevit`, `Autodesk.Revit.DB`.

## Cara Kerja Skrip
1. **Inisialisasi**: Mendapatkan dokumen aktif, UI document, dan active view.
2. **Identifikasi Grid Target**:
   - Jika ada elemen yang dipilih, filter yang merupakan Grid.
   - Jika tidak, kumpulkan semua Grid yang visible di active view menggunakan FilteredElementCollector.
3. **Pengecekan Status Extent**: Untuk setiap grid, cek apakah salah satu ujung (End0 atau End1) dalam mode ViewSpecific (2D).
4. **Toggle Extent**: Menggunakan transaksi untuk mengubah tipe extent:
   - Jika sudah 2D, ubah ke Model (3D).
   - Jika tidak, ubah ke ViewSpecific (2D).
5. **Notifikasi**: Menampilkan jumlah grid yang diproses, di-toggle ke 2D, dan ke 3D menggunakan forms.toast.

## Penggunaan
1. Buka view Revit yang ingin dimodifikasi (misalnya plan view).
2. Pilih grid tertentu jika ingin toggle spesifik (opsional).
3. Jalankan skrip melalui pushbutton pyRevit.
4. Skrip akan memproses grid dan menampilkan ringkasan.

### Contoh Penggunaan
- **Tanpa Seleksi**: Semua grid visible di view akan di-toggle berdasarkan status extent mereka.
- **Dengan Seleksi**: Hanya grid yang dipilih yang akan diproses.

## Struktur Kode
- **Fungsi `get_target_grids()`**: Mengumpulkan grid dari seleksi atau view.
- **Fungsi `grid_is_any_end_2d(grid, view)`**: Mengecek apakah salah satu ujung grid dalam mode 2D.
- **Fungsi `set_grid_extents(grid, view, to_viewspecific)`**: Mengubah tipe extent untuk kedua ujung.
- **Fungsi `main()`**: Mengkoordinasi proses utama dengan transaksi.

## Penanganan Error dan Batasan
- Skrip menggunakan try-except untuk menangani perbedaan API antar versi Revit.
- Jika tidak ada grid ditemukan, skrip akan menampilkan alert dan keluar.
- Tidak berlaku untuk grid melengkung atau tipe khusus; akan dilewati jika API gagal.
- Transaksi dibatalkan jika terjadi error.

## Tips dan Best Practices
- Jalankan di view yang relevan (plan atau section) untuk hasil terbaik.
- Backup view sebelum menjalankan jika extent penting.
- Untuk kontrol presisi, gunakan seleksi grid.

## Lisensi dan Kontribusi
Skrip ini untuk keperluan pribadi. Modifikasi harus mempertimbangkan kompatibilitas versi.

---
*Dokumentasi ini untuk skrip `script.py` di folder `2D3DExtentToggle.pushbutton`.*