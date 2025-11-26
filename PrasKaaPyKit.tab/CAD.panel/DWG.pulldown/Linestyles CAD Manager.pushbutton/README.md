# Linestyles CAD Manager

## Deskripsi

**Linestyles CAD Manager** adalah tool canggih untuk mengelola gaya garis (line styles) dari file CAD yang di-link dalam proyek Autodesk Revit. Tool ini menggunakan interface dua-langkah yang user-friendly untuk memilih file CAD tertentu dan mengelola layer-layer dari file tersebut secara batch.

Tool ini sangat berguna untuk standardisasi tampilan CAD imports dalam proyek BIM, memungkinkan kontrol penuh atas line weight dan line pattern untuk setiap layer CAD.

## Fitur Utama

- **Two-Step Interface**: Proses terstruktur untuk memilih file CAD dan mengelola layer
- **Selective CAD Processing**: Pilih file CAD spesifik yang ingin dimodifikasi
- **Batch Layer Management**: Kelola multiple layer secara bersamaan
- **Advanced Filtering**: Cari dan filter layer berdasarkan nama
- **Line Weight Control**: Atur line weight dari 1-16 atau biarkan default
- **Line Pattern Selection**: Pilih dari semua line pattern yang tersedia di project
- **Batch Editing**: Edit multiple layer sekaligus dengan multi-selection
- **Transaction Safety**: Semua perubahan dalam Revit transaction untuk safety
- **Comprehensive Logging**: Detailed logging untuk troubleshooting

## Cara Kerja

### Arsitektur Two-Step Process

#### Step 1: CAD File Selection
1. **Scan Project**: Tool mengumpulkan semua linked CAD files dalam project
2. **Display List**: Menampilkan daftar CAD files dengan nama dan path
3. **User Selection**: User memilih file CAD yang ingin dimodifikasi
4. **Validation**: Pastikan minimal satu file dipilih sebelum lanjut

#### Step 2: Layer Management
1. **Extract Layers**: Mengumpulkan semua layer dari CAD files terpilih
2. **Display Grid**: Menampilkan layer dalam DataGridView dengan informasi lengkap
3. **Batch Operations**: User dapat select, filter, dan edit multiple layer
4. **Apply Changes**: Terapkan semua perubahan dalam satu transaction

### Data Flow
```
Project CAD Links → User Selection → Layer Extraction → Grid Display → Batch Editing → Transaction Apply
```

## Langkah Penggunaan

### Step 1: Memilih File CAD
1. Jalankan script dari DrawingSet panel
2. **Form Selection** akan muncul menampilkan semua linked CAD files
3. **Review List**: Lihat nama file dan path lengkap
4. **Select Files**: Centang file CAD yang ingin dimodifikasi
5. **Use Buttons**:
   - **Select All**: Pilih semua file
   - **Deselect All**: Hapus semua pilihan
   - **Next →**: Lanjut ke step berikutnya
   - **Cancel**: Batal operasi

### Step 2: Mengelola Layer Styles
1. **Wait for Processing**: Tool akan extract semua layer dari file terpilih
2. **Review Grid**: DataGridView menampilkan:
   - **Select**: Checkbox untuk memilih layer
   - **Layer Name**: Nama layer dari CAD
   - **Source CAD File**: File asal layer
   - **Current Line Weight**: Weight saat ini (1-16)
   - **New Line Weight**: Dropdown untuk weight baru
   - **Current Line Pattern**: Pattern saat ini
   - **New Line Pattern**: Dropdown untuk pattern baru

3. **Filter Layers**: Gunakan textbox filter untuk mencari layer tertentu
4. **Batch Select**: Klik "Select All" atau pilih individual layers
5. **Edit Properties**: 
   - Pilih line weight dari dropdown (1-16 atau Default)
   - Pilih line pattern dari dropdown (semua pattern project atau Default)
   - **Batch Editing**: Pilih multiple rows lalu ubah satu untuk apply ke semua

6. **Apply Changes**: Klik "Apply Changes" untuk konfirmasi dan aplikasi

## Interface Detail

### CAD Selection Form
- **ListView Control**: Menampilkan CAD files dengan columns
- **CheckBoxes**: Multi-selection support
- **Path Display**: Full path untuk verifikasi file location
- **Button Panel**: Select All, Deselect All, Next, Cancel

### Layer Manager Form
- **DataGridView**: Advanced grid dengan sorting dan filtering
- **Filter Panel**: Real-time search dengan Clear button
- **Column Headers**: Tooltips untuk setiap column
- **Dropdown Controls**: Validated input untuk line weights dan patterns
- **Button Panel**: Back, Select All, Apply Changes

## Fitur Advanced

### Batch Editing Logic
```python
# Jika multiple layer dipilih dan user mengubah salah satu
if len(selected_layers) > 1 and current_layer.selected:
    # Apply perubahan ke semua selected layers
    for layer in selected_layers:
        layer.new_line_weight = new_value
```

### Filtering System
- **Real-time Filter**: Filter langsung saat mengetik
- **Multi-criteria**: Cari berdasarkan layer name atau CAD file name
- **Case-insensitive**: Pencarian tidak case-sensitive
- **Instant Results**: Update grid langsung tanpa delay

### Transaction Management
- **Single Transaction**: Semua perubahan dalam satu Revit transaction
- **Rollback Safety**: Jika ada error, semua perubahan di-rollback
- **Performance**: Batch processing untuk efficiency

