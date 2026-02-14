# -*- coding: utf-8 -*-
"""
Geometry Matching Filter Configuration Window

WPF dialog for configuring the modular filter pipeline with reorder support and preset management.
"""

import os
import json

from pyrevit import forms, script
from pyrevit.framework import Windows, Drawing, ObjectModel, Forms, List
import System

# Import filter classes (pyRevit auto-adds extension root to sys.path)
from geometry_matching import (
    FilterPipeline,
    LevelFilter,
    ConcreteBeamDimensionFilter,
    ETABSTypeMarkFilter,
    RevitTypeMarkFilter,
    FamilyNameFilter,
    BoundingBoxFilter,
    GeometryIntersectionFilter
)


# Get config
config = script.get_config(section='geometry_matching')


    # Filter definitions with metadata
FILTER_DEFINITIONS = [
    {'id': 'level', 'name': 'LevelFilter', 'class': LevelFilter, 'params': {}, 'tag': 'Level'},
    {'id': 'etabs', 'name': 'ETABSTypeMarkFilter', 'class': ETABSTypeMarkFilter, 'params': {'use_prefix': True}, 'tag': 'ETABS'},
    {'id': 'revit', 'name': 'RevitTypeMarkFilter', 'class': RevitTypeMarkFilter, 'params': {'use_prefix': True}, 'tag': 'Revit'},
    {'id': 'family', 'name': 'FamilyNameFilter', 'class': FamilyNameFilter, 'params': {'exact_match': True}, 'tag': 'Family'},
    {'id': 'bbox', 'name': 'BoundingBoxFilter', 'class': BoundingBoxFilter, 'params': {'buffer_m': 1.5}, 'tag': 'Bounding'},
    {'id': 'dimension', 'name': 'ConcreteBeamDimensionFilter', 'class': ConcreteBeamDimensionFilter, 'params': {'tolerance_mm': 1.0}, 'tag': 'Concrete'},
    {'id': 'geometry', 'name': 'GeometryIntersectionFilter', 'class': GeometryIntersectionFilter, 'params': {'vol_threshold': 1e-9}, 'tag': 'Geometry'},
]


# Default presets - empty, user will create their own
# Can be added later if needed
DEFAULT_PRESETS = {}


