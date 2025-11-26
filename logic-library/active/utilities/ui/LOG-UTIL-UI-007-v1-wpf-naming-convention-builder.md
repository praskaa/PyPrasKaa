---
id: "LOG-UTIL-UI-007"
version: "v1"
status: "active"
category: "utilities/ui"
element_type: "UI"
operation: "naming_builder"
revit_versions: [2020, 2021, 2022, 2023, 2024, 2026]
tags: ["ui", "wpf", "naming", "format_string", "csv", "family_types", "interactive", "preview"]
created: "2025-10-27"
updated: "2025-10-27"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Templates.panel/Family.pulldown/FamilyTypeGenerator.pushbutton/script.py"
source_location: "Templates.panel/Family.pulldown/FamilyTypeGenerator.pushbutton"
---

# LOG-UTIL-UI-007-v1: WPF Interactive Builder Framework (Crash-Resistant WPF Windows for IronPython)

## Problem Context

Dalam pengembangan berbagai script pyRevit, sering diperlukan WPF windows yang interaktif namun stabil di IronPython environment. Tantangan utama adalah:

1. **Crash Prevention**: WPF controls di IronPython sangat rentan crash Revit
2. **Error Handling**: Event handlers dan UI updates sering gagal tanpa warning
3. **Resource Management**: Temp files dan memory cleanup untuk XAML
4. **Modal Behavior**: Proper window lifecycle management

Dari Family Type Generator, framework ini berhasil menangani WPF window dengan double-click events, real-time text updates, dan DataGrid refresh tanpa crash.

## Solution Summary

Implementasi WPF window interaktif untuk building format string dengan double-click placeholder insertion, real-time preview, dan error handling komprehensif untuk IronPython environment.

## Working Code

### Type Name Builder WPF Window

```python
class TypeNameBuilderWindow(forms.WPFWindow):
    """WPF Window for building type name format strings"""

    def __init__(self, xaml_file_name, csv_headers, csv_rows):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self.csv_headers = csv_headers
        self.csv_rows = csv_rows[:10]  # Preview first 10 rows
        self.name_generator = TypeNameGenerator(csv_headers)
        self.preview_items = []
        self._setup_placeholders()
        self._setup_preview()

    def _setup_placeholders(self):
        """Setup available placeholders in UI"""
        placeholders = self.name_generator.get_available_placeholders()
        self.placeholders_lb.ItemsSource = placeholders

    def _setup_preview(self):
        """Setup initial preview"""
        self._refresh_preview()

    def _refresh_preview(self):
        """Refresh preview with current format string"""
        try:
            self.preview_items = []

            for row in self.csv_rows:
                generated_name = self.name_generator.generate_name(row)
                original_name = row.get('Name', row.get('Type', ''))
                preview_item = TypeNamePreviewItem(row, generated_name, original_name)
                self.preview_items.append(preview_item)

            self.preview_dg.ItemsSource = self.preview_items
            self._refresh_preview_grid()
        except Exception as e:
            # Ignore preview refresh errors to prevent crashes
            pass

    def _refresh_preview_grid(self):
        """Refresh the preview DataGrid"""
        try:
            if hasattr(self, 'preview_dg'):
                self.preview_dg.Items.Refresh()
        except:
            pass  # Ignore DataGrid refresh errors

    def on_placeholder_double_click(self, sender, args):
        """Handle placeholder double-click to insert into format string"""
        try:
            if self.placeholders_lb.SelectedItem:
                placeholder = self.placeholders_lb.SelectedItem
                current_text = self.format_tb.Text or ""
                self.format_tb.Text = current_text + placeholder
        except Exception as e:
            # Ignore double-click errors to prevent crashes
            pass

    def on_format_text_changed(self, sender, args):
        """Handle format string text changes"""
        try:
            self.name_generator.set_format_string(self.format_tb.Text)
            self._refresh_preview()

            # Validate format string
            is_valid, message = self.name_generator.validate_format_string()
            self.validation_tb.Text = ("✅ " if is_valid else "❌ ") + message
        except Exception as e:
            self.validation_tb.Text = "❌ Error: {}".format(str(e))

    def on_apply_format(self, sender, args):
        """Apply the format string and close window"""
        try:
            is_valid, message = self.name_generator.validate_format_string()
            if is_valid:
                self.format_string = self.format_tb.Text
                self.Close()
            else:
                forms.alert(message, title="Invalid Format")
        except Exception as e:
            forms.alert("Error applying format: {}".format(str(e)), title="Error")

    def on_cancel(self, sender, args):
        """Cancel and close window"""
        try:
            self.format_string = None
            self.Close()
        except Exception as e:
            # Force close if normal close fails
            pass
```

### XAML Template for WPF Window

