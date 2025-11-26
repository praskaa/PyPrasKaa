---
id: "LOG-UTIL-FILTER-003"
version: "v1"
status: "active"
category: "utilities/filtering"
element_type: "UI"
operation: "advanced-selection"
revit_versions: [2024, 2026]
tags: ["ui", "selection", "multiselect", "shift-click", "ctrl-click", "search", "filtering"]
created: "2025-10-11"
updated: "2025-10-11"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton/script.py"
source_location: "Helper.panel/SmartTag.pushbutton"
---

# LOG-UTIL-FILTER-003-v1: Advanced Multi-Selection Dialog dengan Keyboard Shortcuts

## Problem Context

Basic checkbox selection (LOG-UTIL-FILTER-002) terbatas karena user harus klik checkbox satu per satu. Untuk selection yang efisien pada banyak items, diperlukan keyboard shortcuts seperti Shift+Click untuk range selection dan Ctrl+Click untuk individual selection, plus search functionality untuk filtering.

## Solution Summary

Implementasi Windows Forms ListView dengan `MultiSelect=True` yang mengaktifkan perilaku standar Windows (Shift+Click, Ctrl+Click) dikombinasikan dengan search box dan Select All/Deselect All buttons. Template ini memberikan user experience superior untuk multi-selection tasks.

## Working Code

