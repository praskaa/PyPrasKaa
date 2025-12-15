# Count Detail Item Reinforcement

Counts reinforcement detail items in the current view by diameter, providing a summary report for quality control and verification against engineering requirements.

## Features

- **Automatic Detection**: Finds all detail items with family name "Detail Item_Tulangan" in selected views
- **Multi-View Selection**: Choose multiple views from an intuitive dialog for batch analysis
- **Diameter Grouping**: Groups reinforcement bars by their `d_tul` parameter values
- **Configurable Spatial Clustering**: Set custom distance threshold for grouping nearby reinforcement bars
- **Location Coordinates**: Shows approximate centroid locations for each spatial group
- **Quantity Counting**: Counts the number of bars for each diameter and location group
- **Unit Conversion**: Displays diameters and coordinates in millimeters
- **Comprehensive Report**: Shows view-by-view breakdown with spatial distribution analysis

## Usage

1. Click the "Count Detail Item Reinforcement" button
2. Select one or more views from the dialog that appears
3. Enter the maximum clustering distance in mm (default: 260mm)
4. Review the generated report in the pyRevit output window

## Report Output

The script generates a comprehensive multi-view report with spatial clustering:

```
Analysis Summary: 3 views processed, 152 total items found
Clustering Distance: 260 mm

## View: SW8-L23 FL

View Summary: 56 items found, 56 with d_tul parameter, 2 unique diameters, 4 spatial groups

Diameter: 16 mm (d_tul = 0.0525, Total: 16 bars)
- Group A: 8 bars (~X: 15000, Y: 5000)
- Group B: 8 bars (~X: 18000, Y: 5000)

Diameter: 22 mm (d_tul = 0.0722, Total: 40 bars)
- Group A: 15 bars (~X: 15000, Y: 5200)
- Group B: 25 bars (~X: 18000, Y: 5200)

Total reinforcement bars in SW8-L23 FL: 56

---

## Overall Summary
Total views analyzed: 3
Total reinforcement bars across all views: 152
```

**Features:**
- **Multi-View Selection**: Choose multiple views from an intuitive dialog
- **Spatial Clustering**: Groups reinforcement bars by proximity (260mm threshold) within the same diameter
- **Diameter + Location Analysis**: Combines diameter classification with location-based grouping
- **Location Coordinates**: Shows approximate centroid coordinates for each spatial group in project units
- **View-Centric Organization**: Each view gets its own clearly labeled section
- **Comprehensive Summaries**: Both per-view and overall totals
- **Automatic Units**: Diameters and coordinates converted to millimeters

## Requirements

- Active view must be a plan, section, elevation, or detail view
- Detail items must have family name "Detail Item_Tulangan"
- Detail items must have a valid `d_tul` parameter

## Error Handling

The script includes robust error handling for:
- Missing or invalid parameters
- Family type access issues
- View type compatibility
- Parameter extraction failures

## Technical Details

- Uses `FilteredElementCollector` with view-specific filtering
- Filters by `BuiltInCategory.OST_DetailComponents`
- Groups results by floating-point precision handling
- Converts Revit internal units (feet) to millimeters for display

## Version History

- v1.0: Initial implementation with basic counting and reporting functionality