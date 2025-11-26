---
id: "LOG-UTIL-REBAR-004"
version: "v1"
status: "active"
category: "structural-elements/rebar"
element_type: "AreaReinforcement"
operation: "parameter-reference"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["rebar", "area-reinforcement", "parameters", "reference", "documentation", "instance-parameters", "type-parameters"]
created: "2025-10-29"
updated: "2025-10-30"
confidence: "high"
performance: "reference"
source_file: "PrasKaaPyKit.tab/Rebar.panel/AreaReinforcement.pulldown/byFilledRegion.pushbutton/script.py"
source_location: "Rebar.panel/AreaReinforcement.pulldown/byFilledRegion.pushbutton"
---

# LOG-UTIL-REBAR-004-v1: Area Reinforcement Parameter Reference

## Problem Context

Area Reinforcement elements in Revit have extensive parameter sets that are not well documented. Scripts often need to inspect or modify these parameters, but without a comprehensive reference, developers waste time on parameter discovery and make errors in parameter names or types.

This reference document provides the complete parameter list for Area Reinforcement elements, including storage types, read/write status, and typical values.

## Parameter Reference Data

### Instance Parameters (Element Level)

| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Host Mark | String | RO | Empty | Host element mark |
| Partition | String | RW | Empty | Partition assignment |
| Image | ElementId | RW | Invalid | Associated image |
| Category | ElementId | RO | -2009003 | Structural Rebar category |
| IFC Predefined Type | String | RW | Empty | IFC classification |
| Export to IFC As | String | RW | Empty | IFC export settings |
| Export to IFC | Integer | RW | 0 | IFC export flag |
| IfcGUID | String | RW | Generated | IFC GUID |
| Reinforcement Volume | Double | RO | 0.0 | Calculated volume |
| **Layout Rule** | **Integer** | **RW** | **3** | **Maximum Spacing = 3** |
| Host Category | Integer | RO | 5 | Host element category |

#### Spacing Parameters (All in feet - convert from mm)
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Bottom/Interior Minor Spacing | Double | RW | 0.984 | Minor bar spacing (bottom) |
| Bottom/Interior Major Spacing | Double | RW | 0.984 | Major bar spacing (bottom) |
| Top/Exterior Minor Spacing | Double | RW | 0.984 | Minor bar spacing (top) |
| Top/Exterior Major Spacing | Double | RW | 0.984 | Major bar spacing (top) |
| **Top Major Spacing** | **Double** | **RW** | **0.984** | **Top major bar spacing** |

#### Number of Lines (Calculated/Read-only)
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Bottom/Interior Minor Number Of Lines | Integer | RO | 5 | Calculated minor bars (bottom) |
| Bottom/Interior Major Number Of Lines | Integer | RO | 5 | Calculated major bars (bottom) |
| Top/Exterior Minor Number Of Lines | Integer | RO | 5 | Calculated minor bars (top) |
| Top/Exterior Major Number Of Lines | Integer | RO | 5 | Calculated major bars (top) |

#### Bar Type Parameters
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Bottom/Interior Minor Bar Type | ElementId | RW | 180243 | Minor bar type (bottom) |
| Bottom/Interior Major Bar Type | ElementId | RW | 180243 | Major bar type (bottom) |
| Top/Exterior Minor Bar Type | ElementId | RW | 180243 | Minor bar type (top) |
| Top/Exterior Major Bar Type | ElementId | RW | 180243 | Major bar type (top) |

#### Visibility Parameters (0=Disabled, 1=Enabled)
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Bottom/Interior Minor Direction | Integer | RW | 1 | Minor bar visibility (bottom) - 0=disabled, 1=enabled |
| Bottom/Interior Major Direction | Integer | RW | 1 | Major bar visibility (bottom) - 0=disabled, 1=enabled |
| Top/Exterior Minor Direction | Integer | RW | 1 | Minor bar visibility (top) - 0=disabled, 1=enabled |
| Top/Exterior Major Direction | Integer | RW | 1 | Major bar visibility (top) - 0=disabled, 1=enabled |

#### Hook Parameters
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Bottom Minor Hook Type | ElementId | RW | Invalid | Bottom minor hook type |
| Bottom Major Hook Type | ElementId | RW | Invalid | Bottom major hook type |
| Top Minor Hook Type | ElementId | RW | Invalid | Top minor hook type |
| Top Major Hook Type | ElementId | RW | Invalid | Top major hook type |

#### Hook Orientation (Read-only)
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Bottom Minor Hook Orientation | Integer | RO | 0 | Bottom minor hook orientation |
| Bottom Major Hook Orientation | Integer | RO | 0 | Bottom major hook orientation |
| Top Minor Hook Orientation | Integer | RO | 2 | Top minor hook orientation |
| Top Major Hook Orientation | Integer | RO | 2 | Top major hook orientation |

