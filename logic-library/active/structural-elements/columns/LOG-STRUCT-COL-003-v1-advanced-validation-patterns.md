# LOG-STRUCT-COL-003-v1-advanced-validation-patterns.md

## Advanced Validation Patterns for Structural Elements

**Version:** 1.0.0
**Date:** 2025-10-22
**Author:** Prasetyo

### Description
Advanced validation patterns extracted from "Check Column Dimensions" script, demonstrating sophisticated approaches for validating structural elements across multiple dimensions including geometry intersection, family type checking, parameter validation, and hierarchical data processing.

### Core Validation Logic Patterns

#### 1. **Multi-Level Validation Hierarchy**
```python
def process_column_validation(host_column, linked_columns_dict):
    """
    Multi-level validation with clear decision hierarchy:
    1. Geometric intersection (spatial matching)
    2. Family type compatibility (semantic matching)
    3. Parameter validation (quantitative matching)
    4. Result classification (status assignment)
    """
    # Level 1: Geometric intersection
    best_match, intersection_volume = find_best_match(host_column, linked_columns_dict)
    if not best_match:
        return "Unmatched", validation_data

    # Level 2: Family type compatibility
    host_family_type = get_family_geometry_type(host_column)
    linked_family_type = get_family_geometry_type(best_match)
    if host_family_type != linked_family_type:
        return "Family unmatched", validation_data

    # Level 3: Parameter validation
    host_dims = get_column_dimensions(host_column)
    linked_dims = get_column_dimensions(best_match)
    if not host_dims or not linked_dims:
        return "Dimension to be checked", validation_data

    # Level 4: Quantitative comparison
    if compare_dimensions(host_dims, linked_dims):
        return "Approved", validation_data
    else:
        return "Dimension to be checked", validation_data
```

#### 2. **Smart Selection with Automatic Fallback**
```python
def collect_host_columns():
    """
    Intelligent element collection with automatic fallback logic:
    - Prioritizes user pre-selection
    - Validates pre-selected elements
    - Falls back to automatic collection
    - Provides clear user feedback
    """
    # Check pre-selected elements
    selection_ids = uidoc.Selection.GetElementIds()
    pre_selected_elements = []

    if selection_ids:
        # Validate pre-selected elements are structural columns
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            if elem and elem.Category:
                if elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralColumns):
                    pre_selected_elements.append(elem)

        if pre_selected_elements:
            return pre_selected_elements  # Use validated pre-selection

    # Automatic fallback - collect all structural columns
    all_columns = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralColumns)\
        .WhereElementIsNotElementType()\
        .ToElements()

    return all_columns
```

#### 3. **Hierarchical Parameter Extraction**
```python
def get_column_dimensions(column):
    """
    Hierarchical parameter extraction with fallback levels:
    1. Built-in parameters (STRUCTURAL_SECTION_COMMON_*)
    2. Instance-level custom parameters (b, h, diameter)
    3. Type-level parameters (family symbol parameters)
    4. Intelligent type inference (square vs rectangular)
    """
    # Level 1: Built-in parameters
    b_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
    h_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
    diameter_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_DIAMETER)

    # Level 2: Instance-level custom parameters
    if not b_param or not b_param.HasValue:
        b_param = column.LookupParameter("b") or column.LookupParameter("B") or column.LookupParameter("Width")

    # Level 3: Type-level parameters
    if not b_param and column.Symbol:
        b_param = column.Symbol.LookupParameter("b") or column.Symbol.LookupParameter("B") or column.Symbol.LookupParameter("Width")

    # Level 4: Intelligent type inference
    if diameter_value is not None:
        return {'diameter': diameter_value, 'type': 'circular'}
    elif b_value is not None and h_value is not None:
        if abs(b_value - h_value) < 1e-6:
            return {'b': b_value, 'type': 'square'}
        else:
            return {'b': b_value, 'h': h_value, 'type': 'rectangular'}
```

