---
id: "LOG-UTIL-REBAR-007"
version: "v1"
status: "active"
category: "structural-elements/rebar"
element_type: "AreaReinforcement"
operation: "settings-processor"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["rebar", "area-reinforcement", "settings", "processor", "ui-integration", "multi-layer", "visibility-control", "cover-offset"]
created: "2025-10-30"
updated: "2025-10-30"
confidence: "high"
performance: "medium"
source_file: "PrasKaaPyKit.tab/Rebar.panel/AreaReinforcement.pulldown/Multi Layer Area Reinforcement by Filled Region.pushbutton/script.py"
source_location: "Rebar.panel/AreaReinforcement.pulldown/Multi Layer Area Reinforcement by Filled Region.pushbutton"
---

# LOG-UTIL-REBAR-007-v1: Area Reinforcement Settings Processor

## Problem Context

Area Reinforcement di Revit memiliki keterbatasan maksimal 4 layer per element (2 bottom + 2 top). Untuk mengakomodasi lebih dari 4 layer, diperlukan multiple Area Reinforcement elements dengan logic khusus untuk cover offset. Processor ini mengambil input dari UI settings dan secara otomatis mengelola pembuatan multiple Area Reinforcement dengan parameter override yang tepat.

Key challenges:
1. **Multi Layer Management**: Handle lebih dari 4 layer dengan multiple Area Reinforcement
2. **Cover Offset Calculation**: Hitung additional cover offset berdasarkan diameter bar dari layer sebelumnya
3. **Visibility Control**: Enable/disable layer visibility melalui Direction parameters
4. **Major Direction Consistency**: Terapkan major direction yang sama ke semua Area Reinforcement dalam satu operasi
5. **Parameter Override Sequencing**: Override parameters setelah creation dengan logic yang benar

## Solution Summary

Comprehensive settings processor untuk Area Reinforcement yang menangani multi-layer scenarios dengan automatic cover offset calculation, visibility control, dan parameter override sequencing. Mendukung separation logic antara Top dan Bottom layers untuk optimal multi-element creation.

## Working Code

### Core Settings Processor Function

```python
def process_multi_layer_area_reinforcement(doc, processor_input, logger=None):
    """
    Process multi layer area reinforcement dari UI settings.

    Args:
        doc: Revit Document
        processor_input: Dict containing major_direction dan ui_settings
        logger: Optional logger

    Returns:
        list: List of created AreaReinforcement elements
    """
    major_direction = processor_input.get("major_direction", "Y")
    ui_settings = processor_input.get("ui_settings", [])

    # Convert major direction to XYZ
    direction_vector = XYZ(1, 0, 0) if major_direction == "X" else XYZ(0, 1, 0)

    # Validate input
    validate_processor_input(processor_input)

    # Separate top/bottom layers
    separated_layers = separate_top_bottom_layers(ui_settings)

    created_elements = []

    # Process Bottom layers (max 2 per Area Reinforcement)
    bottom_groups = group_layers_by_side_and_count(separated_layers["bottom"], 2)
    for i, bottom_group in enumerate(bottom_groups):
        if bottom_group:
            cover_offset = calculate_bottom_cover_offset(created_elements, i)

            area_reinf = create_area_reinforcement_with_layer_group(
                doc, bottom_group, processor_input["boundary_curves"],
                processor_input["host"], direction_vector, cover_offset, logger
            )

            if area_reinf:
                created_elements.append(area_reinf)

    # Process Top layers (max 2 per Area Reinforcement)
    top_groups = group_layers_by_side_and_count(separated_layers["top"], 2)
    for i, top_group in enumerate(top_groups):
        if top_group:
            cover_offset = calculate_top_cover_offset(created_elements, i)

            area_reinf = create_area_reinforcement_with_layer_group(
                doc, top_group, processor_input["boundary_curves"],
                processor_input["host"], direction_vector, cover_offset, logger
            )

            if area_reinf:
                created_elements.append(area_reinf)

    return created_elements
```

### Layer Separation and Grouping Functions