class GeometryMatchingConfigWindow(forms.WPFWindow):
    """WPF Window for configuring geometry matching filters with preset support"""
    
    def __init__(self, xaml_file_name):
        forms.WPFWindow.__init__(self, xaml_file_name)
        
        self._saved = False
        self.pipeline = None
        self._filter_order = None
        self._custom_presets = {}
        self._current_preset = 'default'
        
        # Initialize preset system
        self._load_custom_presets()
        self._populate_preset_combo()
        
        # Load saved configuration
        self.load_config()
        self._apply_filter_order()
        
        # Set initial preset selection
        self._update_preset_ui()
    
    def _load_custom_presets(self):
        """Load custom presets from config"""
        try:
            presets_json = config.get_option('custom_presets', '{}')
            self._custom_presets = json.loads(presets_json)
        except:
            self._custom_presets = {}
    
    def _save_custom_presets(self):
        """Save custom presets to config"""
        try:
            config.custom_presets = json.dumps(self._custom_presets)
            script.save_config()
        except Exception as e:
            print("Error saving custom presets: {}".format(str(e)))
    
    def _populate_preset_combo(self):
        """Populate preset ComboBox with custom presets"""
        self.PresetComboBox.Items.Clear()
        
        # Add custom presets - use simple string items for WinForms
        for preset_id, preset_data in self._custom_presets.items():
            self.PresetComboBox.Items.Add(preset_data['name'])
        
        # Select first if available
        if self.PresetComboBox.Items.Count > 0:
            self.PresetComboBox.SelectedIndex = 0
    
    def _get_filter_order_from_config(self):
        """Get filter order from config"""
        try:
            order_str = config.get_option('filter_order', '')
            if order_str:
                return [int(x) for x in order_str.split(',')]
        except:
            pass
        return None
    
    def _save_filter_order_to_config(self, order):
        """Save filter order to config"""
        config.filter_order = ','.join(str(x) for x in order)
    
    def _apply_filter_order(self):
        """Apply saved filter order to the ListBox"""
        order = self._get_filter_order_from_config()
        if order and len(order) == len(FILTER_DEFINITIONS):
            # Reorder the ListBox items
            items = list(self.FilterList.Items)
            for i, idx in enumerate(order):
                if 0 <= idx < len(items):
                    self.FilterList.Items.Remove(items[idx])
                    self.FilterList.Items.Insert(i, items[idx])
    
    def load_config(self):
        """Load configuration from settings"""
        try:
            # Load enabled states
            level_enabled = config.get_option('level_filter_enabled', True)
            etabs_enabled = config.get_option('etabs_typemark_enabled', True)
            revit_enabled = config.get_option('revit_typemark_enabled', True)
            family_enabled = config.get_option('family_name_enabled', True)
            bbox_enabled = config.get_option('bbox_enabled', True)
            dim_enabled = config.get_option('dimension_enabled', True)
            geo_enabled = config.get_option('geometry_enabled', True)
            
            # Load parameters
            bbox_buffer = config.get_option('bbox_buffer_m', 1.5)
            dim_tolerance = config.get_option('dimension_tolerance_mm', 1.0)
            
            # Set UI values
            self.LevelFilter_Enabled.IsChecked = level_enabled
            self.ETABSTypeMarkFilter_Enabled.IsChecked = etabs_enabled
            self.RevitTypeMarkFilter_Enabled.IsChecked = revit_enabled
            self.FamilyNameFilter_Enabled.IsChecked = family_enabled
            self.BoundingBoxFilter_Enabled.IsChecked = bbox_enabled
            self.ConcreteBeamDimensionFilter_Enabled.IsChecked = dim_enabled
            self.GeometryIntersectionFilter_Enabled.IsChecked = geo_enabled
            
            self.BoundingBoxFilter_Buffer.Text = str(bbox_buffer)
            self.ConcreteBeamDimensionFilter_Tolerance.Text = str(dim_tolerance)
            
        except Exception as e:
            # Use defaults if config not found
            self.LevelFilter_Enabled.IsChecked = True
            self.ETABSTypeMarkFilter_Enabled.IsChecked = True
            self.RevitTypeMarkFilter_Enabled.IsChecked = True
            self.FamilyNameFilter_Enabled.IsChecked = True
            self.BoundingBoxFilter_Enabled.IsChecked = True
            self.ConcreteBeamDimensionFilter_Enabled.IsChecked = True
            self.GeometryIntersectionFilter_Enabled.IsChecked = True
            
            self.BoundingBoxFilter_Buffer.Text = "1.5"
            self.ConcreteBeamDimensionFilter_Tolerance.Text = "1.0"
    
    def _get_current_config(self):
        """Get current configuration as a dict (for saving as preset)"""
        order = self.get_current_filter_order()
        
        return {
            'filters': {
                'level': self.LevelFilter_Enabled.IsChecked,
                'etabs': self.ETABSTypeMarkFilter_Enabled.IsChecked,
                'revit': self.RevitTypeMarkFilter_Enabled.IsChecked,
                'family': self.FamilyNameFilter_Enabled.IsChecked,
                'bbox': self.BoundingBoxFilter_Enabled.IsChecked,
                'dimension': self.ConcreteBeamDimensionFilter_Enabled.IsChecked,
                'geometry': self.GeometryIntersectionFilter_Enabled.IsChecked,
            },
            'params': {
                'bbox_buffer_m': float(self.BoundingBoxFilter_Buffer.Text or '1.5'),
                'dimension_tolerance_mm': float(self.ConcreteBeamDimensionFilter_Tolerance.Text or '1.0'),
            },
            'order': order,
        }
    
    def _apply_preset_config(self, preset_data):
        """Apply preset configuration to UI"""
        if 'filters' in preset_data:
            self.LevelFilter_Enabled.IsChecked = preset_data['filters'].get('level', True)
            self.ETABSTypeMarkFilter_Enabled.IsChecked = preset_data['filters'].get('etabs', True)
            self.RevitTypeMarkFilter_Enabled.IsChecked = preset_data['filters'].get('revit', True)
            self.FamilyNameFilter_Enabled.IsChecked = preset_data['filters'].get('family', True)
            self.BoundingBoxFilter_Enabled.IsChecked = preset_data['filters'].get('bbox', True)
            self.ConcreteBeamDimensionFilter_Enabled.IsChecked = preset_data['filters'].get('dimension', True)
            self.GeometryIntersectionFilter_Enabled.IsChecked = preset_data['filters'].get('geometry', True)
        
        if 'params' in preset_data:
            self.BoundingBoxFilter_Buffer.Text = str(preset_data['params'].get('bbox_buffer_m', 1.5))
            self.ConcreteBeamDimensionFilter_Tolerance.Text = str(preset_data['params'].get('dimension_tolerance_mm', 1.0))
        
        # Apply filter order if present
        if 'order' in preset_data and preset_data['order']:
            self._apply_filter_order_from_list(preset_data['order'])
        
        self._update_preset_ui()
    
    def _apply_filter_order_from_list(self, order):
        """Apply filter order from a list of indices"""
        # Validate order
        if not order:
            return
        
        # Check if order has correct length
        expected_count = len(FILTER_DEFINITIONS)
        if len(order) != expected_count:
            return
        
        # Check if all indices are valid
        for idx in order:
            if idx < 0 or idx >= expected_count:
                return
        
        # Store references to all items before clearing
        all_items = []
        for i in range(self.FilterList.Items.Count):
            all_items.append(self.FilterList.Items[i])
        
        # Verify we have the right number of items
        if len(all_items) != expected_count:
            return
        
        # Clear and rebuild
        self.FilterList.Items.Clear()
        for idx in order:
            self.FilterList.Items.Add(all_items[idx])
        
        # Force visual refresh
        self.FilterList.UpdateLayout()
    
    def _get_current_filter_order_indices(self):
        """Get current filter order as list of original indices"""
        # Map current ListBox positions to original indices
        
        # Use the filter tags from FILTER_DEFINITIONS
        filter_tags = [fd.get('tag', fd['id'].title()) for fd in FILTER_DEFINITIONS]
        
        order = []
        for i in range(self.FilterList.Items.Count):
            item = self.FilterList.Items[i]
            
            # Get content from ListBoxItem - need to extract CheckBox content
            content = ""
            try:
                # ListBoxItem.Content gives us the Border inside
                if hasattr(item, 'Content') and item.Content is not None:
                    border = item.Content
                    # Border.Child should be StackPanel
                    if hasattr(border, 'Child'):
                        stack = border.Child
                        # Stack.Children[0] should be the CheckBox
                        if hasattr(stack, 'Children') and stack.Children.Count > 0:
                            checkbox = stack.Children[0]
                            if hasattr(checkbox, 'Content'):
                                content = str(checkbox.Content)
            except:
                pass
            
            # Find matching filter by tag
            found = False
            for idx, tag in enumerate(filter_tags):
                if tag in content:
                    order.append(idx)
                    found = True
                    break
            
            # Fallback: use position if not found
            if not found:
                order.append(i)
        
        return order
    
    def _update_preset_ui(self):
        """Update UI elements based on current preset selection"""
        selected_item = self.PresetComboBox.SelectedItem
        
        # Enable/disable buttons based on whether there are presets
        has_presets = len(self._custom_presets) > 0
        
        # Save button - enabled if a preset is selected (use IsEnabled for WPF)
        self.SavePresetButton.IsEnabled = has_presets
        
        # Delete button - enabled when there are presets
        self.DeletePresetButton.IsEnabled = has_presets
        
        # Show status based on whether there are custom presets
        if not has_presets:
            self.PresetStatusText.Text = "No presets - click Save As to create one"
        else:
            self.PresetStatusText.Text = "Select a preset or create a new one"
    
    def save_config(self):
        """Save configuration to settings"""
        try:
            # Save enabled states
            config.level_filter_enabled = self.LevelFilter_Enabled.IsChecked
            config.etabs_typemark_enabled = self.ETABSTypeMarkFilter_Enabled.IsChecked
            config.revit_typemark_enabled = self.RevitTypeMarkFilter_Enabled.IsChecked
            config.family_name_enabled = self.FamilyNameFilter_Enabled.IsChecked
            config.bbox_enabled = self.BoundingBoxFilter_Enabled.IsChecked
            config.dimension_enabled = self.ConcreteBeamDimensionFilter_Enabled.IsChecked
            config.geometry_enabled = self.GeometryIntersectionFilter_Enabled.IsChecked
            
            # Save parameters
            try:
                config.bbox_buffer_m = float(self.BoundingBoxFilter_Buffer.Text)
            except:
                config.bbox_buffer_m = 1.5
            
            try:
                config.dimension_tolerance_mm = float(self.ConcreteBeamDimensionFilter_Tolerance.Text)
            except:
                config.dimension_tolerance_mm = 1.0
            
            # Save filter order
            self._save_filter_order_to_config(range(len(FILTER_DEFINITIONS)))
            
            script.save_config()
            
        except Exception as e:
            print("Error saving config: {}".format(str(e)))
    
    def get_filter_checkboxes(self):
        """Get all filter checkbox states in current ListBox order"""
        checkboxes = [
            ('level', self.LevelFilter_Enabled),
            ('etabs', self.ETABSTypeMarkFilter_Enabled),
            ('revit', self.RevitTypeMarkFilter_Enabled),
            ('family', self.FamilyNameFilter_Enabled),
            ('bbox', self.BoundingBoxFilter_Enabled),
            ('dimension', self.ConcreteBeamDimensionFilter_Enabled),
            ('geometry', self.GeometryIntersectionFilter_Enabled),
        ]
        return checkboxes
    
    def get_current_filter_order(self):
        """Get current filter order based on ListBox positions"""
        return self._get_current_filter_order_indices()
    
    def create_pipeline(self):
        """Create filter pipeline from current configuration and order"""
        pipeline = FilterPipeline()
        
        # Get parameter values
        try:
            bbox_buffer = float(self.BoundingBoxFilter_Buffer.Text)
        except:
            bbox_buffer = 1.5
        
        try:
            dim_tolerance = float(self.ConcreteBeamDimensionFilter_Tolerance.Text)
        except:
            dim_tolerance = 1.0
        
        # Map filter IDs to their checkbox controls
        checkbox_map = {
            'level': self.LevelFilter_Enabled,
            'etabs': self.ETABSTypeMarkFilter_Enabled,
            'revit': self.RevitTypeMarkFilter_Enabled,
            'family': self.FamilyNameFilter_Enabled,
            'bbox': self.BoundingBoxFilter_Enabled,
            'dimension': self.ConcreteBeamDimensionFilter_Enabled,
            'geometry': self.GeometryIntersectionFilter_Enabled,
        }
        
        # Get current order from ListBox
        current_order = self.get_current_filter_order()
        
        # Create filters in the current ListBox order
        for list_idx in range(self.FilterList.Items.Count):
            # Find the filter ID at this position
            item = self.FilterList.Items[list_idx]
            filter_id = None
            
            # Determine which filter based on checkbox content (extract from nested structure)
            content = ""
            try:
                if hasattr(item, 'Content') and item.Content is not None:
                    border = item.Content
                    if hasattr(border, 'Child'):
                        stack = border.Child
                        if hasattr(stack, 'Children') and stack.Children.Count > 0:
                            checkbox = stack.Children[0]
                            if hasattr(checkbox, 'Content'):
                                content = str(checkbox.Content)
            except:
                pass
            
            # Match content to filter ID
            if 'Level' in content:
                filter_id = 'level'
            elif 'ETABS' in content:
                filter_id = 'etabs'
            elif 'Revit' in content:
                filter_id = 'revit'
            elif 'Family' in content:
                filter_id = 'family'
            elif 'Bounding' in content:
                filter_id = 'bbox'
            elif 'Concrete' in content:
                filter_id = 'dimension'
            elif 'Geometry' in content:
                filter_id = 'geometry'
            
            if filter_id is None:
                continue
            
            # Get enabled state from checkbox
            checkbox = checkbox_map[filter_id]
            enabled = checkbox.IsChecked
            
            # Create filter instance based on ID
            if filter_id == 'level':
                pipeline.add_filter(LevelFilter(enabled=enabled))
            elif filter_id == 'etabs':
                pipeline.add_filter(ETABSTypeMarkFilter(enabled=enabled, use_prefix=True))
            elif filter_id == 'revit':
                pipeline.add_filter(RevitTypeMarkFilter(enabled=enabled, use_prefix=True))
            elif filter_id == 'family':
                pipeline.add_filter(FamilyNameFilter(enabled=enabled, exact_match=True))
            elif filter_id == 'bbox':
                pipeline.add_filter(BoundingBoxFilter(enabled=enabled, buffer_m=bbox_buffer))
            elif filter_id == 'dimension':
                pipeline.add_filter(ConcreteBeamDimensionFilter(enabled=enabled, tolerance_mm=dim_tolerance))
            elif filter_id == 'geometry':
                pipeline.add_filter(GeometryIntersectionFilter(enabled=enabled, vol_threshold=1e-9))
        
        return pipeline
    
    def FilterList_SelectionChanged(self, sender, args):
        """Handle selection change - enable/disable up/down buttons"""
        selected_index = self.FilterList.SelectedIndex
        item_count = self.FilterList.Items.Count
        
        # Enable Up button if not first item
        self.MoveUpButton.IsEnabled = (selected_index > 0)
        
        # Enable Down button if not last item
        self.MoveDownButton.IsEnabled = (selected_index < item_count - 1)
    
    def MoveUp_Click(self, sender, args):
        """Move selected filter up"""
        selected_index = self.FilterList.SelectedIndex
        if selected_index > 0:
            # Swap items
            item = self.FilterList.Items[selected_index]
            self.FilterList.Items.RemoveAt(selected_index)
            self.FilterList.Items.Insert(selected_index - 1, item)
            self.FilterList.SelectedIndex = selected_index - 1
    
    def MoveDown_Click(self, sender, args):
        """Move selected filter down"""
        selected_index = self.FilterList.SelectedIndex
        item_count = self.FilterList.Items.Count
        if selected_index < item_count - 1:
            # Swap items
            item = self.FilterList.Items[selected_index]
            self.FilterList.Items.RemoveAt(selected_index)
            self.FilterList.Items.Insert(selected_index + 1, item)
            self.FilterList.SelectedIndex = selected_index + 1
    
    def PresetComboBox_SelectionChanged(self, sender, args):
        """Handle preset selection change"""
        selected_item = self.PresetComboBox.SelectedItem
        if not selected_item:
            return
        
        # Get preset name from selected string
        preset_name = str(selected_item)
        
        # Find preset ID by name
        preset_id = None
        for pid, pdata in self._custom_presets.items():
            if pdata['name'] == preset_name:
                preset_id = pid
                break
        
        if preset_id:
            preset_data = self._custom_presets.get(preset_id)
            if preset_data:
                self._apply_preset_config(preset_data)
                self._current_preset = preset_id
    
    def SavePreset_Click(self, sender, args):
        """Update the currently selected preset with current settings"""
        # Check if there's a preset selected
        if not self.PresetComboBox.SelectedItem:
            Forms.MessageBox.Show("No preset selected. Use 'Save As' to create a new preset.", 
                                "Info", Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Information)
            return
        
        preset_name = str(self.PresetComboBox.SelectedItem)
        
        # Find preset ID
        preset_id = None
        for pid, pdata in self._custom_presets.items():
            if pdata['name'] == preset_name:
                preset_id = pid
                break
        
        if not preset_id:
            Forms.MessageBox.Show("Preset not found. Use 'Save As' to create a new preset.", 
                                "Error", Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Warning)
            return
        
        # Update preset
        current_config = self._get_current_config()
        current_config['name'] = preset_name
        self._custom_presets[preset_id] = current_config
        self._save_custom_presets()
        
        Forms.MessageBox.Show("Preset '{}' updated!".format(preset_name), 
                            "Success", Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Information)
    
    def SaveAsPreset_Click(self, sender, args):
        """Save current configuration as a new preset"""
        # Show input dialog for preset name
        input_dialog = Forms.Form()
        input_dialog.Width = 350
        input_dialog.Height = 150
        input_dialog.Text = "Save Preset As"
        input_dialog.FormBorderStyle = Forms.FormBorderStyle.FixedDialog
        input_dialog.StartPosition = Forms.FormStartPosition.CenterParent
        
        # Label
        lbl_name = Forms.Label()
        lbl_name.Text = "Enter new preset name:"
        lbl_name.Location = System.Drawing.Point(20, 20)
        lbl_name.AutoSize = True
        input_dialog.Controls.Add(lbl_name)
        
        # TextBox
        txt_name = Forms.TextBox()
        txt_name.Location = System.Drawing.Point(20, 45)
        txt_name.Width = 300
        input_dialog.Controls.Add(txt_name)
        
        # Buttons
        btn_ok = Forms.Button()
        btn_ok.Text = "Save"
        btn_ok.Location = System.Drawing.Point(175, 80)
        btn_ok.Width = 75
        btn_ok.DialogResult = Forms.DialogResult.OK
        input_dialog.Controls.Add(btn_ok)
        
        btn_cancel = Forms.Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = System.Drawing.Point(255, 80)
        btn_cancel.Width = 75
        btn_cancel.DialogResult = Forms.DialogResult.Cancel
        input_dialog.Controls.Add(btn_cancel)
        
        # Show dialog
        if input_dialog.ShowDialog() == Forms.DialogResult.OK:
            preset_name = txt_name.Text.strip()
            if not preset_name:
                Forms.MessageBox.Show("Please enter a preset name.", "Error", 
                                    Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Warning)
                return
            
            # Check for duplicate name in custom presets
            for pid, pdata in self._custom_presets.items():
                if pdata['name'].lower() == preset_name.lower():
                    Forms.MessageBox.Show("A preset with this name already exists. Please choose a different name.", 
                                        "Error", Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Warning)
                    return
            
            # Create new preset
            preset_id = 'custom_' + preset_name.lower().replace(' ', '_')
            
            # Save current config as preset
            current_config = self._get_current_config()
            current_config['name'] = preset_name
            
            self._custom_presets[preset_id] = current_config
            self._save_custom_presets()
            
            # Refresh ComboBox
            self._populate_preset_combo()
            
            # Select the new preset by name
            for i in range(self.PresetComboBox.Items.Count):
                if self.PresetComboBox.Items[i] == preset_name:
                    self.PresetComboBox.SelectedIndex = i
                    break
            
            Forms.MessageBox.Show("Preset '{}' saved successfully!".format(preset_name), 
                                "Success", Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Information)
    
    def DeletePreset_Click(self, sender, args):
        """Delete selected custom preset"""
        selected_item = self.PresetComboBox.SelectedItem
        if not selected_item:
            return
        
        # Get preset name from selected string
        preset_name = str(selected_item)
        
        # Find preset ID by name
        preset_id = None
        for pid, pdata in self._custom_presets.items():
            if pdata['name'] == preset_name:
                preset_id = pid
                break
        
        # Confirm deletion
        preset_name = selected_item
        result = Forms.MessageBox.Show(
            "Are you sure you want to delete the preset '{}'?".format(preset_name),
            "Confirm Delete",
            Forms.MessageBoxButtons.YesNo,
            Forms.MessageBoxIcon.Question
        )
        
        if result == Forms.DialogResult.Yes:
            # Delete preset by name
            if preset_id and preset_id in self._custom_presets:
                del self._custom_presets[preset_id]
                self._save_custom_presets()
                
                # Refresh ComboBox
                self._populate_preset_combo()
                
                Forms.MessageBox.Show("Preset '{}' deleted.".format(preset_name), 
                                    "Success", Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Information)
    
    def ok_click(self, sender, args):
        """Handle OK button click"""
        # Save current order before saving config
        current_order = self.get_current_filter_order()
        self._save_filter_order_to_config(current_order)
        
        self.save_config()
        self.pipeline = self.create_pipeline()
        self._saved = True
        self.Close()
    
    def cancel_click(self, sender, args):
        """Handle Cancel button click"""
        self._saved = False
        self.Close()
    
    def cancelled(self, sender, args):
        """Handle window closing"""
        if not self._saved:
            # Reset to saved config
            self.load_config()
    
    def show_dialog(self):
        """Show the dialog"""
        self.ShowDialog()


# Standalone test
if __name__ == "__main__":
    xaml_path = os.path.join(os.path.dirname(__file__), 'GeometryMatchingConfig.xaml')
    GeometryMatchingConfigWindow(xaml_path).show_dialog()
