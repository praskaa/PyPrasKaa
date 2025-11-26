---
title: "Unit Conversion Framework"
version: "1.0"
category: "utilities/convert"
tags: ["units", "conversion", "feet", "meters", "coordinates", "layout"]
author: "Kilo Code"
tested_on: "Revit 2021-2026, pyRevit 4.8.x"
status: "active"
last_updated: "2025-10-23"
---

# Unit Conversion Framework

## Problem Statement

Revit uses feet as internal units for all geometric operations, but users typically work with millimeters/centimeters for dimensions and meters for larger measurements. This creates a constant need for unit conversions that leads to code duplication and conversion errors.

## Solution Overview

A comprehensive unit conversion framework that handles all common unit conversions between Revit internal units (feet) and user-friendly display units (mm, cm, m), with automatic Revit version compatibility.

## Key Components

### 1. Universal Unit Converter

```python
def convert_internal_units(value, get_internal=True, units='m'):
    """
    Convert between Revit internal units (feet) and display units.

    Args:
        value (float): Value to convert
        get_internal (bool): True = convert TO feet, False = convert FROM feet
        units (str): Target unit type ('m', 'm2', 'cm')

    Returns:
        float: Converted value

    Examples:
        # Convert 5 meters to feet
        feet = convert_internal_units(5.0, get_internal=True, units='m')

        # Convert feet back to meters
        meters = convert_internal_units(16.4, get_internal=False, units='m')
    """
```

### 2. Length Converters

```python
def convert_cm_to_feet(length):
    """Convert centimeters to feet for UI dimensions."""
    # Implementation uses UnitUtils.Convert with proper Revit version handling

def convert_m_to_feet(length):
    """Convert meters to feet for large dimensions."""

def convert_internal_to_m(length):
    """Convert Revit feet to meters for display."""

def convert_internal_to_cm(length):
    """Convert Revit feet to centimeters for small dimensions."""
```

### 3. Area Converters

```python
def convert_internal_to_m2(area):
    """Convert square feet to square meters."""
    # Handles area unit conversions for floor plans, etc.
```

## Integration Patterns

### With Layout Calculations

```python
from Snippets._convert import convert_cm_to_feet
from Snippets._annotations import create_region

# User inputs dimensions in cm (intuitive)
region_width_cm = 5.0    # 5 cm wide
region_height_cm = 3.0   # 3 cm tall

# Convert to Revit internal units (feet)
width_feet = convert_cm_to_feet(region_width_cm)    # 0.164 feet
height_feet = convert_cm_to_feet(region_height_cm)  # 0.098 feet

# Create geometry
region = create_region(doc, view, x, y, width_feet, height_feet)
```

### With Parameter Setting

```python
from Snippets._convert import convert_m_to_feet

# User inputs in meters (architectural scale)
wall_height_m = 3.5  # 3.5 meters high

# Convert for Revit parameter (must be in feet)
height_feet = convert_m_to_feet(wall_height_m)
wall_height_param.Set(height_feet)
```

### With Coordinate Systems

```python
from Snippets._convert import convert_internal_units

# API returns coordinates in feet
api_x = element.Location.Point.X  # In feet

# Display to user in meters
display_x = convert_internal_units(api_x, get_internal=False, units='m')

# User inputs new position in meters
user_x_m = 10.5  # 10.5 meters
user_x_feet = convert_internal_units(user_x_m, get_internal=True, units='m')

# Move element
new_point = XYZ(user_x_feet, y, z)
element.Location.Move(new_point - element.Location.Point)
```

## Usage Examples

### Legend Layout System

```python
def create_legend_layout(config):
    """Create legend with proper unit conversions."""

    # Configuration in user-friendly units (cm)
    layout = {
        'region_width': 3.0,      # cm
        'region_height': 1.5,     # cm
        'spacing': 0.8,           # cm
        'text_offset': 0.5        # cm
    }

    # Convert to Revit units for geometry creation
    layout_feet = {}
    for key, value_cm in layout.items():
        layout_feet[key] = convert_cm_to_feet(value_cm)

    return layout_feet
```

