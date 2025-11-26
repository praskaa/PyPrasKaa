---
id: "LOG-UTIL-PARAM-005"
version: "v1"
status: "active"
category: "utilities/parameters"
element_type: "Parameter"
operation: "extraction"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["parameters", "extraction", "error-handling", "robust", "safe-access", "storage-types"]
created: "2025-10-24"
updated: "2025-10-24"
confidence: "high"
performance: "medium"
source_file: "PrasKaaPyKit.tab/Utilities.panel/Detail Item.pulldown/DetailItemInspector.pushbutton/script.py"
source_location: "Utilities.panel/Detail Item.pulldown/DetailItemInspector.pushbutton"
---

# LOG-UTIL-PARAM-005-v1: Robust Parameter Extraction dengan Error Handling

## Problem Context

Parameter extraction di Revit sering gagal karena berbagai alasan: parameter yang tidak memiliki value, akses ke Definition.Name yang error, atau storage type yang tidak didukung. Script Detail Item Inspector menunjukkan bahwa meskipun ada warning, sebagian besar parameter berhasil diekstrak dengan benar.

## Solution Summary

Implementasi robust parameter extraction yang menangani berbagai error scenarios dengan graceful degradation, logging yang informatif, dan fallback mechanisms untuk memastikan ekstraksi parameter tetap berjalan meskipun ada beberapa failure.

## Working Code

### Core Robust Parameter Extraction

```python
def robust_get_parameter_value(param):
    """
    Extract parameter value with comprehensive error handling.
    Handles all storage types with safe access patterns.

    Args:
        param: Revit Parameter object

    Returns:
        tuple: (value, storage_type_str, has_value, error_msg)
               value: Parameter value or None
               storage_type_str: String representation of storage type
               has_value: Boolean indicating if parameter has value
               error_msg: Error message if extraction failed, None otherwise
    """
    if not param:
        return None, "None", False, "Parameter is None"

    try:
        # Safe access to storage type
        storage_type = param.StorageType
        storage_type_str = str(storage_type)

        # Check if parameter has value
        has_value = param.HasValue

        if not has_value:
            return None, storage_type_str, False, None

        # Extract value based on storage type
        try:
            if storage_type == StorageType.Double:
                value = param.AsDouble()
            elif storage_type == StorageType.Integer:
                value = param.AsInteger()
            elif storage_type == StorageType.String:
                value = param.AsString()
            elif storage_type == StorageType.ElementId:
                elem_id = param.AsElementId()
                if elem_id and elem_id != ElementId.InvalidElementId:
                    elem = param.Element.Document.GetElement(elem_id)
                    value = elem.Name if elem else "<Element Not Found>"
                else:
                    value = "<None>"
            else:
                return None, storage_type_str, True, f"Unsupported storage type: {storage_type}"

            return value, storage_type_str, True, None

        except Exception as e:
            return None, storage_type_str, True, f"Value extraction failed: {str(e)}"

    except Exception as e:
        return None, "Unknown", False, f"Storage type access failed: {str(e)}"

def safe_get_parameter_name(param):
    """
    Safely extract parameter name with multiple fallback strategies.

    Args:
        param: Revit Parameter object

    Returns:
        str: Parameter name or fallback description
    """
    if not param:
        return "Invalid Parameter"

    # Primary: Try Definition.Name
    try:
        if param.Definition:
            return param.Definition.Name
    except AttributeError:
        pass
    except Exception as e:
        logger.warning(f"Error accessing Definition.Name: {str(e)}")

    # Fallback 1: Try parameter Id
    try:
        param_id = param.Id
        if param_id:
            return f"Parameter_{param_id.IntegerValue}"
    except:
        pass

    # Fallback 2: Generic description
    try:
        storage_type = str(param.StorageType)
        return f"Unnamed_{storage_type}_Parameter"
    except:
        return "Unnamed_Parameter"
```

### Batch Parameter Extraction dengan Error Tracking

```python
def extract_element_parameters_robust(element, logger=None):
    """
    Extract all parameters from element with comprehensive error handling.
    Returns detailed information about each parameter including extraction status.

    Args:
        element: Revit element (FamilyInstance, FamilySymbol, etc.)
        logger: Optional logger for error reporting

    Returns:
        dict: Parameter extraction results with metadata
    """
    parameters_info = {}
    extraction_stats = {
        'total_attempted': 0,
        'successful': 0,
        'failed': 0,
        'no_value': 0,
        'errors': []
    }

    try:
        # Extract instance parameters
        if hasattr(element, 'Parameters'):
            for param in element.Parameters:
                extraction_stats['total_attempted'] += 1

                param_name = safe_get_parameter_name(param)
                value, storage_type, has_value, error_msg = robust_get_parameter_value(param)

                if error_msg:
                    extraction_stats['failed'] += 1
                    extraction_stats['errors'].append(f"{param_name}: {error_msg}")
                    if logger:
                        logger.warning(f"Parameter extraction failed for '{param_name}': {error_msg}")
                elif not has_value:
                    extraction_stats['no_value'] += 1
                else:
                    extraction_stats['successful'] += 1

                parameters_info[param_name] = {
                    'value': value,
                    'storage_type': storage_type,
                    'has_value': has_value,
                    'is_type_param': False,
                    'extraction_error': error_msg
                }

        # Extract type parameters for FamilyInstance
        if isinstance(element, FamilyInstance):
            try:
                elem_type = element.Symbol
                if elem_type and hasattr(elem_type, 'Parameters'):
                    for param in elem_type.Parameters:
                        extraction_stats['total_attempted'] += 1

                        param_name = safe_get_parameter_name(param)

                        # Skip if already extracted as instance parameter
                        if param_name in parameters_info:
                            continue

                        value, storage_type, has_value, error_msg = robust_get_parameter_value(param)

                        if error_msg:
                            extraction_stats['failed'] += 1
                            extraction_stats['errors'].append(f"Type param {param_name}: {error_msg}")
                        elif not has_value:
                            extraction_stats['no_value'] += 1
                        else:
                            extraction_stats['successful'] += 1

                        parameters_info[param_name] = {
                            'value': value,
                            'storage_type': storage_type,
                            'has_value': has_value,
                            'is_type_param': True,
                            'extraction_error': error_msg
                        }
            except Exception as e:
                error_msg = f"Type parameter extraction failed: {str(e)}"
                extraction_stats['errors'].append(error_msg)
                if logger:
                    logger.error(error_msg)

        # Add extraction statistics
        parameters_info['_extraction_stats'] = extraction_stats

    except Exception as e:
        error_msg = f"Critical error in parameter extraction: {str(e)}"
        if logger:
            logger.error(error_msg)
        parameters_info['_extraction_stats'] = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 1,
            'no_value': 0,
            'errors': [error_msg]
        }

    return parameters_info
```

