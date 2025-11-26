# Family Type Generator

## Overview

The **Family Type Generator** is an advanced pyRevit tool designed to create multiple family types in Autodesk Revit from CSV data with flexible parameter matching and custom naming conventions. This tool bridges the gap between spreadsheet data and Revit family parameters, enabling efficient bulk creation of family types with intelligent matching algorithms.

## Features

### Core Functionality
- **CSV-Driven Type Creation**: Generate family types directly from CSV files
- **Flexible Parameter Matching**: Case-insensitive matching with fuzzy logic algorithms
- **Custom Naming Conventions**: Interactive builder for complex naming patterns
- **Unit Conversion**: Automatic conversion between CSV units and Revit internal units
- **Progress Tracking**: Real-time progress with cancellation support
- **Error Handling**: Comprehensive error reporting and recovery

### Advanced Features
- **Dual Naming Methods**: Single column or combined format string naming
- **Interactive UI**: WPF-based naming convention builder with live preview
- **Parameter Validation**: Storage type checking and value conversion
- **Console Behavior**: Follows pyRevit console best practices (no output after commit)
- **Transaction Management**: Single transaction for efficient processing

## How to Use

### Step 1: Prepare Your CSV File

Create a CSV file with your family type data:

```csv
Type Plinth,Length,Width,Foundation Thickness (mm)
PLINTH 1,300,300,795
PLINTH 3,200,200,795
PLINTH 6,500,250,795
```

**Requirements:**
- First row must contain column headers
- Numeric values should be in millimeters (mm)
- Column names can contain spaces and special characters

### Step 2: Open Family Document

Open the Revit family file (.rfa) where you want to create the types.

### Step 3: Run the Tool

1. Navigate to **PrasKaaPyKit** → **Templates** → **Family** → **Family Type Generator**
2. Select your CSV file using the file dialog
3. Choose naming method when prompted

### Step 4: Choose Naming Method

**Option A: Single Column Naming**
- Select which CSV column contains the type names
- Simple and direct approach

**Option B: Combined Naming (Recommended)**
- Build custom format strings using column placeholders
- Example: `{Type Plinth} - {Length}x{Width}x{Foundation Thickness (mm)}mm`
- Interactive WPF builder with live preview

### Step 5: Parameter Matching

The tool automatically matches CSV columns to family parameters:
- **🎯 Exact Match**: Direct case-insensitive matching
- **🧹 Cleaned Match**: Ignores separators (spaces, underscores)
- **🔍 Partial Match**: Substring matching
- **📝 Word Match**: Word-based similarity

### Step 6: Processing

- Progress bar shows real-time processing
- Console displays detailed results for each type
- Summary shows total processed, successful, and failed counts

## Technical Architecture

### Core Classes

#### `FamilyTypeGenerator`
Main orchestrator class handling the complete workflow:
- CSV reading and validation
- User interaction for naming methods
- Parameter matching coordination
- Type creation with transaction management

#### `FlexibleParameterMatcher`
Implements multi-strategy parameter matching:
- Case-insensitive exact matching
- Fuzzy matching with separator cleaning
- Word-based similarity scoring
- Confidence level reporting

#### `TypeNameBuilderWindow`
WPF-based interactive naming builder:
- Double-click placeholder insertion
- Real-time preview of generated names
- Format string validation
- Crash-resistant error handling

#### `TypeNameGenerator`
Handles format string parsing and name generation:
- Placeholder replacement with CSV values
- Format validation
- Error handling for malformed strings

#### `CSVValidator`
Validates CSV structure and content:
- Header presence checking
- Data row validation
- Name column detection (for single column mode)

### Key Algorithms

#### Flexible Parameter Matching Algorithm
```python
# Multi-strategy matching hierarchy
1. Exact match (case-insensitive)
2. Cleaned match (remove separators)
3. Partial match (substring contains)
4. Word match (30%+ word overlap)
```