#### Cover Offset Parameters
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Additional Bottom Cover Offset | Double | RW | 0.0 | Additional bottom cover |
| Additional Top Cover Offset | Double | RW | 0.0 | Additional top cover |

#### Layer Matching Parameters
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Top and Bottom Minor Layers Match | Integer | RW | 1 | Minor layer matching |
| Top and Bottom Major Layers Match | Integer | RW | 1 | Major layer matching |
| Bottom Major and Minor Layers Match | Integer | RW | 1 | Bottom layer matching |
| Top Major and Minor Layers Match | Integer | RW | 1 | Top layer matching |

#### Display Parameters (Read-only)
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Minor, Both Faces (Brief) | String | RO | H6 (T) H6 (B) | Brief display |
| Minor, Both Faces | String | RO | H6 @ 300 mm (T) H6 @ 300 mm (B) | Full display |
| Major, Both Faces (Brief) | String | RO | H6 (T) H6 (B) | Brief display |
| Major, Both Faces | String | RO | H6 @ 300 mm (T) H6 @ 300 mm (B) | Full display |
| Layer Summary (Brief) | String | RO | H6 E.W. E.F. | Brief summary |
| Layer Summary | String | RO | H6 @ 300 mm E.W. E.F. | Full summary |

#### Standard Parameters
| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Comments | String | RW | Empty | User comments |
| Mark | String | RW | Empty | Element mark |
| Family and Type | ElementId | RW | 433364 | Family and type reference |
| Family | ElementId | RW | 433364 | Family reference |
| Type | ElementId | RW | 433364 | Type reference |
| Family Name | String | RO | Empty | Family name |
| Type Name | String | RO | test | Type name |
| Type Id | ElementId | RO | 433364 | Type ID |

### Type Parameters (Family Level)

| Parameter Name | Storage Type | Read/Write | Default Value | Description |
|----------------|--------------|------------|---------------|-------------|
| Type Image | ElementId | RW | Invalid | Type image |
| Keynote | String | RW | Empty | Keynote reference |
| Category | ElementId | RO | -2009003 | Category |
| Type IFC Predefined Type | String | RW | Empty | IFC type |
| Export Type to IFC As | String | RW | Empty | IFC export |
| Export Type to IFC | Integer | RW | 0 | IFC export flag |
| Type IfcGUID | String | RW | Generated | Type IFC GUID |
| Design Option | ElementId | RO | Invalid | Design option |
| Model | String | RW | Empty | Model reference |
| Manufacturer | String | RW | Empty | Manufacturer |
| Type Comments | String | RW | Empty | Type comments |
| URL | String | RW | Empty | Reference URL |
| Description | String | RW | Empty | Type description |
| Assembly Description | String | RO | Empty | Assembly description |
| Assembly Code | String | RW | Empty | Assembly code |
| Family Name | String | RO | Structural Area Reinforcement | Family name |
| Type Name | String | RO | test | Type name |
| Type Mark | String | RW | Empty | Type mark |
| Cost | Double | RW | 0.0 | Cost value |

## Key Parameter Groups

### Critical Override Parameters
```python
# Most commonly overridden parameters
CRITICAL_PARAMETERS = {
    'Layout Rule': 3,  # Maximum Spacing
    'Top Major Spacing': 150.0,  # mm (converted to feet)
    'Top/Exterior Major Direction': 1,  # Major bar visibility (enabled)
    'Top Major Bar Type': None,  # ElementId
}
```

### Spacing Parameters (Convert mm to feet)
```python
# All spacing parameters need mm to feet conversion
SPACING_PARAMETERS = [
    'Bottom Minor Spacing',
    'Bottom Major Spacing', 
    'Top Minor Spacing',
    'Top Major Spacing',
    'Bottom/Interior Minor Spacing',
    'Bottom/Interior Major Spacing',
    'Top/Exterior Minor Spacing',
    'Top/Exterior Major Spacing'
]
```

### Visibility Parameters
```python
# Visibility values: 0 = Disabled, 1 = Enabled
VISIBILITY_VALUES = {
    'Disabled': 0,
    'Enabled': 1
}
```

### Layout Rule Values
```python
# Layout Rule integer values
LAYOUT_RULES = {
    'Minimum Clear Spacing': 0,
    'Fixed Number': 1,
    'Number with Spacing': 2,
    'Maximum Spacing': 3  # Most common
}
```

## Usage Examples

