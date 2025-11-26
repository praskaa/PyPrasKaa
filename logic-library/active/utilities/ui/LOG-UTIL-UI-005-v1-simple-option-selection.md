---
id: "LOG-UTIL-UI-005"
version: "v1"
status: "active"
category: "utilities/ui"
element_type: "Selection"
operation: "option-selection"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["ui", "selection", "options", "command-switch", "forms", "simple-selection"]
created: "2025-10-11"
updated: "2025-10-11"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Modeling.panel/Column.pulldown/AutoDimensionColumn.pushbutton/script.py"
source_location: "Modeling.panel/Column.pulldown/AutoDimensionColumn.pushbutton"
---

# LOG-UTIL-UI-005-v1: Simple Option Selection dengan pyRevit CommandSwitchWindow

## Problem Context

Banyak skrip pyRevit memerlukan user untuk memilih dari beberapa opsi sederhana (seperti mode processing, tipe output, atau konfigurasi). Untuk kasus dimana hanya 1 pilihan yang diperlukan dan opsi terbatas, dibutuhkan pendekatan yang simple namun konsisten dengan pyRevit UI patterns.

## Solution Summary

Gunakan `forms.CommandSwitchWindow.show()` untuk selection opsi sederhana. Method ini menyediakan interface yang clean, konsisten dengan pyRevit, dan cocok untuk scenario dimana user perlu memilih 1 opsi dari beberapa alternatif.

## Working Code

### Basic Option Selection
```python
from pyrevit import forms

def select_processing_mode():
    """Pilih mode processing dengan CommandSwitchWindow"""
    selected_option = forms.CommandSwitchWindow.show(
        ['Current View Only', 'Batch Process All Views', 'Selected Views Only'],
        message='Select processing mode:'
    )

    if not selected_option:
        return None  # User canceled

    if selected_option == 'Current View Only':
        process_current_view()
    elif selected_option == 'Batch Process All Views':
        process_all_views()
    else:  # Selected Views Only
        process_selected_views()

    return selected_option
```

### Integration dengan Script Logic
```python
def run_auto_dimension():
    """Main function dengan option selection"""
    # Pilih mode processing
    processing_mode = forms.CommandSwitchWindow.show(
        ['Current View Only', 'Batch Process in Selected Plan Views'],
        message='Select processing mode:'
    )

    if not processing_mode:
        return  # User canceled

    # Load saved settings automatically
    config = ConfigurationManager()
    offset_mm = config.get_offset_mm()
    dim_type_name = config.get_dimension_type_name()

    # Process berdasarkan mode
    if processing_mode == 'Current View Only':
        process_current_view(offset_mm, dim_type_name)
    else:
        process_batch_views(offset_mm, dim_type_name)
```

## Key Techniques

### 1. **Simple Option Array**
```python
options = ['Option 1', 'Option 2', 'Option 3']
selected = forms.CommandSwitchWindow.show(options, message='Choose option:')
```

### 2. **Custom Message**
```python
selected = forms.CommandSwitchWindow.show(
    options,
    message='Select your preferred method:'
)
```

### 3. **Cancel Handling**
```python
selected = forms.CommandSwitchWindow.show(options, message='Choose:')
if not selected:
    return  # User pressed Cancel or closed dialog
```

### 4. **Direct Comparison**
```python
if selected == 'Option 1':
    execute_option_1()
elif selected == 'Option 2':
    execute_option_2()
```

## Advanced Features

### Conditional Options
```python
def get_available_options():
    """Return options based on context"""
    options = ['Basic Processing']

    # Add advanced options if user has permission
    if user_has_advanced_access():
        options.extend(['Advanced Processing', 'Custom Configuration'])

    return options

# Use dynamic options
selected = forms.CommandSwitchWindow.show(
    get_available_options(),
    message='Select processing level:'
)
```

