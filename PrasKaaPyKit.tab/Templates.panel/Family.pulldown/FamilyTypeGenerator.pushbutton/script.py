# -*- coding: utf-8 -*-
"""
Enhanced Family Type Generator from CSV
Creates family types from CSV files with flexible parameter matching and advanced error handling.

Features:
- Flexible CSV structure support
- Case-insensitive parameter matching
- Type parameters only (family-level)
- Advanced error handling and user feedback
- Progress tracking and cancellation support
- Unit conversion for various data types
- Console behavior best practices (no output after commit)
- Type name generation with format strings
"""

__title__ = "Family Type Generator"
__author__ = "PrasKaa Team"
__doc__ = """Generate family types from CSV with flexible parameter matching"""

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')

from System.Windows.Forms import OpenFileDialog, DialogResult, MessageBox, MessageBoxButtons, MessageBoxIcon
from System.Drawing import Color
import os
import csv
import json
from collections import OrderedDict, defaultdict
import sys
import re

# Import pyRevit modules
from pyrevit import forms
from pyrevit import script
from pyrevit import revit, DB
from pyrevit.revit import doc, uidoc

# Import Revit classes
from Autodesk.Revit.DB import (
    Transaction, TransactionGroup, FilteredElementCollector,
    ElementId, BuiltInParameter, UnitTypeId,
    ForgeTypeId, UnitUtils, FamilySymbol, FamilyManager,
    FamilyType, StorageType, TransactionStatus
)

# Import utility classes
import sys
import os

# Add the UpdateProfiles directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
update_profiles_dir = os.path.join(parent_dir, 'UpdateProfiles.pushbutton')
if update_profiles_dir not in sys.path:
    sys.path.insert(0, update_profiles_dir)

from unit_converter import UnitConverter


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


class TypeNamePreviewItem(object):
    """Item for previewing generated type names"""

    def __init__(self, csv_row, generated_name, original_name=""):
        self.csv_row = csv_row
        self.generated_name = generated_name
        self.original_name = original_name
        self.tooltip = "Generated from format string"

    @property
    def preview_text(self):
        """Get preview text showing original -> generated"""
        if self.original_name:
            return "{} → {}".format(self.original_name, self.generated_name)
        return self.generated_name


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


class FlexibleParameterMatcher:
    """Handles flexible parameter matching between CSV headers and family parameters"""

    def __init__(self, family_doc):
        self.family_doc = family_doc
        self.family_manager = family_doc.FamilyManager
        self.unit_converter = UnitConverter()
        self.type_parameters = self._get_type_parameters()

    def _get_type_parameters(self):
        """Get all type parameters from the family"""
        type_params = {}

        try:
            for param in self.family_manager.Parameters:
                if param.IsDeterminedByFormula:
                    continue  # Skip formula-driven parameters

                param_name = param.Definition.Name
                type_params[param_name.lower()] = {
                    'name': param_name,
                    'parameter': param,
                    'storage_type': param.StorageType,
                    'is_readonly': param.IsReadOnly
                }
        except Exception as e:
            print("Warning: Error getting type parameters: {}".format(str(e)))

        return type_params

    def find_best_matches(self, csv_headers):
        """Find best matches between CSV headers and family parameters"""
        matches = {}
        unmatched = []
        duplicates = []

        # Normalize CSV headers
        normalized_headers = {}
        for header in csv_headers:
            if header.lower() == 'name':
                continue  # Skip name column
            normalized_headers[header.lower()] = header

        # Find exact matches first
        for norm_header, original_header in normalized_headers.items():
            if norm_header in self.type_parameters:
                param_info = self.type_parameters[norm_header]
                if not param_info['is_readonly']:
                    matches[original_header] = {
                        'parameter': param_info['parameter'],
                        'storage_type': param_info['storage_type'],
                        'confidence': 'exact'
                    }
                else:
                    unmatched.append(original_header)
            else:
                unmatched.append(original_header)

        # Try fuzzy matching for unmatched headers
        if unmatched:
            fuzzy_matches = self._find_fuzzy_matches(unmatched)
            for csv_header, match_info in fuzzy_matches.items():
                if match_info:
                    matches[csv_header] = match_info
                    unmatched.remove(csv_header)

        return matches, unmatched, duplicates

    def _find_fuzzy_matches(self, csv_headers):
        """Find fuzzy matches using various strategies"""
        fuzzy_matches = {}

        for csv_header in csv_headers:
            best_match = self._find_single_fuzzy_match(csv_header)
            if best_match:
                fuzzy_matches[csv_header] = best_match

        return fuzzy_matches

    def _find_single_fuzzy_match(self, csv_header):
        """Find best fuzzy match for a single CSV header"""
        csv_lower = csv_header.lower()

        # Strategy 1: Remove common separators and try partial matches
        csv_clean = re.sub(r'[\s_-]', '', csv_lower)

        for param_key, param_info in self.type_parameters.items():
            param_clean = re.sub(r'[\s_-]', '', param_key)

            # Exact match after cleaning
            if csv_clean == param_clean:
                return {
                    'parameter': param_info['parameter'],
                    'storage_type': param_info['storage_type'],
                    'confidence': 'cleaned'
                }

            # Partial match (contains)
            if csv_clean in param_clean or param_clean in csv_clean:
                return {
                    'parameter': param_info['parameter'],
                    'storage_type': param_info['storage_type'],
                    'confidence': 'partial'
                }

        # Strategy 2: Word-based matching
        csv_words = set(re.findall(r'\b\w+\b', csv_lower))
        best_score = 0
        best_match = None

        for param_key, param_info in self.type_parameters.items():
            param_words = set(re.findall(r'\b\w+\b', param_key))
            intersection = csv_words.intersection(param_words)

            if intersection:
                score = len(intersection) / max(len(csv_words), len(param_words))
                if score > best_score and score > 0.3:  # Minimum 30% word overlap
                    best_score = score
                    best_match = {
                        'parameter': param_info['parameter'],
                        'storage_type': param_info['storage_type'],
                        'confidence': 'word_match',
                        'score': score
                    }

        return best_match


