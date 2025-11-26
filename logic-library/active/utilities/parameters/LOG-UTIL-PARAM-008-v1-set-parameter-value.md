---
id: "LOG-UTIL-PARAM-008"
version: "v1"
status: "active"
category: "utilities/parameters"
element_type: "Parameter"
operation: "set-value"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["parameters", "set", "modify", "transaction", "validation", "instance", "type", "overwrite"]
created: "2025-10-24"
updated: "2025-10-24"
confidence: "high"
performance: "medium"
source_file: "PrasKaaPyKit.tab/Utilities.panel/Detail Item.pulldown/DetailItemInspector.pushbutton/script.py"
source_location: "Utilities.panel/Detail Item.pulldown/DetailItemInspector.pushbutton"
---

# LOG-UTIL-PARAM-008-v1: Set Parameter Value dengan Transaction Management

## Problem Context

Script Detail Item Inspector menunjukkan bahwa mengubah nilai parameter membutuhkan logic yang kompleks dengan beberapa tantangan:

1. **Transaction Management**: Parameter changes perlu dilakukan dalam Transaction
2. **Type Validation**: Value harus sesuai dengan StorageType (Double, Integer, String, ElementId)
3. **Instance vs Type Parameters**: Logic berbeda untuk parameter instance dan type
4. **Error Handling**: Rollback jika gagal, logging untuk debugging
5. **ReadOnly Check**: Validasi apakah parameter bisa diubah

Saat ini setiap script mengimplementasikan ini sendiri tanpa standardisasi, menyebabkan code duplication dan inconsistent error handling.

## Solution Summary

Utility terpusat untuk set parameter value dengan automatic transaction management, type validation, dan comprehensive error handling. Mengikuti pola proven dari Detail Item Inspector dengan improvements untuk reusability.

## Working Code

### Core Parameter Setting Function

