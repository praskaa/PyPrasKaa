# Bake Hatch Color

This tool creates new Filled Region types with colors "baked" into the type definition instead of using instance-level overrides.

## Problem Solved

In Revit, filled regions (hatches) often have their colors overridden at the instance level in specific views. This makes it difficult to maintain consistent appearance across different views or projects. This tool allows you to convert those instance overrides into proper type-level color definitions.

## How It Works

1. **Select filled regions** that have color overrides applied
2. **Analyze overrides** in the current view to extract the overridden colors
3. **Create new types** by duplicating existing types and setting the color at the type level
4. **Optionally apply** the new types to the selected elements

## Features

- **Batch processing**: Select multiple filled regions with different override colors
- **Smart grouping**: Automatically groups elements by their override colors
- **Unique naming**: Generates unique type names with automatic numbering
- **Validation**: Skips elements without overrides or with overrides matching type colors
- **User feedback**: Detailed progress reporting and summaries
- **Optional application**: Choose whether to apply new types to selected elements

## Usage

1. **Select filled regions** (optional): If you have filled regions with color overrides already selected, the tool will use them. Otherwise, it will prompt you to select filled regions using a filtered selection that only allows filled regions.
2. **Click the "Bake Hatch Color" button**
3. **Review the analysis** of selected elements and color groups
4. **Enter a prefix name** for the new types (automatically numbered)
5. **Choose whether to apply** the new types to the selected elements

## Smart Selection

The tool includes intelligent selection handling:
- **Pre-selected elements**: If filled regions are already selected, validates and uses them
- **Interactive selection**: If no filled regions are selected, prompts user to select them with filtering (only filled regions can be selected)
- **Mixed selection handling**: Processes valid filled regions while skipping invalid elements

## Requirements

- Revit 2025
- pyRevit
- IronPython 2.7

## Output

The tool provides detailed feedback including:
- Number of elements processed
- Colors found and grouped
- Types created with their properties
- Summary of operations performed

## Author

PrasKaa Team