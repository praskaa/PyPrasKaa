# -*- coding: utf-8 -*-
"""Smart Tag System - Settings Script"""

__title__ = "Smart Tag\nSettings"
__author__ = "Your Name"
__doc__ = "Configure Smart Tag System settings"

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import (
    Form, Button, CheckBox, Label, TextBox, ComboBox,
    FormBorderStyle, FormStartPosition, DialogResult,
    MessageBox, MessageBoxButtons, MessageBoxIcon,
    ComboBoxStyle
)
from System.Drawing import Point, Size, Font, FontStyle

from pyrevit import revit, DB, forms
import sys
import os

# Add lib folder to path
script_dir = os.path.dirname(__file__)
lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from smart_tag_config import SmartTagConfig

doc = revit.doc


class SettingsDialog(Form):
    """Settings dialog for Smart Tag System"""

    def __init__(self, config, tag_types_dict):
        self.config = config
        self.tag_types_dict = tag_types_dict

        # Store original values
        self.framing_config = config.get_category_config('structural_framing').copy()
        self.column_config = config.get_category_config('structural_column').copy()
        self.wall_config = config.get_category_config('walls').copy()

        self.InitializeComponent()

    def InitializeComponent(self):
        """Initialize UI components"""
        self.Text = "Smart Tag System - Settings"
        self.Size = Size(520, 500)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        y_pos = 20

        # ===== STRUCTURAL FRAMING =====
        framing_label = Label()
        framing_label.Text = "Structural Framing:"
        framing_label.Location = Point(20, y_pos)
        framing_label.Size = Size(480, 20)
        framing_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
        self.Controls.Add(framing_label)

        y_pos += 30

        # Tag Type
        label = Label()
        label.Text = "Tag Type:"
        label.Location = Point(40, y_pos)
        label.Size = Size(100, 20)
        self.Controls.Add(label)

        self.framing_tag_combo = ComboBox()
        self.framing_tag_combo.Location = Point(150, y_pos)
        self.framing_tag_combo.Size = Size(330, 25)
        self.framing_tag_combo.DropDownStyle = ComboBoxStyle.DropDownList

        # Populate framing tag types
        framing_tags = self.tag_types_dict.get('framing', [])
        for tag_name in framing_tags:
            self.framing_tag_combo.Items.Add(tag_name)

        # Set current value
        current_tag = self.framing_config.get('tag_type_name', '')
        if current_tag in framing_tags:
            self.framing_tag_combo.SelectedItem = current_tag
        elif framing_tags:
            self.framing_tag_combo.SelectedIndex = 0

        self.Controls.Add(self.framing_tag_combo)

        y_pos += 30

        # Offset
        label = Label()
        label.Text = "Offset (mm):"
        label.Location = Point(40, y_pos)
        label.Size = Size(100, 20)
        self.Controls.Add(label)

        self.framing_offset_txt = TextBox()
        self.framing_offset_txt.Location = Point(150, y_pos)
        self.framing_offset_txt.Size = Size(100, 25)
        self.framing_offset_txt.Text = str(self.framing_config.get('offset_mm', 150))
        self.Controls.Add(self.framing_offset_txt)

        y_pos += 30

        # Enable checkbox
        self.framing_enabled_chk = CheckBox()
        self.framing_enabled_chk.Text = "Enable"
        self.framing_enabled_chk.Location = Point(150, y_pos)
        self.framing_enabled_chk.Size = Size(200, 20)
        self.framing_enabled_chk.Checked = self.framing_config.get('enabled', True)
        self.Controls.Add(self.framing_enabled_chk)

        y_pos += 40

        # ===== STRUCTURAL COLUMNS =====
        column_label = Label()
        column_label.Text = "Structural Columns:"
        column_label.Location = Point(20, y_pos)
        column_label.Size = Size(480, 20)
        column_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
        self.Controls.Add(column_label)

        y_pos += 30

        # Tag Type
        label = Label()
        label.Text = "Tag Type:"
        label.Location = Point(40, y_pos)
        label.Size = Size(100, 20)
        self.Controls.Add(label)

        self.column_tag_combo = ComboBox()
        self.column_tag_combo.Location = Point(150, y_pos)
        self.column_tag_combo.Size = Size(330, 25)
        self.column_tag_combo.DropDownStyle = ComboBoxStyle.DropDownList

        # Populate column tag types
        column_tags = self.tag_types_dict.get('column', [])
        for tag_name in column_tags:
            self.column_tag_combo.Items.Add(tag_name)

        # Set current value
        current_tag = self.column_config.get('tag_type_name', '')
        if current_tag in column_tags:
            self.column_tag_combo.SelectedItem = current_tag
        elif column_tags:
            self.column_tag_combo.SelectedIndex = 0

        self.Controls.Add(self.column_tag_combo)

        y_pos += 30

        # Offset
        label = Label()
        label.Text = "Offset (mm):"
        label.Location = Point(40, y_pos)
        label.Size = Size(100, 20)
        self.Controls.Add(label)

        self.column_offset_txt = TextBox()
        self.column_offset_txt.Location = Point(150, y_pos)
        self.column_offset_txt.Size = Size(100, 25)
        self.column_offset_txt.Text = str(self.column_config.get('offset_mm', 200))
        self.Controls.Add(self.column_offset_txt)

        y_pos += 30

        # Enable checkbox
        self.column_enabled_chk = CheckBox()
        self.column_enabled_chk.Text = "Enable"
        self.column_enabled_chk.Location = Point(150, y_pos)
        self.column_enabled_chk.Size = Size(200, 20)
        self.column_enabled_chk.Checked = self.column_config.get('enabled', True)
        self.Controls.Add(self.column_enabled_chk)

        y_pos += 40

        # ===== WALLS =====
        wall_label = Label()
        wall_label.Text = "Walls:"
        wall_label.Location = Point(20, y_pos)
        wall_label.Size = Size(480, 20)
        wall_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
        self.Controls.Add(wall_label)

        y_pos += 30

        # Tag Type
        label = Label()
        label.Text = "Tag Type:"
        label.Location = Point(40, y_pos)
        label.Size = Size(100, 20)
        self.Controls.Add(label)

        self.wall_tag_combo = ComboBox()
        self.wall_tag_combo.Location = Point(150, y_pos)
        self.wall_tag_combo.Size = Size(330, 25)
        self.wall_tag_combo.DropDownStyle = ComboBoxStyle.DropDownList

        # Populate wall tag types
        wall_tags = self.tag_types_dict.get('wall', [])
        for tag_name in wall_tags:
            self.wall_tag_combo.Items.Add(tag_name)

        # Set current value
        current_tag = self.wall_config.get('tag_type_name', '')
        if current_tag in wall_tags:
            self.wall_tag_combo.SelectedItem = current_tag
        elif wall_tags:
            self.wall_tag_combo.SelectedIndex = 0

        self.Controls.Add(self.wall_tag_combo)

        y_pos += 30

        # Offset
        label = Label()
        label.Text = "Offset (mm):"
        label.Location = Point(40, y_pos)
        label.Size = Size(100, 20)
        self.Controls.Add(label)

        self.wall_offset_txt = TextBox()
        self.wall_offset_txt.Location = Point(150, y_pos)
        self.wall_offset_txt.Size = Size(100, 25)
        self.wall_offset_txt.Text = str(self.wall_config.get('offset_mm', 100))
        self.Controls.Add(self.wall_offset_txt)

        y_pos += 30

        # Enable checkbox
        self.wall_enabled_chk = CheckBox()
        self.wall_enabled_chk.Text = "Enable"
        self.wall_enabled_chk.Location = Point(150, y_pos)
        self.wall_enabled_chk.Size = Size(200, 20)
        self.wall_enabled_chk.Checked = self.wall_config.get('enabled', True)
        self.Controls.Add(self.wall_enabled_chk)

        y_pos += 50

        # ===== BUTTONS =====
        save_btn = Button()
        save_btn.Text = "Save"
        save_btn.Location = Point(270, y_pos)
        save_btn.Size = Size(100, 30)
        save_btn.Click += self.on_save_click
        self.Controls.Add(save_btn)

        cancel_btn = Button()
        cancel_btn.Text = "Cancel"
        cancel_btn.Location = Point(380, y_pos)
        cancel_btn.Size = Size(100, 30)
        cancel_btn.Click += self.on_cancel_click
        self.Controls.Add(cancel_btn)

    def on_save_click(self, sender, args):
        """Save settings"""
        try:
            # Validate and get values
            framing_offset = int(self.framing_offset_txt.Text)
            column_offset = int(self.column_offset_txt.Text)
            wall_offset = int(self.wall_offset_txt.Text)

            # Update config
            self.config.update_category_config(
                'structural_framing',
                str(self.framing_tag_combo.SelectedItem) if self.framing_tag_combo.SelectedItem else '',
                framing_offset,
                self.framing_enabled_chk.Checked
            )

            self.config.update_category_config(
                'structural_column',
                str(self.column_tag_combo.SelectedItem) if self.column_tag_combo.SelectedItem else '',
                column_offset,
                self.column_enabled_chk.Checked
            )

            self.config.update_category_config(
                'walls',
                str(self.wall_tag_combo.SelectedItem) if self.wall_tag_combo.SelectedItem else '',
                wall_offset,
                self.wall_enabled_chk.Checked
            )

            MessageBox.Show(
                "Settings saved successfully!",
                "Success",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )

            self.DialogResult = DialogResult.OK
            self.Close()

        except ValueError:
            MessageBox.Show(
                "Please enter valid numbers for offset values.",
                "Invalid Input",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )

    def on_cancel_click(self, sender, args):
        """Cancel settings"""
        self.DialogResult = DialogResult.Cancel
        self.Close()


