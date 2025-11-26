---
id: "LOG-UTIL-REBAR-005"
version: "v1"
status: "active"
category: "structural-elements/rebar"
element_type: "RebarBarType"
operation: "inspect"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["rebar", "bar-type", "inspection", "parameters", "diameter", "grade", "properties"]
created: "2025-10-30"
updated: "2025-10-30"
confidence: "high"
performance: "low"
source_file: "PrasKaaPyKit.tab/Rebar.panel/AreaReinforcement.pulldown/InspectRebarBarTypes.pushbutton/script.py"
source_location: "Rebar.panel/AreaReinforcement.pulldown/InspectRebarBarTypes.pushbutton"
---

# LOG-UTIL-REBAR-005-v1: Rebar Bar Type Inspection Framework

## Problem Context

Users need to understand what Rebar Bar Types are available in their Revit project, including their properties, parameters, and specifications. The current implementation requires manual inspection of each type individually, which is time-consuming and error-prone. There's no standardized way to collect and display comprehensive information about all available rebar bar types.

Key challenges:
1. **Parameter Extraction**: Getting all relevant parameters from RebarBarType elements
2. **Unit Conversion**: Converting Revit internal units (feet) to user-friendly units (mm)
3. **Information Organization**: Structuring the data for easy consumption
4. **Type Discovery**: Finding all available RebarBarType elements in the project
5. **Error Handling**: Managing cases where parameters might not be accessible

## Solution Summary

Comprehensive Rebar Bar Type inspection utility that collects all available RebarBarType elements, extracts their parameters and properties, converts units appropriately, and presents the information in a structured format. Provides both detailed inspection and summary views with proper error handling.

## Working Code

### Core Rebar Bar Type Inspection Function

```python
def inspect_rebar_bar_type(rebar_bar_type):
    """
    Inspect a single RebarBarType and extract all relevant information.

    Args:
        rebar_bar_type: RebarBarType element to inspect

    Returns:
        Dictionary containing inspection results
    """
    results = {
        'basic_info': {},
        'parameters': [],
        'properties': [],
        'methods': []
    }

    try:
        # Basic info - use Type Name parameter
        results['basic_info']['id'] = rebar_bar_type.Id

        # Try to get Type Name parameter first
        type_name_param = rebar_bar_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        if type_name_param and type_name_param.AsString():
            results['basic_info']['name'] = type_name_param.AsString()
        else:
            results['basic_info']['name'] = getattr(rebar_bar_type, 'Name', 'Unnamed')

        # Get all parameters
        for param in rebar_bar_type.Parameters:
            try:
                param_info = {
                    'name': param.Definition.Name,
                    'value': 'N/A',
                    'type': param.StorageType.ToString(),
                    'readonly': param.IsReadOnly
                }

                # Try to get parameter value
                if param.StorageType == StorageType.String:
                    param_info['value'] = param.AsString() or 'Empty'
                elif param.StorageType == StorageType.Integer:
                    param_info['value'] = str(param.AsInteger())
                elif param.StorageType == StorageType.Double:
                    # Convert feet to mm for diameter parameters
                    double_value = param.AsDouble()
                    if 'diameter' in param.Definition.Name.lower():
                        # Convert from feet to mm (1 foot = 304.8 mm)
                        mm_value = double_value * 304.8
                        param_info['value'] = "{:.1f} mm".format(mm_value)
                    else:
                        param_info['value'] = str(double_value)
                elif param.StorageType == StorageType.ElementId:
                    elem_id = param.AsElementId()
                    if elem_id != ElementId.InvalidElementId:
                        param_info['value'] = str(elem_id)
                    else:
                        param_info['value'] = 'Invalid ElementId'

                results['parameters'].append(param_info)

            except Exception as e:
                results['parameters'].append({
                    'name': param.Definition.Name,
                    'value': 'Error: {}'.format(str(e)),
                    'type': 'Unknown',
                    'readonly': param.IsReadOnly
                })

        # Get properties
        for attr_name in dir(rebar_bar_type):
            if not attr_name.startswith('_') and not callable(getattr(rebar_bar_type, attr_name)):
                try:
                    value = getattr(rebar_bar_type, attr_name)
                    if not callable(value):
                        results['properties'].append({
                            'name': attr_name,
                            'value': str(value),
                            'type': type(value).__name__
                        })
                except:
                    results['properties'].append({
                        'name': attr_name,
                        'value': 'Error accessing property',
                        'type': 'Unknown'
                    })

        # Get methods
        for attr_name in dir(rebar_bar_type):
            if not attr_name.startswith('_') and callable(getattr(rebar_bar_type, attr_name)):
                results['methods'].append(attr_name)

    except Exception as e:
        results['error'] = str(e)

    return results
```

