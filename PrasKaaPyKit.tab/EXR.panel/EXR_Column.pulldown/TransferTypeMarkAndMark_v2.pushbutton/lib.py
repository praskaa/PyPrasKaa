# -*- coding: utf-8 -*-
"""
Transfer Type Mark and Mark v2 - Configuration and UI Library
Migrated to use ParameterSetting framework and modern WPF UI
"""

import os
import re
import json
import clr

# Import Windows Forms for backward compatibility
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
from System.Windows.Forms import (
    Form, Button, Label, TextBox, ListBox, GroupBox,
    FormBorderStyle, FormStartPosition, DialogResult, MessageBox, MessageBoxButtons, MessageBoxIcon
)
from System.Drawing import Point, Size, Font, FontStyle, Color

# Import WPF for modern UI
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
from System.Windows import Window, Application
from System.Windows.Controls import (
    Button as WPFButton, Label as WPFLabel, TextBox as WPFTextBox,
    ListBox as WPFListBox, GroupBox as WPFGroupBox, StackPanel,
    Grid, ColumnDefinition, RowDefinition, TextBlock, ScrollViewer
)
from System.Windows.Media import Brushes, SolidColorBrush
from System.Windows.Media.Imaging import BitmapImage
from System.Windows.Threading import DispatcherPriority

# Import ParameterSetting framework
try:
    from parameters.framework import ParameterSettingFramework, OptimizationLevel
    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False
    # Mock the class if framework is not available
    class OptimizationLevel:
        BATCH = "batch"

from pyrevit import script

logger = script.get_logger()