#### Format String Processing
```python
# Placeholder replacement
result = format_string
for header in csv_headers:
    placeholder = "{" + header + "}"
    value = str(csv_row.get(header, "")).strip()
    result = result.replace(placeholder, value)
```

### Dependencies

#### External Libraries
- **pyRevit**: Core framework and UI components
- **System.Windows.Forms**: File dialogs
- **System.Windows**: WPF for naming builder
- **csv**: Standard CSV processing
- **re**: Regular expressions for fuzzy matching

#### Internal Dependencies
- **unit_converter.py**: Unit conversion utilities
- **Parameter classification logic**: Type vs instance parameter handling

### Performance Characteristics

- **CSV Reading**: O(n) for n rows
- **Parameter Matching**: O(m*p) for m CSV headers, p family parameters
- **Type Creation**: O(t) for t types, with transaction batching
- **Memory Usage**: Low, processes rows sequentially
- **UI Responsiveness**: Real-time preview updates

## Configuration and Customization

### Parameter Mapping Configuration
The tool uses intelligent matching but can be extended with custom mapping rules in `parameter_mappings.json` format.

### Unit Conversion
Supports automatic conversion for LENGTH, WEIGHT, AREA, MOMENT, MODULUS parameters from millimeters to Revit internal units.

### Error Recovery
- Comprehensive try-catch blocks prevent Revit crashes
- Graceful degradation for WPF UI failures
- Detailed error reporting in console
- Transaction rollback on critical failures

## Troubleshooting

### Common Issues

#### "CSV file has no data rows"
- Check CSV file encoding (should be UTF-8)
- Ensure file is not empty
- Verify CSV delimiter (comma-separated)

#### "No parameters could be matched"
- Check family parameter names vs CSV headers
- Ensure parameters are type parameters (not instance)
- Verify parameter storage types are supported

#### WPF Window Crashes
- Tool includes crash-resistant error handling
- WPF operations wrapped in try-catch blocks
- Automatic fallback for UI failures

#### Parameter Setting Errors
- Check parameter storage types (Double, Integer, String)
- Verify unit conversions are appropriate
- Ensure parameters are not read-only

### Debug Information

Enable detailed logging by modifying the script's debug flags:
```python
DEBUG_MODE = True  # Shows detailed parameter processing
```

## Examples

### Basic Usage
```python
# Tool automatically handles:
# 1. CSV file selection
# 2. Naming method choice
# 3. Parameter matching
# 4. Type creation with progress
generator = FamilyTypeGenerator(family_doc)
generator.generate_types_from_csv(csv_path)
```

### Advanced Custom Naming
Format string: `{Type Plinth} - {Length}x{Width}x{Foundation Thickness (mm)}mm`
Results in names like: `PLINTH 1 - 300x300x795mm`

### Parameter Matching Results
```
✅ Matched Parameters (3):
🎯 Length → Length
🎯 Width → Width
🔍 Foundation Thickness (mm) → Foundation Thickness
```

## Integration with Logic Library

This tool demonstrates integration of multiple logic library components:

- **LOG-UTIL-PARAM-010**: Flexible CSV parameter matching
- **LOG-UTIL-UI-007**: WPF naming convention builder
- **LOG-UTIL-PARAM-006**: Parameter type classification
- **Console behavior patterns**: Transaction management

## Future Enhancements

### Planned Features
- Excel file support (.xlsx)
- Batch processing multiple CSV files
- Parameter mapping templates
- Advanced naming templates library
- IFC property mapping integration

### Potential Modifications
- Custom unit conversion rules
- Parameter validation rules
- Template-based family creation
- Integration with external databases

## Version History

- **v1.0**: Initial release with core CSV processing and parameter matching
- **v1.1**: Added WPF naming convention builder
- **v1.2**: Enhanced error handling and console behavior compliance

## Support and Contributing

For issues, feature requests, or contributions, please refer to the main PrasKaaPyKit documentation.

---

*Developed as part of PrasKaaPyKit Extension - Advanced BIM Tools for Revit*