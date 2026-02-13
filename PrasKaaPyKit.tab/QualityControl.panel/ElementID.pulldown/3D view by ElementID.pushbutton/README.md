# 3D View by ElementID

Create a 3D isometric view and isolate specific elements by their Element ID.

## Description

This tool allows you to create a new 3D isometric view and isolate only the specified elements, hiding all other elements in the model. This is particularly useful for:

- Inspecting specific elements from error/warning lists
- Finding and reviewing problematic elements
- Focused element analysis
- Similar to Revit's "Isolate Warning" functionality

## Usage

1. Click the **3D view by ElementID** button in the Quality Control panel
2. A dialog will appear asking for Element IDs
3. Enter or paste the Element IDs (supports multiple formats - see below)
4. Click OK
5. A new 3D view will be created with only the specified elements visible

## Input Formats

The tool supports multiple input formats:

### Newline Separated
```
2687043
2687049
2687057
2687063
```

### Comma Separated
```
2687043, 2687049, 2687057, 2687063
```

### Space Separated
```
2687043 2687049 2687057 2687063
```

### Mixed
```
2687043,2687049 2687057
2687063
```

## Features

- **Auto-parsing**: Automatically detects and handles various input formats
- **Validation**: Checks if elements exist in the document
- **Warning System**: Alerts you if any specified Element IDs are not found
- **Unique Naming**: Automatically handles duplicate view names
- **Auto-focus**: Automatically activates the new view after creation

## How to Get Element IDs

### From Revit Warnings
1. Go to the Warnings panel in Revit
2. Right-click on a warning
3. Select "Show Related Elements" or similar option
4. Note the Element IDs from the warning details

### From Selection
1. Select an element in the model
2. Open the Properties panel
3. Look for the Element ID field

### From Export/Logs
Many BIM tools and exports include Element IDs in their output that can be copied and pasted.

## Example Workflow

1. Run a validation tool that reports problematic Element IDs
2. Copy the list of Element IDs from the output
3. Click "3D view by ElementID"
4. Paste the Element IDs
5. Review the isolated elements in the new 3D view

## Technical Details

- Creates a new **3D Isometric** view (not perspective)
- Uses Revit's `TemporaryHideIsolateMode` for element isolation
- Works with all element types (walls, floors, families, etc.)
- Compatible with Revit 2018-2026

## Requirements

- Active Revit document required
- Valid Element IDs that exist in the current document

## Version History

### v1.0 (2026-02-13)
- Initial release
- Support for multiple input formats
- Element validation and warning system

---

**Author**: PrasKaa Team  
**Version**: 1.0  
**Last Updated**: February 2026