class TransferMarkConfig:
    """Configuration manager for Transfer Type Mark and Mark v2 script"""

    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'transfer_mark_config.json')
        self.default_config = {
            'type_mark_pattern': r'^([A-Za-z]+)([\d.].*)$',
            'mark_parameter_name': 'Mark',
            'preview_examples': ['CAA1.1', 'CBB2.5', 'AAA10.15', 'XYZ100.99'],
            'debug_mode': False,
            'csv_output_enabled': True
        }
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file, fallback to defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
            else:
                logger.debug("Config file not found, using defaults")
                return self.default_config.copy()
        except Exception as e:
            logger.warning("Failed to load config file: {}. Using defaults.".format(e))
            return self.default_config.copy()

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.debug("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error("Failed to save configuration: {}".format(e))
            return False

    def get_type_mark_pattern(self):
        """Get the regex pattern for extracting Type Mark"""
        return self.config.get('type_mark_pattern', self.default_config['type_mark_pattern'])

    def set_type_mark_pattern(self, pattern):
        """Set the regex pattern for extracting Type Mark"""
        self.config['type_mark_pattern'] = pattern

    def get_mark_parameter_name(self):
        """Get the parameter name for Mark values"""
        return self.config.get('mark_parameter_name', self.default_config['mark_parameter_name'])

    def set_mark_parameter_name(self, param_name):
        """Set the parameter name for Mark values"""
        self.config['mark_parameter_name'] = param_name

    def get_preview_examples(self):
        """Get example type names for preview"""
        return self.config.get('preview_examples', self.default_config['preview_examples'])

    def set_preview_examples(self, examples):
        """Set example type names for preview"""
        self.config['preview_examples'] = examples

    def get_debug_mode(self):
        """Get debug mode setting"""
        return self.config.get('debug_mode', self.default_config['debug_mode'])

    def set_debug_mode(self, enabled):
        """Set debug mode"""
        self.config['debug_mode'] = enabled

    def get_csv_output_enabled(self):
        """Get CSV output setting"""
        return self.config.get('csv_output_enabled', self.default_config['csv_output_enabled'])

    def set_csv_output_enabled(self, enabled):
        """Set CSV output enabled"""
        self.config['csv_output_enabled'] = enabled

    def test_pattern(self, pattern, test_string):
        """Test a regex pattern against a string"""
        try:
            match = re.match(pattern, test_string.strip())
            if match and len(match.groups()) >= 2:
                return {
                    'success': True,
                    'type_mark': match.group(1),
                    'mark': match.group(2)
                }
            else:
                return {
                    'success': False,
                    'error': 'Pattern did not match or insufficient capture groups'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_all_config(self):
        """Get all configuration as dictionary"""
        return self.config.copy()


class TransferMarkConfigDialogWPF(Window):
    """Modern WPF-based configuration dialog for Transfer Type Mark and Mark v2"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.DialogResult = None

        # Initialize WPF Window
        self.Title = "Transfer Type Mark and Mark v2 - Configuration"
        self.Width = 600
        self.Height = 700
        self.WindowStartupLocation = 1  # CenterScreen
        self.ResizeMode = 0  # NoResize

        # Create main grid
        self.main_grid = Grid()
        self.main_grid.Margin = 10

        # Define rows
        for i in range(8):
            row_def = RowDefinition()
            if i == 7:  # Button row
                row_def.Height = GridLength(50)
            else:
                row_def.Height = GridLength(1, 1)  # Auto
            self.main_grid.RowDefinitions.Add(row_def)

        # Define columns
        col1 = ColumnDefinition()
        col1.Width = GridLength(1, 1)
        col2 = ColumnDefinition()
        col2.Width = GridLength(1, 1)
        self.main_grid.ColumnDefinitions.Add(col1)
        self.main_grid.ColumnDefinitions.Add(col2)

        # Title
        title_label = WPFLabel()
        title_label.Content = "Naming Convention Configuration"
        title_label.FontSize = 16
        title_label.FontWeight = FontWeights.Bold
        title_label.HorizontalAlignment = 0  # Center
        Grid.SetRow(title_label, 0)
        Grid.SetColumnSpan(title_label, 2)
        self.main_grid.Children.Add(title_label)

        # Pattern Configuration Group
        pattern_group = WPFGroupBox()
        pattern_group.Header = "Regex Pattern Configuration"
        pattern_group.Margin = 5
        Grid.SetRow(pattern_group, 1)
        Grid.SetColumnSpan(pattern_group, 2)

        pattern_grid = Grid()
        pattern_grid.Margin = 5

        # Pattern rows
        for i in range(4):
            row_def = RowDefinition()
            row_def.Height = GridLength(35)
            pattern_grid.RowDefinitions.Add(row_def)

        # Columns for pattern grid
        pattern_grid.ColumnDefinitions.Add(ColumnDefinition())
        pattern_grid.ColumnDefinitions.Add(ColumnDefinition())

        # Type Mark Pattern
        tm_label = WPFLabel()
        tm_label.Content = "Type Mark Pattern:"
        tm_label.VerticalAlignment = 1  # Center
        Grid.SetRow(tm_label, 0)
        Grid.SetColumn(tm_label, 0)
        pattern_grid.Children.Add(tm_label)

        self.tm_pattern_box = WPFTextBox()
        self.tm_pattern_box.Text = self.config_manager.get_type_mark_pattern()
        self.tm_pattern_box.Margin = 5
        Grid.SetRow(self.tm_pattern_box, 0)
        Grid.SetColumn(self.tm_pattern_box, 1)
        pattern_grid.Children.Add(self.tm_pattern_box)

        # Mark Parameter Name
        mark_label = WPFLabel()
        mark_label.Content = "Mark Parameter Name:"
        mark_label.VerticalAlignment = 1  # Center
        Grid.SetRow(mark_label, 1)
        Grid.SetColumn(mark_label, 0)
        pattern_grid.Children.Add(mark_label)

        self.mark_param_box = WPFTextBox()
        self.mark_param_box.Text = self.config_manager.get_mark_parameter_name()
        self.mark_param_box.Margin = 5
        Grid.SetRow(self.mark_param_box, 1)
        Grid.SetColumn(self.mark_param_box, 1)
        pattern_grid.Children.Add(self.mark_param_box)

        # Test Pattern Button
        test_btn = WPFButton()
        test_btn.Content = "Test Pattern"
        test_btn.Width = 100
        test_btn.Height = 30
        test_btn.Click += self.on_test_pattern
        Grid.SetRow(test_btn, 2)
        Grid.SetColumn(test_btn, 1)
        pattern_grid.Children.Add(test_btn)

        pattern_group.Content = pattern_grid
        self.main_grid.Children.Add(pattern_group)

        # Preview Group
        preview_group = WPFGroupBox()
        preview_group.Header = "Pattern Preview"
        preview_group.Margin = 5
        Grid.SetRow(preview_group, 2)
        Grid.SetRowSpan(preview_group, 4)
        Grid.SetColumnSpan(preview_group, 2)

        preview_grid = Grid()
        preview_grid.Margin = 5

        # Preview rows
        for i in range(3):
            row_def = RowDefinition()
            if i == 2:
                row_def.Height = GridLength(1, 1)
            else:
                row_def.Height = GridLength(35)
            preview_grid.RowDefinitions.Add(row_def)

        # Preview columns
        preview_grid.ColumnDefinitions.Add(ColumnDefinition())
        preview_grid.ColumnDefinitions.Add(ColumnDefinition())

        # Examples list
        examples_label = WPFLabel()
        examples_label.Content = "Test Examples:"
        Grid.SetRow(examples_label, 0)
        Grid.SetColumn(examples_label, 0)
        preview_grid.Children.Add(examples_label)

        self.examples_list = WPFListBox()
        self.examples_list.Width = 150
        self.examples_list.Height = 120
        for example in self.config_manager.get_preview_examples():
            self.examples_list.Items.Add(example)
        Grid.SetRow(self.examples_list, 1)
        Grid.SetColumn(self.examples_list, 0)
        Grid.SetRowSpan(self.examples_list, 2)
        preview_grid.Children.Add(self.examples_list)

        # Results display
        results_label = WPFLabel()
        results_label.Content = "Parsing Results:"
        Grid.SetRow(results_label, 0)
        Grid.SetColumn(results_label, 1)
        preview_grid.Children.Add(results_label)

        self.results_box = WPFTextBox()
        self.results_box.IsReadOnly = True
        self.results_box.TextWrapping = 1  # Wrap
        self.results_box.VerticalScrollBarVisibility = 0  # Auto
        self.results_box.Height = 120
        Grid.SetRow(self.results_box, 1)
        Grid.SetColumn(self.results_box, 1)
        Grid.SetRowSpan(self.results_box, 2)
        preview_grid.Children.Add(self.results_box)

        # Update preview when selection changes
        self.examples_list.SelectionChanged += self.on_example_selected

        preview_group.Content = preview_grid
        self.main_grid.Children.Add(preview_group)

        # Buttons
        button_panel = StackPanel()
        button_panel.Orientation = 0  # Horizontal
        button_panel.HorizontalAlignment = 1  # Right
        button_panel.Margin = 10
        Grid.SetRow(button_panel, 6)
        Grid.SetColumnSpan(button_panel, 2)

        save_btn = WPFButton()
        save_btn.Content = "Save Configuration"
        save_btn.Width = 140
        save_btn.Height = 35
        save_btn.Margin = 5
        save_btn.Click += self.on_save
        button_panel.Children.Add(save_btn)

        cancel_btn = WPFButton()
        cancel_btn.Content = "Cancel"
        cancel_btn.Width = 80
        cancel_btn.Height = 35
        cancel_btn.Margin = 5
        cancel_btn.Click += self.on_cancel
        button_panel.Children.Add(cancel_btn)

        self.main_grid.Children.Add(button_panel)

        self.Content = self.main_grid

        # Select first example to show initial preview
        if self.examples_list.Items.Count > 0:
            self.examples_list.SelectedIndex = 0

    def on_test_pattern(self, sender, args):
        """Test the current pattern configuration"""
        pattern = self.tm_pattern_box.Text.strip()
        if not pattern:
            MessageBox.Show("Please enter a pattern to test.", "Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Error)
            return

        # Test against all examples
        results = []
        for example in self.config_manager.get_preview_examples():
            result = self.config_manager.test_pattern(pattern, example)
            if result['success']:
                results.append("{} -> Type Mark: '{}', Mark: '{}'".format(
                    example, result['type_mark'], result['mark']))
            else:
                results.append("{} -> ERROR: {}".format(example, result['error']))

        self.results_box.Text = "\r\n".join(results)

    def on_example_selected(self, sender, args):
        """Update preview when example selection changes"""
        if self.examples_list.SelectedItem:
            example = self.examples_list.SelectedItem
            pattern = self.tm_pattern_box.Text.strip()

            if pattern:
                result = self.config_manager.test_pattern(pattern, example)
                if result['success']:
                    self.results_box.Text = "Type Mark: '{}'\r\nMark: '{}'".format(
                        result['type_mark'], result['mark'])
                else:
                    self.results_box.Text = "ERROR: {}".format(result['error'])
            else:
                self.results_box.Text = "Enter a pattern and click 'Test Pattern'"

    def on_save(self, sender, args):
        """Save the configuration"""
        try:
            # Validate pattern
            pattern = self.tm_pattern_box.Text.strip()
            if not pattern:
                MessageBox.Show("Please enter a valid regex pattern.", "Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Error)
                return

            # Test pattern with first example
            if self.config_manager.get_preview_examples():
                test_result = self.config_manager.test_pattern(
                    pattern, self.config_manager.get_preview_examples()[0])
                if not test_result['success']:
                    result = MessageBox.Show(
                        "Pattern validation failed: {}\n\nSave anyway?".format(test_result['error']),
                        "Warning", MessageBoxButtons.YesNo, MessageBoxIcon.Warning)
                    if result == DialogResult.No:
                        return

            # Update configuration
            self.config_manager.set_type_mark_pattern(pattern)
            self.config_manager.set_mark_parameter_name(self.mark_param_box.Text.strip())

            # Save to file
            if self.config_manager.save_config():
                MessageBox.Show("Configuration saved successfully!", "Success",
                              MessageBoxButtons.OK, MessageBoxIcon.Information)
                self.DialogResult = True
                self.Close()
            else:
                MessageBox.Show("Failed to save configuration.", "Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Error)

        except Exception as e:
            MessageBox.Show("Error saving configuration: {}".format(str(e)), "Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Error)

    def on_cancel(self, sender, args):
        """Cancel and close dialog"""
        self.DialogResult = False
        self.Close()


class TransferMarkConfigDialogWinForms(Form):
    """Fallback Windows Forms-based configuration dialog"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.InitializeComponent()

    def InitializeComponent(self):
        """Initialize the dialog components"""
        self.Text = "Transfer Type Mark and Mark v2 - Configuration"
        self.Size = Size(500, 600)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        y_pos = 20

        # Title
        title_label = Label()
        title_label.Text = "Naming Convention Configuration"
        title_label.Location = Point(20, y_pos)
        title_label.Size = Size(460, 25)
        title_label.Font = Font("Segoe UI", 12, FontStyle.Bold)
        self.Controls.Add(title_label)

        y_pos += 35

        # Pattern Configuration Group
        pattern_group = GroupBox()
        pattern_group.Text = "Regex Pattern Configuration"
        pattern_group.Location = Point(20, y_pos)
        pattern_group.Size = Size(460, 120)

        # Type Mark Pattern
        tm_label = Label()
        tm_label.Text = "Type Mark Pattern:"
        tm_label.Location = Point(15, 25)
        tm_label.Size = Size(120, 20)
        pattern_group.Controls.Add(tm_label)

        self.tm_pattern_box = TextBox()
        self.tm_pattern_box.Text = self.config_manager.get_type_mark_pattern()
        self.tm_pattern_box.Location = Point(140, 22)
        self.tm_pattern_box.Size = Size(300, 20)
        pattern_group.Controls.Add(self.tm_pattern_box)

        # Mark Parameter Name
        mark_label = Label()
        mark_label.Text = "Mark Parameter Name:"
        mark_label.Location = Point(15, 55)
        mark_label.Size = Size(120, 20)
        pattern_group.Controls.Add(mark_label)

        self.mark_param_box = TextBox()
        self.mark_param_box.Text = self.config_manager.get_mark_parameter_name()
        self.mark_param_box.Location = Point(140, 52)
        self.mark_param_box.Size = Size(150, 20)
        pattern_group.Controls.Add(self.mark_param_box)

        # Test Pattern Button
        test_btn = Button()
        test_btn.Text = "Test Pattern"
        test_btn.Location = Point(300, 50)
        test_btn.Size = Size(80, 25)
        test_btn.Click += self.on_test_pattern
        pattern_group.Controls.Add(test_btn)

        self.Controls.Add(pattern_group)

        y_pos += 135

        # Preview Group
        preview_group = GroupBox()
        preview_group.Text = "Pattern Preview"
        preview_group.Location = Point(20, y_pos)
        preview_group.Size = Size(460, 200)

        # Examples list
        examples_label = Label()
        examples_label.Text = "Test Examples:"
        examples_label.Location = Point(15, 25)
        examples_label.Size = Size(100, 20)
        preview_group.Controls.Add(examples_label)

        self.examples_list = ListBox()
        self.examples_list.Location = Point(15, 45)
        self.examples_list.Size = Size(150, 120)
        for example in self.config_manager.get_preview_examples():
            self.examples_list.Items.Add(example)
        preview_group.Controls.Add(self.examples_list)

        # Results display
        results_label = Label()
        results_label.Text = "Parsing Results:"
        results_label.Location = Point(180, 25)
        results_label.Size = Size(100, 20)
        preview_group.Controls.Add(results_label)

        self.results_box = TextBox()
        self.results_box.Location = Point(180, 45)
        self.results_box.Size = Size(260, 120)
        self.results_box.Multiline = True
        self.results_box.ReadOnly = True
        self.results_box.ScrollBars = 2  # Vertical
        preview_group.Controls.Add(self.results_box)

        # Update preview when selection changes
        self.examples_list.SelectedIndexChanged += self.on_example_selected

        self.Controls.Add(preview_group)

        y_pos += 215

        # Buttons
        save_btn = Button()
        save_btn.Text = "Save Configuration"
        save_btn.Location = Point(120, y_pos)
        save_btn.Size = Size(120, 30)
        save_btn.Click += self.on_save
        self.Controls.Add(save_btn)

        cancel_btn = Button()
        cancel_btn.Text = "Cancel"
        cancel_btn.Location = Point(260, y_pos)
        cancel_btn.Size = Size(80, 30)
        cancel_btn.Click += self.on_cancel
        self.Controls.Add(cancel_btn)

        # Select first example to show initial preview
        if self.examples_list.Items.Count > 0:
            self.examples_list.SelectedIndex = 0

    def on_test_pattern(self, sender, args):
        """Test the current pattern configuration"""
        pattern = self.tm_pattern_box.Text.strip()
        if not pattern:
            MessageBox.Show("Please enter a pattern to test.", "Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Error)
            return

        # Test against all examples
        results = []
        for example in self.config_manager.get_preview_examples():
            result = self.config_manager.test_pattern(pattern, example)
            if result['success']:
                results.append("{} -> Type Mark: '{}', Mark: '{}'".format(
                    example, result['type_mark'], result['mark']))
            else:
                results.append("{} -> ERROR: {}".format(example, result['error']))

        self.results_box.Text = "\r\n".join(results)

    def on_example_selected(self, sender, args):
        """Update preview when example selection changes"""
        if self.examples_list.SelectedItem:
            example = self.examples_list.SelectedItem
            pattern = self.tm_pattern_box.Text.strip()

            if pattern:
                result = self.config_manager.test_pattern(pattern, example)
                if result['success']:
                    self.results_box.Text = "Type Mark: '{}'\r\nMark: '{}'".format(
                        result['type_mark'], result['mark'])
                else:
                    self.results_box.Text = "ERROR: {}".format(result['error'])
            else:
                self.results_box.Text = "Enter a pattern and click 'Test Pattern'"

    def on_save(self, sender, args):
        """Save the configuration"""
        try:
            # Validate pattern
            pattern = self.tm_pattern_box.Text.strip()
            if not pattern:
                MessageBox.Show("Please enter a valid regex pattern.", "Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Error)
                return

            # Test pattern with first example
            if self.config_manager.get_preview_examples():
                test_result = self.config_manager.test_pattern(
                    pattern, self.config_manager.get_preview_examples()[0])
                if not test_result['success']:
                    result = MessageBox.Show(
                        "Pattern validation failed: {}\n\nSave anyway?".format(test_result['error']),
                        "Warning", MessageBoxButtons.YesNo, MessageBoxIcon.Warning)
                    if result == DialogResult.No:
                        return

            # Update configuration
            self.config_manager.set_type_mark_pattern(pattern)
            self.config_manager.set_mark_parameter_name(self.mark_param_box.Text.strip())

            # Save to file
            if self.config_manager.save_config():
                MessageBox.Show("Configuration saved successfully!", "Success",
                              MessageBoxButtons.OK, MessageBoxIcon.Information)
                self.DialogResult = DialogResult.OK
                self.Close()
            else:
                MessageBox.Show("Failed to save configuration.", "Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Error)

        except Exception as e:
            MessageBox.Show("Error saving configuration: {}".format(str(e)), "Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Error)

    def on_cancel(self, sender, args):
        """Cancel and close dialog"""
        self.DialogResult = DialogResult.Cancel
        self.Close()


def show_configuration_dialog():
    """Show the configuration dialog - tries WPF first, falls back to WinForms"""
    print("\n" + "="*60)
    print("CONFIGURATION DIALOG CALLED")
    print("="*60)

    try:
        print("Creating TransferMarkConfig instance...")
        config_manager = TransferMarkConfig()
        print("✓ Config manager created")

        # Try WPF first
        try:
            print("Attempting to create WPF dialog...")
            dialog = TransferMarkConfigDialogWPF(config_manager)
            print("✓ WPF dialog created")

            print("Showing WPF dialog...")
            result = dialog.ShowDialog()
            print("✓ WPF dialog closed with result: {}".format(result))

            return result

        except Exception as wpf_error:
            print("WPF dialog failed: {}".format(wpf_error))
            print("Falling back to Windows Forms...")

            # Fallback to WinForms
            dialog = TransferMarkConfigDialogWinForms(config_manager)
            print("✓ WinForms dialog created")

            print("Showing WinForms dialog...")
            result = dialog.ShowDialog()
            print("✓ WinForms dialog closed with result: {}".format(result))

            return result

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print("\n" + "="*60)
        print("ERROR IN CONFIGURATION DIALOG:")
        print("="*60)
        print(error_details)
        print("="*60)

        MessageBox.Show(
            "Error membuka configuration dialog:\n\n{}\n\nLihat pyRevit output window untuk detail.".format(str(e)),
            "Dialog Error",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        )

        return None