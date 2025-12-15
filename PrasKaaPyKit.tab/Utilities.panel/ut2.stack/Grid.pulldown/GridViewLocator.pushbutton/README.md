# Grid View Locator

Find all views on sheets that contain specific grids to help identify where unwanted grids appear in documentation.

## Purpose

This tool helps users locate where specific grids are visible in sheet views. This is particularly useful when grids that should be hidden are appearing on sheets, allowing users to quickly identify which views need to be adjusted.

## How it Works

1. **Grid Selection**: Shows a multi-select dialog with all grids in the model
2. **View Discovery**: Scans all views placed on sheets to find where selected grids are visible
3. **Results Display**: Presents organized results showing sheet numbers, view names, and grid visibility

## Usage

1. Click the "Grid View Locator" button
2. Select one or more grids from the list (use Ctrl+click for multiple selection)
3. Click "Find Views" to search
4. Review the results showing where each selected grid appears on sheets

## Output Format

The results show:
- Grid name and ID
- Number of views where the grid appears
- Sheet number and name for each occurrence
- View name and type

## Technical Details

- Only checks views that are placed on sheets (ignores model views not on documentation)
- Uses `grid.IsHidden(view)` to determine visibility
- Compatible with Revit 2020-2026
- Follows PrasKaaPyKit architecture guidelines using lib imports

## Related Tools

- Grid utilities in the same pulldown menu
- View visibility management tools