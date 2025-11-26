# Disable Filled Region Masking

This tool disables the masking property for selected filled region types, making them transparent instead of masking elements behind them.

## Problem Solved

By default, filled regions in Revit have masking enabled, which can hide elements and annotations behind them. This tool allows you to quickly disable masking for multiple filled region types at once.

## Features

- **Smart Selection**: Works with pre-selected filled region types or shows a selection dialog
- **Batch Processing**: Disable masking for multiple types simultaneously
- **Status Display**: Shows current masking status (MASKING/TRANSPARENT) in selection dialog
- **Selective Processing**: Only modifies types that actually have masking enabled

## Usage

1. **Pre-select filled region types** (optional): Select filled region types in the project browser
2. **Click the "Disable Filled Region Masking" button**
3. **If no types are selected**: Choose types from the dialog (shows masking status)
4. **Review results**: See which types were modified

## How It Works

The tool sets the `IsMasking` property of `FilledRegionType` to `False`, making the filled regions transparent instead of masking elements behind them.

## Requirements

- Revit 2025
- pyRevit
- IronPython 2.7

## Output

Shows a summary of:
- Types that had masking disabled
- Types that were already transparent
- Total counts of processed types

## Related Tools

- **Bake Hatch Color**: Creates new filled region types with baked colors from overrides
- Use this tool after "Bake Hatch Color" to ensure new types don't mask elements