### Multi-Unit Parameter Handling

```python
def set_family_parameters(family_instance, params_dict):
    """Set multiple parameters with automatic unit conversion."""

    for param_name, value_info in params_dict.items():
        value, unit = value_info

        # Convert based on parameter type and unit
        if unit == 'mm':
            revit_value = value / 304.8  # mm to feet
        elif unit == 'm':
            revit_value = convert_m_to_feet(value)
        elif unit == 'degrees':
            revit_value = value  # Already in correct units
        else:
            revit_value = value

        # Set parameter
        param = family_instance.LookupParameter(param_name)
        if param:
            param.Set(revit_value)
```

### Volume Calculations

```python
def calculate_element_volume(element):
    """Calculate element volume in user-friendly units."""

    # Get volume in cubic feet (Revit internal)
    volume_cu_ft = element.get_Geometry(options).GetBoundingBox().Volume

    # Convert to cubic meters for display
    volume_cu_m = volume_cu_ft * (0.3048 ** 3)  # feet³ to meters³

    return volume_cu_m
```

## Revit Version Compatibility

The framework automatically handles different Revit API versions:

```python
# Revit 2021+ (UnitTypeId)
if rvt_year >= 2021:
    from Autodesk.Revit.DB import UnitTypeId
    units = UnitTypeId.Meters
else:
    # Legacy API (DisplayUnitType)
    from Autodesk.Revit.DB import DisplayUnitType
    units = DisplayUnitType.DUT_METERS
```

## Performance Considerations

- **Caching**: Cache conversion factors for repeated operations
- **Precision**: Use appropriate decimal places (avoid floating-point errors)
- **Batch Operations**: Convert multiple values in single operations
- **Memory**: Clean up temporary conversion variables

## Error Handling

```python
def safe_convert_cm_to_feet(value):
    """Safe conversion with error handling."""
    try:
        if not isinstance(value, (int, float)):
            raise ValueError("Value must be numeric")

        if value < 0:
            raise ValueError("Length cannot be negative")

        return convert_cm_to_feet(value)

    except Exception as e:
        logger.error(f"Unit conversion failed: {e}")
        return 0.0  # Safe fallback
```

## Common Conversion Factors

| From | To | Factor | Use Case |
|------|----|--------|----------|
| mm | feet | /304.8 | Small dimensions |
| cm | feet | /30.48 | UI dimensions |
| m | feet | *3.28084 | Large dimensions |
| ft² | m² | *0.092903 | Area calculations |
| ft³ | m³ | *0.0283168 | Volume calculations |

## Cross-References

- **Annotations**: `LOG-UTIL-ANNOTATIONS-001-v1-text-graphics-creation.md`
- **Geometry**: `LOG-UTIL-GEOM-001-v1-precise-geometry-matching.md`
- **Parameters**: `LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction.md`

## Testing Recommendations

```python
def test_unit_conversions():
    """Test conversion accuracy."""

    # Test cases
    test_cases = [
        (1000, 'mm', 3.28084),    # 1000mm = ~3.28 feet
        (5.0, 'm', 16.4042),      # 5m = ~16.4 feet
        (10000, 'mm2', 1.07639), # Area conversion
    ]

    for input_val, unit, expected in test_cases:
        result = convert_internal_units(input_val, get_internal=True, units=unit)
        assert abs(result - expected) < 0.001, f"Conversion failed: {result} != {expected}"
```

## Future Enhancements

- [ ] Add support for imperial units (inches, yards)
- [ ] Add temperature conversions (°C ↔ °F)
- [ ] Add weight/mass conversions (kg ↔ lbs)
- [ ] Add pressure/stress conversions
- [ ] Add currency conversions for cost calculations
- [ ] Add automatic unit detection from strings ("5.2m", "1200mm")