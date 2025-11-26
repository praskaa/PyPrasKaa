---
title: "Legend Layout Engine"
version: "1.0"
category: "utilities/layout"
tags: ["layout", "legend", "positioning", "coordinates", "spacing"]
author: "Kilo Code"
tested_on: "Revit 2024, pyRevit 4.8.x"
status: "active"
last_updated: "2025-10-23"
---

# Legend Layout Engine

## Problem Statement

Creating consistent, professional-looking legends requires complex coordinate calculations, spacing management, and alignment logic. Manual positioning leads to inconsistent layouts and maintenance difficulties.

## Solution Overview

A layout engine that automatically calculates positions for legend elements based on configurable parameters, ensuring consistent spacing, alignment, and professional appearance.

## Key Components

### 1. Layout Configuration

```python
class LegendLayoutConfig:
    """Configuration for legend layout parameters."""

    def __init__(self):
        self.region_width = 2.0      # feet
        self.region_height = 1.0     # feet
        self.horizontal_spacing = 1.5  # feet
        self.vertical_spacing = 1.2   # feet
        self.text_offset = 0.5        # feet
        self.header_offset = 0.8      # feet
        self.max_columns = 10
        self.page_width = 30.0       # feet
```

### 2. Position Calculator

```python
class LegendLayoutEngine:
    """Engine for calculating legend element positions."""

    def __init__(self, config):
        """
        Initialize layout engine with configuration.

        Args:
            config (LegendLayoutConfig): Layout configuration object
        """
        self.config = config
        self.current_x = 0.0
        self.current_y = 0.0
        self.column_count = 0

    def calculate_positions(self, elements):
        """
        Calculate positions for all legend elements.

        Args:
            elements (list): List of elements to position

        Returns:
            dict: Dictionary mapping element IDs to (x, y) coordinates
        """
        positions = {}

        for element in elements:
            # Calculate position based on layout rules
            x, y = self._calculate_next_position(element)

            positions[element.id] = (x, y)

            # Update layout state
            self._update_layout_state()

        return positions
```

## Layout Algorithms

### 1. Grid-Based Layout

```python
def _calculate_grid_position(self, element_index):
    """Calculate position in a grid layout."""

    # Calculate column and row
    column = element_index % self.config.max_columns
    row = element_index // self.config.max_columns

    # Calculate coordinates
    x = column * (self.config.region_width + self.config.horizontal_spacing)
    y = row * (self.config.region_height + self.config.vertical_spacing)

    return x, y
```

### 2. Flow Layout

```python
def _calculate_flow_position(self, element):
    """Calculate position in a flowing layout."""

    # Check if element fits in current row
    if self.current_x + element.width > self.config.page_width:
        # Move to next row
        self.current_x = 0.0
        self.current_y -= self.config.vertical_spacing + element.height

    x = self.current_x
    y = self.current_y

    # Update for next element
    self.current_x += element.width + self.config.horizontal_spacing

    return x, y
```

### 3. Column-Based Layout

```python
def _calculate_column_position(self, column_index, row_index):
    """Calculate position for column-based layout."""

    # Base positions for each column
    column_bases = {
        0: 0.0,                    # Visual column
        1: self.config.region_width + self.config.horizontal_spacing,  # Cut column
        2: 2 * (self.config.region_width + self.config.horizontal_spacing),  # Surface column
        # Text columns follow...
    }

    x = column_bases.get(column_index, 0.0)
    y = row_index * (self.config.region_height + self.config.vertical_spacing)

    return x, y
```

## Integration Patterns

### With ViewFiltersLegend Script

```python
from Snippets._convert import convert_cm_to_feet

def create_filter_legend_layout():
    """Create layout configuration for filter legends."""

    # User-friendly configuration (cm)
    config_cm = {
        'region_width': 3.0,      # 3 cm wide regions
        'region_height': 1.5,     # 1.5 cm tall regions
        'spacing': 0.8,           # 0.8 cm spacing
        'text_offset': 0.5        # 0.5 cm text offset
    }

    # Convert to Revit units
    config_feet = {}
    for key, value_cm in config_cm.items():
        config_feet[key] = convert_cm_to_feet(value_cm)

    return LegendLayoutConfig(**config_feet)
```

