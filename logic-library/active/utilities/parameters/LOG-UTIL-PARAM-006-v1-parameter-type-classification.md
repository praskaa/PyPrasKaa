---
id: "LOG-UTIL-PARAM-006"
version: "v1"
status: "active"
category: "utilities/parameters"
element_type: "Parameter"
operation: "classification"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["parameters", "classification", "instance", "type", "family", "metadata", "organization"]
created: "2025-10-24"
updated: "2025-10-24"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Utilities.panel/Detail Item.pulldown/DetailItemInspector.pushbutton/script.py"
source_location: "Utilities.panel/Detail Item.pulldown/DetailItemInspector.pushbutton"
---

# LOG-UTIL-PARAM-006-v1: Parameter Type Classification (Instance vs Type)

## Problem Context

Di Revit, parameter bisa berada di dua level: **Instance Level** (berlaku per elemen) dan **Type Level** (berlaku untuk semua instance dari type tersebut). Script Detail Item Inspector menunjukkan bahwa klasifikasi ini penting untuk:

1. **Display yang jelas**: Menunjukkan apakah parameter adalah instance atau type parameter
2. **Editing logic**: Type parameter perlu akses melalui Symbol/Family
3. **User understanding**: User perlu tahu parameter mana yang bisa diubah per instance

Dari debug output, kita lihat klasifikasi bekerja dengan baik:
- **Instance Parameter**: `Area`, `Comments`, `Mark`, `Location Text`
- **Type Parameter**: `Array Bot Additional 1.1`, `B Width`, `H Height`, `Diameter Stirrup`

## Solution Summary

Implementasi sistem klasifikasi parameter yang secara otomatis mendeteksi dan mengkategorikan parameter sebagai instance atau type, dengan metadata tambahan untuk membantu user dan developer memahami konteks parameter.

## Working Code

### Core Parameter Classification