### Batch Inspection Function

```python
def inspect_all_rebar_bar_types(doc):
    """
    Inspect all RebarBarType elements in the document.

    Args:
        doc: Revit Document

    Returns:
        List of inspection results for all RebarBarType elements
    """
    try:
        # Get all Rebar Bar Types
        rebar_bar_types = FilteredElementCollector(doc)\
            .OfClass(RebarBarType)\
            .ToElements()

        if not rebar_bar_types:
            return []

        # Inspect each type
        inspection_results = []
        for rbt in rebar_bar_types:
            result = inspect_rebar_bar_type(rbt)
            inspection_results.append(result)

        return inspection_results

    except Exception as e:
        print("Error inspecting Rebar Bar Types: {}".format(str(e)))
        return []
```

### Summary Report Generation

```python
def generate_rebar_bar_types_summary(doc, inspection_results=None):
    """
    Generate a summary report of all RebarBarType elements.

    Args:
        doc: Revit Document
        inspection_results: Optional pre-computed inspection results

    Returns:
        Formatted summary string
    """
    if inspection_results is None:
        inspection_results = inspect_all_rebar_bar_types(doc)

    if not inspection_results:
        return "No Rebar Bar Types found in the project."

    report = "=== REBAR BAR TYPES SUMMARY ===\n\n"
    report += "Total Rebar Bar Types: {}\n\n".format(len(inspection_results))

    # Summary table
    report += "SUMMARY TABLE:\n"
    report += "{:<5} {:<30} {:<15} {:<10}\n".format("No.", "Name", "Diameter", "ID")
    report += "-" * 65 + "\n"

    for i, result in enumerate(inspection_results, 1):
        name = result['basic_info'].get('name', 'Unnamed')[:28]  # Truncate long names

        # Find diameter parameter
        diameter = "N/A"
        for param in result['parameters']:
            if 'diameter' in param['name'].lower() and param['value'] != 'N/A':
                diameter = param['value']
                break

        rbt_id = result['basic_info'].get('id', 'N/A')
        report += "{:<5} {:<30} {:<15} {:<10}\n".format(i, name, diameter, str(rbt_id))

    report += "\nDETAILED INSPECTION:\n\n"

    for i, result in enumerate(inspection_results, 1):
        report += "--- REBAR BAR TYPE {} ---\n".format(i)
        report += "ID: {}\n".format(result['basic_info']['id'])
        report += "Name: {}\n".format(result['basic_info']['name'])

        # Add diameter info
        for param in result['parameters']:
            if 'diameter' in param['name'].lower():
                report += "{}: {}\n".format(param['name'], param['value'])
                break

        # Key parameters (limit to important ones)
        key_params = []
        for param in result['parameters']:
            if any(keyword in param['name'].lower() for keyword in ['diameter', 'size', 'grade', 'type']):
                key_params.append("{}: {}".format(param['name'], param['value']))

        if key_params:
            report += "Key Parameters:\n"
            for param in key_params[:5]:  # Limit to 5 key params
                report += "- {}\n".format(param)
        else:
            report += "No key parameters found\n"

        report += "\n"

    return report
```

### Utility Functions for Specific Data Extraction

