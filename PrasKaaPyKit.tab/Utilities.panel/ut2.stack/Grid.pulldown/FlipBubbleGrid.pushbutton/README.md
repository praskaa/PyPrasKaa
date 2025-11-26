# Dokumentasi Skrip Toggle Bubble Grid

## Deskripsi
Skrip Python ini dirancang untuk digunakan dalam lingkungan pyRevit pada Autodesk Revit. Skrip ini mengubah posisi bubble (label) grid di active view. Jika bubble muncul di satu sisi (End0 atau End1), akan dipindahkan ke sisi lain. Jika kedua sisi on atau keduanya off, grid akan dilewati tanpa perubahan.

## Persyaratan Sistem
- **Autodesk Revit**: Versi yang kompatibel dengan pyRevit (disarankan 2018 atau lebih baru).
- **pyRevit**: Ekstensi Python untuk Revit.
- **Python**: IronPython (versi yang disertakan dengan pyRevit).
- **Modul**: `Autodesk.Revit.DB`, `Autodesk.Revit.UI.Selection`, `pyrevit`.

## Cara Kerja Skrip
1. **Inisialisasi**: Mendapatkan UI document, dokumen, dan active view.
2. **Pemilihan Grid**:
   - Jika ada seleksi, gunakan grid dari seleksi.
   - Jika tidak, prompt pengguna untuk memilih grid menggunakan PickObjects dengan filter GridFilter.
3. **Toggle Bubble**:
   - Untuk setiap grid, cek visibilitas bubble di End0 dan End1.
   - Jika hanya End0 visible, hide End0 dan show End1.
   - Jika hanya End1 visible, hide End1 dan show End0.
   - Jika kedua sama (on/off), lewati.
4. **Transaksi**: Semua perubahan dilakukan dalam satu transaksi Revit.
5. **Notifikasi**: Menampilkan jumlah grid diproses, di-toggle, dan dilewati.

## Penggunaan
1. Buka view Revit yang ingin dimodifikasi.
2. Pilih grid jika sudah ada seleksi, atau biarkan skrip meminta seleksi.
3. Jalankan skrip melalui pushbutton pyRevit.
4. Bubble yang memenuhi kondisi akan di-flip, dan notifikasi ditampilkan.

### Contoh Penggunaan
- **Grid dengan Bubble di End0**: Bubble akan dipindah ke End1.
- **Grid dengan Bubble di End1**: Bubble akan dipindah ke End0.
- **Grid dengan Bubble di kedua sisi atau tidak sama sekali**: Tidak diubah.

## Struktur Kode
- **Kelas `GridFilter`**: Filter untuk seleksi grid.
- **Fungsi `pick_grids()`**: Mengumpulkan grid dari seleksi atau prompt.
- **Fungsi `toggle_bubbles(grids)`**: Melakukan toggle dan mengembalikan hitungan changed/skipped.
- **Fungsi `main()`**: Mengkoordinasi proses utama.

## Penanganan Error dan Batasan
- Menggunakan try-except untuk operasi bubble visibility.
- Jika tidak ada grid dipilih, tampilkan alert dan keluar.
- Transaksi di-rollback jika error terjadi.
- Hanya toggle jika persis satu sisi bubble on; kondisi lain dilewati.

## Tips dan Best Practices
- Gunakan di view yang relevan untuk melihat perubahan bubble.
- Seleksi grid terlebih dahulu untuk efisiensi.
- Periksa hasil setelah toggle.

## Lisensi dan Kontribusi
Skrip ini untuk keperluan pribadi. Modifikasi harus mempertimbangkan kompatibilitas versi.

---
*Dokumentasi ini untuk skrip `script.py` di folder `FlipBubbleGrid.pushbutton`.*