### Option dengan Descriptions
```python
# Gunakan descriptive option names
processing_options = [
    'Quick Process (Current View)',
    'Full Process (All Plan Views)',
    'Custom Process (Manual Selection)'
]

selected = forms.CommandSwitchWindow.show(
    processing_options,
    message='Choose processing scope:'
)
```

## Comparison: Selection Method Matrix

| Method | Use Case | Selection Type | UI Complexity | Code Complexity | Features |
|--------|----------|----------------|----------------|-----------------|----------|
| **CommandSwitchWindow** | 1 option from 2-8 choices | Single choice | Simple | Minimal | Clean, consistent |
| **SelectFromList** | 1+ options from many items | Single/Multi | Basic list | Minimal | Basic filtering |
| **AdvancedMultiSelectDialog** | Complex selection from many items | Multi-select | Advanced | High | Search, shortcuts, pre-select |
| **Custom WPF Forms** | Complex workflows | Any | Custom | Very High | Full control |

## When to Use CommandSwitchWindow

### ✅ Recommended For:
- **2-8 simple options** (processing modes, output formats, etc.)
- **Single choice required** (user picks exactly one)
- **Quick decisions** (no complex filtering needed)
- **Consistent pyRevit UX** (matches other tools)
- **Minimal code** (fast implementation)

### ❌ Not Recommended For:
- **Many options** (>8 choices - use SelectFromList)
- **Complex selection** (search, ranges - use AdvancedMultiSelectDialog)
- **Multi-selection** (user picks multiple - use SelectFromList or Advanced)
- **Custom UI requirements** (build custom WPF form)

## Performance Notes

- **Execution Time**: Instant (< 0.1s)
- **Memory Usage**: Minimal (just option strings)
- **UI Responsiveness**: Immediate dialog display
- **Resource Impact**: None

## Usage Examples

### Processing Mode Selection
```python
def select_column_processing_mode():
    """Pilih mode processing untuk kolom"""
    return forms.CommandSwitchWindow.show(
        ['Current View Only', 'Batch Process in Selected Plan Views'],
        message='Select processing scope:'
    )
```

### Output Format Selection
```python
def select_export_format():
    """Pilih format export"""
    return forms.CommandSwitchWindow.show(
        ['PDF Export', 'DWG Export', 'Image Export'],
        message='Select export format:'
    )
```

### Configuration Mode
```python
def select_configuration_mode():
    """Pilih mode konfigurasi"""
    return forms.CommandSwitchWindow.show(
        ['Use Saved Settings', 'Configure New Settings', 'Reset to Defaults'],
        message='Configuration options:'
    )
```

## Common Pitfalls & Solutions

1. **Empty Options List**: Pastikan array options tidak kosong
   ```python
   if not options:
       forms.alert("No options available")
       return
   ```

2. **None Return Value**: Selalu check untuk None (user cancel)
   ```python
   selected = forms.CommandSwitchWindow.show(options)
   if selected is None:  # or just "if not selected:"
       return
   ```

3. **String Comparison**: Gunakan exact string matching
   ```python
   if selected == 'Exact Option Name':  # Case sensitive
   ```

## Related Logic Entries

- [LOG-UTIL-FILTER-001-v1-view-name-search](LOG-UTIL-FILTER-001-v1-view-name-search.md) - Basic search functionality
- [LOG-UTIL-FILTER-002-v1-multi-select-dialog](LOG-UTIL-FILTER-002-v1-multi-select-dialog.md) - Simple multi-selection
- [LOG-UTIL-FILTER-003-v1-advanced-multi-select-dialog](LOG-UTIL-FILTER-003-v1-advanced-multi-select-dialog.md) - Advanced multi-selection
- [LOG-UTIL-UI-001-v1-forms-integration](LOG-UTIL-UI-001-v1-forms-integration.md) - General forms usage

## Optimization History

*Initial version (v1) with comprehensive simple option selection patterns and method comparisons.*

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-11