### With Position Calculation

```python
def position_legend_elements(elements, layout_engine):
    """Position elements using layout engine."""

    positions = layout_engine.calculate_positions(elements)

    # Create elements at calculated positions
    for element, (x, y) in zip(elements, positions.values()):
        if element.type == 'region':
            create_region(doc, view, x, y,
                         layout_engine.config.region_width,
                         layout_engine.config.region_height)
        elif element.type == 'text':
            create_text_note(doc, view, x, y, element.text, text_type)
```

## Usage Examples

### Basic Legend Creation

```python
def create_simple_legend(doc, view, filters):
    """Create a simple filter legend."""

    # Setup layout
    config = LegendLayoutConfig()
    layout = LegendLayoutEngine(config)

    y_pos = 10.0  # Starting Y position

    for filter_elem in filters:
        # Calculate positions for this filter's elements
        positions = {
            'region': (0.0, y_pos),
            'text': (config.region_width + config.text_offset, y_pos + config.text_offset)
        }

        # Create visual region
        region = create_region(doc, view,
                              positions['region'][0], positions['region'][1],
                              config.region_width, config.region_height)

        # Create text label
        text = create_text_note(doc, view,
                               positions['text'][0], positions['text'][1],
                               filter_elem.Name, text_type)

        # Apply graphics overrides
        overrides = view.GetFilterOverrides(filter_elem.Id)
        override_graphics_region(doc, view, region,
                               fg_color=overrides.SurfaceForegroundPatternColor)

        # Move down for next filter
        y_pos -= config.region_height + config.vertical_spacing
```

### Advanced Multi-Column Layout

```python
def create_multi_column_legend(doc, view, filters):
    """Create legend with multiple information columns."""

    config = LegendLayoutConfig()
    config.max_columns = 8  # 8 columns total

    # Column definitions
    columns = [
        {'name': 'visual', 'width': config.region_width},
        {'name': 'cut', 'width': config.region_width},
        {'name': 'filter_name', 'width': 5.0},
        {'name': 'categories', 'width': 8.0},
        {'name': 'parameter', 'width': 4.0},
        {'name': 'evaluator', 'width': 3.0},
        {'name': 'value', 'width': 4.0},
        {'name': 'status', 'width': 3.0}
    ]

    y_pos = 10.0

    for filter_elem in filters:
        x_pos = 0.0

        # Parse filter data
        parsed_filter = ef_Filter(filter_elem)

        # Create row elements
        row_data = [
            ('region', None),  # Visual placeholder
            ('region', None),  # Cut placeholder
            ('text', filter_elem.Name),
            ('text', ', '.join(parsed_filter.cat_names)),
            ('text', parsed_filter.rules[0].rule_param_name if parsed_filter.rules else ''),
            ('text', parsed_filter.rules[0].rule_eval if parsed_filter.rules else ''),
            ('text', str(parsed_filter.rules[0].rule_value) if parsed_filter.rules else ''),
            ('text', 'Active')
        ]

        for i, (elem_type, content) in enumerate(row_data):
            col_width = columns[i]['width']

            if elem_type == 'region':
                # Create visual region
                region = create_region(doc, view, x_pos, y_pos, col_width, config.region_height)

                # Apply appropriate overrides based on column
                if i == 0:  # Surface
                    overrides = view.GetFilterOverrides(filter_elem.Id)
                    override_graphics_region(doc, view, region,
                                           fg_color=overrides.SurfaceForegroundPatternColor)
                elif i == 1:  # Cut
                    overrides = view.GetFilterOverrides(filter_elem.Id)
                    override_graphics_region(doc, view, region,
                                           fg_color=overrides.CutForegroundPatternColor)

            elif elem_type == 'text':
                # Create text element
                create_text_note(doc, view, x_pos + 0.1, y_pos + config.text_offset,
                               content or '', text_type)

            x_pos += col_width + config.horizontal_spacing

        y_pos -= config.region_height + config.vertical_spacing
```

