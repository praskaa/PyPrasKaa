---
id: "LOG-UTIL-FILTER-001"
version: "v1"
status: "active"
category: "utilities/filtering"
element_type: "View"
operation: "filter"
revit_versions: [2024, 2026]
tags: ["ui", "search", "filtering", "listview", "real-time"]
created: "2025-10-10"
updated: "2025-10-10"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton/script.py"
source_location: "Helper.panel/SmartTag.pushbutton"
---

# LOG-UTIL-FILTER-001-v1: Real-Time View Name Search and Filtering

## Problem Context

When working with large Revit projects containing dozens or hundreds of views, users need an efficient way to find and select specific views for operations. Manual scrolling through long lists is time-consuming and error-prone. A search functionality that filters views in real-time as the user types provides a much better user experience.

## Solution Summary

This pattern implements a real-time search box that filters a ListView of views based on partial name matches. The search is case-insensitive and supports partial matching, allowing users to quickly find views by typing fragments like "L1" to find all Level 1 views or "struct" to find structural views.

## Working Code

```python
from System.Windows.Forms import TextBox, ListView, ListViewItem

class ViewFilterDialog(Form):
    def __init__(self, views):
        self.views = views
        self.filtered_views = views[:]  # Initialize with all views

        # Create search box
        self.search_box = TextBox()
        self.search_box.Location = Point(20, 20)
        self.search_box.Size = Size(200, 20)
        self.search_box.TextChanged += self.on_search_text_changed
        self.Controls.Add(self.search_box)

        # Create views list
        self.views_list = ListView()
        self.views_list.Location = Point(20, 50)
        self.views_list.Size = Size(440, 300)
        self.views_list.View = View.Details
        self.views_list.Columns.Add("", 420, HorizontalAlignment.Left)

        # Populate initial list
        self.populate_views_list(self.views)
        self.Controls.Add(self.views_list)

    def populate_views_list(self, views):
        """Populate the ListView with given views"""
        self.views_list.Items.Clear()
        for view in views:
            item = ListViewItem(view.Name)
            item.Tag = view  # Store view object
            self.views_list.Items.Add(item)

    def on_search_text_changed(self, sender, args):
        """Filter views based on search text with real-time updates"""
        search_text = self.search_box.Text.lower().strip()

        if not search_text:
            # Show all views when search is empty
            self.populate_views_list(self.views)
            self.filtered_views = self.views[:]
        else:
            # Filter views that contain the search text
            self.views_list.Items.Clear()
            self.filtered_views = []

            for view in self.views:
                view_name = view.Name.lower()
                if search_text in view_name:
                    item = ListViewItem(view.Name)
                    item.Tag = view
                    self.views_list.Items.Add(item)
                    self.filtered_views.append(view)
```

## Key Techniques

1. **Real-Time Filtering**: Uses the `TextChanged` event to filter immediately as the user types
2. **Case-Insensitive Search**: Converts both search text and view names to lowercase for matching
3. **Partial Matching**: Uses `in` operator for substring matching, allowing flexible search patterns
4. **ListView Management**: Properly clears and repopulates the ListView to show filtered results
5. **Data Preservation**: Maintains both the original view list and filtered list for different operations

## Revit API Compatibility

- **Element Access**: Uses standard `View.Name` property available in all Revit versions
- **UI Framework**: Uses Windows Forms which is stable across Revit 2024-2026
- **Event Handling**: Standard .NET event handling compatible with pyRevit

## Performance Notes

- **Execution Time**: < 0.1 seconds for typical project sizes (50-200 views)
- **Memory Usage**: Minimal - only stores references to existing view objects
- **Scalability**: Performs well with hundreds of views due to simple string operations

## Usage Examples

### Basic View Selection Dialog
```python
# Get all views in document
all_views = FilteredElementCollector(doc).OfClass(View).ToElements()

# Create filter dialog
dialog = ViewFilterDialog(all_views)
if dialog.ShowDialog() == DialogResult.OK:
    selected_views = [item.Tag for item in dialog.views_list.CheckedItems]
    # Process selected views...
```

### Integration with Multi-Selection
```python
# Combine with checkbox selection
self.views_list.CheckBoxes = True

# Get filtered and checked views
selected_views = []
for item in self.views_list.CheckedItems:
    if item.Tag in self.filtered_views:  # Ensure it's still in filtered list
        selected_views.append(item.Tag)
```

## Common Pitfalls

1. **Case Sensitivity**: Always convert to lowercase for user-friendly search
2. **Empty Search**: Handle empty search box by showing all items
3. **ListView Updates**: Clear the ListView before repopulating to avoid duplicates
4. **Tag Preservation**: Use the `Tag` property to store object references, not just display text

## Related Logic Entries

- [LOG-UTIL-FILTER-002-v1-multi-select-dialog](LOG-UTIL-FILTER-002-v1-multi-select-dialog.md) - Multi-selection with checkboxes
- [LOG-UTIL-FILTER-003-v1-element-category-filter](LOG-UTIL-FILTER-003-v1-element-category-filter.md) - Category-based element filtering

## Optimization History

*This is the initial version (v1) with no optimizations yet.*