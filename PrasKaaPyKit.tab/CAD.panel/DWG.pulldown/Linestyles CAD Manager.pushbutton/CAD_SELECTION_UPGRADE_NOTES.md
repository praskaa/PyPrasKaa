# Catatan Upgrade CADSelectionForm ke Advanced Multi-Select

## Overview
Dokumentasi ini berisi panduan untuk upgrade `CADSelectionForm` di script `Linestyles CAD Manager` dari basic ListView ke Advanced Multi-Select dengan keyboard shortcuts, konsisten dengan SmartTag experience.

## Masalah yang Diatasi
- ❌ Tidak ada Shift+Click/Ctrl+Click untuk keyboard shortcuts
- ❌ Tidak ada search functionality
- ❌ User experience tidak konsisten dengan SmartTag
- ❌ Manual checkbox clicking untuk banyak CAD files

## Solusi: AdvancedCADSelectionForm

### 1. Import yang Diperlukan
Tambahkan import berikut di awal script:

```python
# Existing imports...
from System.Windows.Forms import (
    Form, Button, ListView, View, ColumnHeader,
    ListViewItem, ColumnHeaderStyle, HorizontalAlignment,
    FormBorderStyle, DockStyle, AnchorStyles, FormStartPosition,
    MessageBox, MessageBoxButtons, MessageBoxIcon, TextBox, DialogResult
)
from System.Drawing import Point, Size, Font, FontStyle, Color
from System.ComponentModel import BindingList
```

### 2. Ganti CADSelectionForm dengan AdvancedCADSelectionForm

```python
class AdvancedCADSelectionForm(Form):
    """Advanced CAD file selection dengan keyboard shortcuts dan search"""

    def __init__(self, linked_cad_files):
        self.linked_cad_files = linked_cad_files
        self.selected_cad_files = []

        self.InitializeComponent()
        self.Text = "Step 1: Select Linked CAD Files (Advanced)"

    def InitializeComponent(self):
        """Setup UI components dengan advanced features"""
        self.Size = Size(550, 650)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        # Search section
        self.setup_search_section()

        # ListView section dengan advanced multi-select
        self.setup_list_view()

        # Buttons section
        self.setup_buttons()

    def setup_search_section(self):
        """Setup search functionality"""
        y_pos = 20

        # Search label
        search_label = Label()
        search_label.Text = "Search CAD files:"
        search_label.Location = Point(20, y_pos)
        search_label.Size = Size(120, 20)
        self.Controls.Add(search_label)

        # Search textbox
        self.search_box = TextBox()
        self.search_box.Location = Point(140, y_pos)
        self.search_box.Size = Size(300, 20)
        self.search_box.TextChanged += self.on_search_text_changed
        self.Controls.Add(self.search_box)

        # Clear button
        clear_btn = Button()
        clear_btn.Text = "Clear"
        clear_btn.Location = Point(450, y_pos)
        clear_btn.Size = Size(50, 25)
        clear_btn.Click += self.on_clear_search
        self.Controls.Add(clear_btn)

        # Search tip
        y_pos += 25
        search_tip = Label()
        search_tip.Text = "Tip: Type CAD name or path. Use Shift+Click for range, Ctrl+Click for individual"
        search_tip.Location = Point(20, y_pos)
        search_tip.Size = Size(500, 15)
        search_tip.Font = Font("Segoe UI", 8, FontStyle.Italic)
        search_tip.ForeColor = Color.Gray
        self.Controls.Add(search_tip)

    def setup_list_view(self):
        """Setup ListView dengan advanced multi-select"""
        y_pos = 70

        self.list_view = ListView()
        self.list_view.Location = Point(20, y_pos)
        self.list_view.Size = Size(510, 450)
        self.list_view.View = View.Details
        self.list_view.CheckBoxes = True
        self.list_view.MultiSelect = True  # Enables Shift+Click and Ctrl+Click
        self.list_view.FullRowSelect = True
        self.list_view.GridLines = False

        # Hide headers for clean appearance
        self.list_view.HeaderStyle = ColumnHeaderStyle.Nonclickable
        self.list_view.Columns.Add("", 490, HorizontalAlignment.Left)

        # Populate items
        self.populate_list_view()

        self.Controls.Add(self.list_view)

    def setup_buttons(self):
        """Setup control buttons"""
        y_pos = 530

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

        # Next button
        next_btn = Button()
        next_btn.Text = "Next →"
        next_btn.Location = Point(350, y_pos)
        next_btn.Size = Size(80, 30)
        next_btn.Click += self.on_next_click
        self.Controls.Add(next_btn)

        # Cancel button
        cancel_btn = Button()
        cancel_btn.Text = "Cancel"
        cancel_btn.Location = Point(440, y_pos)
        cancel_btn.Size = Size(80, 30)
        cancel_btn.Click += self.on_cancel_click
        self.Controls.Add(cancel_btn)

    def populate_list_view(self, cad_files=None):
        """Populate ListView dengan CAD files"""
        if cad_files is None:
            cad_files = self.linked_cad_files

        self.list_view.Items.Clear()

        for cad_file in cad_files:
            # Custom display: Name + file path preview
            display_name = "{} ({})".format(
                cad_file.name,
                cad_file.file_path.split('\\')[-1] if len(cad_file.file_path.split('\\')) > 1 else "No path"
            )

            list_item = ListViewItem(display_name)
            list_item.Tag = cad_file  # Store original object
            self.list_view.Items.Add(list_item)

    # Event Handlers
    def on_search_text_changed(self, sender, args):
        """Filter CAD files berdasarkan search text"""
        search_text = self.search_box.Text.lower().strip()

        if not search_text:
            self.populate_list_view(self.linked_cad_files)
        else:
            filtered_files = []
            for cad_file in self.linked_cad_files:
                # Search in name and file path
                name_match = search_text in cad_file.name.lower()
                path_match = search_text in cad_file.file_path.lower()

                if name_match or path_match:
                    filtered_files.append(cad_file)

            self.populate_list_view(filtered_files)

    def on_clear_search(self, sender, args):
        """Clear search"""
        self.search_box.Text = ""

    def on_select_all(self, sender, args):
        """Select all visible CAD files"""
        for item in self.list_view.Items:
            item.Checked = True

    def on_deselect_all(self, sender, args):
        """Deselect all visible CAD files"""
        for item in self.list_view.Items:
            item.Checked = False

    def on_next_click(self, sender, args):
        """Process selection dan continue"""
        self.selected_cad_files = []
        for item in self.list_view.CheckedItems:
            cad_file = item.Tag
            cad_file.selected = True  # Update original object
            self.selected_cad_files.append(cad_file)

        if not self.selected_cad_files:
            MessageBox.Show(
                "Please select at least one CAD file to continue.",
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

### 3. Update Main Function

Ganti pemanggilan `CADSelectionForm` dengan `AdvancedCADSelectionForm`:

```python
# OLD CODE:
# selection_form = CADSelectionForm(all_linked_cad_files)

