# Transfer Type Mark and Mark v2

## Overview

This is the migrated version of the Transfer Type Mark and Mark script, now using the modern ParameterSetting framework and WPF UI. It transfers Type Mark and Mark values from linked EXR model column type names to host Revit columns by geometry intersection matching.

## Key Improvements

### Framework Integration
- **ParameterSetting Framework**: Uses the standardized parameter setting framework for robust parameter operations
- **Fallback Support**: Automatically falls back to legacy methods if framework is unavailable
- **Error Handling**: Enhanced error reporting and validation

### UI Modernization
- **WPF Interface**: Modern Windows Presentation Foundation UI with better user experience
- **Fallback UI**: Windows Forms fallback for compatibility
- **Real-time Preview**: Live pattern testing and validation
- **Configuration Persistence**: Settings saved to JSON file

### Code Architecture
- **Modular Design**: Separated concerns with dedicated library module
- **Enhanced Logging**: Improved debug logging with multiple levels
- **Better Error Handling**: Comprehensive error tracking and reporting

## Features

- **Geometry-based Matching**: Uses solid intersection volumes for accurate column matching
- **Configurable Regex Patterns**: Flexible type name parsing with live validation
- **CSV Export**: Detailed results export with conflict and error reporting
- **Debug Modes**: Multiple debug levels for troubleshooting
- **Framework Detection**: Automatic detection and use of ParameterSetting framework

## Configuration

The script uses a JSON configuration file (`transfer_mark_config.json`) with the following options:

```json
{
  "type_mark_pattern": "^([A-Za-z]+)([\\d.]+)$",
  "mark_parameter_name": "Mark",
  "preview_examples": ["CAA1.1", "CBB2.5", "AAA10.15", "XYZ100.99"],
  "debug_mode": false,
  "csv_output_enabled": true
}
```

## Usage

1. **Configuration**: Click the button to open the configuration dialog
2. **Pattern Setup**: Configure the regex pattern for parsing type names
3. **Test Pattern**: Use the preview to validate your pattern against examples
4. **Save Settings**: Save configuration for future use
5. **Run Transfer**: Execute the mark transfer process

## Requirements

- **Revit 2018+**: Compatible with Revit 2018 and later versions
- **pyRevit**: Required for UI and Revit API integration
- **ParameterSetting Framework**: Recommended for enhanced parameter handling
- **Linked Model**: Requires a linked EXR model with structural columns

## Output

The script provides:
- **Console Output**: Detailed progress and results in pyRevit output window
- **CSV Export**: Comprehensive results file with all transfers, conflicts, and errors
- **Alert Dialog**: Summary of operation results

## Migration Notes

This version maintains full backward compatibility while adding modern features:
- Original functionality preserved
- Enhanced error handling and reporting
- Modern UI with fallback support
- Framework integration for future extensibility

## Troubleshooting

- **Framework Not Available**: Script automatically uses legacy methods
- **UI Issues**: WPF falls back to Windows Forms if needed
- **Pattern Errors**: Use the test function in configuration dialog
- **Debug Mode**: Enable debug logging for detailed operation information

## File Structure

```
TransferTypeMarkAndMark_v2.pushbutton/
├── bundle.yaml              # pyRevit bundle configuration
├── script.py                # Main execution script
├── lib.py                   # Configuration and UI library
├── icon.png                 # Button icon
├── transfer_mark_config.json # Configuration file (auto-generated)
└── README.md               # This documentation