```python
def classify_parameter_type(element, param):
    """
    Classify parameter as instance or type parameter with detailed metadata.

    Args:
        element: Revit element
        param: Revit Parameter object

    Returns:
        dict: Classification information
    """
    classification = {
        'is_instance_param': False,
        'is_type_param': False,
        'param_level': 'unknown',
        'access_path': None,
        'can_modify_instance': False,
        'can_modify_type': False,
        'scope': 'unknown',
        'metadata': {}
    }

    if not param or not element:
        return classification

    try:
        # Check if parameter exists on instance level
        instance_param = element.LookupParameter(param.Definition.Name)
        if instance_param and instance_param.Id == param.Id:
            classification['is_instance_param'] = True
            classification['param_level'] = 'instance'
            classification['can_modify_instance'] = not param.IsReadOnly
            classification['scope'] = 'per_instance'
            return classification

        # Check if parameter exists on type level
        if isinstance(element, FamilyInstance):
            type_param = element.Symbol.LookupParameter(param.Definition.Name)
            if type_param and type_param.Id == param.Id:
                classification['is_type_param'] = True
                classification['param_level'] = 'type'
                classification['can_modify_type'] = not param.IsReadOnly
                classification['scope'] = 'per_type'
                classification['access_path'] = 'element.Symbol'
                return classification

        elif isinstance(element, FamilySymbol):
            # For FamilySymbol, all parameters are type-level
            classification['is_type_param'] = True
            classification['param_level'] = 'type'
            classification['can_modify_type'] = not param.IsReadOnly
            classification['scope'] = 'per_type'
            classification['access_path'] = 'element'
            return classification

        # Fallback: try to determine from parameter properties
        classification['param_level'] = 'undetermined'
        classification['metadata']['needs_investigation'] = True

    except Exception as e:
        classification['metadata']['classification_error'] = str(e)
        classification['param_level'] = 'error'

    return classification

def get_parameter_hierarchy_info(element):
    """
    Get comprehensive parameter hierarchy information for an element.

    Args:
        element: Revit element

    Returns:
        dict: Hierarchical parameter information
    """
    hierarchy = {
        'instance_parameters': {},
        'type_parameters': {},
        'shared_parameters': {},
        'statistics': {
            'total_instance': 0,
            'total_type': 0,
            'total_shared': 0,
            'readonly_instance': 0,
            'readonly_type': 0
        }
    }

    try:
        # Process instance parameters
        if hasattr(element, 'Parameters'):
            for param in element.Parameters:
                try:
                    param_name = param.Definition.Name
                    classification = classify_parameter_type(element, param)

                    param_info = {
                        'value': get_parameter_value_safe(param),
                        'storage_type': str(param.StorageType),
                        'is_readonly': param.IsReadOnly,
                        'classification': classification
                    }

                    if classification['is_instance_param']:
                        hierarchy['instance_parameters'][param_name] = param_info
                        hierarchy['statistics']['total_instance'] += 1
                        if param.IsReadOnly:
                            hierarchy['statistics']['readonly_instance'] += 1

                    elif classification['is_type_param']:
                        hierarchy['type_parameters'][param_name] = param_info
                        hierarchy['statistics']['total_type'] += 1
                        if param.IsReadOnly:
                            hierarchy['statistics']['readonly_type'] += 1

                    # Check if shared parameter
                    if hasattr(param.Definition, 'ParameterGroup'):
                        param_group = param.Definition.ParameterGroup
                        if param_group == ParameterGroupId.SharedParameters:
                            hierarchy['shared_parameters'][param_name] = param_info
                            hierarchy['statistics']['total_shared'] += 1

                except Exception as e:
                    logger.warning(f"Error processing parameter: {str(e)}")
                    continue

        # Add type parameters for FamilyInstance (if not already included)
        if isinstance(element, FamilyInstance) and element.Symbol:
            try:
                for param in element.Symbol.Parameters:
                    param_name = param.Definition.Name

                    # Skip if already processed as instance parameter
                    if param_name in hierarchy['instance_parameters']:
                        continue

                    classification = classify_parameter_type(element, param)
                    param_info = {
                        'value': get_parameter_value_safe(param),
                        'storage_type': str(param.StorageType),
                        'is_readonly': param.IsReadOnly,
                        'classification': classification
                    }

                    hierarchy['type_parameters'][param_name] = param_info
                    hierarchy['statistics']['total_type'] += 1
                    if param.IsReadOnly:
                        hierarchy['statistics']['readonly_type'] += 1

            except Exception as e:
                logger.warning(f"Error processing type parameters: {str(e)}")

    except Exception as e:
        logger.error(f"Critical error in parameter hierarchy analysis: {str(e)}")

    return hierarchy
```

### Parameter Modification Capability Analysis

```python
def analyze_parameter_modification_capabilities(element):
    """
    Analyze which parameters can be modified and how.

    Args:
        element: Revit element

    Returns:
        dict: Modification capabilities analysis
    """
    capabilities = {
        'modifiable_instance_params': [],
        'modifiable_type_params': [],
        'readonly_params': [],
        'requires_transaction': [],
        'modification_methods': {}
    }

    hierarchy = get_parameter_hierarchy_info(element)

    # Analyze instance parameters
    for param_name, param_info in hierarchy['instance_parameters'].items():
        if not param_info['is_readonly']:
            capabilities['modifiable_instance_params'].append(param_name)
            capabilities['requires_transaction'].append(param_name)
            capabilities['modification_methods'][param_name] = {
                'method': 'element.LookupParameter(name).Set(value)',
                'level': 'instance',
                'transaction_required': True
            }
        else:
            capabilities['readonly_params'].append(param_name)

    # Analyze type parameters
    for param_name, param_info in hierarchy['type_parameters'].items():
        if not param_info['is_readonly']:
            capabilities['modifiable_type_params'].append(param_name)
            capabilities['requires_transaction'].append(param_name)
            if isinstance(element, FamilyInstance):
                capabilities['modification_methods'][param_name] = {
                    'method': 'element.Symbol.LookupParameter(name).Set(value)',
                    'level': 'type',
                    'transaction_required': True
                }
            else:
                capabilities['modification_methods'][param_name] = {
                    'method': 'element.LookupParameter(name).Set(value)',
                    'level': 'type',
                    'transaction_required': True
                }
        else:
            capabilities['readonly_params'].append(param_name)

    return capabilities
```

