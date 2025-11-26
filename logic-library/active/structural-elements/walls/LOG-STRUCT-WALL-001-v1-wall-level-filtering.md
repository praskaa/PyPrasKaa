---
id: "LOG-STRUCT-WALL-001"
version: "v1"
status: "active"
category: "structural-elements/walls"
element_type: "Walls"
operation: "level-filtering"
revit_versions: [2024, 2026]
tags: ["walls", "level", "filtering", "vertical", "constraints", "elevation", "top-constraint"]
created: "2025-10-10"
updated: "2025-10-10"
confidence: "high"
performance: "medium"
source_file: "lib/smart_tag_engine.py"
source_location: "lib/smart_tag_engine.py"
---

# LOG-STRUCT-WALL-001-v1: Wall Level Filtering Logic

## Problem Context

Walls in Revit can span multiple levels and appear in multiple plan views. Without proper filtering, walls get tagged in every view they appear in, creating duplicate tags and visual clutter. The challenge is determining whether a wall should be tagged in a specific view based on its complex level constraints - whether it "stops at the reference level" or "continues upward from the reference level."

## Solution Summary

This pattern implements intelligent level-based filtering for walls by analyzing their Top Constraint and Base Constraint parameters. Walls are only tagged in views where they extend above the view's level elevation, handling both connected and unconnected wall scenarios with multiple parameter storage types.

## Working Code

```python
class WallLevelFilter:
    """Filters walls based on level constraints to prevent duplicate tagging"""

    def __init__(self, doc):
        self.doc = doc

    def should_tag_wall_in_view(self, wall, view_level):
        """Determine if wall should be tagged in the given view level"""
        if not view_level:
            return True  # Tag if no view level info

        try:
            view_elevation = view_level.Elevation

            # Get wall base elevation
            base_elevation = self._get_wall_base_elevation(wall)
            if base_elevation is None:
                return True  # Default if can't determine

            # Get wall top elevation
            top_elevation = self._get_wall_top_elevation(wall, base_elevation)
            if top_elevation is None:
                return True  # Default if can't determine

            # KEY LOGIC: Wall should be tagged if it continues upward
            # from the current view level (top > view elevation)
            return top_elevation > view_elevation

        except Exception as e:
            return True  # Default: include if error

    def _get_wall_base_elevation(self, wall):
        """Get wall base elevation from Base Constraint + Base Offset"""
        try:
            # Try different parameter names for Base Constraint
            base_constraint_names = ["Base Constraint", "Base Level", "Wall Base Constraint"]

            for constraint_name in base_constraint_names:
                base_constraint_param = wall.LookupParameter(constraint_name)
                if base_constraint_param and base_constraint_param.HasValue:
                    if base_constraint_param.StorageType == StorageType.ElementId:
                        level_id = base_constraint_param.AsElementId()
                        if level_id and level_id != ElementId.InvalidElementId:
                            level = self.doc.GetElement(level_id)
                            if level and isinstance(level, Level):
                                base_elevation = level.Elevation

                                # Add Base Offset if exists
                                base_offset_param = wall.LookupParameter("Base Offset")
                                if base_offset_param and base_offset_param.HasValue:
                                    base_offset = base_offset_param.AsDouble()
                                    base_elevation += base_offset

                                return base_elevation

            return None

        except Exception as e:
            return None

    def _get_wall_top_elevation(self, wall, base_elevation):
        """Get wall top elevation using complex Top Constraint logic"""
        try:
            # Find Top Constraint parameter
            top_constraint_param = None
            for param in wall.Parameters:
                param_name = param.Definition.Name
                if "top constraint" in param_name.lower() or "top level" in param_name.lower():
                    if param.HasValue:
                        top_constraint_param = param
                        break

            if top_constraint_param:
                # Handle based on StorageType
                if top_constraint_param.StorageType == StorageType.ElementId:
                    # Top Constraint references a level
                    element_id = top_constraint_param.AsElementId()

                    if element_id and element_id != ElementId.InvalidElementId:
                        # Connected to level
                        level = self.doc.GetElement(element_id)
                        if level and isinstance(level, Level):
                            top_elevation = level.Elevation

                            # Add Top Offset if exists
                            top_offset_param = wall.LookupParameter("Top Offset")
                            if top_offset_param and top_offset_param.HasValue:
                                top_offset = top_offset_param.AsDouble()
                                top_elevation += top_offset

                            return top_elevation
                    else:
                        # Unconnected wall - use Unconnected Height
                        unconnected_height_param = wall.LookupParameter("Unconnected Height")
                        if unconnected_height_param and unconnected_height_param.HasValue:
                            unconnected_height = unconnected_height_param.AsDouble()
                            return base_elevation + unconnected_height

                elif top_constraint_param.StorageType == StorageType.String:
                    # Handle string format (fallback)
                    top_constraint_value = top_constraint_param.AsString()

                    if "Up to level:" in top_constraint_value:
                        level_name = top_constraint_value.replace("Up to level:", "").strip()
                        collector = FilteredElementCollector(self.doc).OfClass(Level)
                        for level in collector:
                            if level.Name == level_name:
                                return level.Elevation

                    elif "Unconnected" in top_constraint_value:
                        unconnected_height_param = wall.LookupParameter("Unconnected Height")
                        if unconnected_height_param and unconnected_height_param.HasValue:
                            unconnected_height = unconnected_height_param.AsDouble()
                            return base_elevation + unconnected_height

            return None

        except Exception as e:
            return None

    def get_wall_height(self, wall):
        """Get wall height using various methods"""
        try:
            base_elev = self._get_wall_base_elevation(wall)
            top_elev = self._get_wall_top_elevation(wall, base_elev or 0)

            if base_elev is not None and top_elev is not None:
                return top_elev - base_elev

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

1. **Complex Top Constraint Parsing**: Handles both ElementId and String storage types
2. **Connected vs Unconnected Walls**: Different logic for walls connected to levels vs unconnected
3. **Parameter Name Variations**: Tries multiple parameter names for compatibility
4. **Offset Calculations**: Includes both Base Offset and Top Offset
5. **Fallback Strategies**: Multiple methods to determine wall extents

## Revit API Compatibility

- **Parameter Lookup**: Uses `LookupParameter()` for flexible parameter access
- **StorageType Handling**: Supports both ElementId and String parameter formats
- **Level Relationships**: Compatible with connected and unconnected wall constraints

## Performance Notes

- **Execution Time**: Medium - involves complex parameter parsing
- **Memory Usage**: Low - minimal additional allocations
- **Scalability**: Efficient for large wall sets with early filtering

## Usage Examples

### Basic Wall Level Filtering
```python
# Initialize filter
wall_filter = WallLevelFilter(doc)

