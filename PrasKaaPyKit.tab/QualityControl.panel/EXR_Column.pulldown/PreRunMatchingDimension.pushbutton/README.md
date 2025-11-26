# Pre-run Matching Dimension

## Overview

**Pre-run Matching Dimension** is a pre-check tool for the **Matching Dimension** script. It verifies whether all beam and column types used in a linked EXR model (from ETABS) are available in the host Revit model before running the type transfer process.

## Purpose

This tool prevents failures during the **Matching Dimension** process by identifying missing family types upfront. The **Matching Dimension** tool will fail if target family types don't exist in the host document, so this pre-check ensures a smooth workflow.

## Process

1. **Select Linked EXR Model**: Choose the linked model from ETABS
2. **Collect Elements**: Gather all structural framing (beams) and structural columns from the linked model
3. **Extract Used Types**: Identify unique family and type combinations actually used by elements
4. **Check Host Model**: Verify which types are available in the host document
5. **Generate Report**: Display missing types with element counts and recommendations

## Output

The tool generates a comprehensive report in the pyRevit output console including:

- **Summary**: Total missing types, breakdown by category
- **Missing Beam Types Table**: Family Name, Type Name, Element Count
- **Missing Column Types Table**: Family Name, Type Name, Element Count
- **Recommendations**: Steps to resolve missing types

## Usage

1. Run this tool **before** using **Matching Dimension**
2. Select your linked EXR model from the dialog
3. Review the report for any missing types
4. Load required families into the host model if needed
5. Re-run the check to verify all types are available
6. Proceed with **Matching Dimension** when all types are present

## Requirements

- Revit environment with pyRevit extension
- A linked EXR model from ETABS containing beam and column elements
- Host model to check against

## Error Handling

- Alerts if no Revit links are found
- Alerts if selected link document cannot be accessed
- Continues processing even if some elements fail to provide type information
- Provides clear recommendations for resolving missing types

## Integration

This tool is designed to work seamlessly with the **Matching Dimension** tool in the same pyRevit panel. Use it as a preparatory step to ensure successful type transfers.

## Author

Cline

## Version

1.0.0