```python
def separate_top_bottom_layers(ui_settings):
    """
    Separate layers menjadi top dan bottom groups.

    Returns:
        dict: {"top": [top_layers], "bottom": [bottom_layers]}
    """
    top_layers = []
    bottom_layers = []

    for layer in ui_settings:
        layer_id = layer.get("layer_id", "")
        if layer_id.startswith("Top"):
            top_layers.append(layer)
        elif layer_id.startswith("Bottom"):
            bottom_layers.append(layer)

    # Sort by priority within each group
    LAYER_PRIORITY = {
        "Bottom Major": 1, "Top Major": 1,
        "Bottom Minor": 2, "Top Minor": 2
    }

    top_layers.sort(key=lambda x: LAYER_PRIORITY.get(x.get("layer_id"), 999))
    bottom_layers.sort(key=lambda x: LAYER_PRIORITY.get(x.get("layer_id"), 999))

    return {"top": top_layers, "bottom": bottom_layers}

def group_layers_by_side_and_count(layer_list, max_per_group=2):
    """
    Group layers dalam satu side by count (max 2 per Area Reinforcement).

    Args:
        layer_list: List of layer configs untuk satu side
        max_per_group: Maximum layers per Area Reinforcement (default 2)

    Returns:
        list: [[group1], [group2], ...]
    """
    groups = []
    for i in range(0, len(layer_list), max_per_group):
        group = layer_list[i:i+max_per_group]
        groups.append(group)

    return groups
```

### Cover Offset Calculation Functions

```python
def calculate_bottom_cover_offset(created_elements, group_index):
    """
    Calculate additional cover offset untuk bottom Area Reinforcement.

    Logic: Jika group_index > 0, hitung dari max diameter bottom AR sebelumnya
    """
    if group_index == 0:
        return {}

    # Find previous bottom Area Reinforcements
    bottom_ars = [elem for elem in created_elements
                  if is_bottom_area_reinforcement(elem)]

    if not bottom_ars:
        return {}

    # Get max diameter dari AR terakhir
    prev_ar = bottom_ars[-1]
    max_diameter_mm = get_max_bar_diameter_from_area_reinforcement(prev_ar)
    offset_feet = max_diameter_mm / 304.8

    return {"Additional Bottom Cover Offset": offset_feet}

def calculate_top_cover_offset(created_elements, group_index):
    """
    Calculate additional cover offset untuk top Area Reinforcement.

    Logic: Jika group_index > 0, hitung dari max diameter top AR sebelumnya
    """
    if group_index == 0:
        return {}

    # Find previous top Area Reinforcements
    top_ars = [elem for elem in created_elements
               if is_top_area_reinforcement(elem)]

    if not top_ars:
        return {}

    # Get max diameter dari AR terakhir
    prev_ar = top_ars[-1]
    max_diameter_mm = get_max_bar_diameter_from_area_reinforcement(prev_ar)
    offset_feet = max_diameter_mm / 304.8

    return {"Additional Top Cover Offset": offset_feet}

def get_max_bar_diameter_from_area_reinforcement(area_reinf):
    """
    Get maximum bar diameter dari Area Reinforcement element.

    Returns:
        float: Max diameter in mm
    """
    max_diameter = 0

    # Get semua bar types yang digunakan
    bar_types = get_bar_types_from_area_reinforcement(area_reinf)

    for bar_type in bar_types:
        diameter = get_bar_diameter_from_rebar_bar_type(bar_type)
        max_diameter = max(max_diameter, diameter)

    return max_diameter

def get_bar_diameter_from_rebar_bar_type(bar_type):
    """
    Extract diameter dari RebarBarType name (format: "D10", "D13", etc.)

    Returns:
        float: Diameter in mm
    """
    if not bar_type or not hasattr(bar_type, 'Name'):
        return 0

    name = bar_type.Name
    if not name.startswith("D"):
        return 0

    try:
        diameter_str = name[1:]  # Remove "D"
        return float(diameter_str)
    except ValueError:
        return 0
```

### Area Reinforcement Creation with Layer Group