def get_available_tag_types(doc):
    """Get all available tag types in the project"""
    tag_types = {
        'framing': [],
        'column': [],
        'wall': []
    }

    try:
        # Get Structural Framing Tags
        collector = DB.FilteredElementCollector(doc)
        framing_tags = collector.OfCategory(DB.BuiltInCategory.OST_StructuralFramingTags)\
                                 .WhereElementIsElementType().ToElements()
        
        for tag in framing_tags:
            try:
                family_name = tag.FamilyName if hasattr(tag, 'FamilyName') else ""
                type_name = tag.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name:
                    type_name = type_name.AsString()
                else:
                    type_name = tag.Name if hasattr(tag, 'Name') else ""
                
                if family_name and type_name:
                    full_name = "{}: {}".format(family_name, type_name)
                    if full_name not in tag_types['framing']:
                        tag_types['framing'].append(full_name)
            except:
                continue

        # Get Structural Column Tags
        collector = DB.FilteredElementCollector(doc)
        column_tags = collector.OfCategory(DB.BuiltInCategory.OST_StructuralColumnTags)\
                               .WhereElementIsElementType().ToElements()
        
        for tag in column_tags:
            try:
                family_name = tag.FamilyName if hasattr(tag, 'FamilyName') else ""
                type_name = tag.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name:
                    type_name = type_name.AsString()
                else:
                    type_name = tag.Name if hasattr(tag, 'Name') else ""
                
                if family_name and type_name:
                    full_name = "{}: {}".format(family_name, type_name)
                    if full_name not in tag_types['column']:
                        tag_types['column'].append(full_name)
            except:
                continue

        # Get Wall Tags
        collector = DB.FilteredElementCollector(doc)
        wall_tags = collector.OfCategory(DB.BuiltInCategory.OST_WallTags)\
                             .WhereElementIsElementType().ToElements()
        
        for tag in wall_tags:
            try:
                family_name = tag.FamilyName if hasattr(tag, 'FamilyName') else ""
                type_name = tag.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name:
                    type_name = type_name.AsString()
                else:
                    type_name = tag.Name if hasattr(tag, 'Name') else ""
                
                if family_name and type_name:
                    full_name = "{}: {}".format(family_name, type_name)
                    if full_name not in tag_types['wall']:
                        tag_types['wall'].append(full_name)
            except:
                continue

        # Sort all lists alphabetically
        tag_types['framing'].sort()
        tag_types['column'].sort()
        tag_types['wall'].sort()

    except:
        pass

    return tag_types

def main():
    """Main execution"""
    # Initialize config
    config_manager = SmartTagConfig()

    # Get available tag types
    tag_types = get_available_tag_types(doc)

    # Check if tag types are available
    if not any(tag_types.values()):
        forms.alert("No tag types found in the project. Please load tag families first.",
                   exitscript=True)

    # Show settings dialog
    dialog = SettingsDialog(config_manager, tag_types)
    dialog.ShowDialog()


if __name__ == '__main__':
    main()