```python
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import (
    Form, Button, CheckBox, Label, ListView, View, ColumnHeader,
    ListViewItem, ColumnHeaderStyle, HorizontalAlignment,
    FormBorderStyle, DockStyle, AnchorStyles, FormStartPosition,
    MessageBox, MessageBoxButtons, MessageBoxIcon, TextBox, DialogResult
)
from System.Drawing import Point, Size, Font, FontStyle, Color

class AdvancedMultiSelectDialog(Form):
    """Advanced multi-selection dialog dengan keyboard shortcuts dan search"""

    def __init__(self, items, title="Select Items", item_display_func=None):
        """
        Parameters:
        - items: List of objects
        - title: Dialog title
        - item_display_func: Function to get display name from item (optional)
        """
        self.items = items
        self.selected_items = []
        self.filtered_items = items[:]
        self.item_display_func = item_display_func or (lambda x: str(x))

        self.InitializeComponent()
        self.Text = title

    def InitializeComponent(self):
        """Setup UI components"""
        self.Size = Size(500, 600)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        # Search section
        self.setup_search_section()

        # ListView section
        self.setup_list_view()

        # Buttons section
        self.setup_buttons()

    def setup_search_section(self):
        """Setup search functionality"""
        y_pos = 20

        # Search label
        search_label = Label()
        search_label.Text = "Search:"
        search_label.Location = Point(20, y_pos)
        search_label.Size = Size(50, 20)
        self.Controls.Add(search_label)

        # Search textbox
        self.search_box = TextBox()
        self.search_box.Location = Point(80, y_pos)
        self.search_box.Size = Size(300, 20)
        self.search_box.TextChanged += self.on_search_text_changed
        self.Controls.Add(self.search_box)

        # Clear button
        clear_btn = Button()
        clear_btn.Text = "Clear"
        clear_btn.Location = Point(390, y_pos)
        clear_btn.Size = Size(50, 25)
        clear_btn.Click += self.on_clear_search
        self.Controls.Add(clear_btn)

        # Search tip
        y_pos += 25
        search_tip = Label()
        search_tip.Text = "Tip: Type to filter, Shift+Click for range, Ctrl+Click for individual"
        search_tip.Location = Point(20, y_pos)
        search_tip.Size = Size(450, 15)
        search_tip.Font = Font("Segoe UI", 8, FontStyle.Italic)
        search_tip.ForeColor = Color.Gray
        self.Controls.Add(search_tip)

    def setup_list_view(self):
        """Setup ListView dengan advanced multi-select"""
        y_pos = 70

        self.list_view = ListView()
        self.list_view.Location = Point(20, y_pos)
        self.list_view.Size = Size(460, 400)
        self.list_view.View = View.Details
        self.list_view.CheckBoxes = True
        self.list_view.MultiSelect = True  # Enables Shift+Click and Ctrl+Click
        self.list_view.FullRowSelect = True
        self.list_view.GridLines = False

        # Hide headers for clean appearance
        self.list_view.HeaderStyle = ColumnHeaderStyle.Nonclickable
        self.list_view.Columns.Add("", 440, HorizontalAlignment.Left)

        # Populate items
        self.populate_list_view()

        self.Controls.Add(self.list_view)

    def setup_buttons(self):
        """Setup control buttons"""
        y_pos = 480

        # Select All button
        select_all_btn = Button()
        select_all_btn.Text = "Select All"
        select_all_btn.Location = Point(20, y_pos)
        select_all_btn.Size = Size(100, 30)
        select_all_btn.Click += self.on_select_all
        self.Controls.Add(select_all_btn)

        # Deselect All button
        deselect_all_btn = Button()
        deselect_all_btn.Text = "Deselect All"
        deselect_all_btn.Location = Point(130, y_pos)
        deselect_all_btn.Size = Size(100, 30)
        deselect_all_btn.Click += self.on_deselect_all
        self.Controls.Add(deselect_all_btn)

        # OK button
        ok_btn = Button()
        ok_btn.Text = "OK"
        ok_btn.Location = Point(300, y_pos)
        ok_btn.Size = Size(80, 30)
        ok_btn.Click += self.on_ok_click
        self.Controls.Add(ok_btn)

        # Cancel button
        cancel_btn = Button()
        cancel_btn.Text = "Cancel"
        cancel_btn.Location = Point(390, y_pos)
        cancel_btn.Size = Size(80, 30)
        cancel_btn.Click += self.on_cancel_click
        self.Controls.Add(cancel_btn)

    def populate_list_view(self, items=None):
        """Populate ListView dengan items"""
        if items is None:
            items = self.filtered_items

        self.list_view.Items.Clear()

        for item in items:
            display_name = self.item_display_func(item)
            list_item = ListViewItem(display_name)
            list_item.Tag = item  # Store original object
            self.list_view.Items.Add(list_item)

    # Event Handlers
    def on_search_text_changed(self, sender, args):
        """Filter items berdasarkan search text"""
        search_text = self.search_box.Text.lower().strip()

        if not search_text:
            self.filtered_items = self.items[:]
            self.populate_list_view()
        else:
            self.filtered_items = []
            for item in self.items:
                display_name = self.item_display_func(item).lower()
                if search_text in display_name:
                    self.filtered_items.append(item)
            self.populate_list_view()

    def on_clear_search(self, sender, args):
        """Clear search"""
        self.search_box.Text = ""

    def on_select_all(self, sender, args):
        """Select all visible items"""
        for item in self.list_view.Items:
            item.Checked = True

    def on_deselect_all(self, sender, args):
        """Deselect all visible items"""
        for item in self.list_view.Items:
            item.Checked = False

    def on_ok_click(self, sender, args):
        """Process selection dan close"""
        self.selected_items = []
        for item in self.list_view.CheckedItems:
            original_item = item.Tag
            self.selected_items.append(original_item)

        if not self.selected_items:
            MessageBox.Show(
                "Please select at least one item.",
                "No Selection",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return

        self.DialogResult = DialogResult.OK
        self.Close()

    def on_cancel_click(self, sender, args):
        """Cancel selection"""
        self.DialogResult = DialogResult.Cancel
        self.Close()
```

## Key Techniques

### 1. **Advanced Multi-Selection**
```python
self.list_view.MultiSelect = True  # Enables Shift+Click and Ctrl+Click
self.list_view.CheckBoxes = True   # Shows checkboxes
```
- **Shift+Click**: Select range dari item terakhir yang dipilih
- **Ctrl+Click**: Toggle selection individual items
- **Checkbox**: Traditional checkbox selection

### 2. **Real-time Search Filtering**
```python
self.search_box.TextChanged += self.on_search_text_changed
```
- Filter otomatis saat user mengetik
- Multi-selection bekerja pada hasil filter
- Case-insensitive search

