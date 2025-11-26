---
id: "LOG-UTIL-REBAR-002"
version: "v1"
status: "active"
category: "structural-elements/rebar"
element_type: "AreaReinforcement"
operation: "parameter-override"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["rebar", "area-reinforcement", "parameters", "override", "layout-rule", "spacing", "transaction"]
created: "2025-10-29"
updated: "2025-10-29"
confidence: "high"
performance: "medium"
source_file: "PrasKaaPyKit.tab/Rebar.panel/AreaReinforcement.pulldown/byFilledRegion.pushbutton/script.py"
source_location: "Rebar.panel/AreaReinforcement.pulldown/byFilledRegion.pushbutton"
---

# LOG-UTIL-REBAR-002-v1: Area Reinforcement Parameter Override Framework

## Problem Context

After creating Area Reinforcement elements, users often need to override default parameters like Layout Rule and spacing values. The current implementation requires manual parameter inspection and setting, leading to inconsistent parameter names, unit conversion issues, and error-prone manual processes.

Key challenges:
1. **Parameter Discovery**: Identifying correct parameter names and types
2. **Unit Conversion**: Converting user values (mm) to Revit internal units (feet)
3. **Layout Rule Setting**: Setting Layout Rule to Maximum Spacing (integer value 3)
4. **Spacing Override**: Setting Top Major Spacing to specific values
5. **Transaction Safety**: Safe parameter setting with rollback capability

## Solution Summary

Comprehensive parameter override utility specifically for Area Reinforcement elements with automatic parameter discovery, unit conversion, and transaction-safe setting. Handles common parameter overrides like Layout Rule and spacing values.

## Working Code

### Core Parameter Override Function

```python
def override_area_reinforcement_parameters(area_reinforcement, parameter_overrides=None, logger=None):
    """
    Override Area Reinforcement parameters with automatic unit conversion and validation.

    Args:
        area_reinforcement: AreaReinforcement element
        parameter_overrides: Dict of parameter overrides (optional)
        logger: Optional logger for error reporting

    Returns:
        dict: Override results with success status and messages
    """
    if not area_reinforcement:
        if logger:
            logger.error("Invalid Area Reinforcement element")
        return {'success': False, 'message': 'Invalid element', 'overrides': []}

    # Default parameter overrides
    default_overrides = {
        'Layout Rule': 3,  # Maximum Spacing
        'Top Major Spacing': 150.0  # mm, will be converted to feet
    }

    # Merge with provided overrides
    overrides = default_overrides.copy()
    if parameter_overrides:
        overrides.update(parameter_overrides)

    results = {
        'success': True,
        'message': 'Parameter override completed',
        'overrides': []
    }

    try:
        # Inspect available parameters for debugging
        if logger:
            inspect_area_reinforcement_parameters(area_reinforcement, logger)

        # Apply each parameter override
        for param_name, value in overrides.items():
            success = apply_parameter_override(area_reinforcement, param_name, value, logger)
            results['overrides'].append({
                'parameter': param_name,
                'value': value,
                'success': success
            })

            if not success:
                results['success'] = False
                results['message'] = 'Some parameter overrides failed'

    except Exception as e:
        results['success'] = False
        results['message'] = 'Error during parameter override: {}'.format(str(e))
        if logger:
            logger.error(results['message'])

    return results
```

### Parameter Inspection Function

```python
def inspect_area_reinforcement_parameters(area_reinforcement, logger=None):
    """
    Inspect and log available parameters on Area Reinforcement element.

    Args:
        area_reinforcement: AreaReinforcement element
        logger: Optional logger
    """
    if not logger:
        return

    logger.info("=== AREA REINFORCEMENT PARAMETER INSPECTION ===")
    logger.info("Element ID: {}".format(area_reinforcement.Id))

    try:
        # Instance parameters
        logger.info("--- INSTANCE PARAMETERS ---")
        for param in area_reinforcement.Parameters:
            try:
                param_name = param.Definition.Name
                param_type = param.StorageType.ToString()
                is_readonly = param.IsReadOnly

                value = get_parameter_display_value(param)
                logger.info("  {}: {} ({}) [{}]".format(
                    param_name, value, param_type,
                    'RO' if is_readonly else 'RW'
                ))
            except Exception as e:
                logger.warning("  Error reading parameter: {}".format(str(e)))

        # Type parameters
        area_reinforcement_type_id = area_reinforcement.GetTypeId()
        art_element = area_reinforcement.Document.GetElement(area_reinforcement_type_id)

        logger.info("--- TYPE PARAMETERS ---")
        for param in art_element.Parameters:
            try:
                param_name = param.Definition.Name
                param_type = param.StorageType.ToString()
                is_readonly = param.IsReadOnly

                value = get_parameter_display_value(param)
                logger.info("  {}: {} ({}) [{}]".format(
                    param_name, value, param_type,
                    'RO' if is_readonly else 'RW'
                ))
            except Exception as e:
                logger.warning("  Error reading type parameter: {}".format(str(e)))

    except Exception as e:
        logger.error("Error inspecting parameters: {}".format(str(e)))
```

