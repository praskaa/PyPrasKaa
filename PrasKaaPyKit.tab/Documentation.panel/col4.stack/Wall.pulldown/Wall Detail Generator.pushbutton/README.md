# Wall Plan Generator - Complete Documentation

## Overview

**Wall Plan Generator** adalah script pyRevit yang secara otomatis membuat plan views untuk kelompok dinding berdasarkan klasifikasi parameter "Wall Scheme Classification". Script ini mengelompokkan dinding dengan klasifikasi yang sama dan membuat plan view terpisah untuk setiap kelompok di level yang dipilih user.

## Features

- ✅ **Automatic Wall Classification** - Mengelompokkan dinding berdasarkan parameter "Wall Scheme Classification"
- ✅ **Smart Plan View Creation** - Membuat plan view dengan crop region yang optimal untuk setiap kelompok
- ✅ **Level Selection** - User dapat memilih level target untuk plan views
- ✅ **Unique Naming** - Otomatis memberikan nama unik untuk setiap view
- ✅ **Clean Output** - Output tabel yang rapi dengan informasi lengkap
- ✅ **Debug Mode** - Mode debug untuk troubleshooting (dapat diaktifkan/nonaktifkan)
- ✅ **Error Handling** - Robust error handling dengan reporting yang jelas

## Requirements

### Software Requirements
- **Revit 2020+**
- **pyRevit** (terinstall dan aktif)
- **Python** (built-in dengan pyRevit)

### Parameter Requirements
- Parameter **"Wall Scheme Classification"** harus ada di project
- Parameter dapat berupa instance atau type parameter
- Mendukung shared parameters

### Wall Requirements
- Dinding harus memiliki parameter "Wall Scheme Classification" yang valid
- Dinding harus memiliki geometry yang valid (Location.Curve)

## Installation

1. Copy script files ke folder pyRevit extension:
   ```
   PrasKaaPyKit.tab/Documentation.panel/Section.pulldown/WallPlanGenerator.pushbutton/
   ├── script.py (main script)
   ├── wall_classifier.py (classification logic)
   ├── level_selector.py (level selection UI)
   ├── wall_plan_generator.py (view generation core)
   ├── utils.py (utility functions)
   └── bundle.yaml (pyRevit bundle configuration)
   ```

2. Restart pyRevit atau reload extension

3. Script akan muncul di panel Documentation > Section

## Usage

### Basic Usage

1. **Pilih Dinding**: Klik tombol Wall Plan Generator
2. **Pilih Kategori**: Pilih kategori elemen yang ingin diproses (biasanya Walls)
3. **Pilih Dinding**: Select dinding-dinding yang ingin diproses
4. **Pilih Level**: Pilih level target untuk plan views
5. **Lihat Hasil**: Script akan membuat plan views dan menampilkan tabel hasil

### Debug Mode

Untuk mengaktifkan debug output, ubah variable di `script.py`:

```python
DEBUG_MODE = True  # Set to True untuk debug output detail
```

## Output Format

### Production Mode (Default)
```
Wall Classification Summary

Total Walls Selected: 26

Classifications Found: 8

    W5: 2 walls
    W3: 6 walls
    W1: 4 walls
    W2: 2 walls
    W7: 2 walls
    W6: 4 walls
    W8: 2 walls
    W4: 4 walls

Wall Plan Generation Results
Generated Plan Views
Classification | Level  | View
--------------|--------|------
W5           | L16 FL | 3515511
W3           | L16 FL | 3515521
W1           | L16 FL | 3515531
W2           | L16 FL | 3515541
W7           | L16 FL | 3515551
W6           | L16 FL | 3515561
W8           | L16 FL | 3515571
W4           | L16 FL | 3515581

Summary: 8 views created, 0 failed
```

### Debug Mode
Menampilkan informasi detail tentang:
- Parameter extraction process
- View creation steps
- Bounding box calculations
- Error details (jika ada)

## Architecture

### Core Components

#### 1. `script.py` - Main Script
- Entry point dan orchestrator utama
- User interface dan workflow control
- Result display dan reporting

#### 2. `wall_classifier.py` - Wall Classification
- Logic untuk mengelompokkan dinding berdasarkan klasifikasi
- Parameter extraction dengan support shared parameters
- Validation dan error handling

#### 3. `level_selector.py` - Level Selection
- UI untuk memilih level target
- Level validation dan filtering
- Elevation display dalam feet

#### 4. `wall_plan_generator.py` - View Generation
- Core logic untuk membuat plan views
- Bounding box calculation untuk crop regions
- View naming dan uniqueness handling

#### 5. `utils.py` - Utilities
- Helper functions dan utilities
- Common operations dan calculations

### Dependencies

#### External Libraries
- `Snippets._views.SectionGenerator` (dari EF-Tools)
- `Snippets._vectors.rotate_vector` (dari EF-Tools)
- `GUI.forms.select_from_dict` (dari EF-Tools)

#### Local Libraries
- `lib.view_generator.ViewGenerator` (reusable view generation)

## Algorithm Details

### Wall Classification Algorithm

1. **Parameter Search**: Mencari parameter "Wall Scheme Classification"
   - Instance level terlebih dahulu
   - Type level sebagai fallback
   - Support shared parameters

