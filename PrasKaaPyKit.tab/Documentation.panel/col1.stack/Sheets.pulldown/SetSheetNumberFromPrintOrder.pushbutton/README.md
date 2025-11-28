# Set Sheet Number from Print Order

This pyRevit script assigns sequential numbers to sheets based on their order in a selected Print Set (ViewSheetSet).

## Description

The script performs the following operations:

1. Retrieves all available Print Sets (ViewSheetSet) from the active Revit document
2. Prompts the user to select a Print Set from a list
3. Extracts the ordered list of views from the selected Print Set (representing the print order)
4. Prompts for a starting number for the sequential numbering (default: 1)
5. Iterates through the ordered views, filtering for ViewSheet elements
6. Sets the "Number" parameter of each sheet to its sequential position in the print order

## Usage

1. Click the script button in the pyRevit toolbar
2. Select a Print Set from the displayed list
3. Enter the starting number when prompted (press Enter for default 1)
4. The script will update the "Number" parameter for all eligible sheets

## Requirements

- Active Revit document with at least one Print Set defined
- Sheets must have a writable "Number" parameter (not read-only)
- pyRevit environment

## Compatibility

- Revit 2024 and 2026 (tested)
- Handles API changes across versions:
  - Revit 2025: Uses `OrderedViewList`
  - Revit 2026+: Uses `OrderedViewIds`
  - Fallback attributes: `OrderedViews`, `OrderedViewIdList`

## Parameters

- **Print Set Selection**: User chooses from available ViewSheetSets
- **Starting Number**: Integer value to begin numbering (default: 1)

## Behavior

- Only processes ViewSheet elements from the ordered list
- Skips non-sheet views automatically
- Skips sheets without a "Number" parameter
- Skips sheets with read-only "Number" parameter
- Handles different parameter storage types (Integer converts to int, others to string)
- Uses transaction for safe database modification
- Provides error handling with rollback on failure

## Output

The script updates sheet parameters silently. For reporting, uncomment the summary section in the script to display counts of updated, skipped (no parameter), and skipped (read-only) sheets.

## Error Handling

- Alerts if no Print Sets exist in the document
- Alerts if user cancels Print Set selection
- Alerts if the Print Set's API doesn't expose ordered view lists
- Rolls back transaction and alerts on any processing errors

## Notes

- The "Number" parameter is commonly used for sheet numbering in Revit
- Print order determines the sequence of sheets in PDF exports and printing
- This script helps maintain consistent sheet numbering that matches print order