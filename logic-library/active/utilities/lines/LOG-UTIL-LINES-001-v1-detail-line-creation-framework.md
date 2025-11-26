---
title: "Detail Line Creation Framework"
version: "1.0"
category: "utilities/lines"
tags: ["lines", "detail", "grid", "reinforcement", "geometry", "layout"]
author: "Kilo Code"
tested_on: "Revit 2021-2026, pyRevit 4.8.x"
status: "active"
last_updated: "2025-10-23"
---

# Detail Line Creation Framework

## Problem Statement

Creating grid tables for reinforcement detailing requires precise control over line positioning, orientation, and intersection handling. Manual line creation leads to inconsistent spacing, alignment issues, and difficulty managing complex grid patterns with proper intersections and scaling.

## Solution Overview

A comprehensive framework for creating horizontal and vertical detail lines with automatic positioning, intersection handling, and scale-aware rendering for reinforcement grid tables.

## Key Components

### 1. Line Creation Engine

```python
class DetailLineEngine:
    """Engine for creating and managing detail lines in grid layouts."""

    def __init__(self, view, scale=100):
        """
        Initialize line creation engine.

        Args:
            view (View): Target view for line creation
            scale (float): View scale factor (default: 100)
        """
        self.view = view
        self.scale = scale
        self.doc = view.Document
        self.created_lines = []

    def create_horizontal_line(self, start_x, start_y, length, style=None):
        """
        Create a horizontal detail line.

        Args:
            start_x, start_y (float): Starting coordinates (feet)
            length (float): Line length (feet)
            style: Line style override

        Returns:
            DetailCurve: Created horizontal line
        """
        start_point = XYZ(start_x, start_y, 0)
        end_point = XYZ(start_x + length, start_y, 0)
        line = Line.CreateBound(start_point, end_point)
        detail_line = self.doc.Create.NewDetailCurve(self.view, line)

        if style:
            self.apply_line_style(detail_line, style)

        self.created_lines.append(detail_line)
        return detail_line

    def create_vertical_line(self, start_x, start_y, length, style=None):
        """
        Create a vertical detail line.

        Args:
            start_x, start_y (float): Starting coordinates (feet)
            length (float): Line length (feet) - positive = down, negative = up
            style: Line style override

        Returns:
            DetailCurve: Created vertical line
        """
        start_point = XYZ(start_x, start_y, 0)
        end_point = XYZ(start_x, start_y + length, 0)
        line = Line.CreateBound(start_point, end_point)
        detail_line = self.doc.Create.NewDetailCurve(self.view, line)

        if style:
            self.apply_line_style(detail_line, style)

        self.created_lines.append(detail_line)
        return detail_line
```

### 2. Grid Layout System

```python
class ReinforcementGrid:
    """Manages grid layout for reinforcement detailing tables."""

    def __init__(self, origin_x, origin_y, config):
        """
        Initialize reinforcement grid.

        Args:
            origin_x, origin_y (float): Grid origin coordinates
            config (dict): Grid configuration parameters
        """
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.config = config
        self.line_engine = DetailLineEngine(config['view'], config['scale'])

        # Grid dimensions
        self.rows = config.get('rows', 10)
        self.cols = config.get('cols', 8)

        # Spacing (in feet)
        self.row_height = config.get('row_height', 1.0)
        self.col_width = config.get('col_width', 2.0)

    def create_grid_structure(self):
        """Create the complete grid structure with horizontal and vertical lines."""

        # Create horizontal grid lines
        for row in range(self.rows + 1):
            y_pos = self.origin_y - (row * self.row_height)
            self.line_engine.create_horizontal_line(
                self.origin_x,
                y_pos,
                self.cols * self.col_width,
                style=self.config.get('grid_line_style')
            )

        # Create vertical grid lines
        for col in range(self.cols + 1):
            x_pos = self.origin_x + (col * self.col_width)
            self.line_engine.create_vertical_line(
                x_pos,
                self.origin_y,
                -(self.rows * self.row_height),  # Negative for downward
                style=self.config.get('grid_line_style')
            )

    def add_internal_lines(self, positions):
        """Add internal lines for specific reinforcement details."""

        for pos in positions:
            if pos['type'] == 'horizontal':
                self.line_engine.create_horizontal_line(
                    pos['x'], pos['y'], pos['length'],
                    style=pos.get('style')
                )
            elif pos['type'] == 'vertical':
                self.line_engine.create_vertical_line(
                    pos['x'], pos['y'], pos['length'],
                    style=pos.get('style')
                )
```

