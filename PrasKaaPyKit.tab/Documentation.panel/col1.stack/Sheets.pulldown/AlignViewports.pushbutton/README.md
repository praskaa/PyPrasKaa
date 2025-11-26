# Align Viewports Tool

## Overview
The Align Viewports tool is a powerful pyRevit script designed to automatically align viewports across multiple sheets in Autodesk Revit. It ensures consistent positioning of views while providing flexible options for crop boxes, title blocks, legends, and overlapping viewports.

## Problem Solved
When working with multiple sheets in Revit that should have consistent layouts (such as floor plans, elevations, or sections), manually aligning viewports across sheets is time-consuming and error-prone. This tool automates the alignment process while maintaining design intent.

## Key Features

### Core Functionality
- **Multi-sheet alignment**: Align viewports across multiple selected sheets
- **Main sheet reference**: Use one sheet as the reference for alignment
- **Automatic detection**: Intelligently identifies viewports, title blocks, and legends

### Advanced Options
- **Crop/Scope Box synchronization**: Apply the same crop or scope box settings
- **Title block matching**: Ensure consistent title block types across sheets
- **Legend alignment**: Align legends when they match between sheets
- **Viewport overlapping**: Support for multiple viewports with same scale

## Technical Implementation

### Architecture
The tool uses a modular architecture with separate classes for UI handling and sheet operations:

- `AlignViewportsUI`: Handles the WPF dialog interface
- `SheetObject`: Represents individual sheets with viewport management methods
- `AlignViewports`: Main orchestrator class combining UI and logic

### Key Classes and Methods

#### SheetObject Class
```python
class SheetObject():
    def __init__(self, sheet):
        # Initialize sheet properties and collect viewports

    def get_viewplans(self):
        # Extract ViewPlan viewports from sheet

    def align_viewports(self, MainSheet, apply_CropScopeBox=False, overlap=False):
        # Core alignment logic with crop box and overlap handling

    def ensure_titleblock_on_zero(self, MainSheet, apply_same=False):
        # Title block positioning and type matching

    def align_legend(self, MainSheet):
        # Legend alignment when names match
```

#### Alignment Process
1. **Sheet Selection**: User selects multiple sheets in Revit UI
2. **Main Sheet Validation**: Ensures main sheet has properly configured viewports
3. **Viewport Processing**: Temporarily hides elements for accurate alignment
4. **Position Synchronization**: Aligns viewport centers across sheets
5. **Optional Features**: Applies crop boxes, title blocks, and legends as configured

### Revit API Integration

#### Key API Calls
- `FilteredElementCollector`: For collecting viewports and elements
- `Transaction` and `TransactionGroup`: For atomic operations
- `TemporaryViewMode.TemporaryHideIsolate`: For element hiding during alignment
- `Viewport.SetBoxCenter()`: For viewport positioning
- `CropRegionShapeManager`: For crop box manipulation

#### Error Handling
- Comprehensive validation of sheet configurations
- Graceful handling of missing elements (title blocks, legends)
- Transaction rollback on errors
- User-friendly error messages

## Usage Workflow

### Basic Usage
1. Select multiple sheets in Revit Project Browser
2. Run the Align Viewports tool
3. Choose main reference sheet in the dialog
4. Configure optional settings (crop boxes, title blocks, etc.)
5. Click "Align Viewports" to execute

### Advanced Configuration
- **Apply same CropBox/ScopeBox**: Ensures consistent view extents
- **Overlap multiple ViewPlans**: Allows multiple viewports at same position
- **Align Legend**: Matches legend positions when names are identical
- **Apply same TitleBlock**: Standardizes title block types

## Performance Characteristics

### Execution Time
- **Typical**: 5-15 seconds for 5-10 sheets
- **Factors**: Number of sheets, viewport complexity, element count
- **Optimization**: Uses temporary hide mode to reduce visual updates

### Memory Usage
- **Minimal footprint**: Processes sheets sequentially
- **Cleanup**: Automatic restoration of temporary view modes
- **Batch processing**: Handles large numbers of sheets efficiently

## Compatibility

### Revit Versions
- **Tested**: Revit 2024, 2026
- **Requirements**: pyRevit framework
- **Dependencies**: Custom UI modules, Snippets library

### Limitations
- Requires at least 2 sheets for alignment
- Main sheet must have properly configured viewports
- Crop boxes must be activated on main sheet viewports
- Legends only align when names exactly match

## Code Quality Notes

### Error Handling
- Comprehensive try-catch blocks around API calls
- User-friendly error messages with actionable guidance
- Transaction rollback on critical failures

### Code Structure
- Clear separation of concerns (UI, logic, data)
- Consistent naming conventions
- Comprehensive docstrings
- Modular design for maintainability

## Optimization History

### Version v1.0 (Initial)
- Basic viewport alignment functionality
- Simple UI with checkbox options
- Core alignment algorithms

### Version v1.1 (Current)
- Enhanced error handling and validation
- Improved performance with temporary hide modes
- Better UI feedback and progress reporting
- Support for overlapping viewports

## Related Logic Patterns

### Cross-references
- **LOG-SHEET-FILTER-001**: Sheet filtering and selection
- **LOG-VIEWPORT-POSITION-002**: Viewport positioning logic
- **LOG-CROPBOX-MANAGER-003**: Crop box manipulation
- **LOG-TRANSACTION-MANAGER-004**: Transaction handling patterns

## Common Pitfalls

### Main Sheet Configuration
- Ensure main sheet has activated crop boxes
- Verify consistent scales for overlapping viewports
- Check title block positioning (should be at origin)

### Sheet Preparation
- All sheets should have similar viewport configurations
- Legends should have matching names for alignment
- Title blocks should be properly placed

### Performance Issues
- Large numbers of sheets may require batch processing
- Complex views with many elements benefit from temporary hiding
- Network drives may slow down operations

## Future Enhancements

### Planned Features
- **Coordinate transformation**: Support for linked model transformations
- **Advanced filtering**: Custom viewport selection criteria
- **Batch processing**: Improved handling of large sheet sets
- **Progress feedback**: Real-time alignment progress indicators

---

*This documentation was generated for the Align Viewports tool in the PrasKaaPyKit extension. For questions or contributions, please refer to the project documentation.*