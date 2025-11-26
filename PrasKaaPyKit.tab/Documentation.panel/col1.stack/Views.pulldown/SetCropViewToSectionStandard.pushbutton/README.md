# Set Crop View to Section View Standard

## Deskripsi

**Set Crop View to Section View Standard** adalah tool untuk mengatur graphic overrides pada crop box di section dan detail views yang ditempatkan pada sheets. Tool ini memungkinkan apply atau reset line weight dan line pattern pada crop box untuk standardisasi tampilan dalam dokumentasi.

Tool ini sangat berguna untuk memperbaiki visibility crop box dalam final drawings, memastikan konsistensi visual antara berbagai section views dalam satu set dokumentasi.

## Fitur Utama

- **Dual Action Mode**: Apply standard overrides atau reset ke default
- **Configurable Settings**: Line weight dan pattern dapat dikonfigurasi via config file
- **Batch Processing**: Process multiple views sekaligus dengan progress tracking
- **Smart View Detection**: Hanya memproses views yang placed on sheets
- **Crop Box Finding**: Algoritma canggih untuk menemukan crop box elements
- **Transaction Safety**: Setiap view diproses dalam transaction terpisah
- **Progress Monitoring**: Real-time progress bar dengan cancellation support
- **Detailed Reporting**: Comprehensive results dengan error details

## Cara Kerja

### Algoritma Processing
1. **Load Configuration**: Baca settings dari config.py atau gunakan defaults
2. **Scan Views on Sheets**: Cari semua section/detail views yang placed on sheets
3. **User Selection**: Pilih views yang ingin diproses
4. **Action Selection**: Pilih Apply overrides atau Reset to default
5. **Crop Box Detection**: Temukan crop box element untuk setiap view
6. **Apply Overrides**: Set line weight dan pattern pada crop box
7. **Progress Tracking**: Update progress dan handle cancellations
8. **Results Summary**: Tampilkan hasil processing dengan details

### Crop Box Detection Logic
```python
# Temporarily hide crop box to find elements
with revit.Transaction('TEMP crop box to false', doc=doc):
    view.CropBoxVisible = False
shown_elements = collector.ToElementIds()

# Show crop box again
with revit.Transaction('TEMP crop box to true', doc=doc):
    view.CropBoxVisible = True

# Find crop box element (difference)
collector.Excluding(shown_elements)
crop_box_element = collector.FirstElement()
```

## Konfigurasi

### File config.py
```python
# Default configuration
config = {
    'line_weight': 6,                    # Line weight 1-16
    'line_pattern_name': 'Dash dot',     # Line pattern name
    'allowed_view_types': ['Section', 'Detail'],  # View types to process
    'show_progress_bar': True,           # Show progress bar
    'show_detailed_results': True        # Show detailed error messages
}
```

### Default Settings
- **Line Weight**: 6 (tebal untuk visibility)
- **Line Pattern**: "Dash dot" (untuk distinguish dari model lines)
- **View Types**: Section dan Detail views
- **Progress Bar**: Enabled
- **Detailed Results**: Enabled

## Langkah Penggunaan

### Basic Workflow
1. Jalankan script dari DrawingSet panel → Views pulldown
2. **Automatic Scan**: Script scan semua section/detail views on sheets
3. **Select Views**: Pilih views yang ingin di-override dari list
4. **Choose Action**:
   - **Apply Standard Overrides**: Set line weight 6 + dash dot pattern
   - **Reset Overrides to Default**: Remove semua overrides
5. **Monitor Progress**: Progress bar menampilkan processing status
6. **Review Results**: Summary dialog dengan success/failure details

### Advanced Usage
- **Config Customization**: Edit config.py untuk custom settings
- **Selective Processing**: Pilih hanya views tertentu untuk processing
- **Batch Operations**: Process multiple views dalam satu operation

## Contoh Penggunaan

### Skenario: Documentation Preparation
```
Views on sheets: Section A-A, Section B-B, Detail 1, Detail 2
Action: Apply Standard Overrides

Result:
✅ Section A-A: Crop box line weight 6, dash dot pattern
✅ Section B-B: Crop box line weight 6, dash dot pattern
✅ Detail 1: Crop box line weight 6, dash dot pattern
✅ Detail 2: Crop box line weight 6, dash dot pattern
```

