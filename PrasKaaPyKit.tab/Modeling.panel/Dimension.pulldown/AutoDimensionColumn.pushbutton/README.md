# Auto Dimension Columns - Revit pyRevit Tool

## Overview

This pyRevit tool automatically creates dimensions for structural and architectural columns in Revit plan views. It intelligently places orthogonal dimensions (X and Y directions) for each column that continues upward from the current level.

## Features

- **Automatic Reference Detection**: Finds column faces using multiple fallback methods (named references, geometry analysis, face detection)
- **Smart Column Filtering**: Only dimensions columns that continue above the current plan level
- **Batch Processing**: Process multiple plan views with selective view choosing
- **Flexible Configuration**: Adjustable offset distances, dimension types, and verbosity levels
- **Robust Error Handling**: Continues processing even when individual columns fail
- **Console Output Control**: Configurable verbose output for debugging or clean operation

## Installation

1. Copy the `script.py` file to your pyRevit extensions directory
2. Place it in a pushbutton folder structure:
   ```
   %APPDATA%\pyRevit-Master\extensions\[YourExtension].extension\[YourTab].tab\[YourPanel].panel\[YourTool].pushbutton\script.py
   ```
3. Restart Revit or reload pyRevit

## Usage

### Single View Processing
1. Open the plan view you want to dimension
2. Run the tool
3. Select "Current View Only"
4. Configure offset distance and dimension type
5. Select columns to dimension (or use pre-selection)
6. Dimensions are automatically created

### Batch Processing
1. Run the tool
2. Select "Batch Process All Plan Views"
3. Choose which plan views to process from the multi-select list
4. Confirm your selection
5. Configure offset distance and dimension type
6. The tool processes each selected view sequentially

## Configuration

### Verbose Output
Set `VERBOSE_OUTPUT = True` in the Config class for detailed processing information, or `False` for clean output.

### Default Settings
- **Offset Distance**: 10mm (configurable per run)
- **Dimension Type**: "Arrow - 1.8mm Swis721 BT - Dimensi Kolom" (auto-detected)
- **Dimension Line Length**: 10 feet

## How It Works

### Column Detection
The tool identifies columns by:
- Category (OST_StructuralColumns, OST_Columns)
- Name keywords ("Column", "Kolom")
- Structural type

### Reference Finding
For each column, the tool finds dimension references using:
1. **Named References**: Looks for predefined reference names (x_1, x_2, y_1, y_2, etc.)
2. **Geometry Analysis**: Analyzes column geometry to find opposing faces
3. **Face Detection**: Uses planar face analysis as fallback

### Dimension Creation
- Creates two dimensions per column (X and Y directions)
- Positions dimension lines at specified offset from column center
- Uses the selected dimension type and view scale

### Level Filtering
Only columns that continue above the current plan level are dimensioned, determined by:
- Column top level vs. current view level
- Top level offset consideration

## Troubleshooting

### Common Issues

**"Could not get references from column"**
- Column geometry may be complex or irregular
- Try different column families or adjust geometry

**"The referenced object is not valid"**
- Document state issues during batch processing
- Try processing fewer views at once

**No dimensions created**
- Check that columns continue above current level
- Verify dimension type exists in project
- Ensure view is a plan view

### Debug Mode
Enable verbose output (`VERBOSE_OUTPUT = True`) to see detailed processing information including:
- Column detection process
- Reference finding attempts
- Individual dimension creation results
- Error messages for failed operations

## Technical Details

### Dependencies
- Revit API
- pyRevit framework
- IronPython 2.7

### Classes
- `AutoDimensionController`: Main orchestration
- `ColumnProcessor`: Individual column processing
- `ReferenceHandler`: Reference detection logic
- `Utils`: Utility functions
- `Config`: Configuration constants

### Transaction Management
- Uses standard Revit Transaction for reliability
- Automatic rollback on errors
- View activation for dimension creation

## API Reference

### Config Class
```python
class Config:
    VERBOSE_OUTPUT = False  # Enable/disable detailed console output
    DEFAULT_OFFSET_MM = 10  # Default dimension offset in millimeters
    DEFAULT_DIM_TYPE_NAME = "Arrow - 1.8mm Swis721 BT - Dimensi Kolom"
    DIM_LINE_LENGTH = 10  # Dimension line length in feet

    REF_NAMES = {
        'x1': ['x_1', 'Left', 'Kiri'],
        'x2': ['x_2', 'Right', 'Kanan'],
        'y1': ['y_1', 'Front', 'Depan'],
        'y2': ['y_2', 'Back', 'Belakang']
    }

    COLUMN_CATEGORIES = [
        BuiltInCategory.OST_StructuralColumns,
        BuiltInCategory.OST_Columns
    ]
```

### Key Methods

#### AutoDimensionController
- `run()`: Main entry point with processing mode selection
- `_run_batch_processing()`: Handles multi-view batch processing
- `_run_single_view()`: Processes current active view
- `_process_columns_for_view()`: Core processing logic per view

#### Utils
- `should_dimension_column(column, view, doc)`: Determines if column should be dimensioned
- `is_column(element)`: Validates if element is a column
- `get_view_scale_factor(view)`: Gets view scale for offset calculations

#### ReferenceHandler
- `get_references(column)`: Finds dimension references using multiple methods
- `_get_named_references()`: Tries predefined reference names
- `_get_geometry_references()`: Analyzes column geometry
- `_get_face_references()`: Uses face analysis as fallback

## Changelog

### Version 2.0 (Current)
- ✅ **Selective Batch Processing**: Choose specific plan views instead of processing all
- ✅ **Configurable Verbosity**: Control console output detail level
- ✅ **Improved Error Handling**: Better transaction management and error recovery
- ✅ **Console Summary**: Batch results displayed in console instead of dialog
- ✅ **Enhanced Reference Detection**: Multiple fallback methods for finding column faces

### Version 1.0
- ✅ Basic single-view column dimensioning
- ✅ Automatic reference detection
- ✅ Level-based column filtering
- ✅ Batch processing all plan views

## Performance Notes

- **Memory Usage**: Processes columns one view at a time to minimize memory footprint
- **Transaction Safety**: Uses standard Revit transactions with automatic rollback
- **Error Recovery**: Continues processing other columns/views when individual items fail
- **View Switching**: Temporarily activates views during processing for dimension creation

## Limitations

- Requires plan views with proper level associations
- Column families must have detectable geometry faces
- Dimension creation requires valid dimension types in the project
- Large models may require processing in smaller batches

## Contributing

When modifying the code:
1. Maintain the multi-method reference detection approach
2. Preserve transaction safety and error handling
3. Update verbose output messages consistently
4. Test with various column families and project types

## License

This tool is provided as-is for use with Autodesk Revit and pyRevit framework.

## Support

For technical support:
1. Enable verbose output (`VERBOSE_OUTPUT = True`)
2. Run the tool and capture the complete console output
3. Include project details (Revit version, column types, view configurations)
4. Report specific error messages and failure patterns

The tool is designed to be robust and continue operation despite individual failures, so partial success is normal for complex projects.