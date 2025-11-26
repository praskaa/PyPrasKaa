# Auto Load Missing Types

## Overview
This tool automatically loads missing families and creates missing types from a linked EXR model (from ETABS) into the host Revit model. It serves as a companion to the "Pre-run Matching Dimension" checker tool.

## Purpose
Before running the "Matching Dimension" tools (Column or Framing), all required family types must exist in the host model. This tool automates the process of loading missing families and creating missing types.

## How It Works

### 1. Family Loading
- Identifies families that exist in the linked model but not in the host model
- Loads entire families (including all their types) from the linked model
- Uses Revit's built-in family loading mechanism

### 2. Type Creation Guidance
- **Important Limitation**: Revit API does not support programmatic creation of new family types in project documents
- Identifies families and types that are missing
- Provides detailed instructions for manual type creation in Family Editor
- Lists exact type names and families that need manual intervention

## Workflow Integration

1. **Run "Pre-run Matching Dimension"** to identify missing types
2. **Run "Auto Load Missing Types"** to automatically load/create missing items
3. **Re-run "Pre-run Matching Dimension"** to verify all types are now available
4. **Proceed with "Matching Dimension" tools**

## Requirements

- Revit with pyRevit extension
- A linked EXR model from ETABS
- The linked model must contain loadable family files
- Host model should have basic structural families already loaded

## Limitations

- **Family Loading**: Requires the linked model to have access to the original family files
- **Type Creation**: Revit API does not support programmatic creation of new family types in project documents
- **Manual Intervention Required**: Missing types within existing families must be created manually in Family Editor
- **Parameter Copying**: Not applicable for type creation (manual process required)

## Error Handling

The tool provides detailed reporting of:
- Successfully loaded families
- Successfully created types
- Failed operations with specific error messages
- Recommendations for manual intervention if needed

## Output

Generates a comprehensive report showing:
- Summary of missing items found
- Results of family loading operations
- Results of type creation operations
- Next steps and recommendations