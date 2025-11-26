# pyRevit Logic Library

A comprehensive collection of reusable code patterns and helper functions for structural BIM workflows in Autodesk Revit using pyRevit.

## Overview

This library serves as a knowledge base for proven solutions to common Revit API programming challenges. Each entry contains working code snippets, usage examples, performance metrics, and compatibility information for Revit 2024-2026.

## Structure

- **active/** - Current, recommended implementations
  - **structural-elements/** - Patterns for beams, columns, walls, foundations, slabs
  - **documentation/** - Sheet, view, and annotation workflows
  - **utilities/** - Filtering, parameters, transactions, error handling
- **deprecated/** - Superseded implementations (kept for reference)
- **sources/** - Original source files for reference
- **_index/** - Navigation and search indexes

## Quick Start

1. Browse by category using the index files
2. Search for specific patterns using VS Code's search
3. Copy-paste code snippets directly into your scripts
4. Check compatibility notes for your Revit version

## Contributing

When you develop new working solutions:

1. Extract reusable patterns from your scripts
2. Document them using the library format
3. Test on both Revit 2024 and 2026
4. Add to appropriate category folder

## File Naming Convention

`LOG-{CATEGORY}-{TYPE}-{NUMBER}-v{VERSION}-{DESCRIPTION}.md`

Examples:
- `LOG-UTIL-FILTER-001-v1-view-name-search.md`
- `LOG-STRUCT-BEAM-002-v1-tag-untagged-elements.md`

## Entry Format

Each entry follows a standardized markdown format with:
- YAML frontmatter with metadata
- Problem context and solution summary
- Working code with syntax highlighting
- Key techniques and API usage notes
- Performance metrics and compatibility info
- Usage examples and cross-references