#### 4. **Name-Based Geometry Type Detection**
```python
def get_family_geometry_type(column):
    """
    Multi-stage geometry type detection:
    1. Family/type name analysis (primary method)
    2. Name parsing with separators (-, _, space)
    3. Keyword matching for geometry types
    4. Parameter-based fallback (secondary method)
    """
    family_symbol = get_family_type(column)
    if not family_symbol:
        # Fallback to parameter detection
        dims = get_column_dimensions(column)
        return dims.get('type', 'unknown') if dims else 'unknown'

    # Safe name extraction with null checking
    family_name = ""
    type_name = ""

    try:
        if family_symbol.Family and hasattr(family_symbol.Family, 'Name') and family_symbol.Family.Name:
            family_name = str(family_symbol.Family.Name).lower()
    except Exception as e:
        debug_log("Could not get family name: {}".format(e))

    try:
        if hasattr(family_symbol, 'Name') and family_symbol.Name:
            type_name = str(family_symbol.Name).lower()
    except Exception as e:
        debug_log("Could not get type name: {}".format(e))

    # Parse names with multiple separators
    all_parts = []
    for name in [family_name, type_name]:
        if name:
            for separator in ['-', '_', ' ']:
                if separator in name:
                    all_parts.extend([part.strip() for part in name.split(separator)])
                    break
            else:
                all_parts.append(name)

    # Keyword matching for geometry types
    circular_keywords = ['round', 'circular', 'circle', 'pipe', 'tube', 'diameter', 'ø', 'bulat']
    square_keywords = ['square', 'box', 'kuadrat']
    rectangular_keywords = ['rectangular', 'rectangle', 'rect', 'persegi panjang']

    for part in all_parts:
        part_lower = part.lower()
        if part_lower in circular_keywords:
            return 'circular'
        elif part_lower in square_keywords:
            return 'square'
        elif part_lower in rectangular_keywords:
            return 'rectangular'

    # Final fallback to parameter detection
    dims = get_column_dimensions(column)
    return dims.get('type', 'unknown') if dims else 'unknown'
```

#### 5. **Advanced Geometric Intersection Analysis**
```python
def find_best_match(host_column, linked_columns_dict):
    """
    Sophisticated geometric matching with:
    - Boolean intersection volume calculation
    - Multi-candidate ranking
    - Volume threshold validation
    - Comprehensive debugging output
    """
    host_solid = get_solid(host_column)
    if not host_solid:
        return None, 0.0

    best_match = None
    max_intersection_volume = 0.0
    all_candidates = []

    # Analyze all possible intersections
    for linked_column_id, linked_column_data in linked_columns_dict.items():
        linked_solid = linked_column_data['solid']
        if not linked_solid:
            continue

        try:
            intersection_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, linked_solid, BooleanOperationsType.Intersect
            )

            volume = intersection_solid.Volume if intersection_solid else 0.0
            all_candidates.append((linked_column_id, volume))

            if volume > max_intersection_volume:
                max_intersection_volume = volume
                best_match = linked_column_data['element']

        except Exception as e:
            debug_log("Boolean operation failed: {}".format(e))

    # Sort and log top candidates for debugging
    sorted_candidates = sorted(all_candidates, key=lambda x: x[1], reverse=True)

    debug_log("Top intersection candidates:")
    for i, (linked_id, vol) in enumerate(sorted_candidates[:5]):
        vol_mm3 = feet3_to_mm3(vol)
        marker = "*** BEST MATCH ***" if vol == max_intersection_volume else ""
        debug_log("#{}. Linked {}: {:.6f} cu ft ({:.0f} mm³) {}".format(
            i+1, linked_id, vol, vol_mm3, marker))

    return best_match, max_intersection_volume
```

