# LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction.md

## Definitive Parameter Extraction Utility

**Version:** 1.0.0
**Date:** 2025-10-22
**Author:** Prasetyo

### Description
Direct parameter extraction utility that prioritizes definitive, unambiguous parameter access without layered fallback structures. Focuses on precise parameter identification and extraction using explicit parameter IDs, names, and built-in parameter enums.

### Core Philosophy

**"Direct Access, No Fallbacks"** - This utility prioritizes definitive parameter extraction over hierarchical fallbacks. If a parameter cannot be found through direct means, it returns None rather than attempting multiple fallback strategies.

### Core Functions

#### **Direct Parameter Extraction by Built-in Parameter**
```python
def extract_builtin_parameter(element, builtin_param):
    """
    Extract parameter value using Revit's BuiltInParameter enum.
    Most reliable method for standard Revit parameters.

    Args:
        element: Revit element
        builtin_param: BuiltInParameter enum value

    Returns:
        Parameter value or None if not found/available
    """
    try:
        param = element.get_Parameter(builtin_param)
        if param and param.HasValue:
            return param.AsDouble()  # or AsString(), AsInteger() based on type
        return None
    except:
        return None
```

#### **Direct Parameter Extraction by Name**
```python
def extract_parameter_by_name(element, param_name, search_type_level=False):
    """
    Extract parameter by exact name match.
    Searches instance level first, optionally type level.

    Args:
        element: Revit element
        param_name (str): Exact parameter name
        search_type_level (bool): Also search type/family level

    Returns:
        Parameter value or None
    """
    # Instance level search
    param = element.LookupParameter(param_name)
    if param and param.HasValue:
        return get_parameter_value(param)

    # Optional type level search
    if search_type_level and element.Symbol:
        param = element.Symbol.LookupParameter(param_name)
        if param and param.HasValue:
            return get_parameter_value(param)

    return None
```

#### **Direct Parameter Extraction by GUID**
```python
def extract_parameter_by_guid(element, param_guid):
    """
    Extract parameter using shared parameter GUID.
    Most reliable for custom shared parameters.

    Args:
        element: Revit element
        param_guid (str): Parameter GUID string

    Returns:
        Parameter value or None
    """
    try:
        guid = Guid(param_guid)
        param = element.get_Parameter(guid)
        if param and param.HasValue:
            return get_parameter_value(param)
        return None
    except:
        return None
```

#### **Type-Safe Parameter Value Extraction**
```python
def get_parameter_value(parameter):
    """
    Extract parameter value based on its storage type.
    Handles Double, Integer, String, and ElementId types.

    Args:
        parameter: Revit Parameter object

    Returns:
        Value in appropriate Python type or None
    """
    if not parameter or not parameter.HasValue:
        return None

    storage_type = parameter.StorageType

    if storage_type == StorageType.Double:
        return parameter.AsDouble()
    elif storage_type == StorageType.Integer:
        return parameter.AsInteger()
    elif storage_type == StorageType.String:
        return parameter.AsString()
    elif storage_type == StorageType.ElementId:
        return parameter.AsElementId()
    else:
        return None
```

### Element-Specific Parameter Extractors

#### **Column Parameters**
```python
def extract_column_dimensions(element):
    """
    Extract definitive column dimensions using direct parameter access.
    Returns dimensions in feet (Revit internal units).

    Args:
        element: Column element

    Returns:
        dict: {'b': float, 'h': float, 'diameter': float, 'type': str} or None
    """
    # Direct built-in parameter extraction
    b = extract_builtin_parameter(element, BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
    h = extract_builtin_parameter(element, BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
    diameter = extract_builtin_parameter(element, BuiltInParameter.STRUCTURAL_SECTION_COMMON_DIAMETER)

    # Determine column type and return appropriate dimensions
    if diameter is not None:
        return {'diameter': diameter, 'type': 'circular'}
    elif b is not None and h is not None:
        # Check if square (b ≈ h within tolerance)
        if abs(b - h) < 1e-6:
            return {'b': b, 'type': 'square'}
        else:
            return {'b': b, 'h': h, 'type': 'rectangular'}
    elif b is not None:
        return {'b': b, 'type': 'square'}

    return None
```

#### **Wall Parameters**
```python
def extract_wall_properties(element):
    """
    Extract definitive wall properties.

    Args:
        element: Wall element

    Returns:
        dict: Wall properties or None
    """
    properties = {}

    # Direct parameter extraction
    properties['width'] = extract_builtin_parameter(element, BuiltInParameter.WALL_USER_HEIGHT_PARAM)
    properties['length'] = extract_builtin_parameter(element, BuiltInParameter.CURVE_ELEM_LENGTH)
    properties['area'] = extract_builtin_parameter(element, BuiltInParameter.HOST_AREA_COMPUTED)

    # Wall function/type
    function_param = extract_builtin_parameter(element, BuiltInParameter.WALL_ATTR_ROOM_BOUNDING)
    properties['is_room_bounding'] = function_param == 1 if function_param is not None else None

    return properties if any(v is not None for v in properties.values()) else None
```

#### **Beam Parameters**
```python
def extract_beam_properties(element):
    """
    Extract definitive beam properties.

    Args:
        element: Beam/Framing element

    Returns:
        dict: Beam properties or None
    """
    properties = {}

    # Section dimensions
    properties['b'] = extract_builtin_parameter(element, BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
    properties['h'] = extract_builtin_parameter(element, BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)

    # Length
    properties['length'] = extract_builtin_parameter(element, BuiltInParameter.CURVE_ELEM_LENGTH)

    return properties if any(v is not None for v in properties.values()) else None
```

### Utility Functions

