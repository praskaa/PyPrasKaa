# -*- coding: utf-8 -*-
"""
Refactored CAD Layer Manager - Simplified and Efficient
Manages line styles for linked CAD files in Revit with streamlined workflow.
"""

from pyrevit import revit, DB, script, forms
import clr

clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

import System
from System.Windows.Forms import (
    Form, DataGridView, Button, DockStyle, FormBorderStyle,
    DataGridViewAutoSizeColumnsMode, DataGridViewSelectionMode,
    DataGridViewTextBoxColumn, DataGridViewComboBoxColumn, DialogResult,
    Panel, FormStartPosition, TextBox, Label, CheckBox, GroupBox,
    ComboBox, ComboBoxStyle, Padding, AnchorStyles
)
from System.Drawing import Size, Point, Color, Font, FontStyle
from System.ComponentModel import BindingList

# Initialize
doc = revit.doc
logger = script.get_logger()


# ============================================================================
# DATA MODELS
# ============================================================================

class CADLayer:
    """Simplified CAD layer model."""
    
    def __init__(self, category, cad_name):
        self.category = category
        self.cad_name = cad_name
        self.name = category.Name if category else "Unknown"
        
        # Current values
        self.current_weight = self._get_line_weight()
        self.current_pattern = self._get_line_pattern()
        
        # New values (for changes)
        self.new_weight = None
        self.new_pattern = None
    
    def _get_line_weight(self):
        """Get current line weight."""
        try:
            return self.category.GetLineWeight(DB.GraphicsStyleType.Projection)
        except:
            return 1
    
    def _get_line_pattern(self):
        """Get current line pattern name."""
        try:
            pattern_id = self.category.GetLinePatternId(DB.GraphicsStyleType.Projection)
            if pattern_id and pattern_id != DB.ElementId.InvalidElementId:
                pattern = doc.GetElement(pattern_id)
                return pattern.Name if pattern else "Solid"
            return "Solid"
        except:
            return "Solid"
    
    def has_changes(self):
        """Check if layer has pending changes."""
        return self.new_weight is not None or self.new_pattern is not None
    
    def get_changes_text(self):
        """Get text description of changes."""
        if not self.has_changes():
            return ""
        
        changes = []
        if self.new_weight is not None:
            changes.append("LW: {}→{}".format(self.current_weight, self.new_weight))
        if self.new_pattern is not None:
            changes.append("LP: {}→{}".format(self.current_pattern, self.new_pattern))
        return " | ".join(changes)
    
    def apply_changes(self):
        """Apply pending changes to Revit category."""
        success = True
        
        if self.new_weight is not None:
            try:
                self.category.SetLineWeight(self.new_weight, DB.GraphicsStyleType.Projection)
                self.current_weight = self.new_weight
            except Exception as e:
                logger.error("Failed to set weight for {}: {}".format(self.name, e))
                success = False
        
        if self.new_pattern is not None:
            try:
                pattern = get_pattern_by_name(self.new_pattern)
                if pattern:
                    self.category.SetLinePatternId(pattern.Id, DB.GraphicsStyleType.Projection)
                    self.current_pattern = self.new_pattern
            except Exception as e:
                logger.error("Failed to set pattern for {}: {}".format(self.name, e))
                success = False
        
        return success
    
    def clear_changes(self):
        """Clear pending changes."""
        self.new_weight = None
        self.new_pattern = None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_cad_files():
    """Get all linked CAD files with their layers."""
    cad_data = {}  # {cad_name: [layers]}
    
    # Get all CAD link types
    cad_types = DB.FilteredElementCollector(doc)\
        .OfClass(DB.CADLinkType)\
        .WhereElementIsElementType()\
        .ToElements()
    
    for cad_type in cad_types:
        # Get CAD name
        try:
            cad_name = cad_type.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
        except:
            cad_name = cad_type.Name if hasattr(cad_type, 'Name') else "Unknown"
        
        # Get layers (subcategories)
        layers = []
        if cad_type.Category and cad_type.Category.SubCategories:
            for sub_cat in cad_type.Category.SubCategories:
                if sub_cat and sub_cat.Name:
                    layers.append(CADLayer(sub_cat, cad_name))
        
        if layers:
            cad_data[cad_name] = layers
    
    return cad_data


def get_line_patterns():
    """Get all available line patterns."""
    patterns = []
    collector = DB.FilteredElementCollector(doc).OfClass(DB.LinePatternElement)
    for pattern in collector:
        patterns.append(pattern.Name)
    return sorted(patterns)