#### 6. **Unit Conversion and Precision Handling**
```python
def compare_dimensions(host_dims, linked_dims):
    """
    Precision-aware dimension comparison:
    - Convert to millimeters for human-readable precision
    - Apply appropriate tolerance (0.01mm)
    - Handle different geometry types
    - Provide detailed mismatch information
    """
    if not host_dims or not linked_dims:
        return False

    if host_dims.get('type') != linked_dims.get('type'):
        return False

    # Convert feet to mm for comparison
    tolerance_mm = 0.01
    tolerance_feet = tolerance_mm / 304.8

    def feet_to_mm(feet_value):
        try:
            from Autodesk.Revit.DB import UnitUtils, UnitTypeId
            return UnitUtils.ConvertFromInternalUnits(feet_value, UnitTypeId.Millimeters)
        except ImportError:
            return feet_value * 304.8

    # Compare based on geometry type
    if host_dims['type'] == 'circular':
        host_diam_mm = feet_to_mm(host_dims.get('diameter'))
        linked_diam_mm = feet_to_mm(linked_dims.get('diameter'))
        diff_mm = abs(host_diam_mm - linked_diam_mm)

        if diff_mm > tolerance_mm:
            logger.debug("Circular mismatch: {:.2f}mm vs {:.2f}mm (diff: {:.2f}mm)".format(
                host_diam_mm, linked_diam_mm, diff_mm))
            return False
        return True

    elif host_dims['type'] == 'rectangular':
        # Compare both dimensions with detailed logging
        host_b_mm = feet_to_mm(host_dims.get('b'))
        host_h_mm = feet_to_mm(host_dims.get('h'))
        linked_b_mm = feet_to_mm(linked_dims.get('b'))
        linked_h_mm = feet_to_mm(linked_dims.get('h'))

        b_diff = abs(host_b_mm - linked_b_mm)
        h_diff = abs(host_h_mm - linked_h_mm)

        if b_diff > tolerance_mm or h_diff > tolerance_mm:
            logger.debug("Rectangular mismatch: b({:.2f}mm vs {:.2f}mm), h({:.2f}mm vs {:.2f}mm)".format(
                host_b_mm, linked_b_mm, host_h_mm, linked_h_mm))
            return False
        return True
```

### Applications for Other Structural Elements

#### **Walls - Orientation and Layer Validation**
```python
def validate_wall_orientation(host_wall, linked_walls_dict):
    """
    Wall validation pattern:
    1. Geometric intersection (spatial alignment)
    2. Orientation matching (vertical/horizontal)
    3. Layer composition comparison
    4. Dimension validation (thickness, height)
    """
    # Similar multi-level validation approach
    best_match = find_wall_intersection(host_wall, linked_walls_dict)
    if not best_match:
        return "No intersection"

    # Check orientation
    host_orientation = get_wall_orientation(host_wall)
    linked_orientation = get_wall_orientation(best_match)
    if host_orientation != linked_orientation:
        return "Orientation mismatch"

    # Compare wall composition and dimensions
    # ... similar pattern to column validation
```

#### **Beams - Span and Loading Validation**
```python
def validate_beam_parameters(host_beam, linked_beams_dict):
    """
    Beam validation pattern:
    1. Geometric intersection (alignment)
    2. Span length comparison
    3. Section profile matching
    4. Loading condition validation
    """
    # Multi-level validation similar to columns
    # Focus on beam-specific parameters (span, section, loading)
```

#### **Foundations - Bearing and Capacity Validation**
```python
def validate_foundation_capacity(host_foundation, linked_foundations_dict):
    """
    Foundation validation pattern:
    1. Geometric intersection (positioning)
    2. Bearing capacity comparison
    3. Soil condition matching
    4. Size and shape validation
    """
    # Similar hierarchical validation approach
    # Focus on foundation-specific engineering parameters
```

### Benefits of These Patterns

#### **Modular and Reusable**
- Each validation level can be used independently
- Easy to extend for new element types
- Consistent error handling across all validations

#### **Comprehensive Coverage**
- Handles edge cases and error conditions
- Provides detailed debugging information
- Supports multiple fallback mechanisms

#### **Performance Optimized**
- Pre-calculates geometry for batch processing
- Efficient intersection algorithms
- Memory management with cleanup

#### **User Experience**
- Clear progress feedback
- Detailed error messages
- Automatic fallback behavior

### Implementation Guidelines

#### **For New Structural Element Validators**
1. **Follow the 4-Level Validation Hierarchy**
2. **Implement Smart Selection Pattern**
3. **Use Hierarchical Parameter Extraction**
4. **Apply Name-Based Type Detection**
5. **Include Comprehensive Debugging**

#### **Integration with Logic Library**
- Use existing utilities (smart selection, parameter finder)
- Follow established naming conventions
- Include proper documentation and examples
- Add to logic library index

### Changelog
**v1.0.0 (2025-10-22)**:
- Initial documentation of advanced validation patterns
- Extracted patterns from "Check Column Dimensions" script
- Added examples for walls, beams, and foundations
- Included implementation guidelines and benefits