---
logic_id: LOG-VISUALIZE-OVERRIDE-001
version: v1
status: active
category: visualization
subcategory: override
tags: [override, graphic, pattern, color]
---

# Graphic Overrides Logic

## Problem Solved
Need to apply visual overrides to Revit elements for categorization and highlighting.

## Solution Approach
Use OverrideGraphicSettings to modify projection and cut appearances with solid fill patterns.

## Key Techniques
- Selective override application (line, surface, pattern)
- Solid fill pattern retrieval
- Color assignment to different graphic elements

## Dependencies
- DB.OverrideGraphicSettings
- Solid fill pattern element
- Revit color objects

## Usage Examples
```python
from visualization.colorize import set_colour_overrides_by_option

# Apply surface color override
override = set_colour_overrides_by_option(["Projection Surface Colour"], color, doc)
```

## Performance Notes
- Override application is per-element
- Batch operations recommended for large selections

## Compatibility
- Revit 2024+
- All view types supporting overrides

## Source
Migrated from pyChilizer v1.0