# Set View Title on Sheet

## 📋 Deskripsi

Script ini mengatur parameter "Title on Sheet" (Deskripsi Tampilan) dari tampilan yang dipilih agar sama dengan nama tampilan tersebut.

## 🎯 Tujuan

- Mengatur judul tampilan pada sheet agar sesuai dengan nama tampilan
- Memastikan konsistensi antara nama tampilan dan judul yang muncul di sheet
- Menggunakan library `lib/Snippets/_selection.py` untuk mendapatkan tampilan yang dipilih

## 🔧 Cara Penggunaan

1. Pilih satu atau beberapa tampilan di Revit
2. Jalankan script ini
3. Parameter "Title on Sheet" akan diatur ke nama tampilan masing-masing

## 📚 Dependencies

- `lib/Snippets/_selection.py` - Untuk mendapatkan tampilan yang dipilih
- `Autodesk.Revit.DB.BuiltInParameter.VIEW_DESCRIPTION` - Parameter Title on Sheet
- `pyrevit.forms` - Untuk UI feedback

## ⚙️ Logic

```python
# 1. Dapatkan tampilan yang dipilih
selected_views = get_selected_views(exit_if_none=False)

# 2. Untuk setiap tampilan, set parameter VIEW_DESCRIPTION
for view in selected_views:
    title_param = view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION)
    title_param.Set(view.Name)
```

## 🔍 Parameter yang Digunakan

- **Input**: Tampilan yang dipilih user
- **Output**: Parameter `VIEW_DESCRIPTION` di-set ke `view.Name`
- **Transaction**: Menggunakan Transaction untuk memastikan data integrity

## ⚠️ Catatan

- Hanya berlaku untuk tampilan yang mendukung parameter Title on Sheet
- Parameter yang read-only akan dilewati
- Menampilkan toast notification dengan jumlah tampilan yang berhasil diupdate

## 📝 Changelog

- **v1.0** - Initial implementation
  - Menggunakan `get_selected_views()` dari library
  - Transaction-based operation
  - User feedback dengan toast notification