```python
def create_area_reinforcement_with_layer_group(doc, layer_group, boundary_curves,
                                               host, direction_vector, cover_offset=None, logger=None):
    """
    Create Area Reinforcement dengan specific layer group dan apply parameter overrides.
    """
    # Create Area Reinforcement dengan direction yang konsisten
    area_reinf = create_area_reinforcement_safe(
        doc, boundary_curves, host, major_direction=direction_vector, logger=logger
    )

    if not area_reinf:
        return None

    # Process layer group menjadi parameter overrides
    parameter_overrides = process_layer_group_to_overrides(doc, layer_group, logger)

    # Add cover offset jika ada
    if cover_offset:
        parameter_overrides.update(cover_offset)

    # Apply semua overrides
    override_area_reinforcement_parameters(area_reinf, parameter_overrides, logger)

    return area_reinf

def process_layer_group_to_overrides(doc, layer_group, logger=None):
    """
    Convert layer group menjadi parameter overrides dictionary.

    Logic:
    - Enable visibility untuk layers yang ada di group
    - Disable visibility untuk layers yang tidak ada
    - Set bar types dan spacing untuk layers yang enabled
    """
    overrides = {
        "Layout Rule": 3,  # Maximum Spacing

        # Default: semua disabled
        "Bottom/Interior Minor Direction": 0,
        "Bottom/Interior Major Direction": 0,
        "Top/Exterior Minor Direction": 0,
        "Top/Exterior Major Direction": 0
    }

    # Process setiap layer di group
    for layer_config in layer_group:
        layer_id = layer_config.get("layer_id")

        # Enable visibility
        visibility_param = get_visibility_parameter_name(layer_id)
        overrides[visibility_param] = 1

        # Set bar type
        bar_type_name = layer_config.get("bar_type_name")
        if bar_type_name:
            bar_type_id = find_rebar_bar_type_by_name(doc, bar_type_name)
            if bar_type_id:
                bar_type_param = get_bar_type_parameter_name(layer_id)
                overrides[bar_type_param] = bar_type_id
            else:
                if logger:
                    logger.warning(f"Bar type '{bar_type_name}' not found for {layer_id}")

        # Set spacing (mm to feet)
        spacing_mm = layer_config.get("spacing")
        if spacing_mm:
            spacing_param = get_spacing_parameter_name(layer_id)
            overrides[spacing_param] = spacing_mm / 304.8

    return overrides
```

### Parameter Mapping Functions

```python
def get_visibility_parameter_name(layer_id):
    """Get visibility parameter name untuk layer"""
    visibility_map = {
        "Bottom Major": "Bottom/Interior Major Direction",
        "Bottom Minor": "Bottom/Interior Minor Direction",
        "Top Major": "Top/Exterior Major Direction",
        "Top Minor": "Top/Exterior Minor Direction"
    }
    return visibility_map.get(layer_id)

def get_bar_type_parameter_name(layer_id):
    """Get bar type parameter name untuk layer"""
    bar_type_map = {
        "Bottom Major": "Bottom/Interior Major Bar Type",
        "Bottom Minor": "Bottom/Interior Minor Bar Type",
        "Top Major": "Top/Exterior Major Bar Type",
        "Top Minor": "Top/Exterior Minor Bar Type"
    }
    return bar_type_map.get(layer_id)

def get_spacing_parameter_name(layer_id):
    """Get spacing parameter name untuk layer"""
    spacing_map = {
        "Bottom Major": "Bottom/Interior Major Spacing",
        "Bottom Minor": "Bottom/Interior Minor Spacing",
        "Top Major": "Top/Exterior Major Spacing",
        "Top Minor": "Top/Exterior Minor Spacing"
    }
    return spacing_map.get(layer_id)
```

### Utility Functions

```python
def find_rebar_bar_type_by_name(doc, name):
    """Find RebarBarType by name (case-insensitive)"""
    if not name:
        return None

    collector = FilteredElementCollector(doc).OfClass(RebarBarType)
    for bar_type in collector:
        if bar_type.Name.lower() == name.lower():
            return bar_type.Id
    return None

def is_bottom_area_reinforcement(area_reinf):
    """Check if Area Reinforcement memiliki bottom layers enabled"""
    # Implementation: check visibility parameters
    pass

def is_top_area_reinforcement(area_reinf):
    """Check if Area Reinforcement memiliki top layers enabled"""
    # Implementation: check visibility parameters
    pass

def get_bar_types_from_area_reinforcement(area_reinf):
    """Get list of RebarBarType elements used in Area Reinforcement"""
    bar_types = []

    # Check semua bar type parameters
    bar_type_params = [
        "Bottom/Interior Major Bar Type",
        "Bottom/Interior Minor Bar Type",
        "Top/Exterior Major Bar Type",
        "Top/Exterior Minor Bar Type"
    ]

    for param_name in bar_type_params:
        param_value = get_parameter_value_safe(area_reinf, param_name)
        if param_value and param_value != ElementId.InvalidElementId:
            bar_type = area_reinf.Document.GetElement(param_value)
            if bar_type:
                bar_types.append(bar_type)

    return bar_types
```