### Display Functions dengan Classification

```python
def display_parameter_hierarchy(hierarchy, output_window=None):
    """
    Display parameter hierarchy in organized format.

    Args:
        hierarchy: Parameter hierarchy from get_parameter_hierarchy_info()
        output_window: PyRevit output window (optional)
    """
    def print_line(text):
        if output_window:
            output_window.print_md(text)
        else:
            print(text)

    stats = hierarchy['statistics']

    print_line("# Parameter Hierarchy Analysis")
    print_line("---")
    print_line(f"**Total Parameters:** {stats['total_instance'] + stats['total_type']}")
    print_line(f"- Instance Parameters: {stats['total_instance']}")
    print_line(f"- Type Parameters: {stats['total_type']}")
    print_line(f"- Shared Parameters: {stats['total_shared']}")
    print_line("---")

    # Display instance parameters
    if hierarchy['instance_parameters']:
        print_line("## Instance Parameters (Per Element)")
        for param_name in sorted(hierarchy['instance_parameters'].keys()):
            param_info = hierarchy['instance_parameters'][param_name]
            readonly_marker = " 🔒" if param_info['is_readonly'] else ""
            value_display = param_info['value'] if param_info['value'] is not None else "<No Value>"
            print_line(f"- **{param_name}**{readonly_marker}: `{value_display}` ({param_info['storage_type']})")

    # Display type parameters
    if hierarchy['type_parameters']:
        print_line("## Type Parameters (Shared by Type)")
        for param_name in sorted(hierarchy['type_parameters'].keys()):
            param_info = hierarchy['type_parameters'][param_name]
            readonly_marker = " 🔒" if param_info['is_readonly'] else ""
            value_display = param_info['value'] if param_info['value'] is not None else "<No Value>"
            print_line(f"- **{param_name}**{readonly_marker}: `{value_display}` ({param_info['storage_type']})")

    # Display shared parameters
    if hierarchy['shared_parameters']:
        print_line("## Shared Parameters")
        for param_name in sorted(hierarchy['shared_parameters'].keys()):
            param_info = hierarchy['shared_parameters'][param_name]
            level = "Instance" if param_info['classification']['is_instance_param'] else "Type"
            print_line(f"- **{param_name}** ({level})")
```

## Key Techniques

### 1. **Dual Level Parameter Access**
```python
# Instance level
instance_param = element.LookupParameter(name)

# Type level
if isinstance(element, FamilyInstance):
    type_param = element.Symbol.LookupParameter(name)
```

### 2. **Parameter ID Comparison**
```python
if instance_param and instance_param.Id == param.Id:
    # This is an instance parameter
```

### 3. **Modification Capability Detection**
```python
can_modify = not param.IsReadOnly
requires_transaction = True  # Most parameter modifications need transactions
```

### 4. **Scope Determination**
```python
scope = 'per_instance' if is_instance_param else 'per_type'
```

## Performance Notes

- **Execution Time**: Fast (linear scan of parameters)
- **Memory Usage**: Low (stores classification metadata)
- **Scalability**: Excellent (handles elements with many parameters)
- **Accuracy**: High (uses Revit API parameter relationships)

## Usage Examples

### Basic Parameter Classification

```python
from logic_library.active.utilities.parameters.parameter_classification import get_parameter_hierarchy_info

# Analyze parameter hierarchy
element = get_selected_element()
hierarchy = get_parameter_hierarchy_info(element)

# Display summary
stats = hierarchy['statistics']
print(f"Element has {stats['total_instance']} instance and {stats['total_type']} type parameters")
```