### 3. Intersection and Cleanup System

```python
class LineIntersectionManager:
    """Handles line intersections and cleanup operations."""

    def __init__(self, tolerance=0.01):
        """
        Initialize intersection manager.

        Args:
            tolerance (float): Intersection tolerance in feet
        """
        self.tolerance = tolerance
        self.intersections = []

    def find_intersections(self, lines):
        """Find all intersection points between lines."""

        intersections = []
        for i, line1 in enumerate(lines):
            for j, line2 in enumerate(lines[i+1:], i+1):
                intersection = self.calculate_intersection(line1, line2)
                if intersection:
                    intersections.append({
                        'point': intersection,
                        'lines': [line1, line2],
                        'type': self.classify_intersection(line1, line2)
                    })

        self.intersections = intersections
        return intersections

    def calculate_intersection(self, line1, line2):
        """Calculate intersection point between two lines."""

        # Get line geometries
        geom1 = line1.GeometryCurve
        geom2 = line2.GeometryCurve

        # Calculate intersection
        result = geom1.Intersect(geom2)
        if result == SetComparisonResult.Overlap:
            # Lines overlap - find midpoint
            return self.find_overlap_midpoint(geom1, geom2)
        elif result == SetComparisonResult.Subset:
            # One line is subset of another
            return None

        # Standard intersection
        intersection_points = []
        geom1.IntersectWithCurve(geom2, intersection_points)

        return intersection_points[0] if intersection_points else None

    def classify_intersection(self, line1, line2):
        """Classify intersection type (T-junction, cross, etc.)."""

        # Determine if lines are horizontal/vertical
        dir1 = self.get_line_direction(line1)
        dir2 = self.get_line_direction(line2)

        if dir1 == 'horizontal' and dir2 == 'vertical':
            return 'T-junction'
        elif dir1 == 'vertical' and dir2 == 'horizontal':
            return 'T-junction'
        elif dir1 == dir2:
            return 'parallel'  # Shouldn't intersect
        else:
            return 'cross'
```

## Usage Examples

### Basic Grid Creation

```python
def create_reinforcement_table(view, origin_x=0, origin_y=10):
    """Create a basic reinforcement detailing table."""

    # Configuration
    config = {
        'view': view,
        'scale': 100,
        'rows': 12,
        'cols': 6,
        'row_height': 0.8,  # 8 inches at 1:100 scale
        'col_width': 1.5,   # 15 inches at 1:100 scale
        'grid_line_style': 'Thin Lines'
    }

    # Create grid
    grid = ReinforcementGrid(origin_x, origin_y, config)
    grid.create_grid_structure()

    # Add specific reinforcement lines
    internal_lines = [
        {'type': 'horizontal', 'x': 2.0, 'y': 8.5, 'length': 4.0, 'style': 'Dashed'},
        {'type': 'vertical', 'x': 3.5, 'y': 9.0, 'length': -1.5, 'style': 'Bold'}
    ]

    grid.add_internal_lines(internal_lines)

    return grid
```

### Advanced Intersection Handling

```python
def create_complex_rebar_layout(view):
    """Create complex reinforcement layout with proper intersections."""

    # Initialize systems
    line_engine = DetailLineEngine(view, scale=50)  # 1:50 scale
    intersection_mgr = LineIntersectionManager(tolerance=0.005)  # 1/16" tolerance

    # Create main grid
    main_lines = []

    # Horizontal bars
    for i in range(5):
        y_pos = 10 - (i * 1.5)
        line = line_engine.create_horizontal_line(0, y_pos, 15)
        main_lines.append(line)

    # Vertical stirrups
    for i in range(8):
        x_pos = i * 2.0
        line = line_engine.create_vertical_line(x_pos, 10, -7.5)
        main_lines.append(line)

    # Find and handle intersections
    intersections = intersection_mgr.find_intersections(main_lines)

    # Add corner details or special intersections
    for intersection in intersections:
        if intersection['type'] == 'cross':
            # Add corner mark or special detail
            add_corner_detail(view, intersection['point'])

    return main_lines, intersections
```

### Scale-Aware Line Creation

