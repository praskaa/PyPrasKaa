# Stair Plan Generator

## Overview

**Stair Plan Generator** adalah script pyRevit yang secara otomatis membuat plan views untuk multi-story stairs pada level-level tertentu. Script ini akan membuat denah tangga yang menunjukkan step tangga, landing, dan orientasi yang tepat untuk setiap level yang dipilih user.

**Version:** 1.0.0 (Beta)
**Date:** 02.11.2025
**Author:** PrasKaa (based on Claude's logic breakdown)

## Features

- ✅ **Multi-level stair support** - Mendukung tangga yang melintasi beberapa lantai
- ✅ **Automatic crop region calculation** - Hitung area crop secara otomatis berdasarkan geometry tangga
- ✅ **Landing visibility logic** - Logika cerdas untuk menampilkan landing di level yang tepat
- ✅ **Run direction indication** - Menampilkan arah tangga (naik/turun) dengan benar
- ✅ **View template support** - Dukungan template view untuk konsistensi
- ✅ **Debug mode** - Mode debug untuk troubleshooting
- ✅ **Unique naming** - Penamaan view yang unik dan deskriptif

## User Workflow

### Step-by-Step Usage

#### 1. **Select Stair**
- Pilih tangga multi-story dari model
- Script akan memvalidasi bahwa tangga memiliki multiple runs

#### 2. **Enter Base Name**
- Masukkan nama dasar untuk plan views
- Contoh: "STAIRS-02"
- Default: "STAIRS-01"

#### 3. **Select Target Levels**
- Script akan menampilkan semua level yang relevan dengan tangga
- Pilih level-level mana saja yang ingin dibuat plan view-nya
- Multi-select supported

#### 4. **Choose View Template (Optional)**
- Pilih template view untuk konsistensi
- Opsi "None" untuk menggunakan default

#### 5. **Generate Plan Views**
- Script akan membuat plan view untuk setiap level terpilih
- Nama view: "STAIRS-02_Level16", "STAIRS-02_Level17", dll.
- Setiap view akan memiliki crop region yang tepat

## Technical Architecture

### Core Classes

#### **StairAnalyzer**
```python
class StairAnalyzer:
    """
    Menganalisis struktur tangga dan menentukan visibility per level
    """

    def analyze_stair_structure(self, stair):
        """Ekstrak runs, landings, dan elevations"""

    def find_landing_for_level(self, target_elevation):
        """Tentukan landing mana yang 'belong to' level tertentu"""

    def get_runs_for_level(self, target_elevation):
        """Tentukan run mana yang visible di level tertentu"""

    def get_level_visibility(self, target_elevation):
        """Return visible elements at level"""
```

#### **StairPlanGenerator**
```python
class StairPlanGenerator:
    """
    Generate plan views untuk tangga di level-level tertentu
    """

    def create_stair_plan(self, stair, level, base_name, template=None):
        """Create plan view untuk satu level"""

    def batch_create_stair_plans(self, stair, selected_levels, base_name, template=None):
        """Create multiple plan views untuk banyak level"""
```

#### **StairCropCalculator**
```python
class StairCropCalculator:
    """
    Menghitung bounding box untuk crop region tangga
    Simplified approach: rectangular bounding box
    """

    def calculate_stair_bounds(self, stair, visible_elements):
        """Calculate rectangular crop region"""
```

#### **LevelSelector**
```python
class LevelSelector:
    """
    Menentukan level mana saja yang bisa menampilkan tangga
    """

    def get_applicable_levels(self, stair):
        """Find semua level yang tangga ini 'touch'"""

    def select_target_levels(self, applicable_levels):
        """Present level selection dialog"""
```

## Stair Visibility Logic

### Landing Association Rules

**Architectural Convention:**
- Landing secara fisik berada di antara level (misal L15-L16)
- Tapi dalam plan view, landing ditampilkan di level yang dilayani
- Landing "milik" level yang dia layani (arrival level)

**Implementation:**
```python
def find_landing_for_level(self, target_elevation):
    tolerance = 1.5  # feet

    for landing in self.landings:
        elevation_diff = abs(landing.BaseElevation - target_elevation)
        if elevation_diff <= tolerance:
            return landing  # Landing ini untuk level ini
    return None
```

### Run Visibility Rules

**Two Types of Visible Runs:**

1. **Runs Going DOWN (Full Visibility):**
   - `run.TopElevation ≈ target_elevation`
   - Menampilkan semua step tangga
   - Contoh: Di Level 16, run yang berakhir di L16 (turun dari L17 ke L16)

2. **Runs Going UP (Partial Visibility):**
   - `run.BaseElevation ≈ target_elevation`
   - Menampilkan beberapa step pertama saja
   - Contoh: Di Level 16, run yang dimulai di L16 (naik dari L16 ke L17)

### Example: 3-Story Stair (L15 → L16 → L17)

```
Physical Stair Structure:
├── Run1: Base=50.00', Top=53.00' (L15 → L16)
├── Landing1: BaseElev=51.50' (between L15-L16)
├── Run2: Base=53.00', Top=56.00' (L16 → L17)
├── Landing2: BaseElev=54.50' (between L16-L17)

Level 16 Plan View (elevation: 53.00'):
├── Landing: Landing1 (associated with L16)
├── Runs Below: [Run1] (TopElev = 53.00' → FULL visibility)
├── Runs Above: [Run2] (BaseElev = 53.00' → PARTIAL visibility)
```

## Crop Region Calculation

### Simplified Rectangular Approach

**Why Simplified?**
- Stair shapes vary greatly (L-shape, U-shape, spiral)
- Exact geometry projection is complex and error-prone
- Rectangular crop is standard architectural practice
- Users can adjust crop manually if needed

**Algorithm:**
```python
def calculate_stair_bounds(self, stair, visible_elements):
    # Get stair's overall bounding box
    stair_bbox = stair.get_BoundingBox(None)

    # Calculate center point
    center_x = (stair_bbox.Max.X + stair_bbox.Min.X) / 2
    center_y = (stair_bbox.Max.Y + stair_bbox.Min.Y) / 2

    # Calculate dimensions
    width = abs(stair_bbox.Max.X - stair_bbox.Min.X)
    height = abs(stair_bbox.Max.Y - stair_bbox.Min.Y)

    # Add margin (3 feet standard)
    margin = 3.0

    return {
        'min_x': center_x - (width/2) - margin,
        'max_x': center_x + (width/2) + margin,
        'min_y': center_y - (height/2) - margin,
        'max_y': center_y + (height/2) + margin
    }
```

## Configuration Options

### Debug Mode
```python
DEBUG_MODE = False  # Set to True for detailed debug output
```

### Default Parameters
```python
DEFAULT_SCALE = 50          # 1/4" = 1'-0" scale
CROP_MARGIN = 3.0          # Margin around stair (feet)
ELEVATION_TOLERANCE = 1.5   # Level matching tolerance (feet)
```

## Requirements

### Software Requirements
- **Revit:** 2020, 2021, 2022, 2023, 2024, 2026
- **pyRevit:** 4.8.10 or later
- **Python:** IronPython (included with pyRevit)

### Model Requirements
- **Stair Elements:** Multi-story stairs with runs and landings
- **Levels:** Properly defined building levels
- **View Templates:** Optional, for consistent formatting

## Output Format

### Success Output
```
# Stair Plan Generation Results

## ✅ Successfully Created Views
**Stair:** [link to stair]  |  **Base Name:** STAIRS-02

| Base Name | Level    | View          |
|-----------|----------|---------------|
| STAIRS-02 | L16 FL   | [link to view] |
| STAIRS-02 | L17 FL   | [link to view] |
| STAIRS-02 | L18 FL   | [link to view] |

---
**Summary:** 3 views created, 0 failed
```

### Debug Output (when enabled)
```
STAIR_ANALYSIS: Found 2 runs, 2 landings
LEVEL_ANALYSIS: Found 3 applicable levels: ['L16 FL', 'L17 FL', 'L18 FL']
VIEW_CREATION: Creating plan view 'STAIRS-02_Level16' at level 'L16 FL'
CROP_BOX: Applied to view - Min: (-13.00, -8.00), Max: (8.00, 13.00)
```

## Error Handling

### Validation Checks
- ✅ Stair selection validation (multi-story check)
- ✅ Level applicability verification
- ✅ View name uniqueness
- ✅ Template existence validation

### Graceful Failure
- **No visible elements:** Skip level with warning
- **Duplicate names:** Auto-append numbers
- **API failures:** Continue with other levels
- **Invalid geometry:** Use fallback crop region

## Troubleshooting

### Common Issues

#### **No Applicable Levels Found**
**Cause:** Stair doesn't span multiple levels or levels not properly defined
**Solution:** Check stair properties and level definitions

#### **No Visible Elements at Level**
**Cause:** Level elevation doesn't match any stair run/landing elevations
**Solution:** Check level elevations and stair connectivity

#### **Crop Region Too Large/Small**
**Cause:** Stair bounding box calculation issues
**Solution:** Manually adjust crop region in created views

#### **View Template Not Applied**
**Cause:** Selected template not compatible with floor plans
**Solution:** Choose different template or use "None"

### Debug Mode Usage

Enable debug mode for detailed troubleshooting:
```python
DEBUG_MODE = True  # At top of script
```

Debug output will show:
- Stair structure analysis
- Level matching logic
- View creation steps
- Crop region calculations
- Error details with stack traces

## Examples

### Basic Usage
1. Select 3-story stair
2. Enter "STAIRS-02" as base name
3. Select levels L16, L17, L18
4. Choose "Stair Plan" template
5. Generate → Creates 3 plan views

### Advanced Usage
1. Enable `DEBUG_MODE = True` for troubleshooting
2. Use custom crop margins by modifying `CROP_MARGIN`
3. Adjust elevation tolerance with `ELEVATION_TOLERANCE`

## API Reference

### Main Classes

#### `StairAnalyzer(stair)`
- `analyze_stair_structure()` → Extract stair components
- `get_level_visibility(elevation)` → Get visible elements at level

#### `StairPlanGenerator(doc)`
- `create_stair_plan(stair, level, name, template)` → Create single view
- `batch_create_stair_plans(stair, levels, name, template)` → Create multiple views

#### `LevelSelector(doc)`
- `get_applicable_levels(stair)` → Find relevant levels
- `select_target_levels(levels)` → User level selection

## Version History

### v1.0.0 (2025-11-02)
- ✅ Initial release
- ✅ Multi-level stair support
- ✅ Automatic crop region calculation
- ✅ Landing visibility logic
- ✅ View template support
- ✅ Debug mode implementation
- ✅ Comprehensive error handling

## Future Enhancements

### Planned Features
- [ ] Exact stair geometry projection (instead of rectangular crop)
- [ ] Direction arrows and annotations
- [ ] Multi-stair batch processing
- [ ] Custom naming schemes
- [ ] Stair type detection (straight, L-shaped, U-shaped)
- [ ] Integration with section generators

### Performance Improvements
- [ ] Cached stair analysis for repeated operations
- [ ] Optimized geometry calculations
- [ ] Batch view creation API usage

---

## Support

For issues and questions:
1. Enable debug mode and check output
2. Verify stair and level setup in Revit model
3. Check pyRevit and Revit version compatibility
4. Review troubleshooting section above

**Created by:** PrasKaa Development Team
**Last Updated:** November 2, 2025