# Get Sort Number To Number Sheet Parameter

## Deskripsi

**Get Sort Number To Number Sheet Parameter** adalah tool untuk mengisi parameter "Number" pada sheet berdasarkan urutan print order dari View Sheet Set (Print Set). Tool ini mengambil nomor urut dari print order dan menuliskannya ke parameter sheet yang bernama "Number".

Tool ini sangat berguna untuk otomasi penomoran sheet dalam proyek BIM, memastikan konsistensi antara urutan print dan nomor sheet yang tertera pada drawing.

## Fitur Utama

- **Print Set Integration**: Menggunakan ViewSheetSet untuk mendapatkan urutan print
- **Automatic Numbering**: Assign nomor urut otomatis berdasarkan print order
- **Custom Start Number**: Opsi untuk mulai penomoran dari angka tertentu
- **Parameter Validation**: Check apakah parameter "Number" ada dan dapat diedit
- **Cross-Version Compatibility**: Mendukung multiple Revit API versions
- **Transaction Safety**: Semua perubahan dalam Revit transaction
- **Error Handling**: Comprehensive error handling dengan rollback

## Cara Kerja

### Algoritma Penomoran
1. **Scan Print Sets**: Mengumpulkan semua ViewSheetSet dalam project
2. **User Selection**: User memilih print set yang diinginkan
3. **Extract Order**: Mengambil ordered view list dari print set
4. **Filter Sheets**: Hanya memproses ViewSheet elements
5. **Sequential Numbering**: Assign nomor urut mulai dari angka yang ditentukan
6. **Parameter Writing**: Tulis nomor ke parameter "Number" pada setiap sheet

### API Compatibility
Script menggunakan helper function untuk handle perbedaan API di berbagai versi Revit:
```python
ordered_ids = _get_attr(vss, [
    'OrderedViewList',    # Revit 2025
    'OrderedViewIds',     # Revit 2026+
    'OrderedViews',
    'OrderedViewIdList'
], None)
```

## Langkah Penggunaan

### Basic Usage
1. Jalankan script dari DrawingSet panel → Sheets pulldown
2. **Pilih Print Set**: Dialog akan muncul menampilkan semua print sets
3. **Select Print Set**: Pilih print set yang berisi sheets yang ingin dinomori
4. **Set Start Number**: Masukkan angka awal untuk penomoran (default: 1)
5. **Automatic Processing**: Script akan otomatis assign nomor ke semua sheets

### Advanced Options
- **Custom Start**: Gunakan angka selain 1 untuk penomoran
- **Multiple Sets**: Jalankan script multiple kali untuk sets berbeda

## Contoh Penggunaan

### Skenario: Standard Sheet Numbering
```
Print Set: "Working Drawings"
Sheets dalam set: A101, A102, S201, S202, M101
Urutan print: A101, S201, A102, M101, S202

Hasil penomoran (start=1):
- A101 → Number: 1
- S201 → Number: 2
- A102 → Number: 3
- M101 → Number: 4
- S202 → Number: 5
```

### Skenario: Section Numbering
```
Print Set: "Sections Only"
Start number: 100

Hasil:
- Section A-A → Number: 100
- Section B-B → Number: 101
- Section C-C → Number: 102
```

## Persyaratan

### System Requirements
- **Revit**: 2020+
- **pyRevit**: Terinstall dan aktif
- **Print Sets**: Minimal satu ViewSheetSet dalam project

### Project Requirements
- **Sheets in Print Sets**: Print set harus berisi ViewSheet elements
- **Number Parameter**: Sheets harus memiliki parameter "Number" yang dapat diedit
- **Print Order**: Print set harus memiliki defined print order

## Parameter Handling

### Supported Parameter Types
- **Integer**: Set langsung dengan `p.Set(idx)`
- **String/Text**: Convert ke string dengan `p.Set(str(idx))`
- **Read-Only**: Skipped dengan counter
- **Missing**: Skipped dengan counter

### Validation Logic
```python
p = el.LookupParameter("Number")
if p is None:
    skipped_no_param += 1
    continue
if p.IsReadOnly:
    skipped_ro += 1
    continue
```

## Output dan Reporting

### Process Summary
Script memberikan summary setelah completion:
- **Print Set**: Nama print set yang diproses
- **Start Number**: Angka awal penomoran
- **Updated**: Jumlah sheets yang berhasil diupdate
- **No Parameter**: Sheets tanpa parameter "Number"
- **Read-Only**: Sheets dengan parameter read-only

### Error Handling
- **Transaction Rollback**: Jika ada error, semua changes di-rollback
- **User Notification**: Alert dialog dengan detail error
- **Logging**: Error details tercatat untuk debugging

## Tips Penggunaan

### Best Practices
- **Verify Print Order**: Pastikan urutan print sudah benar sebelum running
- **Backup Project**: Save project sebelum mass changes
- **Test on Sample**: Test pada beberapa sheets terlebih dahulu
- **Consistent Naming**: Pastikan parameter "Number" konsisten di semua sheets

### Workflow Integration
- **Pre-Printing**: Jalankan sebelum membuat PDF sets
- **Sheet Management**: Bagian dari sheet organization workflow
- **Quality Control**: Verifikasi nomor sheet sesuai dengan print order

### Troubleshooting
- **No Print Sets**: Pastikan ada ViewSheetSet dalam project
- **Empty Print Set**: Add sheets ke print set terlebih dahulu
- **Parameter Issues**: Check jika parameter "Number" ada dan editable

## Teknologi

### Core Technologies
- **Language**: Python dengan IronPython
- **API**: Revit Database API
- **UI**: pyRevit forms untuk user interaction
- **Transaction**: Revit Transaction untuk data safety

### Key Functions
- **_get_attr()**: Cross-version API compatibility helper
- **FilteredElementCollector**: Query ViewSheetSet elements
- **LookupParameter()**: Access sheet parameters
- **Transaction**: Safe database modifications

## Integration

### Complementary Tools
- **Sheet Management**: Tools lain untuk sheet organization
- **Print Set Tools**: Utilities untuk managing print sets
- **Parameter Tools**: Bulk parameter editing tools

### Workflow Position
- **Pre-Output**: Jalankan sebelum PDF generation
- **Post-Sheet Creation**: Setelah semua sheets dibuat
- **Quality Assurance**: Sebelum final documentation

## Versi

- **Versi**: 1.0
- **Penulis**: PrasKaa Development Team
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+
- **Dependencies**: pyRevit forms

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - DrawingSet.panel/Sheets/Get Sort Number To Number Sheet Parameter**
*Professional Sheet Management Tools untuk BIM Documentation*