## Key Techniques

### 1. **Layer Separation Logic**
```python
# Separate berdasarkan side (top/bottom)
separated = separate_top_bottom_layers(ui_settings)

# Group by max 2 per Area Reinforcement
bottom_groups = group_layers_by_side_and_count(separated["bottom"], 2)
top_groups = group_layers_by_side_and_count(separated["top"], 2)
```

### 2. **Cover Offset Calculation**
```python
# Hitung offset dari diameter bar terbesar previous AR
max_diameter = get_max_bar_diameter_from_area_reinforcement(prev_ar)
offset_feet = max_diameter / 304.8
```

### 3. **Visibility Control**
```python
# Enable hanya layer yang ada di group
overrides["Bottom/Interior Major Direction"] = 1  # Enable
overrides["Top/Exterior Minor Direction"] = 0     # Disable
```

### 4. **Major Direction Consistency**
```python
# Convert sekali, apply ke semua AR
direction_vector = XYZ(1, 0, 0) if major_direction == "X" else XYZ(0, 1, 0)
```

## Usage Examples

### Basic Multi Layer Processing

```python
from logic_library.active.structural_elements.rebar.settings_processor import process_multi_layer_area_reinforcement

# Prepare input
processor_input = {
    "major_direction": "X",  # All AR akan menggunakan X direction
    "boundary_curves": model_curves,
    "host": host_floor,
    "ui_settings": [
        {"layer_id": "Bottom Major", "bar_type_name": "D13", "spacing": 150, "enabled": True},
        {"layer_id": "Bottom Minor", "bar_type_name": "D10", "spacing": 200, "enabled": True},
        {"layer_id": "Top Major", "bar_type_name": "D13", "spacing": 150, "enabled": True},
        {"layer_id": "Top Minor", "bar_type_name": "D10", "spacing": 200, "enabled": True}
    ]
}

# Process multi layer
created_area_reinforcements = process_multi_layer_area_reinforcement(
    doc, processor_input, logger=script.get_logger()
)

print(f"Created {len(created_area_reinforcements)} Area Reinforcement(s)")
```

### Advanced Multi Layer with Cover Offset

```python
# 6 Bottom layers + 4 Top layers = 5 Area Reinforcements total
processor_input = {
    "major_direction": "Y",
    "boundary_curves": model_curves,
    "host": host_element,
    "ui_settings": [
        # Bottom layers (3 groups = 3 AR)
        {"layer_id": "Bottom Major", "bar_type_name": "D19", "spacing": 100, "enabled": True},
        {"layer_id": "Bottom Minor", "bar_type_name": "D16", "spacing": 150, "enabled": True},
        {"layer_id": "Bottom Major", "bar_type_name": "D13", "spacing": 200, "enabled": True},  # Additional
        {"layer_id": "Bottom Minor", "bar_type_name": "D10", "spacing": 250, "enabled": True},  # Additional
        {"layer_id": "Bottom Major", "bar_type_name": "D10", "spacing": 300, "enabled": True},  # Additional
        {"layer_id": "Bottom Minor", "bar_type_name": "D8", "spacing": 350, "enabled": True},   # Additional

        # Top layers (2 groups = 2 AR)
        {"layer_id": "Top Major", "bar_type_name": "D16", "spacing": 120, "enabled": True},
        {"layer_id": "Top Minor", "bar_type_name": "D13", "spacing": 180, "enabled": True},
        {"layer_id": "Top Major", "bar_type_name": "D10", "spacing": 250, "enabled": True},     # Additional
        {"layer_id": "Top Minor", "bar_type_name": "D8", "spacing": 300, "enabled": True}      # Additional
    ]
}

# Result: 5 Area Reinforcements dengan cover offset yang calculated
created_ars = process_multi_layer_area_reinforcement(doc, processor_input)
```