2. **Value Extraction**: Mengekstrak nilai parameter
   - String processing dan trimming
   - Null/empty value handling
   - Type conversion

3. **Grouping**: Mengelompokkan dinding berdasarkan klasifikasi
   - Dictionary-based grouping
   - Statistics calculation

### Plan View Creation Algorithm

1. **Bounding Box Calculation**:
   ```
   For each wall in group:
       Get wall curve endpoints
       Calculate perpendicular vectors for wall thickness
       Create wall footprint polygon
       Expand bounds with padding (10% of dimensions)
   ```

2. **View Naming**:
   ```
   Format: "{WallType}-{Classification}-{LevelName}"
   Example: "Basic Wall-W5-L16 FL"
   ```

3. **Crop Region Setup**:
   - Enable crop box
   - Set Min/Max coordinates
   - Apply padding untuk visibility

### Level Selection Algorithm

1. **Level Collection**: Mengumpulkan semua levels dari document
2. **Elevation Display**: Convert ke feet untuk display
3. **Multi-Selection UI**: Allow multiple level selection
4. **Validation**: Check untuk duplicate elevations

## Configuration

### Debug Configuration

```python
# In script.py
DEBUG_MODE = False  # True untuk debug output detail
```

### Parameter Configuration

```python
# In wall_classifier.py
self.classification_param = "Wall Scheme Classification"
```

### UI Configuration

```python
# In level_selector.py - Level display format
elevation_text = "{:.2f}'".format(level.Elevation * 3.28084)
```

## Error Handling

### Classification Errors
- Missing parameter: Skip wall dengan warning
- Invalid parameter type: Attempt conversion atau skip
- Empty values: Treated sebagai unclassified

### View Creation Errors
- Duplicate names: Auto-increment dengan suffix
- Invalid geometry: Skip dengan error logging
- Level issues: Fallback ke selected level

### User Input Errors
- No walls selected: Clear error message dengan exit
- No levels selected: Cancel operation
- Invalid selections: Validation dengan retry option

## Performance Considerations

### Optimization Features
- **Batch Processing**: Process multiple walls efficiently
- **Lazy Loading**: Load data only when needed
- **Memory Management**: Release references after processing
- **Transaction Scoping**: Minimal transaction duration

### Performance Metrics
- **Typical Processing**: 26 walls in ~2-3 seconds
- **Memory Usage**: Low (stores only essential data)
- **API Calls**: Optimized (minimal Revit API usage)

## Troubleshooting

### Common Issues

#### 1. "No walls found with valid classifications"
**Cause**: Parameter "Wall Scheme Classification" missing atau empty
**Solution**:
- Check parameter exists in project
- Ensure parameter has values
- Verify parameter name spelling

#### 2. "View creation failed"
**Cause**: Invalid wall geometry atau level issues
**Solution**:
- Check wall has valid Location.Curve
- Verify selected level exists
- Enable debug mode for detailed error info

#### 3. "Duplicate view names"
**Cause**: Multiple views dengan nama sama
**Solution**: Script auto-handles dengan suffix numbering

### Debug Mode Usage

1. Set `DEBUG_MODE = True` in script.py
2. Run script untuk melihat detailed output
3. Check console untuk parameter extraction details
4. Review bounding box calculations
5. Identify specific failure points

## Customization

### Adding New Element Types

```python
# In wall_classifier.py - modify classification_param
self.classification_param = "Custom_Parameter_Name"
```

### Changing Naming Convention

```python
# In wall_plan_generator.py - modify generate_view_name
view_name = "{}-{}-{}".format(custom_prefix, classification, level_name)
```

### Custom Crop Region Logic

```python
# In wall_plan_generator.py - modify calculate_group_bounding_box
# Add custom padding or calculation logic
padding_x = width * custom_percentage
```

## Examples

### Basic Usage
```python
# Script automatically handles:
# 1. Wall selection and classification
# 2. Level selection
# 3. View creation with optimal crop regions
# 4. Clean result reporting
```

### Advanced Usage with Custom Parameters
```python
# Modify wall_classifier.py for custom parameter
self.classification_param = "Zone_Classification"
# Script will use this parameter for grouping
```

## Changelog

### Version 1.0.0 (Current)
- ✅ Initial release dengan wall classification
- ✅ Plan view generation dengan smart cropping
- ✅ Multi-level support
- ✅ Clean output dengan debug toggle
- ✅ Comprehensive error handling
- ✅ Modular architecture

### Future Enhancements
- [ ] Support untuk multiple classification parameters
- [ ] Custom view templates per classification
- [ ] Batch processing untuk multiple levels
- [ ] Export capabilities (PDF, DWG)
- [ ] Integration dengan project standards

## Support

### Documentation Location
- Main documentation: `logic-library/sources/Element Section Generator by EF/README.md`
- Script location: `PrasKaaPyKit.tab/Documentation.panel/Section.pulldown/WallPlanGenerator.pushbutton/`

### Related Files
- EF Element Sections Generator analysis
- Wall Plan Generator specification documents
- Implementation and workflow diagrams

---

**Wall Plan Generator** - Efficient, automated plan view creation for classified wall groups in Autodesk Revit.