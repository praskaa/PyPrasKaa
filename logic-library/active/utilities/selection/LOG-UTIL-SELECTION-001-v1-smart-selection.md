# LOG-UTIL-SELECTION-001-v1-smart-selection.md

## Smart Selection Utility

**Version:** 1.0.0
**Date:** 2025-10-16
**Author:** Prasetyo

### Description
Utility untuk intelligent element selection yang memprioritaskan seleksi user yang sudah ada sambil mempertahankan kemampuan filtering kategori. Mendukung baik elemen yang sudah terseleksi maupun fallback ke seleksi manual.

### Features
- ✅ Mengecek seleksi yang sudah ada terlebih dahulu untuk elemen valid
- ✅ Menerapkan category filtering pada pre-selected elements
- ✅ Fallback ke manual selection jika tidak ada elemen valid
- ✅ Mendukung multiple categories melalui filter functions
- ✅ Error handling dan user feedback yang konsisten

### Usage Examples

#### Basic Usage - Single Category
```python
from logic-library.active.utilities.selection.smart_selection import get_filtered_selection, create_single_category_filter
from Autodesk.Revit.DB import BuiltInCategory

# Define filter for structural framing
framing_filter = create_single_category_filter(BuiltInCategory.OST_StructuralFraming)

# Get filtered selection
elements_to_process = get_filtered_selection(
    doc=doc,
    uidoc=uidoc,
    category_filter_func=framing_filter,
    prompt_message="Select Structural Framing",
    no_selection_message="No structural framing elements were selected."
)
```

#### Advanced Usage - Multiple Categories
```python
from logic-library.active.utilities.selection.smart_selection import get_filtered_selection, create_category_filter
from Autodesk.Revit.DB import BuiltInCategory

# Define filter for multiple categories
multi_filter = create_category_filter([
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns
])

# Get filtered selection
elements_to_process = get_filtered_selection(
    doc=doc,
    uidoc=uidoc,
    category_filter_func=multi_filter,
    prompt_message="Select Structural Elements",
    no_selection_message="No structural elements were selected."
)
```

#### Custom Filter Function
```python
from logic-library.active.utilities.selection.smart_selection import get_filtered_selection

# Custom filter function
def is_valid_structural_element(elem):
    valid_categories = [
        BuiltInCategory.OST_StructuralFraming,
        BuiltInCategory.OST_StructuralColumns,
        BuiltInCategory.OST_Walls
    ]
    return elem.Category.Id in [ElementId(cat) for cat in valid_categories]

# Get filtered selection
elements_to_process = get_filtered_selection(
    doc=doc,
    uidoc=uidoc,
    category_filter_func=is_valid_structural_element,
    prompt_message="Select Structural Elements",
    no_selection_message="No valid structural elements selected."
)
```

#### Real-World Implementation Example - Join Walls to Structure
```python
# Import smart selection utility
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logic-library', 'active', 'utilities', 'selection'))
from smart_selection import get_filtered_selection

# Get filtered walls using smart selection
walls_to_process = get_filtered_selection(
    doc=doc,
    uidoc=uidoc,
    category_filter_func=lambda elem: isinstance(elem, Wall),
    prompt_message="Select Walls to join with structure",
    no_selection_message="No walls selected. Please select walls to process.",
    filter_name="Wall Selection"
)
```

### Implementation Details

#### Selection Logic Flow
1. **Get Existing Selection**: Ambil semua elemen yang sudah terseleksi di UI Revit
2. **Filter Existing Selection**: Validasi setiap elemen menggunakan filter function
3. **Fallback to Manual**: Jika tidak ada elemen valid, prompt user untuk seleksi manual
4. **Final Validation**: Pastikan ada elemen untuk diproses

#### File Structure
```
logic-library/active/utilities/selection/
├── LOG-UTIL-SELECTION-001-v1-smart-selection.md  # Documentation
└── smart_selection.py                            # Implementation
```

#### Import Path
```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logic-library', 'active', 'utilities', 'selection'))
from smart_selection import get_filtered_selection, create_single_category_filter, create_category_filter
```

#### Function Signatures

```python
def get_filtered_selection(doc, uidoc, category_filter_func, prompt_message="Select Elements",
                          no_selection_message="No valid elements were selected. Please select valid elements.",
                          filter_name="Element Filter"):
    """
    Returns: List of valid elements or exits script if cancelled
    """

def create_category_filter(categories):
    """
    Args: List of BuiltInCategory enums
    Returns: Filter function for multiple categories
    """

def create_single_category_filter(category):
    """
    Args: BuiltInCategory enum
    Returns: Filter function for single category
    """
```

### Dependencies
- pyrevit (forms, script, revit)
- Revit API (Autodesk.Revit.DB, Autodesk.Revit.UI.Selection)
- **Important**: Requires `ObjectType` import from `Autodesk.Revit.UI.Selection`