```python
def get_rebar_bar_type_diameters(doc):
    """
    Get all available rebar bar type diameters in mm.

    Args:
        doc: Revit Document

    Returns:
        List of tuples (name, diameter_mm) sorted by diameter
    """
    try:
        rebar_bar_types = FilteredElementCollector(doc)\
            .OfClass(RebarBarType)\
            .ToElements()

        diameters = []
        for rbt in rebar_bar_types:
            try:
                # Get name
                type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                name = type_name_param.AsString() if type_name_param and type_name_param.AsString() else "Unnamed"

                # Get diameter
                bar_diameter_param = rbt.get_Parameter(BuiltInParameter.REBAR_BAR_DIAMETER)
                if bar_diameter_param:
                    diameter_feet = bar_diameter_param.AsDouble()
                    diameter_mm = diameter_feet * 304.8
                    diameters.append((name, round(diameter_mm, 1)))
            except:
                continue

        # Sort by diameter
        return sorted(diameters, key=lambda x: x[1])

    except Exception:
        return []

def get_rebar_bar_type_names(doc):
    """
    Get all available rebar bar type names.

    Args:
        doc: Revit Document

    Returns:
        List of rebar bar type names
    """
    try:
        rebar_bar_types = FilteredElementCollector(doc)\
            .OfClass(RebarBarType)\
            .ToElements()

        names = []
        for rbt in rebar_bar_types:
            try:
                type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name_param and type_name_param.AsString():
                    names.append(type_name_param.AsString())
                else:
                    names.append(getattr(rbt, 'Name', 'Unnamed'))
            except:
                names.append('Unnamed')

        return sorted(names)

    except Exception:
        return []

def get_rebar_bar_type_ids(doc):
    """
    Get all available rebar bar type IDs.

    Args:
        doc: Revit Document

    Returns:
        List of tuples (name, element_id) for all rebar bar types
    """
    try:
        rebar_bar_types = FilteredElementCollector(doc)\
            .OfClass(RebarBarType)\
            .ToElements()

        ids = []
        for rbt in rebar_bar_types:
            try:
                # Get name
                type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                name = type_name_param.AsString() if type_name_param and type_name_param.AsString() else "Unnamed"

                # Get ElementId
                element_id = rbt.Id
                ids.append((name, element_id))
            except:
                continue

        # Sort by name
        return sorted(ids, key=lambda x: x[0])

    except Exception:
        return []

def get_rebar_bar_type_by_id(doc, element_id):
    """
    Get a specific RebarBarType by its ElementId.

    Args:
        doc: Revit Document
        element_id: ElementId of the RebarBarType

    Returns:
        RebarBarType element or None if not found
    """
    try:
        return doc.GetElement(element_id)
    except Exception:
        return None

def get_rebar_bar_type_by_name(doc, name):
    """
    Get a specific RebarBarType by its name.

    Args:
        doc: Revit Document
        name: Name of the RebarBarType

    Returns:
        RebarBarType element or None if not found
    """
    try:
        rebar_bar_types = FilteredElementCollector(doc)\
            .OfClass(RebarBarType)\
            .ToElements()

        for rbt in rebar_bar_types:
            try:
                type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name_param and type_name_param.AsString() == name:
                    return rbt
                elif getattr(rbt, 'Name', None) == name:
                    return rbt
            except:
                continue

        return None

    except Exception:
        return None
```

## Key Techniques

### 1. **Parameter Value Extraction with Type Handling**
```python
# Handle different parameter storage types
if param.StorageType == StorageType.String:
    param_info['value'] = param.AsString() or 'Empty'
elif param.StorageType == StorageType.Double:
    # Special handling for diameter conversion
    double_value = param.AsDouble()
    if 'diameter' in param.Definition.Name.lower():
        mm_value = double_value * 304.8
        param_info['value'] = "{:.1f} mm".format(mm_value)
```

### 2. **Unit Conversion for User-Friendly Display**
```python
# Convert Revit internal units (feet) to millimeters
diameter_feet = bar_diameter_param.AsDouble()
diameter_mm = diameter_feet * 304.8
param_info['value'] = "{:.1f} mm".format(diameter_mm)
```

### 3. **Robust Error Handling**
```python
try:
    value = getattr(rebar_bar_type, attr_name)
    results['properties'].append({
        'name': attr_name,
        'value': str(value),
        'type': type(value).__name__
    })
except:
    results['properties'].append({
        'name': attr_name,
        'value': 'Error accessing property',
        'type': 'Unknown'
    })
```

