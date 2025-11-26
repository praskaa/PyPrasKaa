# PrasKaa UI Module

Reusable UI components untuk script-script pyRevit dengan konsistensi visual dan code reusability.

## 🎯 Purpose

Module ini menyediakan:
- **Visual Consistency**: Tema dan styling yang sama di semua dialog
- **Code Reusability**: Base classes dan utilities untuk common functionality
- **Easy Maintenance**: Centralized styling dan component management

## 📁 Structure

```
ui/
├── __init__.py                 # Module initialization
├── README.md                   # This file
├── base_window.py             # Base window classes
├── ui_styles.py               # Theme constants & styling
├── ui_items.py                # List item classes
├── ui_utils.py                # Utility functions
├── ui_styles.xaml             # Shared XAML styles
├── repository_ui.py           # Repository-specific UI
├── dialog_ui.py               # Dialog-specific UI
└── examples/                  # Usage examples
```

## 🚀 Quick Start

### Basic Usage
```python
from ui.base_window import BaseRevitWindow

class MyDialog(BaseRevitWindow):
    def __init__(self):
        BaseRevitWindow.__init__(self, "MyDialog.xaml", "My Dialog Title")
        self.setup_common_ui()
        # Your specific setup here
```

### Using Styled Components
```python
from ui.ui_utils import create_modern_button
from ui.ui_styles import DARK_BLUE_THEME

button = create_modern_button("Click Me", self.button_click)
button.Background = DARK_BLUE_THEME['accent_color']
```

### Repository UI
```python
from ui.repository_ui import FamilyRepositoryUI

class MyFamilyRepo(FamilyRepositoryUI):
    def __init__(self):
        FamilyRepositoryUI.__init__(self, "RepoUI.xaml", "My Family Repo")
        # Inherits all repository functionality
```

### Dialog UI
```python
from ui.dialog_ui import AlignViewportsUI

class MyAlignDialog(AlignViewportsUI):
    def __init__(self):
        AlignViewportsUI.__init__(self, "AlignUI.xaml", "Align My Viewports")
        # Inherits all dialog functionality
```

## 📖 Documentation

- [Base Window Classes](base_window.md)
- [Styling Guide](styling.md)
- [Component Library](components.md)
- [Migration Guide](migration.md)
- [Examples](examples/)

## 🎨 Theme & Styling

### Color Scheme
```python
DARK_BLUE_THEME = {
    "header_background": "#1E2A3B",
    "text_white": "#FFFFFF",
    "accent_color": "#2B5797",
    "warning_color": "#FF6B6B",
    "success_color": "#90EE90",
    # ... more colors
}
```

### XAML Integration
```xml
<Window.Resources>
    <ResourceDictionary>
        <ResourceDictionary.MergedDictionaries>
            <ResourceDictionary Source="pack://application:,,,/ui/ui_styles.xaml"/>
        </ResourceDictionary.MergedDictionaries>
    </ResourceDictionary>
</Window.Resources>
```

## 🏗️ Architecture

### Class Hierarchy
```
BaseRevitWindow
├── BaseRepositoryUI (bulk operations)
│   ├── FamilyRepositoryUI
│   └── ViewTemplateRepositoryUI
└── BaseDialogUI (single operations)
    ├── AlignViewportsUI
    └── BaseSettingsDialog
```

### Key Features

#### BaseRevitWindow
- ✅ Common window setup
- ✅ Event handlers (drag, close)
- ✅ Theme consistency
- ✅ UI element management

#### BaseRepositoryUI
- ✅ Item loading & filtering
- ✅ Bulk selection (all/none)
- ✅ Progress tracking
- ✅ Status management

#### BaseDialogUI
- ✅ Settings management
- ✅ Input validation
- ✅ State persistence
- ✅ Single operations

## 🔧 Utility Functions

### Button Factory
```python
from ui.ui_utils import create_modern_button

button = create_modern_button("Sync", self.sync_click, height=40)
```

### Item Creation
```python
from ui.ui_items import create_family_item

item = create_family_item(family, current_doc)
```

### Window Setup
```python
from ui.ui_utils import setup_window_properties

setup_window_properties(window, "My Title", width=600, height=700)
```

## 📋 Migration Guide

### From Old Scripts
```python
# OLD
class MyDialog(WPFWindow):
    def __init__(self):
        WPFWindow.__init__(self, xaml)
        self.Title = "Manual Setup"
        # Manual styling...

# NEW
class MyDialog(BaseRevitWindow):
    def __init__(self):
        BaseRevitWindow.__init__(self, xaml, "Auto Setup")
        # Inherits styling & setup
```

### Benefits
- ✅ 60% less code
- ✅ Consistent appearance
- ✅ Automatic theme updates
- ✅ Built-in error handling

## 🧪 Testing

### Unit Tests
```bash
# Run UI module tests
python -m pytest ui/tests/
```

### Integration Tests
```python
# Test in Revit environment
from ui import BaseRevitWindow

def test_basic_window():
    window = BaseRevitWindow("test.xaml", "Test")
    assert window.Title == "Test"
    assert window.Width == 600
```

## 📈 Performance

- **Memory**: Efficient WPF controls dengan virtualization
- **Loading**: Lazy loading untuk large datasets
- **Styling**: Shared resources minimize memory usage
- **Updates**: Incremental UI updates untuk responsiveness

## 🔒 Error Handling

- Graceful degradation untuk missing XAML elements
- Comprehensive logging untuk debugging
- User-friendly error messages
- Automatic recovery mechanisms

## 🚀 Future Enhancements

- [ ] Dark/Light theme switching
- [ ] Custom theme builder
- [ ] Advanced filtering options
- [ ] Drag & drop support
- [ ] Keyboard shortcuts
- [ ] Accessibility improvements

## 📞 Support

For issues or feature requests:
- Check [Examples](examples/) first
- Review [Migration Guide](migration.md)
- Create issue dengan code sample

---

**Version**: 1.0.0
**Author**: PrasKaa
**Last Updated**: 2025-01-20
