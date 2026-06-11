# Dimension Text Override Find & Replace

A pyRevit tool to find and replace text patterns in dimension text overrides.

## Description

This tool allows you to search and replace text in dimension text overrides across your Revit project. It's particularly useful for batch updating dimension text patterns like changing "Leff=" to "Heff=".

## Features

- **Scope Selection**: Work on active view, selected dimensions, or entire document
- **Multiple Override Properties**: Searches in:
  - ValueOverride (complete value replacement)
  - Prefix (text before the value)
  - Suffix (text after the value)
  - Above (text above dimension line)
  - Below (text below dimension line)
- **Case Sensitivity**: Option for case-sensitive or case-insensitive search
- **Preview Mode**: See changes before applying
- **Progress Bar**: Visual feedback for large operations
- **Transaction Safety**: All changes are wrapped in a transaction with rollback on error

## Usage

1. Click the "Text Replace" button in the Dimension panel
2. Select the scope:
   - **Active View**: Search dimensions in the current view
   - **Selected Dimensions**: Search only selected dimensions
   - **Entire Document**: Search all dimensions in the project
3. Enter the text to FIND (e.g., `Leff=`)
4. Enter the text to REPLACE with (e.g., `Heff=`)
5. Choose whether the search should be case-sensitive
6. Preview the changes in the output window
7. Confirm to apply the changes

## Example

### Before
You have dimensions with override text:
- `Leff=180mm`
- `Leff=200mm`
- `Leff=250mm`

### Action
Find: `Leff=`  
Replace: `Heff=`

### After
- `Heff=180mm`
- `Heff=200mm`
- `Heff=250mm`

## Technical Details

### How Dimension Text Overrides Work

In Revit, dimensions can display custom text instead of (or in addition to) the measured value. This is done through dimension properties:

| Property | Description | Example |
|----------|-------------|---------|
| ValueOverride | Replaces the entire value | "Leff=180mm" |
| Prefix | Text before the value | "< " before value |
| Suffix | Text after the value | " mm" after value |
| Above | Text above dimension line | "Centerline" |
| Below | Text below dimension line | "Exact" |

### Requirements

- Revit 2020 or later
- pyRevit 4.8 or later

## Troubleshooting

### "No dimensions with text overrides found"

The tool only finds dimensions that have text overrides. If your dimensions are showing their actual measured values (no overrides), this tool won't find them.

To check if a dimension has an override:
1. Select the dimension
2. Check Properties panel
3. Look for Value Override, Prefix, or Suffix fields

### "Dimensions are read-only"

Some dimensions may be read-only due to:
- Worksharing (checked out by another user)
- In a linked model
- In a locked workset

The tool will skip these and continue with others.

## Version History

### v1.0.0 (2026-02-19)
- Initial release
- Basic find and replace functionality
- Support for all dimension override properties
- Preview mode
- Progress bar for large operations