# Get view level
view_level = wall_filter.get_view_level(active_view)

# Filter walls before tagging
filtered_walls = []
for wall in all_walls:
    if wall_filter.should_tag_wall_in_view(wall, view_level):
        filtered_walls.append(wall)
        # Tag this wall
        create_tag_for_wall(wall)
```

### Wall Elevation Analysis
```python
def analyze_wall_levels(walls):
    """Analyze wall level distribution"""
    filter = WallLevelFilter(doc)

    for wall in walls:
        base_elev = filter._get_wall_base_elevation(wall)
        top_elev = filter._get_wall_top_elevation(wall, base_elev or 0)
        height = filter.get_wall_height(wall)

        if base_elev is not None and top_elev is not None:
            print("Wall {}: Base={:.2f}, Top={:.2f}, Height={:.2f}".format(
                wall.Id, base_elev, top_elev, height or 0))
```

### Multi-Level Wall Detection
```python
def find_walls_spanning_levels(walls, view_level):
    """Find walls that span multiple levels from current view"""
    filter = WallLevelFilter(doc)
    view_elev = view_level.Elevation

    spanning_walls = []
    for wall in walls:
        base_elev = filter._get_wall_base_elevation(wall)
        top_elev = filter._get_wall_top_elevation(wall, base_elev or 0)

        if base_elev and top_elev and base_elev < view_elev and top_elev > view_elev:
            # This wall spans across the current level
            spanning_walls.append(wall)

    return spanning_walls
```

## Common Pitfalls

1. **Parameter Name Variations**: Different wall families use different parameter names
2. **Storage Type Complexity**: Handle both ElementId and String parameter formats
3. **Unconnected Walls**: Special logic for walls not connected to levels
4. **Offset Parameters**: Include both Base Offset and Top Offset calculations
5. **Level References**: Handle cases where constraint levels are invalid

## Related Logic Entries

- [LOG-STRUCT-COL-001-v1-column-level-filtering](LOG-STRUCT-COL-001-v1-column-level-filtering.md) - Similar logic for columns
- [LOG-STRUCT-PARAM-001-v1-category-based-parameter-management](LOG-STRUCT-PARAM-001-v1-category-based-parameter-management.md) - Category configuration

## Optimization History

*This is the initial version (v1) with no optimizations yet.*