```xml
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Type Name Builder"
        Height="500" Width="700" MinHeight="400" MinWidth="600"
        ShowInTaskbar="False"
        ResizeMode="CanResizeWithGrip"
        WindowStartupLocation="CenterScreen"
        HorizontalContentAlignment="Center">
    <DockPanel Margin="10">
        <StackPanel DockPanel.Dock="Top">
            <TextBlock FontSize="14" Margin="0,0,0,10">
                Build a custom format for type names using column placeholders
            </TextBlock>
            <Border Background="#f0f0f0" CornerRadius="3" Padding="10" Margin="0,0,0,10">
                <TextBlock TextWrapping="Wrap">
                    <Bold>How to use:</Bold>
                    <LineBreak />
                    1. Double-click column names below to insert placeholders
                    <LineBreak />
                    2. Build your format string (e.g., "{Type Plinth} - {Length}x{Width}x{Foundation Thickness (mm)}")
                    <LineBreak />
                    3. Preview shows how names will be generated
                </TextBlock>
            </Border>
            <DockPanel Margin="0,10,0,0">
                <TextBlock FontSize="14" Margin="0,0,10,0" Width="120" DockPanel.Dock="Left" VerticalAlignment="Center">Format String:</TextBlock>
                <TextBox x:Name="format_tb"
                         Height="24"
                         FontSize="14" FontFamily="Courier New"
                         VerticalAlignment="Center"
                         TextChanged="on_format_text_changed"/>
            </DockPanel>
            <TextBlock x:Name="validation_tb"
                       Margin="0,5,0,0"
                       FontSize="12"
                       Foreground="{x:Static SystemColors.GrayTextBrush}"
                       Text="Enter a format string to see validation"/>
        </StackPanel>

        <Grid DockPanel.Dock="Bottom" Margin="0,10,0,0">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*" />
                <ColumnDefinition Width="*" />
            </Grid.ColumnDefinitions>
            <Button x:Name="cancel_b"
                    Margin="5,0,0,0"
                    Grid.Column="0" Grid.Row="0"
                    Height="24"
                    Content="Cancel"
                    Click="on_cancel"/>
            <Button x:Name="apply_b"
                    Margin="0,0,5,0"
                    Grid.Column="1" Grid.Row="0"
                    Height="24"
                    Content="Apply Format"
                    Click="on_apply_format"/>
        </Grid>

        <Grid Margin="0,10,0,0">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="200" />
                <ColumnDefinition Width="*" />
            </Grid.ColumnDefinitions>

            <GroupBox Header="Available Columns" Grid.Column="0" Margin="0,0,10,0">
                <ListBox x:Name="placeholders_lb"
                         MouseDoubleClick="on_placeholder_double_click">
                    <ListBox.ItemTemplate>
                        <DataTemplate>
                            <TextBlock Text="{Binding}" FontFamily="Courier New" />
                        </DataTemplate>
                    </ListBox.ItemTemplate>
                </ListBox>
            </GroupBox>

            <GroupBox Header="Preview (First 10 Rows)" Grid.Column="1">
                <DataGrid x:Name="preview_dg"
                          AutoGenerateColumns="False"
                          CanUserSortColumns="False"
                          IsReadOnly="True">
                    <DataGrid.Columns>
                        <DataGridTextColumn Header="Generated Name"
                                           Binding="{Binding generated_name}"
                                           MinWidth="100" Width="*" />
                        <DataGridTextColumn Header="Original Name"
                                           Binding="{Binding original_name}"
                                           MinWidth="100" Width="*" />
                    </DataGrid.Columns>
                </DataGrid>
            </GroupBox>
        </Grid>
    </DockPanel>
</Window>
```

### Type Name Generator Core

```python
class TypeNameGenerator:
    """Handles type name generation using format strings with column placeholders"""

    def __init__(self, csv_headers):
        self.csv_headers = csv_headers
        self.format_string = ""

    def set_format_string(self, format_str):
        """Set the format string for name generation"""
        self.format_string = format_str

    def generate_name(self, csv_row):
        """Generate type name from CSV row using format string"""
        if not self.format_string:
            return ""

        try:
            # Replace {column_name} placeholders with actual values
            result = self.format_string

            for header in self.csv_headers:
                placeholder = "{" + header + "}"
                value = str(csv_row.get(header, "")).strip()
                result = result.replace(placeholder, value)

            return result.strip()

        except Exception as e:
            return "Error: {}".format(str(e))

    def validate_format_string(self):
        """Validate that format string contains valid placeholders"""
        if not self.format_string:
            return False, "Format string cannot be empty"

        # Check if format string contains at least one placeholder
        has_placeholder = any("{" + header + "}" in self.format_string for header in self.csv_headers)
        if not has_placeholder:
            return False, "Format string must contain at least one column placeholder like {ColumnName}"

        return True, "Format string is valid"

    def get_available_placeholders(self):
        """Get list of available placeholders for the UI"""
        return ["{" + header + "}" for header in self.csv_headers]
```

## Key Techniques

### 1. Interactive Placeholder Insertion

**Double-click to Insert:**
```python
def on_placeholder_double_click(self, sender, args):
    if self.placeholders_lb.SelectedItem:
        placeholder = self.placeholders_lb.SelectedItem
        current_text = self.format_tb.Text or ""
        self.format_tb.Text = current_text + placeholder
```

### 2. Real-time Preview System