```python
def set_parameter_value_safe(element, param_name, new_value, logger=None):
    """
    Set parameter value with comprehensive validation and transaction management.
    Based on proven patterns from Detail Item Inspector.

    Args:
        element: Revit element (FamilyInstance, FamilySymbol, etc.)
        param_name (str): Parameter name to set
        new_value: New value to set (type must match parameter storage type)
        logger: Optional logger for error reporting

    Returns:
        bool: True if successful, False if failed
    """
    # Input validation
    if not element or not param_name or param_name.strip() == "":
        if logger:
            logger.error("Invalid input: element or param_name is empty")
        return False

    try:
        # Find the parameter (instance or type)
        param = find_parameter_for_setting(element, param_name)

        if not param:
            if logger:
                logger.warning("Parameter '{}' not found on element or its type".format(param_name))
            return False

        # Validate parameter can be modified
        if param.IsReadOnly:
            if logger:
                logger.warning("Parameter '{}' is read-only and cannot be modified".format(param_name))
            return False

        # Validate and convert value based on storage type
        converted_value = validate_and_convert_value(param, new_value)
        if converted_value is None:
            if logger:
                logger.error("Value '{}' is invalid for parameter '{}' (StorageType: {})".format(
                    new_value, param_name, param.StorageType))
            return False

        # Set the value within a transaction
        return set_parameter_with_transaction(element, param, converted_value, logger)

    except Exception as e:
        if logger:
            logger.error("Unexpected error setting parameter '{}': {}".format(param_name, str(e)))
        return False

def find_parameter_for_setting(element, param_name):
    """
    Find parameter for setting (checks instance first, then type).

    Args:
        element: Revit element
        param_name (str): Parameter name

    Returns:
        Parameter object or None
    """
    try:
        # Try instance parameter first
        param = element.LookupParameter(param_name)
        if param:
            return param

        # Try type parameter for FamilyInstance
        if isinstance(element, FamilyInstance):
            elem_type = element.Symbol
            if elem_type:
                param = elem_type.LookupParameter(param_name)
                if param:
                    return param

        # Try type parameter for FamilySymbol
        elif isinstance(element, FamilySymbol):
            param = element.LookupParameter(param_name)
            if param:
                return param

        return None

    except Exception:
        return None

def validate_and_convert_value(param, new_value):
    """
    Validate and convert value based on parameter storage type.

    Args:
        param: Revit Parameter object
        new_value: Value to validate/convert

    Returns:
        Converted value or None if invalid
    """
    if not param or new_value is None:
        return None

    storage_type = param.StorageType

    try:
        if storage_type == StorageType.Double:
            # Handle numeric strings and convert to float
            if isinstance(new_value, str):
                # Remove units if present (e.g., "100 mm" -> "100")
                clean_value = ''.join(c for c in new_value if c.isdigit() or c in '.-')
                return float(clean_value)
            return float(new_value)

        elif storage_type == StorageType.Integer:
            # Handle numeric strings and convert to int
            if isinstance(new_value, str):
                clean_value = ''.join(c for c in new_value if c.isdigit() or c == '-')
                return int(clean_value)
            return int(new_value)

        elif storage_type == StorageType.String:
            # Convert to string
            return str(new_value)

        elif storage_type == StorageType.ElementId:
            # ElementId setting not supported in this utility
            # (would require complex element resolution)
            return None

        else:
            # Unsupported storage type
            return None

    except (ValueError, TypeError):
        return None

def set_parameter_with_transaction(element, param, value, logger=None):
    """
    Set parameter value within a transaction with proper error handling.

    Args:
        element: Revit element
        param: Parameter to set
        value: Converted value to set
        logger: Optional logger

    Returns:
        bool: True if successful
    """
    transaction_name = "Set Parameter '{}'".format(param.Definition.Name)

    t = Transaction(element.Document, transaction_name)
    try:
        t.Start()

        # Set the parameter value
        if param.StorageType == StorageType.Double:
            param.Set(float(value))
        elif param.StorageType == StorageType.Integer:
            param.Set(int(value))
        elif param.StorageType == StorageType.String:
            param.Set(str(value))
        else:
            # This shouldn't happen due to validation, but safety check
            if logger:
                logger.error("Unsupported storage type in transaction: {}".format(param.StorageType))
            t.RollBack()
            return False

        t.Commit()

        if logger:
            logger.info("Parameter '{}' set to '{}' successfully".format(param.Definition.Name, value))

        return True

    except Exception as e:
        if t.HasStarted() and t.GetStatus() == TransactionStatus.Started:
            t.RollBack()

        if logger:
            logger.error("Failed to set parameter '{}': {}".format(param.Definition.Name, str(e)))

        return False
```

### Advanced Parameter Setting dengan Batch Operations

```python
def set_multiple_parameters_safe(element, param_value_pairs, logger=None):
    """
    Set multiple parameters in a single transaction.
    All changes are rolled back if any parameter fails.

    Args:
        element: Revit element
        param_value_pairs: List of (param_name, value) tuples
        logger: Optional logger

    Returns:
        dict: Results with 'success': bool and 'failed_params': list
    """
    if not param_value_pairs:
        return {'success': True, 'failed_params': []}

    # Pre-validate all parameters
    validated_params = []
    failed_params = []

    for param_name, value in param_value_pairs:
        param = find_parameter_for_setting(element, param_name)
        if not param:
            failed_params.append(param_name)
            continue

        if param.IsReadOnly:
            failed_params.append(param_name)
            continue

        converted_value = validate_and_convert_value(param, value)
        if converted_value is None:
            failed_params.append(param_name)
            continue

        validated_params.append((param, converted_value))

    if failed_params:
        if logger:
            logger.warning("Pre-validation failed for parameters: {}".format(failed_params))
        return {'success': False, 'failed_params': failed_params}

    # Execute all changes in single transaction
    transaction_name = "Set Multiple Parameters ({})".format(len(validated_params))

    t = Transaction(element.Document, transaction_name)
    try:
        t.Start()

        for param, value in validated_params:
            if param.StorageType == StorageType.Double:
                param.Set(float(value))
            elif param.StorageType == StorageType.Integer:
                param.Set(int(value))
            elif param.StorageType == StorageType.String:
                param.Set(str(value))

        t.Commit()

        if logger:
            logger.info("Successfully set {} parameters".format(len(validated_params)))

        return {'success': True, 'failed_params': []}

    except Exception as e:
        if t.HasStarted() and t.GetStatus() == TransactionStatus.Started:
            t.RollBack()

        if logger:
            logger.error("Failed to set multiple parameters: {}".format(str(e)))

        return {'success': False, 'failed_params': [p.Definition.Name for p, v in validated_params]}

def can_modify_parameter(element, param_name):
    """
    Check if a parameter can be modified without actually modifying it.

    Args:
        element: Revit element
        param_name (str): Parameter name

    Returns:
        dict: {'can_modify': bool, 'reason': str, 'param_type': str}
    """
    try:
        param = find_parameter_for_setting(element, param_name)

        if not param:
            return {
                'can_modify': False,
                'reason': 'Parameter not found',
                'param_type': 'unknown'
            }

        if param.IsReadOnly:
            return {
                'can_modify': False,
                'reason': 'Parameter is read-only',
                'param_type': 'readonly'
            }

        # Determine parameter type
        param_type = 'instance'
        if isinstance(element, FamilyInstance):
            elem_type = element.Symbol
            if elem_type:
                type_param = elem_type.LookupParameter(param_name)
                if type_param and type_param.Id == param.Id:
                    param_type = 'type'

        return {
            'can_modify': True,
            'reason': 'Parameter can be modified',
            'param_type': param_type
        }

    except Exception as e:
        return {
            'can_modify': False,
            'reason': 'Error checking parameter: {}'.format(str(e)),
            'param_type': 'error'
        }
```