### Error Handling
- Selection cancellation → User-friendly alert + script exit
- No valid elements → Clear message + script exit
- API errors → Detailed error messages

### Benefits
- **Improved UX**: Mengurangi klik manual jika elemen sudah terseleksi
- **Consistent Filtering**: Filter diterapkan di semua jalur seleksi
- **Reusable**: Bisa digunakan di berbagai script dengan kategori berbeda
- **Maintainable**: Logic terpusat dalam satu utility
- **Automatic Fallback**: Tidak memerlukan input manual jika tidak ada pre-selection
- **Validation**: Memastikan hanya elemen yang valid yang diproses
- **Clear Feedback**: User tahu metode seleksi mana yang digunakan

### Troubleshooting

#### Common Issues

**Issue: `global name 'ObjectType' is not defined`**
```
Selection error: global name 'ObjectType'
is not defined
```

**Solution:**
- Ensure `ObjectType` is imported in the smart_selection.py file:
```python
from Autodesk.Revit.UI.Selection import ObjectType
```
- This import is required for the `PickObjects()` method to work properly
- The utility will fail when users need to manually select elements without this import

**Issue: No elements found in selection**
- Check that the category filter function is correctly implemented
- Verify that elements exist in the model with the specified category
- Ensure the filter function returns boolean values correctly

### Real-World Implementation Examples

#### ✅ **Check Column Dimensions Script - Advanced Smart Selection (2025-10-22)**

**Implementation Pattern**: Custom logic that prioritizes pre-selected elements while auto-collecting all elements when no selection exists.

```python
def collect_host_columns():
    """
    Advanced smart selection for column validation:
    1. Check for pre-selected structural columns
    2. Validate pre-selected elements are actually columns
    3. Auto-collect ALL columns if no valid pre-selection
    4. Provide clear feedback about selection method used
    """
    # Step 1: Check for pre-selected elements
    selection_ids = uidoc.Selection.GetElementIds()
    pre_selected_elements = []

    if selection_ids:
        debug_log("Found {} pre-selected elements".format(len(selection_ids)), level='NORMAL')

        # Validate pre-selected elements are structural columns
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            if elem and elem.Category:
                # Check if it's a structural column
                if elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralColumns):
                    pre_selected_elements.append(elem)
                    debug_log("Validated pre-selected column: ID={}".format(elem.Id), level='VERBOSE')

        if pre_selected_elements:
            debug_log("Using {} pre-selected structural columns".format(len(pre_selected_elements)), level='NORMAL')
            return pre_selected_elements
        else:
            debug_log("No valid structural columns found in pre-selection", level='NORMAL')

    # Step 2: No valid pre-selection - collect ALL structural columns
    debug_log("Collecting ALL structural columns from host model", level='NORMAL')

    all_columns = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralColumns)\
        .WhereElementIsNotElementType()\
        .ToElements()

    if not all_columns:
        forms.alert("No structural column elements found in the host model. "
                   "Please ensure your model contains structural columns.", exitscript=True)

    debug_log("Collected {} structural columns from host model".format(len(all_columns)), level='NORMAL')
    return all_columns
```

**Key Features of This Implementation:**
- ✅ **Pre-selection Priority**: Uses pre-selected elements if they are valid columns
- ✅ **Automatic Fallback**: Collects all columns when no valid pre-selection exists
- ✅ **Validation Logic**: Ensures only structural columns are processed
- ✅ **User Feedback**: Clear messages about which selection method was used
- ✅ **Error Handling**: Specific error messages for host vs linked models
- ✅ **Debug Integration**: Comprehensive logging for troubleshooting

**Benefits:**
- **No Manual Intervention Required**: Script works automatically in both scenarios
- **Efficient Processing**: Only processes relevant elements
- **User-Friendly**: Clear feedback about what's being processed
- **Robust**: Handles edge cases and provides meaningful error messages

### Changelog
**v1.0.3 (2025-10-22)**:
- Added real-world implementation example from "Check Column Dimensions" script
- Documented advanced smart selection pattern with pre-selection validation
- Enhanced documentation with automatic fallback logic
- Added user feedback and error handling patterns

**v1.0.2 (2025-10-22)**:
- Fixed ObjectType import issue causing manual selection to fail
- Added troubleshooting section for common import errors
- Enhanced documentation with error handling guidance

**v1.0.1 (2025-10-16)**:
- Added real-world implementation example in Join Walls to Structure script
- Added file structure and import path documentation
- Enhanced documentation with practical usage patterns

**v1.0.0 (2025-10-16)**:
- Initial implementation
- Smart selection logic dengan pre-selection support
- Multiple category filtering
- Consistent error handling
- Helper functions untuk common use cases