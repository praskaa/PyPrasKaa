# Quick Reference - pyRevit Logic Library

## Most Used Patterns

### View Management
- [LOG-UTIL-FILTER-001-v1-view-name-search](utilities/filtering/LOG-UTIL-FILTER-001-v1-view-name-search.md) - Real-time view filtering with search box
- [LOG-UTIL-FILTER-002-v1-multi-select-dialog](utilities/filtering/LOG-UTIL-FILTER-002-v1-multi-select-dialog.md) - Multi-selection list with checkboxes
- [LOG-UTIL-FILTER-003-v1-advanced-multi-select-dialog](utilities/filtering/LOG-UTIL-FILTER-003-v1-advanced-multi-select-dialog.md) - Advanced multi-selection with keyboard shortcuts

### Parameter Management
- [LOG-UTIL-PARAM-001-v1-parameter-finder](utilities/parameters/LOG-UTIL-PARAM-001-v1-parameter-finder.py) - Parameter finding and type detection utilities for shared/project parameters
- [LOG-UTIL-PARAM-003-v1-configuration-management](utilities/parameters/LOG-UTIL-PARAM-003-v1-configuration-management.md) - Configuration persistence and management
- [LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching](utilities/parameters/LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching.md) - Flexible CSV header-to-parameter mapping with fuzzy matching
- [LOG-UTIL-PARAM-011-v1-family-type-parameter-access](utilities/parameters/LOG-UTIL-PARAM-011-v1-family-type-parameter-access.md) - Family type parameter access patterns using FamilyManager API

### Output Management & Console Behavior
- [pyrevit_console_behavior](pyrevit_console_behavior.md) - PyRevit console output behavior best practices and console splitting prevention

### Selection & User Interface
- [LOG-UTIL-SELECTION-001-v1-smart-selection](utilities/selection/LOG-UTIL-SELECTION-001-v1-smart-selection.md) - Intelligent element selection with pre-selection support
- [LOG-UTIL-UI-005-v1-simple-option-selection](utilities/ui/LOG-UTIL-UI-005-v1-simple-option-selection.md) - Simple option selection dengan pyRevit CommandSwitchWindow
- [LOG-UTIL-UI-006-v1-tag-type-access](utilities/ui/LOG-UTIL-UI-006-v1-tag-type-access.md) - Akses Family dan Type Tag dengan Format "Family: Type"
- [LOG-UTIL-UI-007-v1-wpf-interactive-builder-framework](utilities/ui/LOG-UTIL-UI-007-v1-wpf-naming-convention-builder.md) - Crash-resistant WPF windows for IronPython with modal behavior
- [LOG-UTIL-UI-008-v1-format-string-naming-generator](utilities/ui/LOG-UTIL-UI-008-v1-format-string-naming-generator.md) - Format string naming generation with placeholder replacement
- [LOG-UTIL-MODKEY-001-v1-modifier-keys-detection](utilities/LOG-UTIL-MODKEY-001.md) - Modifier keys detection for multi-mode buttons
- [LOG-UTIL-ERROR-003-v1-modifier-key-handling](utilities/error-handling/LOG-UTIL-ERROR-003-v1-modifier-key-handling.md) - Shift/Ctrl+Click for different behaviors
- [LOG-UTIL-ERROR-004-v1-statistics-display](utilities/error-handling/LOG-UTIL-ERROR-004-v1-statistics-display.md) - User feedback with statistics

### Error Handling
- [LOG-UTIL-ERROR-001-v1-graceful-failures](utilities/error-handling/LOG-UTIL-ERROR-001-v1-graceful-failures.md) - Handling API failures gracefully
- [LOG-UTIL-ERROR-002-v1-user-messaging](utilities/error-handling/LOG-UTIL-ERROR-002-v1-user-messaging.md) - Clear error messages for users

## Performance Benchmarks

| Pattern | Execution Time | Memory Usage | Revit Compatibility |
|---------|---------------|--------------|-------------------|
| Console splitting prevention | Instant | Minimal | 2020+ |
| Smart selection | < 0.1s | Minimal | 2024-2026 |
| View filtering | < 0.1s | Minimal | 2024-2026 |
| Multi-selection UI | < 0.5s | Low | 2024-2026 |
| Advanced multi-selection | < 0.5s | Low | 2024-2026 |
| Parameter management | Instant | Low | 2024-2026 |
| Configuration persistence | < 0.1s | Low | 2024-2026 |
| Modifier key detection | Instant | Minimal | 2024-2026 |
| Statistics display | Instant | Low | 2024-2026 |
| Tag processing | 0.2-2.0s per view | Medium | 2024-2026 |
| Tag type access | < 0.1s | Minimal | 2024-2026 |
| Geometry extraction | 1-2s per 100 elements | Medium | 2020+ |
| Intersection matching | 0.5-1s per host column | Medium | 2020+ |
| CSV parameter matching | < 0.1s | Low | 2020+ |
| Family type parameter access | < 0.1s | Low | 2020+ |
| WPF window creation | 0.5-2.0s | Medium | 2020+ |
| Format string naming | Instant | Minimal | 2020+ |