# NEW CODE:
selection_form = AdvancedCADSelectionForm(all_linked_cad_files)
```

Dan update bagian yang menggunakan hasil selection:

```python
# OLD CODE: Check individual .selected property
# layers = get_layers_from_selected_cads(all_linked_cad_files)

# NEW CODE: Use selected_cad_files property
layers = get_layers_from_selected_cads(selection_form.selected_cad_files)
```

## Keuntungan Upgrade

### ✅ Keyboard Shortcuts
- **Shift+Click**: Select range dari CAD files
- **Ctrl+Click**: Toggle individual CAD files
- **Checkbox**: Traditional selection

### ✅ Real-time Search
- Search di CAD file name dan path
- Filter otomatis saat mengetik
- Case-insensitive

### ✅ Enhanced Display
- Tampilkan nama CAD + file path preview
- Lebih informatif untuk user

### ✅ Better UX
- Tooltips dan hints yang jelas
- Consistent dengan SmartTag experience
- Select All/Deselect All buttons

### ✅ Performance
- Handles 100+ CAD files dengan baik
- Memory efficient
- Fast filtering

## Testing Checklist

- [ ] Shift+Click selects range correctly
- [ ] Ctrl+Click toggles individual items
- [ ] Search filters by name and path
- [ ] Select All/Deselect All works
- [ ] Integration dengan existing workflow
- [ ] Error handling untuk edge cases
- [ ] Performance dengan 50+ CAD files

## File yang Perlu Dimodifikasi

1. **script.py** - Ganti class dan update main function
2. **Test thoroughly** dengan berbagai skenario selection

## Backup Plan

Sebelum implementasi:
1. Backup script.py original
2. Test dengan project yang memiliki banyak CAD files
3. Verify integration dengan EnhancedLayerManagerForm

## Future Enhancements

- [ ] Add sorting by name/path
- [ ] Add column for file size/modified date
- [ ] Add preview of CAD file contents
- [ ] Add drag-drop reordering
- [ ] Add export/import selection presets

---

*Catatan ini dibuat untuk pengembangan lebih lanjut script CAD Manager. Implementasi ini akan meningkatkan user experience secara signifikan dengan konsistensi yang lebih baik dengan SmartTag.*