#### **Parameter Existence Check**
```python
def parameter_exists(element, param_name_or_builtin):
    """
    Check if parameter exists on element without extracting value.

    Args:
        element: Revit element
        param_name_or_builtin: Parameter name (str) or BuiltInParameter

    Returns:
        bool: True if parameter exists and has value
    """
    try:
        if isinstance(param_name_or_builtin, str):
            param = element.LookupParameter(param_name_or_builtin)
        else:
            param = element.get_Parameter(param_name_or_builtin)

        return param is not None and param.HasValue
    except:
        return False
```

#### **Multiple Parameter Extraction**
```python
def extract_multiple_parameters(element, param_specs):
    """
    Extract multiple parameters in single call.

    Args:
        element: Revit element
        param_specs: List of parameter specifications
            Each spec: {'name': str} or {'builtin': BuiltInParameter} or {'guid': str}

    Returns:
        dict: Parameter values keyed by spec identifier
    """
    results = {}

    for spec in param_specs:
        key = spec.get('key', str(spec))

        if 'builtin' in spec:
            value = extract_builtin_parameter(element, spec['builtin'])
        elif 'guid' in spec:
            value = extract_parameter_by_guid(element, spec['guid'])
        elif 'name' in spec:
            search_type = spec.get('search_type_level', False)
            value = extract_parameter_by_name(element, spec['name'], search_type)
        else:
            value = None

        results[key] = value

    return results
```

### Usage Examples

#### **Basic Column Dimension Extraction**
```python
from logic_library.active.utilities.parameters.definitive_extraction import extract_column_dimensions

# Extract column dimensions
column = get_selected_column()
dimensions = extract_column_dimensions(column)

if dimensions:
    if dimensions['type'] == 'circular':
        diameter = dimensions['diameter']
        print(f"Circular column with diameter: {diameter}")
    elif dimensions['type'] == 'rectangular':
        b, h = dimensions['b'], dimensions['h']
        print(f"Rectangular column: {b} x {h}")
```

#### **Multiple Parameter Extraction**
```python
from logic_library.active.utilities.parameters.definitive_extraction import extract_multiple_parameters

# Define parameters to extract
param_specs = [
    {'key': 'width', 'builtin': BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH},
    {'key': 'height', 'builtin': BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT},
    {'key': 'material_name', 'name': 'Material Name', 'search_type_level': True},
    {'key': 'custom_param', 'guid': '550c3e8a-7b6d-4f8e-9c4a-123456789abc'}
]

# Extract all parameters
element = get_selected_element()
params = extract_multiple_parameters(element, param_specs)

print(f"Width: {params.get('width')}")
print(f"Material: {params.get('material_name')}")
```

#### **Batch Parameter Extraction**
```python
def extract_parameters_for_elements(elements, param_specs):
    """
    Extract parameters for multiple elements efficiently.
    """
    results = {}

    for element in elements:
        element_id = element.Id.IntegerValue
        params = extract_multiple_parameters(element, param_specs)
        results[element_id] = params

    return results

# Usage
columns = get_all_columns()
column_specs = [
    {'key': 'b', 'builtin': BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH},
    {'key': 'h', 'builtin': BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT},
    {'key': 'diameter', 'builtin': BuiltInParameter.STRUCTURAL_SECTION_COMMON_DIAMETER}
]

all_params = extract_parameters_for_elements(columns, column_specs)
```

### Benefits

#### **Precision and Reliability**
- Direct parameter access eliminates ambiguity
- No fallback confusion - parameter either exists or doesn't
- Clear failure modes (returns None)

#### **Performance**
- Single API calls instead of multiple attempts
- No unnecessary parameter searches
- Efficient batch processing

#### **Maintainability**
- Explicit parameter specifications
- Clear error handling
- Easy to debug and extend

#### **Type Safety**
- Proper handling of different parameter storage types
- Appropriate return types for each parameter type

### Integration with Logic Library

#### **File Structure**
```
logic-library/active/utilities/parameters/
├── LOG-UTIL-PARAM-001-v1-parameter-finder.py                    # Existing hierarchical finder
├── LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction.md    # This documentation
└── definitive_extraction.py                                    # Implementation
```

#### **Import Pattern**
```python
# For definitive extraction (recommended for new code)
from logic_library.active.utilities.parameters.definitive_extraction import (
    extract_builtin_parameter,
    extract_parameter_by_name,
    extract_column_dimensions,
    extract_multiple_parameters
)

# For legacy hierarchical extraction (when fallbacks needed)
from logic_library.active.utilities.parameters.parameter_finder import (
    find_parameter_element,
    get_parameter_type_info
)
```

### Comparison with Hierarchical Approach

| Aspect | Definitive Extraction | Hierarchical Extraction |
|--------|----------------------|-------------------------|
| **Reliability** | High - Direct access | Variable - Multiple fallbacks |
| **Performance** | Fast - Single calls | Slower - Multiple attempts |
| **Clarity** | Clear - Explicit | Complex - Layered logic |
| **Debugging** | Easy - Direct failures | Complex - Multiple paths |
| **Use Case** | Known parameters | Unknown/exploratory |

### Best Practices

#### **When to Use Definitive Extraction**
- When you know exactly which parameters you need
- For production code requiring high reliability
- When parameter existence is guaranteed by template/standard
- For performance-critical operations

#### **When to Use Hierarchical Extraction**
- When exploring unknown parameter structures
- For backward compatibility with varying templates
- When parameter names vary across projects
- For research/debugging purposes

### Changelog
**v1.0.0 (2025-10-22)**:
- Initial implementation of definitive parameter extraction
- Direct access functions for built-in, named, and GUID parameters
- Element-specific extractors for columns, walls, beams
- Type-safe parameter value extraction
- Multiple parameter batch extraction
- Comprehensive documentation and examples