---
id: "LOG-STRUCT-COL-001"
version: "v1"
status: "active"
category: "structural-elements/columns"
element_type: "StructuralColumn"
operation: "level-filtering"
revit_versions: [2024, 2026]
tags: ["columns", "level", "filtering", "vertical", "constraints", "elevation", "top-level"]
created: "2025-10-10"
updated: "2025-10-10"
confidence: "high"
performance: "medium"
source_file: "lib/smart_tag_engine.py"
source_location: "lib/smart_tag_engine.py"
---

# LOG-STRUCT-COL-001-v1: Column Level Filtering Logic

## Problem Context

Structural columns span multiple levels in buildings and appear in multiple plan views. Without proper filtering, columns get tagged in every view they appear in, creating duplicate tags and visual clutter. The challenge is determining whether a column should be tagged in a specific view based on its vertical extent - whether it "stops at the reference level" or "continues upward from the reference level."

## Solution Summary

This pattern implements intelligent level-based filtering for structural columns by analyzing their top level constraints. Columns are only tagged in views where they extend above the view's level elevation, preventing duplicate tags while ensuring proper annotation coverage.

## Working Code

```python
class ColumnLevelFilter:
    """Filters columns based on level constraints to prevent duplicate tagging"""

    def __init__(self, doc):
        self.doc = doc

    def should_tag_column_in_view(self, column, view_level):
        """Determine if column should be tagged in the given view level"""
        if not view_level:
            return True  # Tag if no view level info

        try:
            view_elevation = view_level.Elevation

            # Get column's top level and offset
            top_level_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
            top_offset_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)

            if top_level_param and top_level_param.HasValue:
                top_level_id = top_level_param.AsElementId()
                if top_level_id and top_level_id != ElementId.InvalidElementId:
                    top_level = self.doc.GetElement(top_level_id)
                    if top_level:
                        top_elevation = top_level.Elevation

                        # Add top offset if exists
                        if top_offset_param and top_offset_param.HasValue:
                            top_elevation += top_offset_param.AsDouble()

                        # KEY LOGIC: Column should be tagged if it continues upward
                        # from the current view level (top > view elevation)
                        return top_elevation > view_elevation

            return True  # Default: include if can't determine

        except Exception as e:
            return True  # Default: include if error

    def get_column_top_elevation(self, column):
        """Get the top elevation of a column including offsets"""
        try:
            top_level_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
            top_offset_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)

            if top_level_param and top_level_param.HasValue:
                top_level_id = top_level_param.AsElementId()
                if top_level_id and top_level_id != ElementId.InvalidElementId:
                    top_level = self.doc.GetElement(top_level_id)
                    if top_level:
                        top_elevation = top_level.Elevation

                        # Add top offset if exists
                        if top_offset_param and top_offset_param.HasValue:
                            top_elevation += top_offset_param.AsDouble()

                        return top_elevation

            return None

        except Exception as e:
            return None

    def get_column_base_elevation(self, column):
        """Get the base elevation of a column"""
        try:
            base_level_param = column.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
            base_offset_param = column.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM)

            if base_level_param and base_level_param.HasValue:
                base_level_id = base_level_param.AsElementId()
                if base_level_id and base_level_id != ElementId.InvalidElementId:
                    base_level = self.doc.GetElement(base_level_id)
                    if base_level:
                        base_elevation = base_level.Elevation

                        # Add base offset if exists
                        if base_offset_param and base_offset_param.HasValue:
                            base_elevation += base_offset_param.AsDouble()

                        return base_elevation

            return None

        except Exception as e:
            return None

    def get_view_level(self, view):
        """Get the level associated with a view"""
        try:
            return view.GenLevel
        except:
            return None
```

## Key Techniques

1. **Top Level Analysis**: Uses `FAMILY_TOP_LEVEL_PARAM` to determine column extent
2. **Offset Handling**: Includes both top and base offset parameters
3. **Elevation Comparison**: Compares column top elevation with view level elevation
4. **Safe Parameter Access**: Handles missing or invalid parameter values gracefully

## Revit API Compatibility

- **BuiltInParameter**: Uses standard column parameters like `FAMILY_TOP_LEVEL_PARAM`
- **Level Relationships**: Compatible with multi-story column constraints
- **Offset Support**: Handles both top and base offset parameters

## Performance Notes

- **Execution Time**: Medium - involves parameter lookups and level calculations
- **Memory Usage**: Low - minimal additional allocations
- **Scalability**: Efficient for large column sets

## Usage Examples

### Basic Column Level Filtering
```python
# Initialize filter
column_filter = ColumnLevelFilter(doc)

# Get view level
view_level = column_filter.get_view_level(active_view)

# Filter columns before tagging
filtered_columns = []
for column in all_columns:
    if column_filter.should_tag_column_in_view(column, view_level):
        filtered_columns.append(column)
        # Tag this column
        create_tag_for_column(column)
```

### Column Elevation Analysis
```python
def analyze_column_levels(columns):
    """Analyze column level distribution"""
    filter = ColumnLevelFilter(doc)

    for column in columns:
        base_elev = filter.get_column_base_elevation(column)
        top_elev = filter.get_column_top_elevation(column)

        if base_elev is not None and top_elev is not None:
            height = top_elev - base_elev
            print("Column {}: Base={:.2f}, Top={:.2f}, Height={:.2f}".format(
                column.Id, base_elev, top_elev, height))
```

### Multi-Level Column Detection
```python
def find_multi_level_columns(columns, view_level):
    """Find columns that span multiple levels from current view"""
    filter = ColumnLevelFilter(doc)
    view_elev = view_level.Elevation

    multi_level = []
    for column in columns:
        top_elev = filter.get_column_top_elevation(column)
        if top_elev and top_elev > view_elev:
            # This column extends above current level
            levels_above = calculate_levels_above(view_elev, top_elev)
            multi_level.append((column, levels_above))

    return multi_level
```

## Common Pitfalls

1. **Parameter Availability**: Different column families may have different parameter sets
2. **Level References**: Handle cases where top level is not set or invalid
3. **Offset Calculations**: Don't forget to include both base and top offsets
4. **Multi-Story Columns**: Logic works for columns spanning multiple levels

## Related Logic Entries

- [LOG-STRUCT-WALL-001-v1-wall-level-filtering](LOG-STRUCT-WALL-001-v1-wall-level-filtering.md) - Similar logic for walls
- [LOG-STRUCT-PARAM-001-v1-category-based-parameter-management](LOG-STRUCT-PARAM-001-v1-category-based-parameter-management.md) - Category configuration

## Optimization History

*This is the initial version (v1) with no optimizations yet.*