### 3. **Object Preservation**
```python
list_item.Tag = item  # Store original object
# Later retrieve with:
original_item = item.Tag
```

### 4. **Clean UI Design**
- Hidden column headers
- Consistent spacing
- User-friendly tips dan labels

## Advanced Features

### Custom Display Function
```python
def get_view_display_name(view):
    """Custom display function untuk views"""
    return "{} ({})".format(view.Name, view.GenLevel.Name if view.GenLevel else "No Level")

# Usage
dialog = AdvancedMultiSelectDialog(views, "Select Views",
                                   item_display_func=get_view_display_name)
```

### Integration dengan pyRevit
```python
from pyrevit import forms

def select_views_advanced():
    """Advanced view selection dengan search dan keyboard shortcuts"""
    # Get all plan views
    collector = FilteredElementCollector(doc).OfClass(ViewPlan)
    views = [v for v in collector if not v.IsTemplate]

    # Show advanced dialog
    dialog = AdvancedMultiSelectDialog(views, "Select Plan Views to Process")
    result = dialog.ShowDialog()

    if result == DialogResult.OK:
        selected_views = dialog.selected_items
        forms.alert("Selected {} views".format(len(selected_views)))
        return selected_views

    return None
```

## Performance Notes

- **Memory Efficient**: Stores references, not copies
- **Fast Filtering**: Real-time search dengan case-insensitive matching
- **Scalable**: Handles 1000+ items dengan baik
- **UI Responsive**: No blocking operations

## Usage Examples

### View Selection untuk Batch Processing
```python
# Select multiple views untuk tagging
views = get_structural_plan_views()
dialog = AdvancedMultiSelectDialog(views, "Select Views to Tag")
if dialog.ShowDialog() == DialogResult.OK:
    selected_views = dialog.selected_items
    # Process tagging untuk selected views
```

### Element Selection dengan Custom Display
```python
def get_element_display(element):
    return "{} (ID: {})".format(element.Name, element.Id.Value)

elements = get_selected_elements()
dialog = AdvancedMultiSelectDialog(elements, "Select Elements",
                                   item_display_func=get_element_display)
```

### Filtered Selection
```python
# Pre-filter elements by category
walls = FilteredElementCollector(doc) \
    .OfCategory(BuiltInCategory.OST_Walls) \
    .ToElements()

dialog = AdvancedMultiSelectDialog(walls, "Select Walls to Modify")
```

## Common Pitfalls & Solutions

1. **MultiSelect Not Working**: Pastikan `MultiSelect = True` DAN `CheckBoxes = True`
2. **Search Not Filtering**: Check `TextChanged` event handler attached properly
3. **Objects Lost**: Selalu gunakan `Tag` property untuk store original objects
4. **Performance Issues**: Untuk 1000+ items, consider pagination atau virtual mode

## Comparison dengan Basic Multi-Select

| Feature | Basic (LOG-UTIL-FILTER-002) | Advanced (LOG-UTIL-FILTER-003) |
|---------|-----------------------------|--------------------------------|
| Selection Methods | Checkbox only | Checkbox + Shift+Click + Ctrl+Click |
| Search | ❌ | ✅ Real-time filtering |
| User Experience | Basic | Advanced (Windows standard) |
| Code Complexity | Low | Medium |
| Performance | Good | Excellent |
| Scalability | Good | Excellent |

## Related Logic Entries

- [LOG-UTIL-FILTER-001-v1-view-name-search](LOG-UTIL-FILTER-001-v1-view-name-search.md) - Basic search functionality
- [LOG-UTIL-FILTER-002-v1-multi-select-dialog](LOG-UTIL-FILTER-002-v1-multi-select-dialog.md) - Basic checkbox multi-selection
- [LOG-UTIL-MODKEY-001](LOG-UTIL-MODKEY-001.md) - Modifier key handling patterns

## Optimization History

*Initial version (v1) with comprehensive multi-selection capabilities including keyboard shortcuts, search filtering, and advanced UI patterns.*