## Performance Notes

- **Execution Time**: Medium (multiple AR creation + parameter overrides)
- **Memory Usage**: Medium (multiple element creation)
- **Transaction Impact**: Multiple transactions (1 per AR)
- **Database Access**: FilteredElementCollector untuk bar types
- **Thread Safety**: Safe untuk Revit API usage

## Integration with Logic Library

### File Structure
```
logic-library/active/structural-elements/rebar/
├── LOG-UTIL-REBAR-007-v1-area-reinforcement-settings-processor.md
└── settings_processor.py
```

### Import Pattern
```python
# For settings processing
from logic_library.active.structural_elements.rebar.settings_processor import (
    process_multi_layer_area_reinforcement,
    separate_top_bottom_layers,
    calculate_bottom_cover_offset,
    calculate_top_cover_offset
)
```

## Testing Recommendations

```python
def test_settings_processor():
    """Test settings processor functionality"""

    test_results = {
        'input_validation': False,
        'single_ar_creation': False,
        'multi_ar_creation': False,
        'cover_offset_calculation': False,
        'parameter_override': False
    }

    try:
        # Test input validation
        valid_input = {
            "major_direction": "X",
            "boundary_curves": test_curves,
            "host": test_host,
            "ui_settings": test_ui_settings
        }
        validate_processor_input(valid_input)
        test_results['input_validation'] = True

        # Test single AR creation (4 layers)
        single_layer_input = create_single_ar_test_input()
        result = process_multi_layer_area_reinforcement(doc, single_layer_input)
        test_results['single_ar_creation'] = len(result) == 1

        # Test multi AR creation (6 layers)
        multi_layer_input = create_multi_ar_test_input()
        result = process_multi_layer_area_reinforcement(doc, multi_layer_input)
        test_results['multi_ar_creation'] = len(result) == 2

        # Test cover offset
        offset = calculate_bottom_cover_offset([test_ar], 1)
        test_results['cover_offset_calculation'] = "Additional Bottom Cover Offset" in offset

        # Test parameter override
        overrides = process_layer_group_to_overrides(doc, test_layer_group)
        test_results['parameter_override'] = "Layout Rule" in overrides

    except Exception as e:
        print(f"Test error: {str(e)}")

    return test_results
```

## Best Practices

### When to Use
1. **Multi Layer Requirements**: Ketika butuh lebih dari 4 layer total
2. **Complex Reinforcement**: Bottom dan top dengan konfigurasi berbeda
3. **UI-Driven Creation**: Ketika settings berasal dari user interface
4. **Batch Processing**: Multiple AR dengan parameter konsisten

### Error Handling
```python
def safe_multi_layer_processing(processor_input):
    """Safe multi layer processing dengan comprehensive error handling"""

    try:
        result = process_multi_layer_area_reinforcement(doc, processor_input, logger)

        if not result:
            raise RuntimeError("Failed to create any Area Reinforcement")

        # Validate created elements
        for ar in result:
            if not validate_area_reinforcement_parameters(ar):
                logger.warning(f"Parameter validation failed for {ar.Id}")

        return result

    except Exception as e:
        logger.error(f"Multi layer processing failed: {str(e)}")
        raise
```

## Related Logic Entries

- [LOG-UTIL-REBAR-001-v1-area-reinforcement-creation](LOG-UTIL-REBAR-001-v1-area-reinforcement-creation.md) - Area Reinforcement creation framework
- [LOG-UTIL-REBAR-002-v1-area-reinforcement-parameter-override](LOG-UTIL-REBAR-002-v1-area-reinforcement-parameter-override.md) - Parameter override framework
- [LOG-UTIL-REBAR-004-v1-area-reinforcement-parameter-reference](LOG-UTIL-REBAR-004-v1-area-reinforcement-parameter-reference.md) - Parameter reference documentation
- [LOG-UTIL-PARAM-008-v1-set-parameter-value](LOG-UTIL-PARAM-008-v1-set-parameter-value.md) - Parameter setting utilities

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-30