## Common API Patterns

### FilteredElementCollector Usage
```python
# Get all structural framing in active view
framing = FilteredElementCollector(doc, active_view.Id) \
    .OfCategory(BuiltInCategory.OST_StructuralFraming) \
    .WhereElementIsNotElementType() \
    .ToElements()
```

### Transaction Handling
```python
with Transaction(doc, "Operation Name") as t:
    t.Start()
    # Your operations here
    t.Commit()
```

### Parameter Access
```python
# Safe parameter access with null checking
param = element.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM)
if param and not param.IsReadOnly:
    elevation = param.AsDouble()
```

## Quick Search Tips

- Use VS Code's Ctrl+Shift+F for full-text search
- Search for API method names (e.g., "FilteredElementCollector")
- Look for category names (e.g., "OST_StructuralFraming")
- Check tags for common operations (filtering, tagging, ui)

## Recent Additions

- [LOG-UTIL-PARAM-011-v1-family-type-parameter-access](utilities/parameters/LOG-UTIL-PARAM-011-v1-family-type-parameter-access.md) - Family type parameter access patterns using FamilyManager API
- [LOG-UTIL-UI-008-v1-format-string-naming-generator](utilities/ui/LOG-UTIL-UI-008-v1-format-string-naming-generator.md) - Format string naming generation with placeholder replacement
- [LOG-UTIL-UI-007-v1-wpf-interactive-builder-framework](utilities/ui/LOG-UTIL-UI-007-v1-wpf-naming-convention-builder.md) - Crash-resistant WPF windows for IronPython with modal behavior
- [LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching](utilities/parameters/LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching.md) - Flexible CSV header-to-parameter mapping with fuzzy matching
- [pyrevit_console_behavior](pyrevit_console_behavior.md) - PyRevit console output behavior best practices and console splitting prevention
- [LOG-UTIL-UI-006-v1-tag-type-access](utilities/ui/LOG-UTIL-UI-006-v1-tag-type-access.md) - Akses Family dan Type Tag dengan Format "Family: Type"
- [LOG-UTIL-SELECTION-001-v1-smart-selection](utilities/selection/LOG-UTIL-SELECTION-001-v1-smart-selection.md) - Intelligent element selection with pre-selection support
- [LOG-UTIL-FILTER-003-v1-advanced-multi-select-dialog](utilities/filtering/LOG-UTIL-FILTER-003-v1-advanced-multi-select-dialog.md) - Advanced multi-selection with keyboard shortcuts
- [LOG-UTIL-MODKEY-001-v1-modifier-keys-detection](utilities/LOG-UTIL-MODKEY-001.md) - Modifier keys detection for multi-mode buttons
- [LOG-STRUCT-COL-001-v1-column-level-filtering](structural-elements/columns/LOG-STRUCT-COL-001-v1-column-level-filtering.md) - Column level filtering logic
- [LOG-STRUCT-COL-002-v1-geometry-intersection-matching](structural-elements/columns/LOG-STRUCT-COL-002-v1-geometry-intersection-matching.md) - Advanced geometry intersection matching with volume-based selection
- [LOG-STRUCT-WALL-001-v1-wall-level-filtering](structural-elements/walls/LOG-STRUCT-WALL-001-v1-wall-level-filtering.md) - Wall level filtering logic
- [LOG-STRUCT-WALL-002-v1-wall-orientation-guide](structural-elements/walls/LOG-STRUCT-WALL-002-v1-wall-orientation-guide.md) - Wall orientation detection using Wall.Orientation property
- [LOG-UTIL-PARAM-003-v1-configuration-management](utilities/parameters/LOG-UTIL-PARAM-003-v1-configuration-management.md) - Configuration persistence

## Categories Overview

- **Structural Elements**: Beams, columns, walls, foundations, slabs
- **Documentation**: Sheets, views, annotations, schedules
- **Utilities**: Filtering, parameters, transactions, error handling

---

*Last updated: 2025-10-27*