# Hide Adaptive Points on Sheets

## Deskripsi

Skrip PyRevit ini digunakan untuk memastikan **Adaptive Points** tersembunyi di semua view yang ditempatkan pada sheet di Autodesk Revit. Script ini akan secara otomatis menyembunyikan semua adaptive points yang terlihat di setiap view yang ada di sheet, memastikan presentasi yang bersih pada dokumentasi.

Adaptive Points adalah elemen khusus yang digunakan dalam Adaptive Components di Revit, biasanya untuk parametric modeling dan family creation yang kompleks. Pada sheet dokumentasi, adaptive points biasanya tidak diinginkan terlihat.

## Fitur Utama

- **Automatic Hiding**: Menyembunyikan adaptive points di semua view pada sheet
- **Sheet-wide Scope**: Memproses semua view yang ditempatkan di sheet
- **Project-wide Coverage**: Mengumpulkan semua adaptive points dalam project
- **Safe Operation**: Hanya memproses elemen yang dapat di-hide
- **No User Interaction**: Berjalan otomatis tanpa memerlukan input user

## Cara Kerja

### Algoritma Hide on Sheets
1. **Kumpulkan Sheets**: Mengumpulkan semua sheets dalam project menggunakan `FilteredElementCollector`
2. **Identifikasi Views**: Mengumpulkan semua view yang ditempatkan pada sheet melalui viewport
3. **Kumpulkan Adaptive Points**: Mengumpulkan semua adaptive points dalam project
4. **Periksa Visibility per View**: Untuk setiap view pada sheet:
    - Periksa apakah adaptive point terlihat dalam view tersebut
    - Pastikan point dapat disembunyikan dalam view tersebut
5. **Hide Action**: Sembunyikan semua visible adaptive points di setiap view pada sheet

### Filter dan Kriteria
- **Category**: `OST_AdaptivePoints`
- **Element Type**: Hanya instance elements (bukan element types)
- **View Compatibility**: Hanya memproses points yang dapat di-hide dalam view tersebut

## Penggunaan

### Langkah Penggunaan
1. **Jalankan Script**: Klik button "AdaptivePoint" di Control panel
2. **Otomatis Processing**: Script akan otomatis memproses semua sheet dan view
3. **Verifikasi**: Periksa sheet untuk memastikan adaptive points sudah tersembunyi

### Kondisi Penggunaan
- **Sheet Preparation**: Sebelum finalizing dokumentasi
- **Presentation Cleanup**: Membersihkan view pada sheet dari reference points
- **Quality Control**: Memastikan konsistensi visibility di semua sheet
- **Batch Processing**: Ketika ada banyak sheet yang perlu dibersihkan

## Contoh Skenario

### Skenario 1: Sheet Cleanup
```
1. Buka project dengan banyak sheet
2. Jalankan Hide Adaptive Points on Sheets
3. Semua adaptive points di semua sheet tersembunyi otomatis
4. Sheet siap untuk presentasi final
```

### Skenario 2: Quality Control
```
1. Sebelum submit dokumentasi
2. Jalankan script untuk memastikan konsistensi
3. Semua sheet memiliki visibility yang bersih
4. Tidak ada adaptive points yang terlihat
```

## Persyaratan

- **Revit Version**: 2020+
- **pyRevit**: Terinstall dan aktif
- **View Type**: Mendukung semua view types
- **Permissions**: User harus memiliki permission untuk modify view visibility

## Teknologi

- **Bahasa**: Python
- **Framework**: pyRevit
- **API**: Autodesk Revit API
- **UI Framework**: pyRevit forms (toast notifications)
- **Transaction**: Menggunakan Revit Transaction untuk safety

## Kode Utama

```python
def get_views_on_sheets():
    """Get all views that are placed on sheets."""
    views_on_sheets = []

    # Get all sheets in the project
    all_sheets = DB.FilteredElementCollector(revit.doc)\
                   .OfCategory(DB.BuiltInCategory.OST_Sheets)\
                   .WhereElementIsNotElementType()\
                   .ToElements()

    # Collect all unique views from all sheets
    view_ids = set()
    for sheet in all_sheets:
        viewport_ids = sheet.GetAllViewports()
        for viewport_id in viewport_ids:
            viewport = revit.doc.GetElement(viewport_id)
            if viewport:
                view_ids.add(viewport.ViewId)

    # Convert view IDs to view objects
    for view_id in view_ids:
        view = revit.doc.GetElement(view_id)
        if view:
            views_on_sheets.append(view)

    return views_on_sheets

@revit.carryout('Hide Adaptive Points on Sheets')
def hide_adaptive_points_on_sheets():
    # Get all adaptive points in the project
    all_adaptive_points = DB.FilteredElementCollector(revit.doc)\
                            .OfCategory(DB.BuiltInCategory.OST_AdaptivePoints)\
                            .WhereElementIsNotElementType()\
                            .ToElements()

    # Get all views that are placed on sheets
    sheet_views = get_views_on_sheets()

    # Process each sheet view
    for view in sheet_views:
        # Collect points that are visible in this view and can be hidden
        visible_points_in_view = []

        for point in all_adaptive_points:
            # Check if the element can be hidden in this view
            if point.CanBeHidden(view) and not point.IsHidden(view):
                visible_points_in_view.append(point.Id)

        # Hide visible points in this view
        if visible_points_in_view:
            view.HideElements(framework.List[DB.ElementId](visible_points_in_view))
```

## Troubleshooting

### Masalah: Script Tidak Bereaksi
**Penyebab**: Tidak ada adaptive points dalam project atau tidak ada sheets
**Solusi**: Pastikan project memiliki adaptive components dan sheets dengan viewports

### Masalah: Points Tidak Berubah
**Penyebab**: Points tidak dapat di-hide dalam view tertentu atau sudah tersembunyi
**Solusi**: Check view properties atau pastikan ada visible adaptive points

### Masalah: Unexpected Behavior
**Penyebab**: View templates atau visibility overrides
**Solusi**: Check view templates dan reset visibility overrides jika diperlukan

## Tips Penggunaan

- **Batch Processing**: Jalankan sebelum finalizing semua sheets
- **Quality Control**: Bagian dari checklist sebelum submit dokumentasi
- **Automation**: Cocok untuk workflow dengan banyak sheets
- **Consistency**: Memastikan semua sheets memiliki visibility yang seragam

## Integration dengan Tools Lain

- **Bekerja dengan**: Semua documentation tools di PrasKaaPyKit
- **Complementary**: Sheet management tools untuk organizing sheets
- **Workflow**: Bagian dari documentation finalization workflow

## Versi

- **Versi**: 1.0
- **Penulis**: PrasKaa Development Team
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+, pyRevit

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - Utilities.panel/AdaptivePoint**
*Professional BIM Tools untuk Sheet Documentation Cleanup*