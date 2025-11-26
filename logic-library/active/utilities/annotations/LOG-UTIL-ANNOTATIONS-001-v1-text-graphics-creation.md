---
title: "Text & Graphics Creation Utilities"
version: "1.0"
category: "utilities/annotations"
tags: ["annotations", "text", "graphics", "legend", "documentation"]
author: "Kilo Code"
tested_on: "Revit 2024, pyRevit 4.8.x"
status: "active"
last_updated: "2025-10-23"
---

# Text & Graphics Creation Utilities

## Problem Statement

Creating consistent text annotations and graphical elements in Revit views requires repetitive code for positioning, styling, and unit conversions. This leads to code duplication and inconsistent implementations across different scripts.

## Solution Overview

A centralized utility module for creating text notes, filled regions, and detail curves with proper unit handling and positioning calculations.

## Key Components

### 1. Text Note Creation

```python
def create_text_note(doc, view, x, y, text, text_note_type, bold=False):
    """
    Create a TextNote at specified coordinates in a view.

    Args:
        doc (Document): Revit document
        view (View): Target view for text placement
        x, y (float): Coordinates in feet (Revit internal units)
        text (str): Text content to display
        text_note_type (TextNoteType): Text style definition
        bold (bool): Whether to apply bold formatting

    Returns:
        TextNote: Created text annotation element

    Example:
        header = create_text_note(doc, legend_view, 0, 10,
                                "Filter Legend", text_type, bold=True)
    """
```

### 2. Filled Region Creation

```python
def create_region(doc, view, X, Y, region_width=120.0, region_height=60.0):
    """
    Create a rectangular FilledRegion for visual representation.

    Args:
        doc (Document): Revit document
        view (View): Target view
        X, Y (float): Bottom-left corner coordinates (feet)
        region_width (float): Width in feet (default: 120 = ~3.6m)
        region_height (float): Height in feet (default: 60 = ~1.8m)

    Returns:
        FilledRegion: Created filled region element

    Example:
        visual_region = create_region(doc, view, 5, 5, 2, 1)  # 2x1 feet region
    """
```

### 3. Detail Line Creation

```python
def create_horizontal_line(doc, view, X, Y, line_width_feet, scale=100):
    """
    Create a horizontal detail line (DetailCurve).

    Args:
        doc (Document): Revit document
        view (View): Target view
        X, Y (float): Starting point coordinates
        line_width_feet (float): Line length in feet
        scale (float): View scale factor (default: 100)

    Returns:
        DetailCurve: Created detail line element

    Example:
        separator = create_horizontal_line(doc, view, 0, 5, 10)  # 10-foot line
    """
```

## Integration Patterns

### With Unit Conversion

```python
from Snippets._convert import convert_cm_to_feet
from Snippets._annotations import create_text_note, create_region

# Convert user input (cm) to Revit units (feet)
width_cm = 5.0
width_feet = convert_cm_to_feet(width_cm)

# Create visual elements
region = create_region(doc, view, 0, 0, width_feet, 2.0)
label = create_text_note(doc, view, width_feet + 1, 1, "Sample", text_type)
```

### With Graphics Overrides

```python
from Snippets._overrides import override_graphics_region
from Snippets._annotations import create_region

# Create and style region
region = create_region(doc, view, x, y, width, height)
override_graphics_region(doc, view, region,
                        fg_color=Color(255, 0, 0),  # Red fill
                        lineweight=3)
```

### In Transaction Context

```python
from Snippets._context_manager import ef_Transaction
from Snippets._annotations import create_text_note, create_region

with ef_Transaction(doc, "Create Legend"):
    # Create multiple annotations
    header = create_text_note(doc, view, 0, 10, "Legend", text_type, bold=True)
    region = create_region(doc, view, 0, 8, 5, 2)
    separator = create_horizontal_line(doc, view, 0, 7, 5)
```

## Usage Examples

### Legend Generation

```python
def create_filter_legend(doc, view, filters):
    """Create a visual legend for view filters."""

    y_pos = 10.0
    x_offset = 2.0

    for filter_elem in filters:
        # Create visual representation
        region = create_region(doc, view, 0, y_pos, 1.5, 0.8)

        # Add text labels
        name_text = create_text_note(doc, view, x_offset, y_pos + 0.4,
                                   filter_elem.Name, text_type)

        # Apply filter graphics
        overrides = view.GetFilterOverrides(filter_elem.Id)
        override_graphics_region(doc, view, region,
                               fg_color=overrides.SurfaceForegroundPatternColor)

        y_pos -= 1.2  # Move down for next item
```

### Layout Calculations

```python
def calculate_legend_positions(base_x, base_y, config):
    """Calculate positions for legend elements."""

    positions = {
        'header': (base_x, base_y + config['header_offset']),
        'region': (base_x, base_y),
        'text': (base_x + config['text_offset'], base_y + config['text_vertical_offset'])
    }

    return positions
```

## Performance Considerations

- **Batch Operations**: Create multiple elements in single transaction
- **Coordinate Caching**: Pre-calculate positions to avoid repeated conversions
- **View Scale Awareness**: Consider view scale for appropriate sizing
- **Memory Management**: Clean up references for large operations

## Compatibility

- **Revit Versions**: 2021+ (uses modern TextNote.Create API)
- **pyRevit**: 4.8.x+
- **Dependencies**: Requires Snippets._convert for unit conversions

## Error Handling

```python
try:
    text_note = create_text_note(doc, view, x, y, text, text_type)
except Exception as e:
    logger.warning(f"Failed to create text note: {e}")
    # Fallback or error recovery
```

## Cross-References

- **Unit Conversion**: `Snippets._convert` module
- **Graphics Overrides**: `Snippets._overrides` module
- **Transaction Management**: `Snippets._context_manager` module
- **Filter Processing**: `LOG-UTIL-FILTER-001-v1-filter-rule-parser.md`

## Future Enhancements

- [ ] Multi-column layout support
- [ ] Auto-sizing based on content
- [ ] Template-based legend generation
- [ ] Rich text formatting options
- [ ] Shape variations (circles, arrows, etc.)