class CSVValidator:
    """Validates CSV structure and data"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.headers = []
        self.rows = []
        self.validation_errors = []

    def validate(self, name_column=None):
        """Validate CSV file structure and content"""
        try:
            with open(self.csv_path, 'r') as file:
                reader = csv.DictReader(file)
                self.headers = reader.fieldnames or []
                self.rows = list(reader)

            # Basic validation
            if not self.headers:
                self.validation_errors.append("CSV file has no headers")
                return False

            if not self.rows:
                self.validation_errors.append("CSV file has no data rows")
                return False

            # Check for name column (flexible)
            if name_column:
                if name_column not in self.headers:
                    self.validation_errors.append("Selected name column '{}' not found in CSV".format(name_column))
                    return False
            else:
                # Auto-detect name column
                name_columns = [h for h in self.headers if h.lower() in ['name', 'type', 'typename', 'type_name']]
                if not name_columns:
                    self.validation_errors.append("CSV must have a column for type names (Name, Type, TypeName, etc.)")
                    return False
                name_column = name_columns[0]  # Use first match

            # Check for data columns
            data_columns = [h for h in self.headers if h != name_column]
            if not data_columns:
                self.validation_errors.append("CSV must have at least one data column")
                return False

            # Validate each row has name
            for i, row in enumerate(self.rows):
                if not row.get(name_column, '').strip():
                    self.validation_errors.append("Row {}: Missing or empty '{}' value".format(i+1, name_column))

            return len(self.validation_errors) == 0

        except Exception as e:
            self.validation_errors.append("Error reading CSV file: {}".format(str(e)))
            return False

    def get_validation_report(self):
        """Get validation report"""
        if not self.validation_errors:
            return "✅ CSV validation passed"

        report = "❌ CSV validation failed:\n"
        for error in self.validation_errors:
            report += "  - {}\n".format(error)
        return report

    def suggest_name_columns(self):
        """Suggest possible columns for type names"""
        suggestions = []
        for header in self.headers:
            header_lower = header.lower()
            if any(keyword in header_lower for keyword in ['name', 'type', 'typename', 'type_name', 'id']):
                suggestions.append(header)
        return suggestions


class FamilyTypeGenerator:
    """Main class for generating family types from CSV"""

    def __init__(self, family_doc):
        self.family_doc = family_doc
        self.family_manager = family_doc.FamilyManager
        self.unit_converter = UnitConverter()
        self.output = script.get_output()

    def generate_types_from_csv(self, csv_path):
        """Main method to generate family types from CSV"""
        # Step 1: Load and analyze CSV
        self.output.print_md("# 📄 CSV Analysis")
        validator = CSVValidator(csv_path)

        # Read CSV headers and rows
        try:
            with open(csv_path, 'r') as file:
                reader = csv.DictReader(file)
                validator.headers = reader.fieldnames or []
                validator.rows = list(reader)
        except Exception as e:
            self.output.print_md("❌ Error reading CSV: {}".format(str(e)))
            forms.alert("Error reading CSV file: {}".format(str(e)), title="File Error")
            return

        if not validator.headers:
            self.output.print_md("❌ CSV file has no headers")
            forms.alert("CSV file has no headers", title="Invalid CSV")
            return

        if not validator.rows:
            self.output.print_md("❌ CSV file has no data rows")
            forms.alert("CSV file has no data rows", title="Invalid CSV")
            return

        # Step 2: Choose naming method
        naming_method = self._choose_naming_method()
        if not naming_method:
            return

        # Step 3: Configure naming based on method
        if naming_method == 'single_column':
            name_column = self._select_name_column(validator)
            if not name_column:
                return
            self.output.print_md("✅ Selected '{}' as type name column".format(name_column))
        else:  # combined_naming
            name_generator = self._build_naming_format(validator)
            if not name_generator:
                return
            name_column = None  # Will generate names dynamically
            self.output.print_md("✅ Using custom naming format: {}".format(name_generator.format_string))

        # Step 4: Validate CSV
        # Skip name column validation when using combined naming (names are generated)
        if name_column and not validator.validate(name_column):
            self.output.print_md(validator.get_validation_report())
            forms.alert("CSV validation failed. Check the console for details.", title="Validation Error")
            return
        elif not name_column:
            # For combined naming, just check basic CSV structure
            if not validator.rows:
                self.output.print_md("❌ CSV file has no data rows")
                forms.alert("CSV file has no data rows", title="Invalid CSV")
                return
            self.output.print_md("✅ CSV structure validated for combined naming")

        self.output.print_md("✅ CSV validation passed")
        self.output.print_md("📊 Found {} rows with {} columns".format(len(validator.rows), len(validator.headers)))

        # Step 5: Parameter matching
        self.output.print_md("\n# 🔍 Parameter Matching")
        matcher = FlexibleParameterMatcher(self.family_doc)
        # Exclude name column from parameter matching
        param_headers = [h for h in validator.headers if h != name_column]
        matches, unmatched, duplicates = matcher.find_best_matches(param_headers)

        # Report matching results
        self._report_matching_results(matches, unmatched, duplicates)

        if not matches:
            forms.alert("No parameters could be matched between CSV and family.", title="No Matches")
            return

        # Step 6: Process types
        self.output.print_md("\n# ⚙️ Processing Family Types")

        results = self._process_types(validator.rows, matches, name_column, name_generator if naming_method == 'combined_naming' else None)

        # Summary is now shown BEFORE commit in _process_types() to prevent console splitting

    def _choose_naming_method(self):
        """Choose between single column or combined naming"""
        options = [
            "Single Column - Use existing column for type names",
            "Combined Naming - Build custom format with multiple columns"
        ]

        selected = forms.CommandSwitchWindow.show(
            options,
            message="Choose type naming method:",
            title="Type Name Generation"
        )

        if selected == options[0]:
            return 'single_column'
        elif selected == options[1]:
            return 'combined_naming'
        else:
            return None

    def _select_name_column(self, validator):
        """Let user select which column to use for type names"""
        suggestions = validator.suggest_name_columns()

        if not suggestions:
            # No automatic suggestions, show all columns
            options = validator.headers
            message = "Select column for type names:"
        else:
            # Show suggestions first, then all columns
            options = suggestions + ["--- Other columns ---"] + [h for h in validator.headers if h not in suggestions]
            message = "Select column for type names (suggestions first):"

        selected = forms.CommandSwitchWindow.show(
            options,
            message=message,
            title="Select Type Name Column"
        )

        if selected and selected != "--- Other columns ---":
            return selected
        else:
            return None

    def _build_naming_format(self, validator):
        """Build custom naming format using WPF window"""
        try:
            # Create XAML content for the naming builder window
            xaml_content = self._create_naming_builder_xaml()

            # Write XAML to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xaml', delete=False) as f:
                f.write(xaml_content)
                xaml_file = f.name

            # Show the naming builder window
            builder_window = TypeNameBuilderWindow(xaml_file, validator.headers, validator.rows)
            builder_window.show(modal=True)

            # Clean up temp file
            try:
                os.unlink(xaml_file)
            except:
                pass

            # Check if user completed the format
            if hasattr(builder_window, 'format_string') and builder_window.format_string is not None:
                name_generator = TypeNameGenerator(validator.headers)
                name_generator.set_format_string(builder_window.format_string)
                return name_generator
            else:
                return None

        except Exception as e:
            forms.alert("Error creating naming builder: {}".format(str(e)), title="Error")
            return None

    def _create_naming_builder_xaml(self):
        """Create XAML content for the naming builder window"""
        return '''<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
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
</Window>'''

    def _report_matching_results(self, matches, unmatched, duplicates):
        """Report parameter matching results"""
        if matches:
            self.output.print_md("## ✅ Matched Parameters ({}):".format(len(matches)))
            for csv_header, match_info in matches.items():
                confidence_icon = {
                    'exact': '🎯',
                    'cleaned': '🧹',
                    'partial': '🔍',
                    'word_match': '📝'
                }.get(match_info['confidence'], '❓')

                score_text = ""
                self.output.print_md("  {} **{}** → `{}`{}".format(
                    confidence_icon, csv_header, match_info['parameter'].Definition.Name, score_text))

        if unmatched:
            self.output.print_md("\n## ⚠️ Unmatched CSV Columns ({}):".format(len(unmatched)))
            for header in unmatched:
                self.output.print_md("  ❌ **{}** - No matching family parameter found".format(header))

        if duplicates:
            self.output.print_md("\n## 🔄 Duplicate Matches ({}):".format(len(duplicates)))
            for dup in duplicates:
                self.output.print_md("  ⚠️ **{}** - Multiple possible matches".format(dup))

    def _process_types(self, csv_rows, parameter_matches, name_column, name_generator=None):
        """Process CSV rows into family types"""
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        # Use single transaction for all operations
        with Transaction(doc, "Generate Family Types from CSV") as t:
            t.Start()

            # Progress bar for user feedback
            with forms.ProgressBar(title='Creating family types...', cancellable=True) as pb:
                for i, row in enumerate(csv_rows):
                    if pb.cancelled:
                        t.RollBack()
                        forms.alert("Operation cancelled by user", title="Cancelled")
                        return results

                    result = self._create_single_type(row, parameter_matches, name_column, name_generator)
                    results['processed'] += 1
                    results['details'].append(result)

                    if result['success']:
                        results['successful'] += 1
                        self.output.print_md("  ✅ **{}**: {}".format(result['type_name'], result['message']))
                    else:
                        results['failed'] += 1
                        self.output.print_md("  ❌ **{}**: {}".format(result['type_name'], result['message']))

                    # Update progress
                    pb.update_progress(i + 1, len(csv_rows))

            # Print summary BEFORE commit (CRITICAL - prevents console splitting)
            self.output.print_md("\\n## 📊 **Results Summary**")
            self.output.print_md("---")
            self.output.print_md("📈 **Total processed:** {}".format(results['processed']))
            self.output.print_md("✅ **Successful:** {}".format(results['successful']))
            self.output.print_md("❌ **Failed:** {}".format(results['failed']))

            if results['failed'] > 0:
                self.output.print_md("⚠️  **Warning:** {} types failed processing".format(results['failed']))

            success_rate = (results['successful'] / results['processed'] * 100) if results['processed'] > 0 else 0
            self.output.print_md("🎯 **Success rate:** {}%".format(int(success_rate)))
            self.output.print_md("\\n💾 **Saving changes...**")

            # Commit transaction (NO OUTPUT AFTER THIS!)
            status = t.Commit()

            if status != TransactionStatus.Committed:
                forms.alert("❌ Transaction failed! Changes not saved.", exitscript=True)
                return results

            # Show completion dialog (safe - after commit)
            forms.alert(
                "Family type generation complete!\\n\\n"
                "Processed: {}\\n"
                "Successful: {}\\n"
                "Failed: {}\\n"
                "Success Rate: {}%".format(
                    results['processed'],
                    results['successful'],
                    results['failed'],
                    int(success_rate)
                ),
                title="Generation Complete",
                ok=True
            )

        return results

    def _create_single_type(self, csv_row, parameter_matches, name_column, name_generator=None):
        """Create a single family type from CSV row"""
        try:
            # Generate type name
            if name_generator:
                type_name = name_generator.generate_name(csv_row)
            else:
                type_name = csv_row.get(name_column, '').strip()

            if not type_name:
                return {
                    'success': False,
                    'type_name': 'Unknown',
                    'message': 'Missing type name'
                }

            # Check if type already exists
            existing_types = [ft.Name for ft in self.family_manager.Types]
            if type_name in existing_types:
                return {
                    'success': False,
                    'type_name': type_name,
                    'message': 'Type already exists'
                }

            # Create new type
            new_type = self.family_manager.NewType(type_name)
            self.family_manager.CurrentType = new_type

            # Set parameters
            params_set = 0
            params_failed = 0

            for csv_header, value in csv_row.items():
                if (name_column and csv_header == name_column) or (not value or not value.strip()):
                    continue

                if csv_header in parameter_matches:
                    match_info = parameter_matches[csv_header]
                    param = match_info['parameter']
                    storage_type = match_info['storage_type']

                    try:
                        success = self._set_parameter_value(param, value, storage_type)
                        if success:
                            params_set += 1
                        else:
                            params_failed += 1
                    except Exception as e:
                        params_failed += 1
                        print("    ⚠️ Failed to set {}: {}".format(csv_header, str(e)))

            message = "Created with {}/{} parameters set".format(params_set, params_set + params_failed)
            return {
                'success': True,
                'type_name': type_name,
                'message': message,
                'params_set': params_set,
                'params_failed': params_failed
            }

        except Exception as e:
            type_name = 'Unknown'
            if name_generator:
                type_name = name_generator.generate_name(csv_row) or 'Unknown'
            elif name_column:
                type_name = csv_row.get(name_column, 'Unknown')

            return {
                'success': False,
                'type_name': type_name,
                'message': 'Error: {}'.format(str(e))
            }

    def _set_parameter_value(self, parameter, value_str, storage_type):
        """Set parameter value with proper type conversion"""
        try:
            if storage_type == StorageType.Double:
                # Convert to float and then to Revit internal units
                numeric_value = float(value_str)
                # Assume LENGTH unit type for now (can be extended)
                converted_value = self.unit_converter.convert_value(numeric_value, 'LENGTH')
                self.family_manager.Set(parameter, converted_value)
                return True

            elif storage_type == StorageType.Integer:
                int_value = int(float(value_str))
                self.family_manager.Set(parameter, int_value)
                return True

            elif storage_type == StorageType.String:
                self.family_manager.Set(parameter, value_str)
                return True

            else:
                print("    ⚠️ Unsupported storage type: {}".format(storage_type))
                return False

        except (ValueError, TypeError) as e:
            print("    ⚠️ Value conversion error for {}: {}".format(parameter.Definition.Name, str(e)))
            return False
        except Exception as e:
            print("    ⚠️ Error setting parameter {}: {}".format(parameter.Definition.Name, str(e)))
            return False

    def _show_summary(self, results):
        """Show processing summary - REMOVED to prevent console splitting"""
        # Summary is now shown BEFORE commit in _process_types()
        # This prevents the dreaded console splitting issue
        pass


def get_family_document():
    """Get the current family document"""
    if doc.IsFamilyDocument:
        return doc
    else:
        forms.alert("Please open a family document to use this tool.")
        return None


def main():
    """Main execution function"""
    output = script.get_output()

    output.print_md("# 🚀 FAMILY TYPE GENERATOR")
    output.print_md("---")

    try:
        # Get family document
        family_doc = get_family_document()
        if not family_doc:
            return

        output.print_md("✅ Family document: **{}**".format(family_doc.Title))

        # File selection
        file_dialog = OpenFileDialog()
        file_dialog.Filter = "CSV files (*.csv)|*.csv|All files (*.*)|*.*"
        file_dialog.Title = "Select CSV file for family type generation"

        if file_dialog.ShowDialog() == DialogResult.OK:
            csv_path = file_dialog.FileName
            output.print_md("✅ Selected CSV: **{}**".format(os.path.basename(csv_path)))

            # Generate types
            generator = FamilyTypeGenerator(family_doc)
            generator.generate_types_from_csv(csv_path)

        else:
            output.print_md("❌ No CSV file selected.")

    except Exception as e:
        output.print_md("❌ **Error:** {}".format(str(e)))
        import traceback
        traceback.print_exc()
        forms.alert("Error: {}".format(str(e)), title="Script Error")


# Entry point
if __name__ == '__main__':
    main()