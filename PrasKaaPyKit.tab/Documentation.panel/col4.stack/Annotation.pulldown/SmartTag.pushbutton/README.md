# Smart Tag System - Intelligent Structural Element Tagging

## Overview
Smart Tag System adalah tool otomatis untuk tagging elemen struktural (framing, columns, walls) di multiple views Revit dengan positioning yang intelligent dan filtering yang akurat.

## Features

### 🎯 Core Functionality
- **Automatic Detection**: Mendeteksi EngineeringPlan views secara akurat
- **Intelligent Positioning**: Tag positioning berdasarkan geometry element dengan offset configurable
- **Multi-Category Support**: Structural Framing, Columns, dan Walls
- **Tag Existence Validation**: Cek elemen sudah tertag sebelumnya

### 🏗️ Advanced Features
- **Level-based Wall Filtering**: Filter walls berdasarkan level constraints
  - Connected walls: Tag berdasarkan top level
  - Unconnected walls: Tag berdasarkan unconnected height
- **Tag Mode Options**:
  - "Tag untagged elements only": Skip elemen yang sudah tertag
  - "Retag all elements": Tag ulang semua elemen
- **Batch Processing**: Optimized untuk performance tinggi

### 🎨 User Interface
- **Clean Dialog**: Search functionality, multi-select views
- **Elevation-based Sorting**: Views di-sort dari atas ke bawah
- **Configuration Display**: Real-time preview kategori aktif
- **Progress Tracking**: Visual feedback selama processing

### 🔧 Debug & Maintenance
- **Verbose Mode**: Ctrl+Click untuk enable debug logging
- **Silent Operation**: No console output by default
- **Error Recovery**: Robust error handling
- **Performance Monitoring**: Optional statistics

## Usage

### Basic Operation
1. **Normal Click**: Launch Smart Tag dialog
2. **Select Views**: Pilih views yang ingin ditag (sorted by elevation)
3. **Configure Mode**: Pilih "untagged only" atau "retag all"
4. **Execute**: Klik Execute untuk mulai tagging

### Advanced Options
- **Search**: Filter views dengan typing di search box
- **Verbose Mode**: Ctrl+Click untuk debug output
- **Settings**: Shift+Click untuk konfigurasi advanced

## Technical Details

### View Detection
```python
# Detects EngineeringPlan views (not FloorPlan)
if view.ViewType == ViewType.EngineeringPlan:
    structural_plans.append(view)
```

### Tag Positioning
- **Framing**: Perpendicular offset dari beam center
- **Columns**: Top-right corner dengan diagonal offset
- **Walls**: Midpoint dengan offset sesuai orientation

### Level Filtering Logic
```python
# Connected walls: use level elevation
if element_id and element_id != ElementId.InvalidElementId:
    top_elevation = level.Elevation

# Unconnected walls: use unconnected height
else:
    unconnected_height = wall.LookupParameter("Unconnected Height")
    top_elevation = base_elevation + unconnected_height
```

## Configuration

### Categories Configuration
```json
{
  "structural_framing": {
    "tag_type_name": "Structural Framing Tag",
    "offset_mm": 150,
    "enabled": true
  },
  "structural_column": {
    "tag_type_name": "Structural Column Tag",
    "offset_mm": 200,
    "enabled": true
  },
  "walls": {
    "tag_type_name": "Wall Tag",
    "offset_mm": 100,
    "enabled": true
  }
}
```

### Tag Mode
- `untagged_only`: Skip elements yang sudah memiliki tag
- `retag_all`: Tag ulang semua elements

## Requirements
- **Revit**: 2020+
- **pyRevit**: Required
- **Python**: IronPython 2.7

## Troubleshooting

### Verbose Mode
Enable verbose mode untuk debug output:
1. Ctrl+Click pada button Smart Tag
2. Lihat console untuk detailed logging
3. Check wall filtering logic dan tag positioning

### Common Issues
- **No structural plans found**: Pastikan project memiliki EngineeringPlan views
- **Tag type not found**: Check tag families di project
- **Wall not tagged**: Check level constraints dan unconnected height

## Performance
- **Batch Processing**: 20 elements per batch untuk stability
- **Cache System**: Tag collection caching per view
- **Memory Efficient**: Progressive processing tanpa memory spikes

## Architecture

### Core Components
- `SmartTagEngine`: Core tagging logic
- `SmartTagConfig`: Configuration management
- `SmartTagDialog`: User interface

### Key Methods
- `get_structural_plans()`: View detection dan sorting
- `tag_elements_in_view()`: Main tagging workflow
- `calculate_[element]_tag_position()`: Positioning calculations
- `is_element_tagged_in_view()`: Tag existence validation

## Changelog

### v1.0.0 (2025-10-10)
- ✅ Initial release dengan full functionality
- ✅ EngineeringPlan view detection
- ✅ Level-based wall filtering
- ✅ Debug toggle system
- ✅ Elevation-based view sorting
- ✅ Silent operation mode

---

**Developed for**: PrasKaaPyKit Extension
**Last Updated**: 2025-10-10
**Compatibility**: Revit 2020+, pyRevit