## Key Techniques

### 1. **Comprehensive Parameter Finding**
```python
# Instance first, then type
param = element.LookupParameter(param_name)  # Instance
if isinstance(element, FamilyInstance):
    param = element.Symbol.LookupParameter(param_name)  # Type
```

### 2. **Storage Type Validation**
```python
# Convert based on storage type
if storage_type == StorageType.Double:
    param.Set(float(value))
elif storage_type == StorageType.Integer:
    param.Set(int(value))
```

### 3. **Transaction Safety**
```python
t = Transaction(element.Document, transaction_name)
try:
    t.Start()
    # Set parameter
    t.Commit()
except Exception as e:
    t.RollBack()  # Always rollback on error
```

### 4. **Value Sanitization**
```python
# Clean numeric strings
clean_value = ''.join(c for c in new_value if c.isdigit() or c in '.-')
return float(clean_value)
```

## Performance Notes

- **Execution Time**: Medium (parameter lookup + transaction)
- **Memory Usage**: Low (minimal object creation)
- **Transaction Impact**: Single transaction per operation
- **Thread Safety**: Safe for Revit API usage

## Usage Examples

### Basic Parameter Setting

```python
from logic_library.active.utilities.parameters.set_parameter_value import set_parameter_value_safe

# Set a single parameter
element = get_selected_element()
success = set_parameter_value_safe(element, "Mark", "A-001", logger=script.get_logger())

if success:
    print("Parameter updated successfully")
else:
    print("Failed to update parameter")
```

### Batch Parameter Setting

```python
from logic_library.active.utilities.parameters.set_parameter_value import set_multiple_parameters_safe

# Set multiple parameters at once
param_updates = [
    ("Mark", "B-002"),
    ("Comments", "Updated via script"),
    ("Length", "5000")  # Will be converted to float
]

result = set_multiple_parameters_safe(element, param_updates, logger=script.get_logger())

if result['success']:
    print("All parameters updated successfully")
else:
    print("Failed to update: {}".format(result['failed_params']))
```

### Pre-Modification Validation

```python
from logic_library.active.utilities.parameters.set_parameter_value import can_modify_parameter

# Check if parameter can be modified
check_result = can_modify_parameter(element, "Mark")

if check_result['can_modify']:
    print("Parameter can be modified (type: {})".format(check_result['param_type']))
else:
    print("Cannot modify: {}".format(check_result['reason']))
```

### Integration with UI