def get_pattern_by_name(pattern_name):
    """Get line pattern element by name."""
    collector = DB.FilteredElementCollector(doc).OfClass(DB.LinePatternElement)
    for pattern in collector:
        if pattern.Name == pattern_name:
            return pattern
    return None


# ============================================================================
# MAIN UI FORM
# ============================================================================

class CADLayerManagerForm(Form):
    """Single unified form for CAD layer management."""
    
    def __init__(self, cad_data):
        self.cad_data = cad_data
        self.all_layers = []
        self.filtered_layers = []
        self.line_patterns = get_line_patterns()
        
        # Flatten all layers
        for layers in cad_data.values():
            self.all_layers.extend(layers)
        
        self.filtered_layers = self.all_layers[:]
        
        # Form setup
        self.Text = "CAD Layer Manager"
        self.Size = Size(1000, 700)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MinimumSize = Size(900, 600)
        
        self._build_ui()
        self._populate_grid()
    
    def _build_ui(self):
        """Build the user interface."""
        
        # Top panel - Filters and CAD selection
        top_panel = self._create_top_panel()
        top_panel.Dock = DockStyle.Top
        top_panel.Height = 80
        
        # Middle panel - Data grid
        grid_panel = self._create_grid_panel()
        grid_panel.Dock = DockStyle.Fill
        
        # Batch editor panel
        batch_panel = self._create_batch_panel()
        batch_panel.Dock = DockStyle.Bottom
        batch_panel.Height = 120
        
        # Bottom panel - Buttons
        button_panel = self._create_button_panel()
        button_panel.Dock = DockStyle.Bottom
        button_panel.Height = 50
        
        # Add controls
        self.Controls.Add(grid_panel)
        self.Controls.Add(batch_panel)
        self.Controls.Add(button_panel)
        self.Controls.Add(top_panel)
    
    def _create_top_panel(self):
        """Create filter and CAD selection panel."""
        panel = Panel()
        panel.BackColor = Color.FromArgb(245, 245, 245)
        
        # CAD file filter
        lbl_cad = Label()
        lbl_cad.Text = "CAD File:"
        lbl_cad.Location = Point(10, 15)
        lbl_cad.Size = Size(60, 20)
        
        self.cmb_cad = ComboBox()
        self.cmb_cad.Location = Point(75, 12)
        self.cmb_cad.Size = Size(250, 20)
        self.cmb_cad.DropDownStyle = ComboBoxStyle.DropDownList
        self.cmb_cad.Items.Add("All CAD Files")
        for cad_name in sorted(self.cad_data.keys()):
            self.cmb_cad.Items.Add(cad_name)
        self.cmb_cad.SelectedIndex = 0
        self.cmb_cad.SelectedIndexChanged += self._on_filter_changed
        
        # Layer name filter
        lbl_filter = Label()
        lbl_filter.Text = "Layer Filter:"
        lbl_filter.Location = Point(340, 15)
        lbl_filter.Size = Size(70, 20)
        
        self.txt_filter = TextBox()
        self.txt_filter.Location = Point(415, 12)
        self.txt_filter.Size = Size(200, 20)
        self.txt_filter.TextChanged += self._on_filter_changed
        
        btn_clear = Button()
        btn_clear.Text = "Clear"
        btn_clear.Location = Point(625, 11)
        btn_clear.Size = Size(60, 22)
        btn_clear.Click += self._clear_filters
        
        # Quick presets
        lbl_presets = Label()
        lbl_presets.Text = "Quick Presets:"
        lbl_presets.Location = Point(10, 45)
        lbl_presets.Size = Size(80, 20)
        lbl_presets.Font = Font("Segoe UI", 8, FontStyle.Bold)
        
        presets = [
            ("Solid LW1", "Solid", 1),
            ("Dashed LW1", "Dashed", 1),
            ("Solid LW2", "Solid", 2),
            ("LW1 Only", None, 1),
        ]
        
        x_pos = 95
        for i, (text, pattern, weight) in enumerate(presets):
            btn = Button()
            btn.Text = text
            btn.Location = Point(x_pos, 43)
            btn.Size = Size(85, 24)
            btn.Tag = (pattern, weight)
            btn.Click += self._apply_preset
            panel.Controls.Add(btn)
            x_pos += 90
        
        panel.Controls.Add(lbl_cad)
        panel.Controls.Add(self.cmb_cad)
        panel.Controls.Add(lbl_filter)
        panel.Controls.Add(self.txt_filter)
        panel.Controls.Add(btn_clear)
        panel.Controls.Add(lbl_presets)
        
        return panel
    
    def _create_grid_panel(self):
        """Create data grid panel."""
        panel = Panel()
        
        # Grid
        self.grid = DataGridView()
        self.grid.Dock = DockStyle.Fill
        self.grid.AutoGenerateColumns = False
        self.grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        self.grid.MultiSelect = True
        self.grid.AllowUserToAddRows = False
        self.grid.AllowUserToDeleteRows = False
        self.grid.RowHeadersVisible = False
        self.grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
        
        # Columns
        col_cad = DataGridViewTextBoxColumn()
        col_cad.HeaderText = "CAD File"
        col_cad.DataPropertyName = "cad_name"
        col_cad.FillWeight = 25
        col_cad.ReadOnly = True
        
        col_layer = DataGridViewTextBoxColumn()
        col_layer.HeaderText = "Layer Name"
        col_layer.DataPropertyName = "name"
        col_layer.FillWeight = 25
        col_layer.ReadOnly = True
        
        col_curr_lw = DataGridViewTextBoxColumn()
        col_curr_lw.HeaderText = "Current LW"
        col_curr_lw.DataPropertyName = "current_weight"
        col_curr_lw.FillWeight = 12
        col_curr_lw.ReadOnly = True
        
        col_curr_lp = DataGridViewTextBoxColumn()
        col_curr_lp.HeaderText = "Current Pattern"
        col_curr_lp.DataPropertyName = "current_pattern"
        col_curr_lp.FillWeight = 18
        col_curr_lp.ReadOnly = True
        
        col_changes = DataGridViewTextBoxColumn()
        col_changes.HeaderText = "Pending Changes"
        col_changes.Name = "col_changes"
        col_changes.FillWeight = 20
        col_changes.ReadOnly = True
        
        self.grid.Columns.Add(col_cad)
        self.grid.Columns.Add(col_layer)
        self.grid.Columns.Add(col_curr_lw)
        self.grid.Columns.Add(col_curr_lp)
        self.grid.Columns.Add(col_changes)
        
        self.grid.SelectionChanged += self._on_selection_changed
        
        # Info label
        self.lbl_info = Label()
        self.lbl_info.Text = "Total layers: {} | Select rows to batch edit".format(len(self.all_layers))
        self.lbl_info.Dock = DockStyle.Top
        self.lbl_info.Height = 25
        self.lbl_info.Padding = Padding(5, 5, 0, 0)
        
        panel.Controls.Add(self.grid)
        panel.Controls.Add(self.lbl_info)
        
        return panel
    
    def _create_batch_panel(self):
        """Create batch editing panel."""
        panel = Panel()
        panel.BackColor = Color.FromArgb(250, 250, 250)
        
        # Title
        self.lbl_batch = Label()
        self.lbl_batch.Text = "BATCH EDIT (0 selected)"
        self.lbl_batch.Location = Point(10, 10)
        self.lbl_batch.Font = Font("Segoe UI", 9, FontStyle.Bold)
        self.lbl_batch.AutoSize = True
        
        # Line Weight
        grp_lw = GroupBox()
        grp_lw.Text = "Line Weight"
        grp_lw.Location = Point(10, 35)
        grp_lw.Size = Size(200, 75)
        
        self.chk_lw = CheckBox()
        self.chk_lw.Text = "Change to:"
        self.chk_lw.Location = Point(10, 25)
        self.chk_lw.Size = Size(80, 20)
        
        self.cmb_lw = ComboBox()
        self.cmb_lw.Location = Point(95, 23)
        self.cmb_lw.Size = Size(60, 20)
        self.cmb_lw.DropDownStyle = ComboBoxStyle.DropDownList
        for i in range(1, 17):
            self.cmb_lw.Items.Add(str(i))
        self.cmb_lw.SelectedIndex = 0
        
        btn_apply_lw = Button()
        btn_apply_lw.Text = "Apply"
        btn_apply_lw.Location = Point(10, 48)
        btn_apply_lw.Size = Size(80, 22)
        btn_apply_lw.Click += lambda s, e: self._apply_batch(weight_only=True)
        
        grp_lw.Controls.Add(self.chk_lw)
        grp_lw.Controls.Add(self.cmb_lw)
        grp_lw.Controls.Add(btn_apply_lw)
        
        # Line Pattern
        grp_lp = GroupBox()
        grp_lp.Text = "Line Pattern"
        grp_lp.Location = Point(220, 35)
        grp_lp.Size = Size(300, 75)
        
        self.chk_lp = CheckBox()
        self.chk_lp.Text = "Change to:"
        self.chk_lp.Location = Point(10, 25)
        self.chk_lp.Size = Size(80, 20)
        
        self.cmb_lp = ComboBox()
        self.cmb_lp.Location = Point(95, 23)
        self.cmb_lp.Size = Size(150, 20)
        self.cmb_lp.DropDownStyle = ComboBoxStyle.DropDownList
        for pattern in self.line_patterns:
            self.cmb_lp.Items.Add(pattern)
        if self.cmb_lp.Items.Count > 0:
            self.cmb_lp.SelectedIndex = 0
        
        btn_apply_lp = Button()
        btn_apply_lp.Text = "Apply"
        btn_apply_lp.Location = Point(10, 48)
        btn_apply_lp.Size = Size(80, 22)
        btn_apply_lp.Click += lambda s, e: self._apply_batch(pattern_only=True)
        
        grp_lp.Controls.Add(self.chk_lp)
        grp_lp.Controls.Add(self.cmb_lp)
        grp_lp.Controls.Add(btn_apply_lp)
        
        # Apply both button
        btn_both = Button()
        btn_both.Text = "Apply Both"
        btn_both.Location = Point(530, 60)
        btn_both.Size = Size(100, 30)
        btn_both.BackColor = Color.FromArgb(220, 240, 255)
        btn_both.Click += lambda s, e: self._apply_batch(weight_only=False, pattern_only=False)
        
        panel.Controls.Add(self.lbl_batch)
        panel.Controls.Add(grp_lw)
        panel.Controls.Add(grp_lp)
        panel.Controls.Add(btn_both)
        
        return panel
    
    def _create_button_panel(self):
        """Create bottom button panel."""
        panel = Panel()
        panel.BackColor = Color.FromArgb(240, 240, 240)
        
        btn_clear = Button()
        btn_clear.Text = "Clear All Changes"
        btn_clear.Location = Point(10, 10)
        btn_clear.Size = Size(130, 30)
        btn_clear.Click += self._clear_all_changes
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(540, 10)
        btn_cancel.Size = Size(100, 30)
        btn_cancel.Click += lambda s, e: self.Close()
        
        # Large prominent "Apply All Pending Changes" button
        self.btn_apply = Button()
        self.btn_apply.Text = "Apply All Pending Changes (0)"
        self.btn_apply.Location = Point(650, 5)
        self.btn_apply.Size = Size(330, 40)
        self.btn_apply.BackColor = Color.FromArgb(50, 200, 50)
        self.btn_apply.ForeColor = Color.White
        self.btn_apply.Font = Font("Segoe UI", 10, FontStyle.Bold)
        self.btn_apply.Click += self._apply_all_changes
        self.btn_apply.Enabled = False
        
        panel.Controls.Add(btn_clear)
        panel.Controls.Add(btn_cancel)
        panel.Controls.Add(self.btn_apply)
        
        return panel
    
    def _populate_grid(self):
        """Populate grid with layer data."""
        # IronPython compatible way to create BindingList
        from System.Collections.Generic import List
        from System.ComponentModel import BindingList as BL
        
        layer_list = List[object]()
        for layer in self.filtered_layers:
            layer_list.Add(layer)
        
        binding_list = BL[object](layer_list)
        self.grid.DataSource = binding_list
        self._update_changes_display()
    
    def _on_filter_changed(self, sender, e):
        """Handle filter changes."""
        cad_filter = str(self.cmb_cad.SelectedItem)
        text_filter = self.txt_filter.Text.lower()
        
        self.filtered_layers = []
        for layer in self.all_layers:
            # CAD filter
            if cad_filter != "All CAD Files" and layer.cad_name != cad_filter:
                continue
            
            # Text filter
            if text_filter and text_filter not in layer.name.lower():
                continue
            
            self.filtered_layers.append(layer)
        
        self._populate_grid()
        self._update_info_label()
    
    def _clear_filters(self, sender, e):
        """Clear all filters."""
        self.txt_filter.Text = ""
        self.cmb_cad.SelectedIndex = 0
    
    def _on_selection_changed(self, sender, e):
        """Handle selection changes."""
        count = self.grid.SelectedRows.Count
        self.lbl_batch.Text = "BATCH EDIT ({} selected)".format(count)
    
    def _apply_preset(self, sender, e):
        """Apply a quick preset."""
        if self.grid.SelectedRows.Count == 0:
            forms.alert("Select layers first", title="No Selection")
            return
        
        pattern, weight = sender.Tag
        
        for row in self.grid.SelectedRows:
            layer = self.filtered_layers[row.Index]
            if weight is not None:
                layer.new_weight = weight
            if pattern is not None:
                layer.new_pattern = pattern
        
        self._update_changes_display()
    
    def _apply_batch(self, weight_only=False, pattern_only=False):
        """Apply batch changes to selected layers."""
        if self.grid.SelectedRows.Count == 0:
            forms.alert("Select layers first", title="No Selection")
            return
        
        for row in self.grid.SelectedRows:
            layer = self.filtered_layers[row.Index]
            
            if not pattern_only and self.chk_lw.Checked:
                layer.new_weight = int(self.cmb_lw.SelectedItem)
            
            if not weight_only and self.chk_lp.Checked:
                layer.new_pattern = str(self.cmb_lp.SelectedItem)
        
        self._update_changes_display()
    
    def _update_info_label(self):
        """Update info label with current status and pending changes."""
        pending_count = sum(1 for layer in self.all_layers if layer.has_changes())
        if pending_count > 0:
            self.lbl_info.Text = "Showing {} of {} layers | {} PENDING CHANGES - Click 'Apply All Pending Changes' button".format(
                len(self.filtered_layers), len(self.all_layers), pending_count)
            self.lbl_info.ForeColor = Color.FromArgb(200, 0, 0)  # Red text
            self.lbl_info.Font = Font("Segoe UI", 9, FontStyle.Bold)
        else:
            self.lbl_info.Text = "Showing {} of {} layers | Select rows to batch edit".format(
                len(self.filtered_layers), len(self.all_layers))
            self.lbl_info.ForeColor = Color.Black
            self.lbl_info.Font = Font("Segoe UI", 9, FontStyle.Regular)
    
    def _update_changes_display(self):
        """Update the changes display in grid."""
        changes_count = sum(1 for layer in self.all_layers if layer.has_changes())
        
        # Update grid colors and text
        for i, row in enumerate(self.grid.Rows):
            if i < len(self.filtered_layers):
                layer = self.filtered_layers[i]
                row.Cells["col_changes"].Value = layer.get_changes_text()
                
                if layer.has_changes():
                    row.DefaultCellStyle.BackColor = Color.FromArgb(255, 255, 200)
                else:
                    row.DefaultCellStyle.BackColor = Color.White
        
        # Update apply button
        self.btn_apply.Text = "Apply All Pending Changes ({})".format(changes_count)
        self.btn_apply.Enabled = changes_count > 0
        
        # Change button color based on whether there are changes
        if changes_count > 0:
            self.btn_apply.BackColor = Color.FromArgb(50, 200, 50)  # Green
        else:
            self.btn_apply.BackColor = Color.FromArgb(150, 150, 150)  # Gray
        
        # Update info label
        self._update_info_label()
        
        self.grid.Refresh()
    
    def _clear_all_changes(self, sender, e):
        """Clear all pending changes."""
        for layer in self.all_layers:
            layer.clear_changes()
        self._update_changes_display()
    
    def _apply_all_changes(self, sender, e):
        """Apply all pending changes to Revit."""
        layers_with_changes = [l for l in self.all_layers if l.has_changes()]
        
        if not layers_with_changes:
            return
        
        # Confirm
        result = forms.alert(
            "Apply changes to {} layers?".format(len(layers_with_changes)),
            title="Confirm Changes",
            ok=False,
            yes=True,
            no=True
        )
        
        if not result:
            return
        
        # Apply in transaction
        success_count = 0
        with revit.Transaction("Apply CAD Layer Changes"):
            for layer in layers_with_changes:
                if layer.apply_changes():
                    success_count += 1
                layer.clear_changes()
        
        self._update_changes_display()
        
        forms.alert(
            "Successfully applied {} changes!".format(success_count),
            title="Success"
        )
        
        self.DialogResult = DialogResult.OK
        self.Close()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution."""
    # Get CAD data
    cad_data = get_cad_files()
    
    if not cad_data:
        forms.alert("No linked CAD files found in the document.", title="No CAD Files")
        return
    
    total_layers = sum(len(layers) for layers in cad_data.values())
    logger.info("Found {} CAD files with {} total layers".format(len(cad_data), total_layers))
    
    # Show form
    form = CADLayerManagerForm(cad_data)
    form.ShowDialog()


if __name__ == '__main__':
    main()