## Layout Strategies

### 1. Fixed Grid Layout

```python
class FixedGridLayout(LegendLayoutEngine):
    """Fixed grid with predefined columns."""

    def __init__(self, columns, rows):
        super().__init__()
        self.columns = columns
        self.rows = rows
        self.cell_width = 3.0   # feet
        self.cell_height = 1.5  # feet

    def get_position(self, col, row):
        """Get position for specific grid cell."""
        x = col * (self.cell_width + self.config.horizontal_spacing)
        y = row * (self.cell_height + self.config.vertical_spacing)
        return x, y
```

### 2. Flow Layout

```python
class FlowLayout(LegendLayoutEngine):
    """Flow layout that wraps to next line."""

    def __init__(self, max_width):
        super().__init__()
        self.max_width = max_width
        self.current_x = 0.0
        self.current_y = 0.0

    def add_element(self, element):
        """Add element and calculate its position."""

        if self.current_x + element.width > self.max_width:
            # Wrap to next line
            self.current_x = 0.0
            self.current_y -= element.height + self.config.vertical_spacing

        position = (self.current_x, self.current_y)
        self.current_x += element.width + self.config.horizontal_spacing

        return position
```

### 3. Hierarchical Layout

```python
class HierarchicalLayout(LegendLayoutEngine):
    """Layout with grouping and indentation."""

    def __init__(self):
        super().__init__()
        self.indent_levels = {'group': 0.0, 'item': 1.0, 'detail': 2.0}

    def position_by_hierarchy(self, element, level):
        """Position element based on hierarchy level."""

        indent = self.indent_levels.get(level, 0.0)
        x = indent
        y = self.current_y

        self.current_y -= self.config.vertical_spacing

        return x, y
```

## Performance Considerations

- **Pre-calculation**: Calculate all positions before creating elements
- **Batch Creation**: Create elements in single transaction
- **Memory Efficiency**: Reuse layout configurations
- **Coordinate Caching**: Cache calculated positions

## Error Handling

```python
def safe_calculate_layout(elements, config):
    """Calculate layout with error handling."""

    try:
        layout = LegendLayoutEngine(config)

        # Validate configuration
        if config.region_width <= 0:
            raise ValueError("Region width must be positive")

        positions = layout.calculate_positions(elements)
        return positions

    except Exception as e:
        logger.error(f"Layout calculation failed: {e}")
        # Return fallback positions
        return {elem.id: (0.0, i * -2.0) for i, elem in enumerate(elements)}
```

## Compatibility

- **Revit Versions**: 2021+ (coordinate system consistent)
- **pyRevit**: 4.8.x+
- **Dependencies**: Requires Snippets._convert for unit conversions

## Cross-References

- **Annotations**: `LOG-UTIL-ANNOTATIONS-001-v1-text-graphics-creation.md`
- **Unit Conversion**: `LOG-UTIL-CONVERT-001-v1-unit-conversion-framework.md`
- **Filter Parsing**: `LOG-UTIL-FILTER-001-v1-filter-rule-parser.md`

## Testing Recommendations

```python
def test_layout_calculations():
    """Test layout position calculations."""

    config = LegendLayoutConfig()
    layout = LegendLayoutEngine(config)

    # Test basic positioning
    elements = [MockElement(width=2.0, height=1.0) for _ in range(3)]
    positions = layout.calculate_positions(elements)

    # Verify spacing
    assert positions[1][0] > positions[0][0] + 2.0  # Horizontal spacing
    assert positions[1][1] < positions[0][1]       # Vertical stacking

    # Test boundary conditions
    assert positions[0][0] >= 0.0  # Non-negative X
    assert positions[0][1] <= 10.0 # Within expected range
```

## Future Enhancements

- [ ] Add support for rotated layouts
- [ ] Add auto-sizing based on content
- [ ] Add layout templates (table, grid, flow)
- [ ] Add responsive layout for different view sizes
- [ ] Add layout validation and collision detection