### 4. **Filtered Parameter Display**
```python
# Focus on key parameters for summary view
key_params = []
for param in result['parameters']:
    if any(keyword in param['name'].lower() for keyword in ['diameter', 'size', 'grade', 'type']):
        key_params.append("{}: {}".format(param['name'], param['value']))
```

## Usage Examples

### Basic Inspection of All Rebar Bar Types

```python
from logic_library.active.structural_elements.rebar.inspect_rebar_bar_types import inspect_all_rebar_bar_types

# Get all inspection results
inspection_results = inspect_all_rebar_bar_types(doc)

if not inspection_results:
    TaskDialog.Show("Info", "No Rebar Bar Types found in the project!")
else:
    # Display summary
    summary = generate_rebar_bar_types_summary(doc, inspection_results)
    TaskDialog.Show("Rebar Bar Types Summary", summary[:2000])  # Limit dialog size
```

### Get Available Diameters for Selection

```python
from logic_library.active.structural_elements.rebar.inspect_rebar_bar_types import get_rebar_bar_type_diameters

# Get all available diameters
diameters = get_rebar_bar_type_diameters(doc)

if diameters:
    print("Available Rebar Diameters:")
    for name, diameter in diameters:
        print("  {}: {} mm".format(name, diameter))
else:
    print("No rebar bar types found")
```

### Get Rebar Bar Type IDs for Selection

```python
from logic_library.active.structural_elements.rebar.inspect_rebar_bar_types import get_rebar_bar_type_ids

# Get all available IDs
rebar_ids = get_rebar_bar_type_ids(doc)

if rebar_ids:
    print("Available Rebar Bar Types:")
    for name, element_id in rebar_ids:
        print("  {}: ID {}".format(name, element_id))
        print("  {}: ID {}".format(name, element_id.IntegerValue))  # Numeric value
else:
    print("No rebar bar types found")
```

### Get Specific Rebar Bar Type by ID

```python
from logic_library.active.structural_elements.rebar.inspect_rebar_bar_types import get_rebar_bar_type_by_id

# Get specific rebar type by ID
target_id = ElementId(442238)  # Example ID from inspection
rebar_type = get_rebar_bar_type_by_id(doc, target_id)

if rebar_type:
    print("Found rebar type: {}".format(rebar_type.Name))
else:
    print("Rebar type not found")
```

### Get Specific Rebar Bar Type by Name

```python
from logic_library.active.structural_elements.rebar.inspect_rebar_bar_types import get_rebar_bar_type_by_name

# Get specific rebar type by name
rebar_type = get_rebar_bar_type_by_name(doc, "D13")

if rebar_type:
    print("Found rebar type ID: {}".format(rebar_type.Id.IntegerValue))
else:
    print("Rebar type 'D13' not found")
```

### Detailed Inspection with Console Output

```python
from logic_library.active.structural_elements.rebar.inspect_rebar_bar_types import inspect_rebar_bar_type

# Inspect each type individually
rebar_bar_types = FilteredElementCollector(doc).OfClass(RebarBarType).ToElements()

print("=== DETAILED REBAR BAR TYPES INSPECTION ===")

for i, rbt in enumerate(rebar_bar_types, 1):
    print("\n--- REBAR BAR TYPE {} ---".format(i))

    # Inspect detailed parameters
    inspection_results = inspect_rebar_bar_type(rbt)

    print("Basic Info:")
    print("  ID:", inspection_results['basic_info']['id'])
    print("  Name:", inspection_results['basic_info']['name'])

    print("\nParameters:")
    for param in inspection_results['parameters']:
        print("  {}: {} ({}) [{}]".format(param['name'], param['value'], param['type'], 'RO' if param['readonly'] else 'RW'))

    print("\nProperties:")
    for prop in inspection_results['properties'][:10]:  # Limit properties
        print("  {}: {} ({})".format(prop['name'], prop['value'], prop['type']))

    print("\nMethods ({} total):".format(len(inspection_results['methods'])))
    for method in inspection_results['methods'][:15]:  # Limit methods
        print("  {}".format(method))

    if len(inspection_results['methods']) > 15:
        print("  ... and {} more methods".format(len(inspection_results['methods']) - 15))

print("\n=== INSPECTION COMPLETE ===")
print("Total Rebar Bar Types inspected: {}".format(len(rebar_bar_types)))
```

