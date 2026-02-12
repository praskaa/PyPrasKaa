---
id: "LOG-UTIL-ELEMENT-002"
version: "v1"
status: "active"
category: "utilities/elements"
element_type: "Element"
operation: "element-names"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["elements", "family", "type", "extraction", "name", "robust"]
created: "2025-02-10"
updated: "2025-02-10"
confidence: "high"
performance: "fast"
source_file: "lib/elements/element_names.py"
---

# LOG-UTIL-ELEMENT-002-v1: Element Names Extraction

## Problem Context

Many pyRevit scripts need to extract Family Name and Type Name from elements. The standard `element.Symbol.Family.Name` approach doesn't always work, especially with:
- Linked model elements
- Certain family types
- Cached or proxied elements

## Solution Summary

Robust utility functions that use multiple API methods to reliably extract element names. Based on proven patterns from LOG-UTIL-ELEMENT-001-v1 documentation.

## Implementation Location

**Library:** `lib/elements/element_names.py`

**Status:** ✅ PRODUCTION READY - Can be imported by scripts

## Usage

```python
from elements.element_names import get_family_name, get_type_name, get_family_and_type_name
```

## Functions

### get_type_name(element)

Get type name from element using the most reliable method: `Symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)`.

```python
type_name = get_type_name(element)
# Returns: "W24x76" or "Unknown Type"
```

**Methods tried (in order):**
1. `Symbol.get_Parameter(SYMBOL_NAME_PARAM)` - Most reliable
2. `Symbol.Name`
3. `ElementType` via `GetTypeId()`
4. `Element.Name` directly

### get_family_name(element)

Get family name from element.

```python
family_name = get_family_name(element)
# Returns: "W-Wide Flange" or "Unknown Family"
```

**Methods tried (in order):**
1. `Symbol.Family.Name` for FamilyInstance
2. `ElementType.FamilyName` via `GetTypeId()`
3. `ELEM_FAMILY_PARAM` parameter

### get_family_and_type_name(element)

Get both names as a tuple.

```python
family, type_name = get_family_and_type_name(element)
# Returns: ("W-Wide Flange", "W24x76")
```

## Scripts Using This Module

1. **Transfer.pushbutton** - Transfers GIS_Element_UID between models
   - Validates Family + Type match

## Related Documentation

- [LOG-UTIL-ELEMENT-001-v1](active/utilities/elements/LOG-UTIL-ELEMENT-001-v1-instance-type-name-extraction.md) - Type name extraction patterns