## Key Techniques

### 1. **Multi-Level Error Handling**
```python
try:
    # Primary extraction
    value = param.AsDouble()
except Exception as e:
    # Fallback with error reporting
    return None, storage_type_str, True, f"Value extraction failed: {str(e)}"
```

### 2. **Safe Property Access**
```python
def safe_get_parameter_name(param):
    try:
        if param.Definition:
            return param.Definition.Name
    except AttributeError:
        pass  # Continue to fallbacks
```

### 3. **Comprehensive Status Tracking**
```python
extraction_stats = {
    'total_attempted': 0,
    'successful': 0,
    'failed': 0,
    'no_value': 0,
    'errors': []
}
```

### 4. **Graceful Degradation**
- Jika satu parameter gagal, lanjutkan ke parameter berikutnya
- Tetap return partial results meskipun ada error
- Log error tapi jangan hentikan proses

## Performance Notes

- **Execution Time**: Medium (karena comprehensive error checking)
- **Memory Usage**: Medium (stores error messages and statistics)
- **Success Rate**: High (handles various failure scenarios)
- **Scalability**: Good (processes parameters individually)

## Usage Examples

### Basic Robust Extraction

```python
from logic_library.active.utilities.parameters.robust_extraction import extract_element_parameters_robust

# Extract parameters with error handling
element = get_selected_element()
params = extract_element_parameters_robust(element, logger=script.get_logger())

# Check extraction statistics
stats = params.get('_extraction_stats', {})
print(f"Successfully extracted {stats.get('successful', 0)} parameters")
print(f"Failed to extract {stats.get('failed', 0)} parameters")

# Process parameters
for param_name, param_info in params.items():
    if param_name.startswith('_'):
        continue  # Skip metadata

    if param_info['extraction_error']:
        print(f"Warning: {param_name} - {param_info['extraction_error']}")
    elif param_info['has_value']:
        print(f"{param_name}: {param_info['value']} ({param_info['storage_type']})")
```

### Filtered Parameter Display

```python
def display_parameters_filtered(params, show_errors=True, show_no_value=False):
    """Display parameters with filtering options"""

    for param_name, param_info in sorted(params.items()):
        if param_name.startswith('_'):
            continue

        error = param_info.get('extraction_error')
        has_value = param_info.get('has_value', False)

        # Filter based on options
        if error and not show_errors:
            continue
        if not has_value and not show_no_value:
            continue

        # Display with appropriate formatting
        if error:
            print(f"❌ {param_name}: ERROR - {error}")
        elif not has_value:
            print(f"⚠️  {param_name}: <No Value> ({param_info.get('storage_type', 'Unknown')})")
        else:
            value = param_info.get('value', 'Unknown')
            param_type = "Type" if param_info.get('is_type_param') else "Instance"
            print(f"✅ {param_name} ({param_type}): {value}")
```

## Comparison with Basic Extraction

| Aspect | Basic Extraction | Robust Extraction |
|--------|------------------|-------------------|
| **Error Handling** | Minimal | Comprehensive |
| **Failure Impact** | Stops on error | Continues processing |
| **Information** | Value only | Value + metadata + errors |
| **Debugging** | Difficult | Detailed error reporting |
| **Performance** | Fast | Medium |
| **Reliability** | Variable | High |

## Common Pitfalls Solved

1. **Definition.Name Access**: Handles AttributeError dengan fallback
2. **Storage Type Issues**: Comprehensive type checking
3. **Element Resolution**: Safe ElementId to element name conversion
4. **Partial Failures**: Continues processing despite individual parameter errors
5. **Memory Issues**: Avoids storing large error objects

## Integration with Logic Library

### File Structure
```
logic-library/active/utilities/parameters/
├── LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction.md
├── LOG-UTIL-PARAM-005-v1-robust-parameter-extraction.md
└── robust_extraction.py
```

### Import Pattern
```python
# For robust extraction with error handling
from logic_library.active.utilities.parameters.robust_extraction import (
    robust_get_parameter_value,
    safe_get_parameter_name,
    extract_element_parameters_robust
)
```

## Related Logic Entries

- [LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction](LOG-UTIL-PARAM-002-v1-definitive-parameter-extraction.md) - Direct parameter access
- [LOG-UTIL-ERROR-003-v1-modifier-key-handling](LOG-UTIL-ERROR-003-v1-modifier-key-handling.md) - Error handling patterns
- [LOG-UTIL-ERROR-004-v1-statistics-display](LOG-UTIL-ERROR-004-v1-statistics-display.md) - Statistics and feedback

## Optimization History

*Initial version (v1) with comprehensive error handling and robust parameter extraction patterns derived from Detail Item Inspector script analysis.*

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-24