### Individual Parameter Override Function

```python
def apply_parameter_override(area_reinforcement, param_name, value, logger=None):
    """
    Apply single parameter override with proper type conversion.

    Args:
        area_reinforcement: AreaReinforcement element
        param_name: Parameter name to override
        value: New value to set
        logger: Optional logger

    Returns:
        bool: True if successful
    """
    try:
        # Handle special parameter conversions
        converted_value = convert_parameter_value(param_name, value, logger)

        # Try to set on instance first
        success = set_parameter_value_safe(
            area_reinforcement, param_name, converted_value, logger
        )

        if success:
            if logger:
                logger.info("✓ {} set to {} (instance)".format(param_name, converted_value))
            return True

        # If instance setting failed, try on type
        area_reinforcement_type_id = area_reinforcement.GetTypeId()
        art_element = area_reinforcement.Document.GetElement(area_reinforcement_type_id)

        success = set_parameter_value_safe(
            art_element, param_name, converted_value, logger
        )

        if success:
            if logger:
                logger.info("✓ {} set to {} (type)".format(param_name, converted_value))
            return True

        if logger:
            logger.warning("✗ Could not set parameter: {}".format(param_name))
        return False

    except Exception as e:
        if logger:
            logger.error("Error setting parameter '{}': {}".format(param_name, str(e)))
        return False
```

### Parameter Value Conversion Function

```python
def convert_parameter_value(param_name, value, logger=None):
    """
    Convert parameter values based on parameter type and units.

    Args:
        param_name: Name of the parameter
        value: Raw value to convert
        logger: Optional logger

    Returns:
        Converted value ready for Revit API
    """
    # Layout Rule - should be integer
    if param_name == "Layout Rule":
        if isinstance(value, str):
            # Convert string representations to integers
            layout_rules = {
                "Maximum Spacing": 3,
                "Number with Spacing": 2,
                "Fixed Number": 1,
                "Minimum Clear Spacing": 0
            }
            return layout_rules.get(value, int(value))
        return int(value)

    # Spacing parameters - convert mm to feet
    elif "Spacing" in param_name:
        if isinstance(value, (int, float)):
            # Assume mm input, convert to feet
            feet_value = value / 304.8
            if logger:
                logger.debug("Converting {} mm to {} feet for {}".format(value, feet_value, param_name))
            return feet_value
        return value

    # Other parameters - return as-is
    return value
```

### Parameter Display Value Function

```python
def get_parameter_display_value(param):
    """
    Get display-friendly value for parameter inspection.

    Args:
        param: Revit Parameter object

    Returns:
        str: Display value
    """
    try:
        if param.StorageType == StorageType.String:
            return param.AsString() or "Empty"
        elif param.StorageType == StorageType.Integer:
            return str(param.AsInteger())
        elif param.StorageType == StorageType.Double:
            return str(param.AsDouble())
        elif param.StorageType == StorageType.ElementId:
            elem_id = param.AsElementId()
            return str(elem_id) if elem_id != ElementId.InvalidElementId else "Invalid"
        else:
            return "N/A"
    except:
        return "Error"
```

## Key Techniques

### 1. **Parameter Inspection**
```python
# Comprehensive parameter discovery
for param in area_reinforcement.Parameters:
    param_name = param.Definition.Name
    param_type = param.StorageType.ToString()
    is_readonly = param.IsReadOnly
```

### 2. **Smart Value Conversion**
```python
# Convert based on parameter name and type
if "Spacing" in param_name:
    feet_value = value / 304.8  # mm to feet
elif param_name == "Layout Rule":
    return int(value)  # Ensure integer
```

### 3. **Instance vs Type Parameter Handling**
```python
# Try instance first, then type
success = set_parameter_value_safe(element, param_name, value)
if not success:
    type_element = doc.GetElement(element.GetTypeId())
    success = set_parameter_value_safe(type_element, param_name, value)
```

## Usage Examples

### Basic Parameter Override

```python
from logic_library.active.structural_elements.rebar.parameter_override import override_area_reinforcement_parameters

# After creating Area Reinforcement
area_reinf = create_area_reinforcement_safe(doc, curves, host)

# Apply default parameter overrides
result = override_area_reinforcement_parameters(
    area_reinf,
    logger=script.get_logger()
)

if result['success']:
    print("All parameters overridden successfully")
else:
    print("Some overrides failed: {}".format(result['message']))
```