### Modification Capability Analysis

```python
from logic_library.active.utilities.parameters.parameter_classification import analyze_parameter_modification_capabilities

# Check what can be modified
capabilities = analyze_parameter_modification_capabilities(element)

print("Modifiable instance parameters:")
for param in capabilities['modifiable_instance_params']:
    method = capabilities['modification_methods'][param]
    print(f"- {param}: {method['method']}")

print("Modifiable type parameters:")
for param in capabilities['modifiable_type_params']:
    method = capabilities['modification_methods'][param]
    print(f"- {param}: {method['method']}")
```

### Interactive Parameter Editor

```python
def create_parameter_editor(element):
    """Create interactive parameter editor based on classification"""

    capabilities = analyze_parameter_modification_capabilities(element)

    # Build options menu
    options = []
    param_methods = {}

    # Instance parameters
    for param_name in capabilities['modifiable_instance_params']:
        options.append(f"Edit Instance: {param_name}")
        param_methods[f"Edit Instance: {param_name}"] = {
            'name': param_name,
            'level': 'instance',
            'method': capabilities['modification_methods'][param_name]
        }

    # Type parameters
    for param_name in capabilities['modifiable_type_params']:
        options.append(f"Edit Type: {param_name}")
        param_methods[f"Edit Type: {param_name}"] = {
            'name': param_name,
            'level': 'type',
            'method': capabilities['modification_methods'][param_name]
        }

    if not options:
        forms.alert("No modifiable parameters found.", title="Parameter Editor")
        return

    # Show selection dialog
    selected_option = forms.CommandSwitchWindow.show(
        options,
        message="Select parameter to edit:"
    )

    if selected_option and selected_option in param_methods:
        param_info = param_methods[selected_option]
        edit_parameter_interactive(element, param_info)
```

## Comparison with Basic Parameter Access

| Aspect | Basic Access | Classification-Based |
|--------|--------------|---------------------|
| **Information** | Value only | Value + type + capabilities |
| **Modification** | Manual logic | Guided by classification |
| **User Experience** | Generic | Context-aware |
| **Error Prevention** | None | Prevents invalid modifications |
| **Code Complexity** | Low | Medium |

## Integration with Logic Library

### File Structure
```
logic-library/active/utilities/parameters/
├── LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction.md
├── LOG-UTIL-PARAM-005-v1-robust-parameter-extraction.md
├── LOG-UTIL-PARAM-006-v1-parameter-type-classification.md
└── parameter_classification.py
```

### Import Pattern
```python
# For parameter classification and hierarchy analysis
from logic_library.active.utilities.parameters.parameter_classification import (
    classify_parameter_type,
    get_parameter_hierarchy_info,
    analyze_parameter_modification_capabilities,
    display_parameter_hierarchy
)
```

## Related Logic Entries

- [LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction](LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction.md) - Parameter value extraction
- [LOG-UTIL-PARAM-005-v1-robust-parameter-extraction](LOG-UTIL-PARAM-005-v1-robust-parameter-extraction.md) - Error-resilient extraction
- [LOG-UTIL-UI-005-v1-simple-option-selection](LOG-UTIL-UI-005-v1-simple-option-selection.md) - UI for parameter selection

## Best Practices

### When to Use Classification

1. **Parameter Inspection Tools**: Show users parameter types clearly
2. **Bulk Parameter Editing**: Know which parameters can be modified
3. **Template Development**: Understand parameter scope for families
4. **Debugging**: Identify why parameter access fails

### Classification Accuracy Tips

1. **Always check both levels**: Instance and type parameters
2. **Use parameter IDs for comparison**: Names can conflict
3. **Handle FamilySymbol specially**: All parameters are type-level
4. **Check IsReadOnly**: Determines modification capability

## Optimization History

*Initial version (v1) with comprehensive parameter classification derived from Detail Item Inspector's successful parameter organization patterns.*

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-24