### Quick Parameter Override
```python
# Override critical parameters only
critical_overrides = {
    'Layout Rule': 3,  # Maximum Spacing
    'Top Major Spacing': convert_internal_units(150.0, get_internal=True, units='mm')
}

result = override_area_reinforcement_parameters(area_reinf, critical_overrides)
```

### Complete Parameter Setup
```python
# Full parameter configuration
full_config = {
    'Layout Rule': 3,
    'Top Major Spacing': convert_internal_units(150.0, get_internal=True, units='mm'),
    'Top/Exterior Major Direction': 1,  # Major bar visibility (enabled)
    'Top Major Bar Type': bar_type_id,
    'Top Minor Spacing': convert_internal_units(200.0, get_internal=True, units='mm'),
    'Comments': 'Auto-generated from Filled Region'
}

result = override_area_reinforcement_parameters(area_reinf, full_config)
```

### Parameter Validation
```python
def validate_area_reinforcement_parameters(area_reinf):
    """Validate current parameter values"""
    issues = []
    
    # Check Layout Rule
    layout_rule = get_parameter_value_safe(area_reinf, 'Layout Rule')
    if layout_rule != 3:
        issues.append("Layout Rule should be 3 (Maximum Spacing)")
    
    # Check spacing values (should be reasonable)
    top_spacing = get_parameter_value_safe(area_reinf, 'Top Major Spacing')
    if top_spacing and top_spacing < 0.1:  # Less than ~30mm
        issues.append("Top Major Spacing too small")
        
    return issues
```

## Performance Notes

- **Parameter Count**: ~60 instance parameters + ~20 type parameters
- **Access Pattern**: Instance parameters preferred over type parameters
- **Storage Types**: Mixed (Integer, Double, String, ElementId)
- **Read/Write Ratio**: ~70% read-only, 30% writable

## Integration with Logic Library

### File Structure
```
logic-library/active/structural-elements/rebar/
├── LOG-UTIL-REBAR-004-v1-area-reinforcement-parameter-reference.md
└── parameter_reference.py
```

### Import Pattern
```python
# For parameter reference and validation
from logic_library.active.structural_elements.rebar.parameter_reference import (
    CRITICAL_PARAMETERS,
    SPACING_PARAMETERS,
    LAYOUT_RULES,
    validate_area_reinforcement_parameters
)
```

## Testing Recommendations

```python
def test_parameter_reference():
    """Test parameter reference accuracy"""
    
    # Create test Area Reinforcement
    test_area_reinf = create_test_area_reinforcement()
    
    # Test parameter existence
    for param_name in CRITICAL_PARAMETERS.keys():
        value = get_parameter_value_safe(test_area_reinf, param_name)
        assert value is not None, f"Parameter {param_name} not found"
    
    # Test parameter types
    layout_rule = get_parameter_value_safe(test_area_reinf, 'Layout Rule')
    assert isinstance(layout_rule, int), "Layout Rule should be integer"
    
    spacing = get_parameter_value_safe(test_area_reinf, 'Top Major Spacing')
    assert isinstance(spacing, float), "Spacing should be float"
```

## Best Practices

### Parameter Override Order
1. **Layout Rule** - Set first (affects other parameters)
2. **Spacing parameters** - Convert mm to feet properly
3. **Visibility parameters** - Use 0=disabled, 1=enabled convention
4. **Bar type parameters** - Validate ElementId exists
5. **Display parameters** - Read-only, use for verification

### Unit Conversion
```python
# Always convert spacing from mm to feet
spacing_mm = 150.0
spacing_feet = spacing_mm / 304.8  # Convert mm to feet
set_parameter_value_safe(area_reinf, 'Top Major Spacing', spacing_feet)
```

### Error Handling
```python
# Check parameter exists before setting
if can_modify_parameter(area_reinf, 'Layout Rule')['can_modify']:
    set_parameter_value_safe(area_reinf, 'Layout Rule', 3)
else:
    logger.warning("Cannot modify Layout Rule parameter")
```

## Related Logic Entries

- [LOG-UTIL-REBAR-001-v1-area-reinforcement-creation](LOG-UTIL-REBAR-001-v1-area-reinforcement-creation.md) - Creation utilities
- [LOG-UTIL-REBAR-002-v1-area-reinforcement-parameter-override](LOG-UTIL-REBAR-002-v1-area-reinforcement-parameter-override.md) - Override framework
- [LOG-UTIL-PARAM-008-v1-set-parameter-value](LOG-UTIL-PARAM-008-v1-set-parameter-value.md) - Parameter setting
- [LOG-UTIL-CONVERT-001-v1-unit-conversion-framework](LOG-UTIL-CONVERT-001-v1-unit-conversion-framework.md) - Unit conversion

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-30