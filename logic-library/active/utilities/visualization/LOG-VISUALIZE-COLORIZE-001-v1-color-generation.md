---
logic_id: LOG-VISUALIZE-COLORIZE-001
version: v1
status: active
category: visualization
subcategory: colorize
tags: [color, palette, generation, hsv, gradient]
---

# Color Generation Logic

## Problem Solved
Need to generate consistent, visually distinct color palettes for categorizing Revit elements by parameter values.

## Solution Approach
Use HSV-based color generation with gradient interpolation to create smooth color transitions.

## Key Techniques
- HSV color space for better perceptual uniformity
- Polylinear gradient interpolation between base colors
- Random shuffling to avoid positional bias

## Dependencies
- colorsys module for HSV-RGB conversion
- Revit DB.Color for API compatibility

## Usage Examples
```python
from visualization.colorize import get_colours

# Generate 5 distinct colors
colors = get_colours(5)
```

## Performance Notes
- O(n) complexity for gradient generation
- Suitable for up to 100+ categories

## Compatibility
- Revit 2024+
- Python 2.7/3.x

## Source
Migrated from pyChilizer v1.0