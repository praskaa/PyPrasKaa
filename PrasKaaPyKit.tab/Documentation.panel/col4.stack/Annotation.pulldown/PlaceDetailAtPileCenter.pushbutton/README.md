# Place Detail Item at Pile Center

## Overview

This pyRevit script automatically places detail items at the center of all "Foundation Pile" instances visible in the active ViewPlan. The script is designed for structural documentation workflows where you need to quickly annotate pile locations with detail symbols.

## Features

- ✅ **Automatic Pile Detection**: Finds all "Foundation Pile" family instances in the active plan view
- ✅ **2D Placement**: Places detail items with Z=0 for proper plan view annotation
- ✅ **User Selection**: Interactive selection of detail item types from available families
- ✅ **Single Transaction**: Efficient processing with single Revit transaction
- ✅ **Error Handling**: Graceful handling of placement failures with detailed reporting
- ✅ **View Validation**: Ensures script only runs in plan views

## Requirements

- **Revit Version**: 2020-2026
- **pyRevit**: Latest version
- **Active View**: Must be a plan view (Floor Plan, Structural Plan, etc.)
- **Pile Family**: "Foundation Pile" family must exist in the project
- **Detail Items**: At least one detail item family loaded in the project

## Usage

### Preparation

1. **Load Pile Family**: Ensure "Foundation Pile" family is loaded in your project
2. **Load Detail Items**: Load the detail item families you want to use for pile annotation
3. **Switch to Plan View**: Make sure you're in a plan view where piles are visible

### Execution

1. **Run the Script**: Click the "Place Detail at Pile Center" button in the NerdyThings pulldown
2. **Select Detail Item**: Choose from available detail item types in the dropdown
3. **Confirm Placement**: Click "Place at Pile Centers" to proceed
4. **Review Results**: Check the results summary for success/failure counts

### Output

The script provides:
- **Console Output**: Detailed progress and results in pyRevit output window
- **Alert Dialog**: Summary of placement results
- **Error Details**: Information about any failed placements

## Technical Details

### Pile Detection Logic

```python
# Filters piles by:
# 1. Category: OST_StructuralFoundation
# 2. Family Name: "Foundation Pile" (hardcoded)
# 3. View Visibility: Appears in active ViewPlan (including hidden piles)
```

### Center Point Extraction

```python
# For vertical piles:
# - Uses LocationPoint.X and LocationPoint.Y
# - Sets Z = 0.0 for 2D plan placement
# - Handles standard vertical pile geometry
```

### Detail Item Placement

```python
# Places detail items using:
# - doc.Create.NewFamilyInstance(center_point, detail_type, view)
# - Origin of detail item aligns with pile center
# - Single transaction for all placements
```

## Configuration

### Hardcoded Settings

```python
FOUNDATION_PILE_FAMILY_NAME = "Foundation Pile"  # Pile family filter
```

### Error Scenarios

The script handles these error conditions:

- **No Plan View**: Script exits if not in plan view
- **No Piles Found**: Alerts if no "Foundation Pile" instances exist
- **No Detail Items**: Alerts if no detail item families are loaded
- **Placement Failures**: Continues processing other piles if one fails
- **Invalid Center Points**: Skips piles without valid location points

## Troubleshooting

### Common Issues

**"No Foundation Pile instances found"**
- Check that "Foundation Pile" family is loaded
- Verify piles exist in the current plan view
- Ensure family name matches exactly "Foundation Pile"

**"No detail item types found"**
- Load detail item families into the project
- Check that families are properly loaded and not corrupted

**"Invalid View Type"**
- Switch to a plan view (Floor Plan, Structural Plan, etc.)
- Avoid running in 3D views, sections, or elevations

### Debug Information

The script provides detailed console output including:
- Number of piles found
- Selected detail item type
- Success/failure counts
- Specific error messages for failed placements

## Future Enhancements

Potential improvements for future versions:

1. **Type Mapping**: Automatic mapping between pile types and detail item types
2. **Batch Processing**: For very large numbers of piles
3. **Configuration File**: Save user preferences and mappings
4. **Multiple Views**: Process multiple plan views at once
5. **Placement Options**: Offset placement, rotation options

## Version History

- **v1.0**: Initial implementation with basic pile detection and placement
- Core functionality for single detail item placement at pile centers
- Error handling and user feedback
- Plan view validation and family filtering

## Support

For issues or questions:
1. Check the pyRevit output window for detailed error messages
2. Verify all requirements are met (family names, view types, etc.)
3. Ensure detail item families are properly loaded
4. Check that piles have valid location points

---

**Note**: This script is designed for standard vertical pile families. Complex or custom pile geometries may require adjustments to the center point extraction logic.