### Skenario: Reset for Presentation
```
Action: Reset Overrides to Default

Result:
✅ All crop boxes: Reset to default line weight dan pattern
```

## Persyaratan

### System Requirements
- **Revit**: 2020+
- **pyRevit**: Terinstall dan aktif
- **Views on Sheets**: Minimal satu section/detail view placed on sheets

### Project Requirements
- **Line Patterns**: Project harus memiliki "Dash dot" pattern (atau custom via config)
- **Crop Boxes**: Views harus memiliki visible crop boxes
- **Sheet Placement**: Views harus placed on sheets (bukan floating)

## Output dan Reporting

### Success Messages
- **Toast Notification**: "Successfully applied overrides for X view(s)!"
- **Details Dialog**: Settings yang diterapkan + error summary
- **Applied Settings**: Line weight value + line pattern name

### Error Handling
- **No Views Found**: Alert jika tidak ada qualifying views
- **No Selection**: Alert jika user tidak select views
- **Crop Box Not Found**: Listed dalam failed views
- **Pattern Not Found**: Alert dengan config check instruction

### Statistics Tracking
```python
stats = {
    'processed': 0,    # Successfully processed
    'skipped': 0,      # Skipped (wrong type)
    'errors': 0,       # Failed processing
    'cancelled': False # User cancellation
}
```

## Tips Penggunaan

### Best Practices
- **Consistent Standards**: Gunakan settings yang sama across projects
- **Config Management**: Backup config.py untuk reuse
- **View Verification**: Check crop box visibility sebelum processing
- **Batch Processing**: Process dalam batches untuk large projects

### Workflow Integration
- **Pre-Plotting**: Apply overrides sebelum PDF generation
- **Quality Control**: Ensure crop boxes visible dalam final drawings
- **Template Setup**: Include dalam view templates untuk consistency

### Troubleshooting
- **Views Not Found**: Pastikan views placed on sheets, bukan floating
- **Crop Box Issues**: Check view crop box aktif dan visible
- **Pattern Missing**: Verify line pattern name di config.py
- **Performance**: Disable progress bar untuk faster processing

## Teknologi

### Core Technologies
- **Language**: Python dengan IronPython
- **UI Framework**: pyRevit forms dengan progress bar
- **API**: Revit Database API untuk view manipulation
- **Configuration**: File-based config dengan exec() loading

### Key Classes
- **OverrideGraphicSettings**: Container untuk graphic overrides
- **ProgressBar**: Real-time progress monitoring
- **FilteredElementCollector**: View scanning dan filtering
- **Transaction**: Safe database modifications

### Advanced Features
- **Dummy Progress Bar**: Fallback untuk disabled progress tracking
- **Threading Safety**: UI updates dengan exception handling
- **Config Isolation**: Local scope execution untuk security

## Integration

### Complementary Tools
- **View Management**: Tools untuk bulk view operations
- **Sheet Tools**: Sheet organization dan numbering
- **Template Tools**: View template management

### Workflow Position
- **Documentation Phase**: Apply sebelum final plotting
- **Quality Assurance**: Verify crop box visibility
- **Presentation Prep**: Standardize appearance untuk client deliverables

## Performance Considerations

### Optimization Features
- **Batch Processing**: Minimize API calls dengan efficient algorithms
- **Memory Management**: Proper cleanup dan resource disposal
- **UI Responsiveness**: Non-blocking progress updates
- **Cancellation Support**: User dapat cancel long operations

### Typical Performance
- **Small Projects**: < 10 seconds untuk 10-20 views
- **Large Projects**: 30-60 seconds untuk 50+ views
- **Memory Usage**: Minimal additional memory overhead

## Versi

- **Versi**: 1.0
- **Penulis**: PrasKaa Development Team
- **Tanggal**: 2024
- **Compatibility**: Revit 2020+
- **Dependencies**: pyRevit, config.py (optional)

## Lisensi

Script ini adalah bagian dari PrasKaaPyKit extension untuk pyRevit, digunakan untuk keperluan internal dan profesional BIM workflow.

---

**PrasKaaPyKit - DrawingSet.panel/Views/Set Crop View to Section View Standard**
*Professional Documentation Tools untuk BIM Presentation*