```python
def update_parameter_with_ui_validation(element, param_name):
    """Update parameter with user input validation"""

    # Check if modifiable
    check = can_modify_parameter(element, param_name)
    if not check['can_modify']:
        forms.alert("Cannot modify parameter: {}".format(check['reason']), title="Parameter Error")
        return False

    # Get current value for default
    current_value = get_parameter_value_safe(element, param_name) or ""

    # Show input dialog
    new_value = forms.ask_for_string(
        default=str(current_value),
        prompt="Enter new value for '{}':".format(param_name),
        title="Update Parameter"
    )

    if new_value is not None:
        return set_parameter_value_safe(element, param_name, new_value.strip())

    return False
```

## Comparison with Manual Implementation

| Aspect | Manual Implementation | Utility-Based |
|--------|----------------------|----------------|
| **Code Lines** | 50-100 lines | 5-10 lines |
| **Error Handling** | Variable | Comprehensive |
| **Transaction Safety** | Manual | Automatic |
| **Type Validation** | Manual | Automatic |
| **Testing** | Manual | Built-in validation |
| **Maintenance** | Per-script | Centralized |

## Integration with Logic Library

### File Structure
```
logic-library/active/utilities/parameters/
├── LOG-UTIL-PARAM-008-v1-set-parameter-value.md
└── set_parameter_value.py
```

### Import Pattern
```python
# For parameter setting operations
from logic_library.active.utilities.parameters.set_parameter_value import (
    set_parameter_value_safe,
    set_multiple_parameters_safe,
    can_modify_parameter
)
```

## Testing Recommendations

```python
def test_parameter_setting():
    """Comprehensive test for parameter setting functionality"""

    test_results = {
        'single_param_tests': [],
        'batch_param_tests': [],
        'validation_tests': []
    }

    # Test elements (use test model elements)
    test_elements = get_test_elements()

    for element in test_elements:
        # Test single parameter setting
        success = set_parameter_value_safe(element, "Mark", "TEST-001")
        test_results['single_param_tests'].append({
            'element_id': element.Id.IntegerValue,
            'success': success
        })

        # Test batch setting
        batch_data = [("Comments", "Batch test"), ("Length", "1000")]
        batch_result = set_multiple_parameters_safe(element, batch_data)
        test_results['batch_param_tests'].append({
            'element_id': element.Id.IntegerValue,
            'success': batch_result['success'],
            'failed_count': len(batch_result['failed_params'])
        })

        # Test validation
        validation = can_modify_parameter(element, "Mark")
        test_results['validation_tests'].append({
            'element_id': element.Id.IntegerValue,
            'can_modify': validation['can_modify'],
            'param_type': validation['param_type']
        })

    return test_results
```

## Best Practices

### When to Use

1. **Single Parameter Updates**: Use `set_parameter_value_safe`
2. **Bulk Updates**: Use `set_multiple_parameters_safe` for atomic operations
3. **UI Integration**: Combine with `can_modify_parameter` for user feedback
4. **Error Recovery**: Always check return values and handle failures

### Error Handling

```python
def safe_parameter_update(element, param_name, value):
    """Wrapper with comprehensive error handling"""

    # Pre-check
    validation = can_modify_parameter(element, param_name)
    if not validation['can_modify']:
        raise ValueError("Parameter cannot be modified: {}".format(validation['reason']))

    # Attempt update
    if not set_parameter_value_safe(element, param_name, value):
        raise RuntimeError("Failed to update parameter '{}'".format(param_name))

    return True
```

## Related Logic Entries

- [LOG-UTIL-PARAM-005-v1-robust-parameter-extraction](LOG-UTIL-PARAM-005-v1-robust-parameter-extraction.md) - Parameter reading
- [LOG-UTIL-PARAM-006-v1-parameter-type-classification](LOG-UTIL-PARAM-006-v1-parameter-type-classification.md) - Parameter classification
- [LOG-UTIL-UI-005-v1-simple-option-selection](LOG-UTIL-UI-005-v1-simple-option-selection.md) - UI integration

## Optimization History

*Initial version (v1) with comprehensive parameter setting patterns derived from Detail Item Inspector's proven transaction and validation logic.*

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-24