### Custom Parameter Overrides

```python
# Override with custom values
custom_overrides = {
    'Layout Rule': 2,  # Number with Spacing
    'Top Major Spacing': 200.0,  # 200mm
    'Bottom Major Spacing': 150.0  # 150mm
}

result = override_area_reinforcement_parameters(
    area_reinf,
    parameter_overrides=custom_overrides,
    logger=script.get_logger()
)
```

### Integration with Creation Workflow

```python
def create_and_configure_area_reinforcement(boundary_curves, host_element, spacing_mm=150):
    """Complete workflow: create and configure Area Reinforcement"""

    # Create the element
    area_reinf = create_area_reinforcement_safe(
        doc, boundary_curves, host_element, logger=logger
    )

    if not area_reinf:
        raise RuntimeError("Failed to create Area Reinforcement")

    # Apply parameter overrides
    overrides = {'Top Major Spacing': spacing_mm}
    result = override_area_reinforcement_parameters(
        area_reinf, parameter_overrides=overrides, logger=logger
    )

    if not result['success']:
        logger.warning("Parameter override partially failed: {}".format(result['message']))

    return area_reinf
```

## Performance Notes

- **Execution Time**: Medium (parameter inspection + setting)
- **Memory Usage**: Low (minimal object creation)
- **Transaction Impact**: Uses existing parameter setting framework
- **Thread Safety**: Safe for Revit API usage

## Integration with Logic Library

### File Structure
```
logic-library/active/structural-elements/rebar/
├── LOG-UTIL-REBAR-002-v1-area-reinforcement-parameter-override.md
└── parameter_override.py
```

### Import Pattern
```python
# For parameter override operations
from logic_library.active.structural_elements.rebar.parameter_override import (
    override_area_reinforcement_parameters,
    inspect_area_reinforcement_parameters,
    apply_parameter_override,
    convert_parameter_value
)
```

## Testing Recommendations

```python
def test_parameter_override():
    """Test parameter override functionality"""

    test_results = {
        'layout_rule_override': False,
        'spacing_override': False,
        'custom_override': False,
        'error_handling': False
    }

    try:
        # Create test Area Reinforcement
        test_area_reinf = create_test_area_reinforcement()

        # Test Layout Rule override
        result = override_area_reinforcement_parameters(
            test_area_reinf,
            parameter_overrides={'Layout Rule': 3}
        )
        test_results['layout_rule_override'] = result['success']

        # Test spacing override
        result = override_area_reinforcement_parameters(
            test_area_reinf,
            parameter_overrides={'Top Major Spacing': 200.0}
        )
        test_results['spacing_override'] = result['success']

        # Test custom overrides
        custom_overrides = {
            'Layout Rule': 2,
            'Top Major Spacing': 250.0,
            'Bottom Major Spacing': 150.0
        }
        result = override_area_reinforcement_parameters(
            test_area_reinf,
            parameter_overrides=custom_overrides
        )
        test_results['custom_override'] = result['success']

        # Test error handling
        result = override_area_reinforcement_parameters(None)
        test_results['error_handling'] = not result['success']

    except Exception as e:
        print("Test error: {}".format(str(e)))

    return test_results
```

## Best Practices

### When to Use
1. **Post-Creation Configuration**: Always use after Area Reinforcement creation
2. **Standard Overrides**: Use default Layout Rule and spacing values
3. **Custom Configuration**: Provide specific parameter values as needed
4. **Batch Operations**: Apply to multiple Area Reinforcement elements

### Error Handling
```python
def safe_parameter_override(area_reinf, overrides):
    """Safe parameter override with comprehensive error handling"""

    result = override_area_reinforcement_parameters(
        area_reinf, parameter_overrides=overrides, logger=logger
    )

    if not result['success']:
        # Log failed overrides
        failed = [o for o in result['overrides'] if not o['success']]
        logger.warning("Failed overrides: {}".format(failed))

        # Decide whether to continue or raise error
        if len(failed) > 0:
            raise RuntimeError("Critical parameter override failed")

    return result
```

## Related Logic Entries

- [LOG-UTIL-REBAR-001-v1-area-reinforcement-creation](LOG-UTIL-REBAR-001-v1-area-reinforcement-creation.md) - Creation utilities
- [LOG-UTIL-PARAM-008-v1-set-parameter-value](LOG-UTIL-PARAM-008-v1-set-parameter-value.md) - Parameter setting framework
- [LOG-UTIL-CONVERT-001-v1-unit-conversion-framework](LOG-UTIL-CONVERT-001-v1-unit-conversion-framework.md) - Unit conversion utilities

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-29