## Persyaratan

### System Requirements
- **Revit**: 2020+
- **pyRevit**: Latest version
- **Windows Forms**: .NET Framework support
- **Memory**: Sufficient RAM untuk large CAD files

### Project Requirements
- **Linked CAD Files**: Minimal satu CAD file yang di-link
- **Line Patterns**: Project harus memiliki line patterns yang diinginkan
- **Permissions**: User harus memiliki permission untuk modify CAD links

## Konfigurasi

### Default Settings
```python
LINE_WEIGHTS = range(1, 17)  # 1-16 available weights
DEFAULT_LINE_WEIGHT = "Default"  # Keep current
DEFAULT_LINE_PATTERN = "Default"  # Keep current
```

### Customization Options
- **Form Sizes**: Dapat diubah dalam code untuk different screen sizes
- **Column Widths**: Adjustable column widths dalam DataGridView
- **Button Positions**: Fixed positioning untuk consistency

## Troubleshooting

### Masalah Umum

#### "No linked CAD files found"
**Penyebab**: Tidak ada CAD files yang di-link dalam project
**Solusi**: Link CAD files terlebih dahulu menggunakan Insert → Link CAD

#### "No layers found in selected CAD files"
**Penyebab**: CAD files tidak memiliki layer atau corrupt
**Solusi**: Check CAD files di AutoCAD atau software lain

#### "Line pattern not found"
**Penyebab**: Line pattern tidak ada di project Revit
**Solusi**: Import line patterns yang diperlukan ke project

#### "Transaction failed"
**Penyebab**: Permission issues atau file locked
**Solusi**: Pastikan file tidak read-only dan user memiliki permissions

### Debug Information
Enable verbose logging untuk troubleshooting:
```python
logger.info("Detailed operation logs")
# Check pyRevit output window untuk detailed logs
```

## Contoh Penggunaan

### Skenario: Standardisasi CAD Imports
```
1. Link multiple CAD files dari consultants
2. Jalankan Linestyles CAD Manager
3. Pilih semua CAD files dari satu consultant
4. Set line weight 2 untuk semua annotation layers
5. Set line weight 6 untuk semua structural layers
6. Apply changes untuk konsistensi visual
```

### Skenario: Project Cleanup
```
1. Identifikasi CAD files dengan styling inconsistent
2. Filter layers berdasarkan nama (misal: "ANNO*")
3. Batch select semua annotation layers
4. Set uniform line weight dan pattern
5. Apply untuk standardization
```

## Teknologi

### Core Technologies
- **Language**: Python dengan IronPython
- **UI Framework**: Windows Forms (.NET)
- **Data Binding**: ArrayList untuk DataGridView binding
- **API Integration**: Revit API untuk CAD link manipulation

### Key Classes
- **LinkedCADFile**: Representasi file CAD dengan metadata
- **EnhancedCadLayer**: Layer dengan styling information
- **CADSelectionForm**: Form untuk selection CAD files
- **EnhancedLayerManagerForm**: Form utama untuk layer management

### Performance Optimizations
- **Lazy Loading**: Load data saat diperlukan
- **Memory Management**: Proper disposal of objects
- **Batch Operations**: Minimize API calls dengan batching
- **UI Responsiveness**: Non-blocking UI updates

## Integration dengan Tools Lain

### Complementary Tools
- **Line Color Tools**: Untuk additional styling control
- **View Management**: Untuk visibility control
- **Template System**: Untuk save/load styling presets

### Workflow Integration
- **Pre-Processing**: Jalankan sebelum import massal CAD files
- **Post-Processing**: Cleanup setelah link CAD files
- **Quality Control**: Bagian dari BIM quality assurance workflow

## Best Practices

### Project Setup
1. **Standardize CAD Layer Names**: Gunakan naming convention yang konsisten
2. **Pre-define Line Patterns**: Setup line patterns sebelum import
3. **Test on Sample Files**: Test styling pada file sample sebelum production

### Usage Guidelines
1. **Work in Teams**: Koordinasi dengan team untuk styling standards
2. **Document Changes**: Catat perubahan styling untuk reference
3. **Backup Files**: Backup project sebelum mass changes
4. **Test Views**: Verify changes di multiple views

### Performance Tips
1. **Filter First**: Gunakan filter untuk reduce dataset
2. **Batch Wisely**: Jangan select semua layers sekaligus untuk large projects
3. **Monitor Memory**: Close unnecessary applications
4. **Save Frequently**: Save project setelah major changes

## Versi

- **Versi**: 2.0 Enhanced
- **Penulis**: PrasKaa Development Team
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+, pyRevit
- **Dependencies**: Windows Forms, .NET Framework

## Changelog

### v2.0 (2024) - Enhanced Release
- ✅ Two-step interface dengan improved UX
- ✅ Advanced filtering dan search capabilities
- ✅ Batch editing dengan multi-selection support
- ✅ Enhanced error handling dan logging
- ✅ Transaction safety untuk all operations
- ✅ Performance optimizations untuk large datasets

### v1.0 (2023) - Initial Release
- ✅ Basic CAD link layer management
- ✅ Line weight dan pattern modification
- ✅ Single file processing
- ✅ Basic error handling

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - DrawingSet.panel/Linestyles CAD Manager**
*Professional CAD Integration Tools untuk BIM Workflow*