```python
def create_scale_aware_grid(view, scale, physical_size_inches):
    """Create grid that maintains physical size regardless of scale."""

    # Convert physical size to feet at given scale
    # 1 inch at 1:100 scale = 100 inches in reality = 8.333 feet
    feet_per_inch_at_scale = scale / 12.0  # 12 inches per foot

    # Calculate line spacing in feet
    spacing_feet = physical_size_inches * feet_per_inch_at_scale

    # Create grid with consistent physical spacing
    grid = ReinforcementGrid(0, 10, {
        'view': view,
        'scale': scale,
        'row_height': spacing_feet,
        'col_width': spacing_feet * 2,  # Wider columns
        'rows': 10,
        'cols': 8
    })

    grid.create_grid_structure()
    return grid
```

## Integration with Existing Systems

### With Unit Conversion

```python
from Snippets._convert import convert_cm_to_feet

# User inputs in cm (intuitive)
user_spacing_cm = 5.0  # 5 cm spacing
spacing_feet = convert_cm_to_feet(user_spacing_cm)

# Create grid lines
line_engine.create_horizontal_line(x, y, spacing_feet * 10)  # 10 spacings wide
```

### With Transaction Management

```python
from Snippets._context_manager import ef_Transaction

def create_rebar_detailing_grid(view, config):
    """Create complete rebar detailing grid in transaction."""

    with ef_Transaction(view.Document, "Create Rebar Grid"):
        grid = ReinforcementGrid(config['origin_x'], config['origin_y'], config)
        grid.create_grid_structure()

        # Add reinforcement symbols, text, etc.
        add_rebar_symbols(view, grid.get_intersection_points())
        add_dimension_lines(view, grid.get_line_positions())

    return grid
```

### With Error Handling

```python
def safe_create_detail_lines(view, line_specs):
    """Create detail lines with comprehensive error handling."""

    created_lines = []
    failed_lines = []

    for spec in line_specs:
        try:
            if spec['orientation'] == 'horizontal':
                line = create_horizontal_line(view, spec['x'], spec['y'], spec['length'])
            else:
                line = create_vertical_line(view, spec['x'], spec['y'], spec['length'])

            created_lines.append(line)

        except Exception as e:
            logger.warning(f"Failed to create line at {spec['x']}, {spec['y']}: {e}")
            failed_lines.append(spec)

    return created_lines, failed_lines
```

## Performance Considerations

- **Batch Creation**: Create multiple lines in single transaction
- **Intersection Caching**: Cache intersection calculations for large grids
- **Lazy Evaluation**: Only calculate intersections when needed
- **Memory Management**: Clean up line references for large layouts

## Compatibility

- **Revit Versions**: 2021+ (DetailCurve API consistent)
- **pyRevit**: 4.8.x+
- **Dependencies**: Requires Snippets._convert for unit conversions

## Cross-References

- **Unit Conversion**: `LOG-UTIL-CONVERT-001-v1-unit-conversion-framework.md`
- **Layout Engine**: `LOG-UTIL-LAYOUT-001-v1-legend-layout-engine.md`
- **Annotations**: `LOG-UTIL-ANNOTATIONS-001-v1-text-graphics-creation.md`

## Testing Recommendations

```python
def test_line_creation():
    """Test detail line creation accuracy."""

    # Test horizontal line
    line = create_horizontal_line(view, 0, 0, 5.0)
    assert line.GeometryCurve.Length == 5.0

    # Test vertical line
    line = create_vertical_line(view, 0, 0, -3.0)
    start = line.GeometryCurve.GetEndPoint(0)
    end = line.GeometryCurve.GetEndPoint(1)
    assert abs(start.Y - end.Y) == 3.0

    # Test intersection detection
    h_line = create_horizontal_line(view, 0, 5, 10)
    v_line = create_vertical_line(view, 5, 10, -10)
    intersections = find_intersections([h_line, v_line])
    assert len(intersections) == 1
    assert intersections[0]['point'].X == 5.0
    assert intersections[0]['point'].Y == 5.0
```

## Future Enhancements

- [ ] Add curved line support for complex reinforcement shapes
- [ ] Add automatic dimensioning system
- [ ] Add rebar symbol placement automation
- [ ] Add collision detection and resolution
- [ ] Add export to CAD formats
- [ ] Add parametric reinforcement patterns