# Add Running Number to Sheet List

## Deskripsi

**Add Running Number to Sheet List** adalah tool integrasi Dynamo yang secara otomatis menambahkan nomor urut berjalan ke parameter "Number" pada semua sheet yang muncul dalam sheet list. Tool ini menggunakan Dynamo script untuk memproses semua sheets dalam project dan memberikan penomoran sequential mulai dari angka 1.

Tool ini sangat berguna untuk otomasi penomoran sheet dalam proyek BIM besar, memastikan konsistensi penomoran dan menghemat waktu manual numbering.

## Fitur Utama

- **Dynamo Integration**: Menjalankan Dynamo script dari pyRevit interface
- **Automatic Sheet Detection**: Mendeteksi semua sheets yang appear in sheet list
- **Sequential Numbering**: Penomoran otomatis mulai dari 1
- **Parameter Validation**: Memastikan parameter "Number" dapat diedit
- **Batch Processing**: Memproses semua qualifying sheets sekaligus
- **Transaction Safety**: Semua perubahan dalam Dynamo transaction

## Cara Kerja

### Dynamo Graph Logic
1. **Get All Sheets**: Mengumpulkan semua sheet elements dari project menggunakan `Categories.OST_Sheets`
2. **Filter Sheet List**: Memfilter sheets yang memiliki parameter "Appears In Sheet List" = true
3. **Create Number Sequence**: Generate sequence angka mulai dari 1
4. **Set Parameters**: Mengisi parameter "Number" pada setiap sheet dengan nomor urut
5. **Transaction Commit**: Menyimpan semua perubahan dalam satu transaction

### Filter Criteria
```python
# Hanya memproses sheets yang:
- Appear in sheet list (parameter "Appears In Sheet List" = true)
- Memiliki parameter "Number" yang dapat diedit
- Termasuk dalam project sheets (bukan template)
```

## Langkah Penggunaan

### Basic Usage
1. Jalankan script dari Helper panel → DynamoScript pulldown
2. **Automatic Processing**: Script otomatis mendeteksi dan memproses semua sheets
3. **No User Input Required**: Tool berjalan secara otomatis tanpa input manual
4. **Completion Notification**: Dynamo akan menampilkan completion status

### Advanced Usage
- **Pre-Filtering**: Pastikan sheets yang tidak diinginkan tidak appear in sheet list
- **Parameter Check**: Verify bahwa parameter "Number" ada pada semua sheets
- **Backup**: Save project sebelum running untuk safety

## Persyaratan

### System Requirements
- **Revit**: 2020+
- **Dynamo**: Terinstall dan terintegrasi dengan Revit
- **pyRevit**: Latest version dengan Dynamo support

### Project Requirements
- **Sheets in Project**: Minimal satu sheet dalam project
- **Sheet List Visibility**: Sheets harus appear in sheet list
- **Number Parameter**: Parameter "Number" harus ada dan editable pada sheets

## Output dan Results

### Processing Results
- **Sequential Numbers**: Setiap sheet mendapat nomor urut (1, 2, 3, ...)
- **Parameter Update**: Parameter "Number" terupdate pada semua qualifying sheets
- **Transaction Log**: Dynamo menampilkan log processing dan errors

### Example Results
```
Sheet A101 → Number: 1
Sheet A102 → Number: 2
Sheet S201 → Number: 3
Sheet M101 → Number: 4
```

## Dynamo Graph Structure

### Key Nodes Used
- **Categories**: Mengakses OST_Sheets category
- **All Elements of Category**: Mendapatkan semua sheet elements
- **Element.GetParameterValueByName**: Membaca parameter values
- **List.FilterByBoolMask**: Filter berdasarkan "Appears In Sheet List"
- **Sequence**: Generate nomor urut
- **Element.SetParameterByName**: Set parameter "Number"
- **Transaction**: Handle database changes

### Graph Flow
```
Sheets → Filter by "Appears In Sheet List" → Create Sequence → Set "Number" Parameter
```

## Tips Penggunaan

### Best Practices
- **Sheet Organization**: Pastikan semua sheets yang perlu dinomori appear in sheet list
- **Parameter Consistency**: Verify parameter "Number" ada pada semua sheet families
- **Sequential Logic**: Nomor urut berdasarkan urutan sheet dalam list
- **Error Checking**: Check Dynamo console untuk error messages

### Workflow Integration
- **Post-Sheet Creation**: Jalankan setelah semua sheets dibuat
- **Pre-Plotting**: Pastikan numbering benar sebelum PDF generation
- **Team Coordination**: Koordinasi dengan team untuk sheet list management

### Troubleshooting
- **Sheets Not Numbered**: Check "Appears In Sheet List" parameter
- **Parameter Errors**: Verify parameter "Number" exists dan editable
- **Dynamo Errors**: Check Dynamo console untuk detailed error messages

## Teknologi

### Core Technologies
- **Dynamo**: Visual programming untuk Revit automation
- **Revit API**: Database access melalui Dynamo nodes
- **pyRevit Integration**: Launcher untuk Dynamo scripts
- **Transaction System**: Safe database modifications

### Integration Method
- **Script File**: .dyn file berisi Dynamo graph definition
- **pyRevit Launcher**: Menjalankan Dynamo dari pyRevit interface
- **Parameter Binding**: Input parameters untuk customization

## Integration dengan Tools Lain

### Complementary Tools
- **Sheet Management**: Tools untuk bulk sheet operations
- **Parameter Tools**: Utilities untuk parameter management
- **Dynamo Scripts**: Other Dynamo automation tools

### Workflow Position
- **Sheet Setup Phase**: Bagian dari initial sheet configuration
- **Documentation Phase**: Sebelum final documentation preparation
- **Quality Assurance**: Verification step sebelum plotting

## Parameter Configuration

### Input Parameters
- **Numbering parameter name**: Default "Number" (configurable)
- **Start sequence**: Fixed at 1 (tidak dapat diubah)

### Output Parameters
- **Number**: Sequential numbers assigned to sheets
- **Processing Log**: Dynamo console output

## Versi

- **Versi**: 1.0
- **Penulis**: PrasKaa Development Team
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+, Dynamo
- **Dependencies**: Dynamo for Revit

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - Helper.panel/DynamoScript/Add Running Number to Sheet List**
*Professional Sheet Numbering Automation untuk BIM Documentation*