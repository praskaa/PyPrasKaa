# Detail Item Parameter Lister

Lists all parameters of selected detail item instances with clean, organized formatting and type classification.

## Features

- **Robust Parameter Extraction**: Handles various storage types (Double, Integer, String, ElementId) with comprehensive error handling
- **Type Classification**: Automatically classifies parameters as Instance or Type parameters
- **Clean Output Format**: Displays parameters in organized markdown format with clear labeling
- **Error Reporting**: Shows extraction statistics and any errors encountered
- **Safe Element Access**: Gracefully handles missing or corrupted element data

## Usage

1. Select a Detail Item (Family Instance) or Detail Item Type (Family Symbol) in the model
2. Click the "Detail Item Parameter Lister" button
3. View the organized parameter list in the pyRevit output window

## Output Format

The script displays parameters in the following format with automatic unit conversion:

```
# Detail Item Parameter Lister
---

## Selected Detail Item Instance:
**Name:** Standard
**Category:** Detail Items
**Family:** Detail Penulangan Balok
**Type:** Standard
**Element ID:** [1559778](revit://element/1559778)

---

### Parameters:

**Instance Parameters:**
- **Area** (Instance Parameter): `0.02 mm` (Storage: Double)
- **Comments** (Instance Parameter): `<No Value>` (Storage: String)

**Type Parameters:**
- **Array Bot Additional 1.1** (Type Parameter): `2` (Storage: Integer)
- **B Width** (Type Parameter): `1.97 m` (Storage: Double)
- **Diameter Stirrup** (Type Parameter): `43 mm` (Storage: Double)
- **H Height** (Type Parameter): `3 m` (Storage: Double)
- **Clear Cover** (Type Parameter): `131 mm` (Storage: Double)

---

### Extraction Summary:
- **Total Parameters:** 150
- **Successfully Extracted:** 148
- **No Value:** 2
- **Failed:** 0
- **Success Rate:** 98.7%
```

## Unit Conversion

The script automatically converts length parameters from Revit internal units (feet) to metric units:

- **Small dimensions** (< 1000mm): Displayed in **millimeters (mm)**
- **Large dimensions** (≥ 1000mm): Displayed in **meters (m)**
- **Non-length parameters**: Displayed in original units

### Length Parameter Detection

Parameters are identified as length parameters if their names contain keywords like:
- length, width, height, depth, diameter, radius
- spacing, clear, cover, offset, distance, size
- location, position, coordinate, dimension

### Conversion Examples

| Original (feet) | Converted Display | Parameter Type |
|-----------------|-------------------|----------------|
| 0.019999 | 6.1 mm | Small dimension |
| 1.96850393701 | 1.97 m | B Width |
| 0.0426509186352 | 43 mm | Diameter |
| 2.95275590551 | 3 m | H Height |
| 0.131233595801 | 131 mm | Clear Cover |

## Technical Details

### Parameter Classification Logic

- **Instance Parameters**: Parameters that can vary per element instance
- **Type Parameters**: Parameters shared across all instances of the same type

### Error Handling

- **Definition.Name Access**: Falls back to parameter ID if name access fails
- **ElementId Resolution**: Safely resolves referenced elements with error handling
- **Storage Type Issues**: Handles unsupported storage types gracefully
- **Missing Values**: Clearly indicates parameters without values

### Performance

- Processes parameters individually to avoid batch failures
- Caches parameter information to reduce repeated API calls
- Provides detailed extraction statistics for monitoring

## Dependencies

- Revit API (Autodesk.Revit.DB, Autodesk.Revit.UI)
- pyRevit (revit, forms, script, output)

## Error Scenarios Handled

1. **Corrupted Parameter Definitions**: Uses fallback naming strategies
2. **Deleted Referenced Elements**: Shows "<Element Not Found>" for invalid ElementIds
3. **Unsupported Storage Types**: Reports unsupported types without crashing
4. **Access Permission Issues**: Gracefully handles read-only or inaccessible parameters
5. **Null/Missing Values**: Clearly indicates parameters without values

## Related Scripts

- **Detail Item Inspector**: Interactive parameter inspection and editing
- **Parameter Finder**: Advanced parameter search and filtering utilities

## Version History

- **v1.0**: Initial implementation with robust parameter extraction and classification