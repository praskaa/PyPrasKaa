---
logic_id: LOG-VISUALIZE-FILTER-001
version: v1
status: active
category: visualization
subcategory: filter
tags: [filter, parameter, rule, dynamic]
---

# Dynamic Filter Creation Logic

## Problem Solved
Need to create Revit parameter filters programmatically based on element parameter values for visualization.

## Solution Approach
Use ParameterFilterRuleFactory to create filter rules and combine them with logical operators.

## Key Techniques
- Parameter value extraction by storage type
- Rule-based filtering with AND/OR logic
- Filter naming conflict resolution

## Dependencies
- DB.ParameterFilterRuleFactory
- DB.ElementParameterFilter
- Logical filter combinations

## Usage Examples
```python
from utilities.revit_database import create_filter_by_name_bics, filter_from_rules

# Create filter for structural categories
filter = create_filter_by_name_bics("Structural Elements", [DB.BuiltInCategory.OST_StructuralFraming])
```

## Performance Notes
- Filter creation is lightweight
- Rule evaluation depends on model size

## Compatibility
- Revit 2024+
- Supports all parameter storage types

## Source
Migrated from pyChilizer v1.0