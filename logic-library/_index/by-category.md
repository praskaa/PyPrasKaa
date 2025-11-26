# Logic Library - Organized by Category

## Structural Elements

### Columns
- [LOG-STRUCT-COL-001-v1-column-level-filtering](active/structural-elements/columns/LOG-STRUCT-COL-001-v1-column-level-filtering.md) - Level-based filtering for columns to prevent duplicate tags
- [LOG-STRUCT-COL-002-v1-geometry-intersection-matching](active/structural-elements/columns/LOG-STRUCT-COL-002-v1-geometry-intersection-matching.md) - Advanced geometry intersection matching with volume-based selection and comprehensive debug logging

### Walls
- [LOG-STRUCT-WALL-001-v1-wall-level-filtering](active/structural-elements/walls/LOG-STRUCT-WALL-001-v1-wall-level-filtering.md) - Level-based filtering for walls to prevent duplicate tags
- [LOG-STRUCT-WALL-002-v1-wall-orientation-guide](active/structural-elements/walls/LOG-STRUCT-WALL-002-v1-wall-orientation-guide.md) - Wall orientation detection using Wall.Orientation property for accurate tag positioning

### Beams
*Placeholder for beam-related patterns*

### Columns
*Placeholder for column-related patterns*

### Walls
*Placeholder for wall-related patterns*

### Foundations
*Placeholder for foundation-related patterns*

### Slabs
*Placeholder for slab-related patterns*

## Documentation

*No entries yet - awaiting documentation workflow patterns*

### Sheets
*Placeholder for sheet management patterns*

### Views
*Placeholder for view management patterns*

### Annotations
*Placeholder for annotation patterns*

## Utilities

### Output Management
- [pyrevit_console_behavior](pyrevit_console_behavior.md) - PyRevit console output behavior best practices and console splitting prevention

### Selection
- [LOG-UTIL-SELECTION-001-v1-smart-selection](active/utilities/selection/LOG-UTIL-SELECTION-001-v1-smart-selection.md) - Intelligent element selection with pre-selection support and category filtering

### Filtering
- [LOG-UTIL-FILTER-001-v1-view-name-search](active/utilities/filtering/LOG-UTIL-FILTER-001-v1-view-name-search.md) - Real-time view filtering with search box
- [LOG-UTIL-FILTER-002-v1-multi-select-dialog](active/utilities/filtering/LOG-UTIL-FILTER-002-v1-multi-select-dialog.md) - Multi-selection list with checkboxes
- [LOG-UTIL-FILTER-003-v1-advanced-multi-select-dialog](active/utilities/filtering/LOG-UTIL-FILTER-003-v1-advanced-multi-select-dialog.md) - Advanced multi-selection with keyboard shortcuts and search

### Parameters
- [LOG-UTIL-PARAM-001-v1-parameter-finder](active/utilities/parameters/LOG-UTIL-PARAM-001-v1-parameter-finder.py) - Parameter finding and type detection utilities for shared/project parameters
- [LOG-UTIL-PARAM-003-v1-configuration-management](active/utilities/parameters/LOG-UTIL-PARAM-003-v1-configuration-management.md) - Configuration management and persistence
- [LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching](active/utilities/parameters/LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching.md) - Flexible CSV header-to-parameter mapping with fuzzy matching
- [LOG-UTIL-PARAM-011-v1-family-type-parameter-access](active/utilities/parameters/LOG-UTIL-PARAM-011-v1-family-type-parameter-access.md) - Family type parameter access patterns using FamilyManager API

### Transactions
*Placeholder for transaction handling patterns*

### Error Handling
- [LOG-UTIL-ERROR-003-v1-modifier-key-handling](active/utilities/error-handling/LOG-UTIL-ERROR-003-v1-modifier-key-handling.md) - Shift/Ctrl+Click for different behaviors
- [LOG-UTIL-ERROR-004-v1-statistics-display](active/utilities/error-handling/LOG-UTIL-ERROR-004-v1-statistics-display.md) - Operation statistics and summary display

### UI
- [LOG-UTIL-UI-005-v1-simple-option-selection](active/utilities/ui/LOG-UTIL-UI-005-v1-simple-option-selection.md) - Simple option selection dengan pyRevit CommandSwitchWindow
- [LOG-UTIL-UI-006-v1-tag-type-access](active/utilities/ui/LOG-UTIL-UI-006-v1-tag-type-access.md) - Akses Family dan Type Tag dengan Format "Family: Type"
- [LOG-UTIL-UI-007-v1-wpf-interactive-builder-framework](active/utilities/ui/LOG-UTIL-UI-007-v1-wpf-naming-convention-builder.md) - Crash-resistant WPF windows for IronPython with modal behavior and error handling
- [LOG-UTIL-UI-008-v1-format-string-naming-generator](active/utilities/ui/LOG-UTIL-UI-008-v1-format-string-naming-generator.md) - Format string naming generation with placeholder replacement for structured names

### Modifier Keys
- [LOG-UTIL-MODKEY-001-v1-modifier-keys-detection](active/utilities/LOG-UTIL-MODKEY-001.md) - Modifier keys detection for multi-mode pyRevit buttons

---

## Current Status

**Active Entries: 19** (from Family Type Generator analysis + previous patterns)
- 1 Selection pattern
- 3 Filtering patterns
- 4 UI patterns (added WPF framework + naming generator)
- 2 Error Handling patterns
- 1 Modifier Keys pattern
- 2 Column patterns (level filtering + geometry intersection)
- 2 Wall filtering/orientation patterns
- 1 Configuration management pattern
- 2 Parameter patterns (CSV matching + family type access)
- 1 Console behavior pattern

**Placeholder Categories**: Structural Elements, Documentation, Parameters, Transactions
*These sections show planned organization structure. Actual entries will be added as patterns are identified and documented from working scripts.*

---

*This index is automatically updated when new entries are added.*