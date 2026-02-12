# LOG-UTIL-PARAM-GIS-001-v1: GIS Categories Configuration

## Overview

This module provides centralized categories configuration for GIS-related scripts in PrasKaaPyKit.

## Implementation Location

**Library:** `lib/parameters/gis_categories.py`

**Status:** ✅ PRODUCTION READY - Can be imported by scripts

## Description

The `gis_categories.py` module defines shared categories and parameter names for GIS element operations across multiple scripts.

## Categories Supported

| Display Name | BuiltInCategory | UID Prefix |
|--------------|-----------------|------------|
| Floors | OST_Floors | FLOOR |
| Walls | OST_Walls | WALL |
| Structural Framing | OST_StructuralFraming | BEAM |
| Structural Columns | OST_StructuralColumns | COL |
| Structural Foundation | OST_StructuralFoundation | FOUND |
| Stairs | OST_Stairs | STAIR |

## Usage

### Import Pattern

```python
# ✅ CORRECT: Import from lib/parameters folder
from parameters.gis_categories import (
    GIS_CATEGORIES,
    PARAM_NAME,
    get_all_category_enums
)
```

### Available Functions

#### `get_categories_dict()`
Returns the complete GIS_CATEGORIES dictionary.

```python
categories = get_categories_dict()
# Returns: {
#     "Floors": (BuiltInCategory.OST_Floors, "FLOOR"),
#     "Walls": (BuiltInCategory.OST_Walls, "WALL"),
#     ...
# }
```

#### `get_category_by_name(category_name)`
Get category tuple by display name.

```python
result = get_category_by_name("Walls")
# Returns: (BuiltInCategory.OST_Walls, "WALL")
```

#### `get_all_category_enums()`
Get all BuiltInCategory enums for iteration.

```python
enums = get_all_category_enums()
# Returns: [BuiltInCategory.OST_Floors, BuiltInCategory.OST_Walls, ...]
```

#### `get_uid_prefix(category_name)`
Get the UID prefix for a category.

```python
prefix = get_uid_prefix("Structural Framing")
# Returns: "BEAM"
```

## Scripts Using This Module

1. **Generate.pushbutton** (`PrasKaaPyKit.tab/Documentation.panel/col3.stack/Gistama UID.pulldown/`)
   - Generates unique GIS_Element_UID for elements
   - Uses CATEGORIES for iteration

2. **Transfer.pushbutton** (`PrasKaaPyKit.tab/Documentation.panel/col3.stack/Gistama UID.pulldown/`)
   - Transfers GIS_Element_UID from linked model to host
   - Uses geometry intersection matching
   - Validates Family + Type name match

## Parameter

- **PARAM_NAME:** `"GIS_Element_UID"` - The shared parameter name used across scripts

## Related Documentation

- [Generate Script Documentation]()
- [Transfer Script Documentation]()

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2024-02-10 | Initial implementation |

## Architecture Notes

This module follows the PrasKaaPyKit architecture:
- ✅ Implementation in `lib/` (importable)
- ✅ Documentation in `logic-library/` (reference only)
- ✅ No circular dependencies
- ✅ Single responsibility for categories configuration