**Live Preview Updates:**
```python
def on_format_text_changed(self, sender, args):
    self.name_generator.set_format_string(self.format_tb.Text)
    self._refresh_preview()  # Update preview immediately
```

### 3. Format String Validation

**Real-time Validation:**
```python
is_valid, message = self.name_generator.validate_format_string()
self.validation_tb.Text = ("✅ " if is_valid else "❌ ") + message
```

### 4. Crash-Resistant WPF Handling

**Error Handling for IronPython:**
```python
try:
    # WPF operations that might fail
    self.preview_dg.Items.Refresh()
except:
    pass  # Ignore errors to prevent Revit crashes
```

## Performance Notes

- **Execution Time**: Fast (format parsing is O(n) for n placeholders)
- **Memory Usage**: Low (stores preview items for 10 rows max)
- **UI Responsiveness**: Real-time updates without lag
- **Stability**: Error handling prevents crashes

## Usage Examples

### Basic Naming Convention Builder

```python
def build_naming_convention(csv_headers, csv_rows):
    """Build naming convention interactively"""

    # Create XAML content
    xaml_content = create_naming_builder_xaml()

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xaml', delete=False) as f:
        f.write(xaml_content)
        xaml_file = f.name

    try:
        # Show builder window
        builder = TypeNameBuilderWindow(xaml_file, csv_headers, csv_rows)
        builder.show(modal=True)

        # Get result
        if hasattr(builder, 'format_string') and builder.format_string:
            return builder.format_string
        else:
            return None

    finally:
        # Clean up temp file
        try:
            os.unlink(xaml_file)
        except:
            pass
```

### Integration with CSV Processing

```python
def process_csv_with_custom_names(csv_path):
    """Process CSV with custom naming convention"""

    # Read CSV
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)

    # Build naming convention
    format_string = build_naming_convention(headers, rows)
    if not format_string:
        return  # User cancelled

    # Create name generator
    name_gen = TypeNameGenerator(headers)
    name_gen.set_format_string(format_string)

    # Process rows
    for row in rows:
        type_name = name_gen.generate_name(row)
        # Create family type with generated name...
```

## Comparison with Basic Input Methods

| Aspect | Basic Text Input | Interactive Builder |
|--------|------------------|---------------------|
| **User Experience** | Manual typing | Guided with double-click |
| **Error Prevention** | None | Real-time validation |
| **Preview** | None | Live preview of results |
| **Learning Curve** | High | Low (visual) |
| **Crash Risk** | Low | Medium (WPF) |
| **Flexibility** | High | High |

## Integration with Logic Library

### File Structure
```
logic-library/active/utilities/ui/
├── LOG-UTIL-UI-005-v1-simple-option-selection.md
├── LOG-UTIL-UI-007-v1-wpf-naming-convention-builder.md
└── naming_convention_builder.py
```

### Import Pattern
```python
# For interactive naming convention building
from logic_library.active.utilities.ui.naming_convention_builder import (
    TypeNameBuilderWindow,
    TypeNameGenerator,
    create_naming_builder_xaml
)
```

## Related Logic Entries

- [LOG-UTIL-UI-005-v1-simple-option-selection](LOG-UTIL-UI-005-v1-simple-option-selection.md) - Basic UI selection
- [LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching](LOG-UTIL-PARAM-010-v1-flexible-csv-parameter-matching.md) - CSV parameter matching
- [LOG-UTIL-FILTER-001-v1-filter-rule-parser](LOG-UTIL-FILTER-001-v1-filter-rule-parser.md) - Text processing

## Best Practices

### WPF Window Design

1. **Modal Windows**: Use `show(modal=True)` for focused interaction
2. **Temp Files**: Create XAML as temp files, clean up after use
3. **Error Handling**: Wrap all WPF operations in try-catch
4. **Resource Management**: Explicitly dispose resources

### User Experience Guidelines

1. **Clear Instructions**: Show how-to-use text in the window
2. **Visual Feedback**: Color-coded validation messages
3. **Immediate Preview**: Update preview as user types
4. **Safe Cancellation**: Allow users to cancel without errors

### Format String Conventions

1. **Placeholder Syntax**: Use `{ColumnName}` format consistently
2. **Case Sensitivity**: Match CSV headers exactly
3. **Validation Rules**: Require at least one placeholder
4. **Error Messages**: Provide clear, actionable feedback

## Future Applications

### 1. Advanced Form Builders
Any interactive WPF form with validation and preview (parameter editors, filter builders, etc.)

### 2. Data Grid Interfaces
Complex DataGrid operations with sorting, filtering, and real-time updates

### 3. Multi-step Wizards
Modal window sequences with proper state management and cleanup

### 4. Dynamic UI Generation
Runtime XAML generation for customizable interfaces based on data structure

## Optimization History

*Initial implementation (v1) developed for Family Type Generator, successfully creating format strings like "{Type Plinth} x{Length}x{Width}x{Foundation Thickness (mm)}mm" with real-time preview and validation. WPF error handling prevents Revit crashes while maintaining full interactivity.*

---

Developed for PrasKaaPyKit Extension Logic Library
Last Updated: 2025-10-27