## Performance Notes

- **Execution Time**: Low (simple element collection and parameter reading)
- **Memory Usage**: Low (minimal object creation)
- **API Calls**: Efficient (single FilteredElementCollector call)
- **Thread Safety**: Safe for Revit API usage

## Integration with Logic Library

### File Structure
```
logic-library/active/structural-elements/rebar/
├── LOG-UTIL-REBAR-005-v1-rebar-bar-type-inspection.md
└── inspect_rebar_bar_types.py
```

### Import Pattern
```python
# For comprehensive inspection
from logic_library.active.structural_elements.rebar.inspect_rebar_bar_types import (
    inspect_rebar_bar_type,
    inspect_all_rebar_bar_types,
    generate_rebar_bar_types_summary,
    get_rebar_bar_type_diameters,
    get_rebar_bar_type_names,
    get_rebar_bar_type_ids,
    get_rebar_bar_type_by_id,
    get_rebar_bar_type_by_name
)
```

## Testing Recommendations

```python
def test_rebar_bar_type_inspection():
    """Test Rebar Bar Type inspection functionality"""

    test_results = {
        'collection_success': False,
        'inspection_success': False,
        'parameter_extraction': False,
        'unit_conversion': False,
        'summary_generation': False
    }

    try:
        # Test collection
        rebar_types = FilteredElementCollector(doc).OfClass(RebarBarType).ToElements()
        test_results['collection_success'] = len(rebar_types) >= 0

        if rebar_types:
            # Test single inspection
            first_type = rebar_types[0]
            inspection = inspect_rebar_bar_type(first_type)
            test_results['inspection_success'] = 'basic_info' in inspection and 'parameters' in inspection

            # Test parameter extraction
            if inspection['parameters']:
                diameter_found = any('diameter' in p['name'].lower() for p in inspection['parameters'])
                test_results['parameter_extraction'] = diameter_found

                # Test unit conversion
                diameter_param = next((p for p in inspection['parameters'] if 'diameter' in p['name'].lower()), None)
                if diameter_param and 'mm' in diameter_param['value']:
                    test_results['unit_conversion'] = True

            # Test summary generation
            summary = generate_rebar_bar_types_summary(doc, [inspection])
            test_results['summary_generation'] = len(summary) > 0

    except Exception as e:
        print("Test failed: {}".format(str(e)))

    return test_results
```

## Best Practices

### When to Use
1. **Project Setup**: Use at the beginning of rebar work to understand available types
2. **Type Selection**: Before creating rebar elements to choose appropriate types
3. **Documentation**: Generate reports for project documentation
4. **Troubleshooting**: When rebar creation fails due to type issues

### Error Handling
```python
def safe_rebar_inspection():
    """Wrapper with comprehensive error handling"""

    try:
        inspection_results = inspect_all_rebar_bar_types(doc)

        if not inspection_results:
            TaskDialog.Show("Warning", "No Rebar Bar Types found in the project.")
            return None

        return inspection_results

    except Exception as e:
        TaskDialog.Show("Error", "Failed to inspect Rebar Bar Types: {}".format(str(e)))
        return None
```

## Related Logic Entries

- [LOG-UTIL-REBAR-001-v1-area-reinforcement-creation](LOG-UTIL-REBAR-001-v1-area-reinforcement-creation.md) - Area Reinforcement creation
- [LOG-UTIL-REBAR-002-v1-area-reinforcement-parameter-override](LOG-UTIL-REBAR-002-v1-area-reinforcement-parameter-override.md) - Parameter setting
- [LOG-UTIL-REBAR-003-v1-filled-region-to-geometry-conversion](LOG-UTIL-REBAR-003-v1-filled-region-to-geometry-conversion.md) - Geometry conversion
- [LOG-UTIL-PARAM-001-v1-parameter-extraction](LOG-UTIL-PARAM-001-v1-parameter-extraction.md) - Parameter utilities
- [LOG-UTIL-GENERAL-001-v1-element-collection](LOG-UTIL-GENERAL-001-v1-element-collection.md) - Element collection patterns

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-30