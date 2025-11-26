# -*- coding: utf-8 -*-
"""
Two-step interface for managing CAD link line styles.

This script provides a comprehensive two-step interface:
1. Select specific linked CAD files to modify
2. Manage layers from selected CAD files with enhanced headers
"""

print("Starting imports...")

try:
    print("Importing pyrevit...")
    from pyrevit import revit, DB
    from pyrevit import script
    print("pyrevit imported successfully")
except Exception as e:
    print("Error importing pyrevit: {}".format(e))
    raise

try:
    print("Importing clr...")
    import clr
    clr.AddReference('System.Windows.Forms')
    clr.AddReference('System.Drawing')
    print("clr imported successfully")
except Exception as e:
    print("Error importing clr: {}".format(e))
    raise

try:
    print("Importing System.Windows.Forms...")
    from System.Windows.Forms import (
        Form, DataGridView, Button, DockStyle, FormBorderStyle,
        DataGridViewAutoSizeColumnsMode, DataGridViewSelectionMode,
        DataGridViewCheckBoxColumn, DataGridViewTextBoxColumn,
        DataGridViewComboBoxColumn, DialogResult, ListView, ListViewItem,
        ColumnHeader, View, Panel, FormStartPosition, AnchorStyles,
        TextBox, Label, Padding, DataGridViewEditMode, DataGridViewHitTestType,
        RadioButton, GroupBox, ComboBox, ComboBoxStyle, ListBox
    )
    print("System.Windows.Forms imported successfully")
except Exception as e:
    print("Error importing System.Windows.Forms: {}".format(e))
    raise

try:
    print("Importing System.Drawing and System.ComponentModel...")
    from System.Drawing import Size, Point, Color, Font, FontStyle
    from System.ComponentModel import BindingList
    print("System.Drawing and System.ComponentModel imported successfully")
except Exception as e:
    print("Error importing System.Drawing/ComponentModel: {}".format(e))
    raise

print("All imports completed successfully")

# Create a logger for this script
try:
    print("Creating logger...")
    logger = script.get_logger()
    print("Logger created successfully")
except Exception as e:
    print("Error creating logger: {}".format(e))
    print("Error type: {}".format(type(e)))
    # Create a fallback logger that just prints
    class FallbackLogger:
        def info(self, msg): print("INFO: {}".format(msg))
        def error(self, msg): print("ERROR: {}".format(msg))
    logger = FallbackLogger()

# Access the current Revit document
try:
    print("Accessing Revit document...")
    doc = revit.doc
    uidoc = revit.uidoc
    print("Revit document accessed successfully")
except Exception as e:
    print("Error accessing Revit document: {}".format(e))
    raise

class LinkedCADFile:
    """Represents a linked CAD file for selection."""
    def __init__(self, cad_link_instance, cad_link_type):
        try:
            logger.info("Creating LinkedCADFile...")
            self.cad_link_instance = cad_link_instance
            self.cad_link_type = cad_link_type
            
            if cad_link_type:
                try:
                    # Try getting name from parameter first, as it's more reliable
                    param = cad_link_type.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)
                    if param and param.HasValue:
                        name_value = param.AsString()
                        logger.info("Parameter name type: {}, value: {}".format(type(name_value), name_value))
                        self.name = str(name_value)  # Ensure it's a string
                    else:
                        # Fallback to the .Name property
                        name_value = cad_link_type.Name
                        logger.info("Type.Name type: {}, value: {}".format(type(name_value), name_value))
                        self.name = str(name_value)  # Ensure it's a string
                except Exception as e:
                    logger.error("Could not get name for CAD link type {}: {}".format(cad_link_type.Id, e))
                    logger.error("Error type: {}".format(type(e)))
                    self.name = "Unnamed CAD"
            else:
                self.name = "Unnamed CAD"
            
            logger.info("Getting file path...")
            self.file_path = self._get_file_path()
            self.selected = False
            logger.info("LinkedCADFile created successfully")
        except Exception as e:
            logger.error("Error in LinkedCADFile constructor: {}".format(e))
            logger.error("Error type: {}".format(type(e)))
            import traceback
            logger.error("Traceback: {}".format(traceback.format_exc()))
            raise
        
    def _get_file_path(self):
        """Get the absolute file path of the linked CAD."""
        try:
            ext_ref = self.cad_link_type.GetExternalFileReference()
            if ext_ref:
                # Convert the FilePath object to a string
                return str(ext_ref.GetAbsolutePath())
        except:
            pass
        return "Path not available"
    
    def __str__(self):
        return self.name

class EnhancedCadLayer:
    """Enhanced CAD layer with source file reference."""
    def __init__(self, cad_link_name, category, source_cad_file):
        logger.info("Creating EnhancedCadLayer with cad_link_name type: {}, value: {}".format(type(cad_link_name), cad_link_name))

        # Ensure cad_link_name is a string
        self.cad_link_name = str(cad_link_name) if cad_link_name is not None else "Unknown CAD"
        self.category = category
        self.source_cad_file = source_cad_file

        try:
            if category and hasattr(category, 'Name'):
                name_value = category.Name
                logger.info("Category.Name type: {}, value: {}".format(type(name_value), name_value))
                self.name = str(name_value)  # Ensure it's a string
            else:
                self.name = "Unnamed Layer"
        except Exception as e:
            logger.error("Error getting category name: {}".format(e))
            self.name = "Layer {}".format(category.Id.IntegerValue if category else "Unknown")

        try:
            self.line_weight = category.GetLineWeight(DB.GraphicsStyleType.Projection) if category else 1
        except:
            self.line_weight = 1

        try:
            line_pattern_id = category.GetLinePatternId(DB.GraphicsStyleType.Projection)
            self._line_pattern_element = doc.GetElement(line_pattern_id) if line_pattern_id and line_pattern_id != DB.ElementId.InvalidElementId else None
            if self._line_pattern_element:
                pattern_name = self._line_pattern_element.Name
                logger.info("Line pattern element Name type: {}, value: {}".format(type(pattern_name), pattern_name))
                self.line_pattern = str(pattern_name)  # Ensure it's a string
            else:
                self.line_pattern = ""
        except Exception as e:
            logger.error("Error getting line pattern: {}".format(e))
            self._line_pattern_element = None
            self.line_pattern = ""

        # Removed selected property - using DataGridView row selection instead
        self.new_line_weight = "Default"
        self.new_line_pattern = "Default"

        # Track pending changes for this layer
        self.pending_changes = {}  # {'lw': value, 'lp': value}
    
    def __str__(self):
        return "{} - {}".format(self.cad_link_name, self.name)


class CADSelectionForm(Form):
    """First step: Select linked CAD files to modify."""
    
    def __init__(self, linked_cad_files):
        self.linked_cad_files = linked_cad_files
        logger.info("Initializing CADSelectionForm...")
        
        # Form setup
        self.Text = "Step 1: Select Linked CAD Files"
        self.Size = Size(600, 500)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        
        # Create ListView for CAD file selection
        self.list_view = ListView()
        self.list_view.Dock = DockStyle.Fill
        self.list_view.View = View.Details
        self.list_view.CheckBoxes = True
        self.list_view.FullRowSelect = True
        self.list_view.GridLines = True
        
        # Create columns
        self.create_columns()
        
        # Create buttons
        self.create_buttons()
        
        # Populate data
        self.populate_data()
        
        # Add controls to form
        self.Controls.Add(self.list_view)
        
    def create_columns(self):
        """Create ListView columns."""
        # CAD File Name column
        name_column = ColumnHeader()
        name_column.Text = "CAD File Name"
        name_column.Width = 200
        self.list_view.Columns.Add(name_column)
        
        # File Path column
        path_column = ColumnHeader()
        path_column.Text = "File Path"
        path_column.Width = 350
        self.list_view.Columns.Add(path_column)
        
    def create_buttons(self):
        """Create buttons for the form."""
        from System.Windows.Forms import Button
        
        # Button panel
        button_panel = Panel()
        button_panel.Dock = DockStyle.Bottom
        button_panel.Height = 50
        
        # Select All button
        self.select_all_btn = Button()
        self.select_all_btn.Text = "Select All"
        self.select_all_btn.Size = Size(100, 30)
        self.select_all_btn.Location = Point(10, 10)
        self.select_all_btn.Click += self.on_select_all_click
        
        # Deselect All button
        self.deselect_all_btn = Button()
        self.deselect_all_btn.Text = "Deselect All"
        self.deselect_all_btn.Size = Size(100, 30)
        self.deselect_all_btn.Location = Point(120, 10)
        self.deselect_all_btn.Click += self.on_deselect_all_click
        
        # Next button
        self.next_btn = Button()
        self.next_btn.Text = "Next →"
        self.next_btn.Size = Size(100, 30)
        self.next_btn.Location = Point(470, 10)
        self.next_btn.Click += self.on_next_click
        
        # Cancel button
        self.cancel_btn = Button()
        self.cancel_btn.Text = "Cancel"
        self.cancel_btn.Size = Size(100, 30)
        self.cancel_btn.Location = Point(360, 10)
        self.cancel_btn.Click += self.on_cancel_click
        
        button_panel.Controls.Add(self.select_all_btn)
        button_panel.Controls.Add(self.deselect_all_btn)
        button_panel.Controls.Add(self.next_btn)
        button_panel.Controls.Add(self.cancel_btn)
        
        self.Controls.Add(button_panel)
        
    def populate_data(self):
        """Populate the ListView with CAD file data."""
        for cad_file in self.linked_cad_files:
            item = ListViewItem()
            item.Checked = cad_file.selected
            item.Text = cad_file.name
            item.SubItems.Add(cad_file.file_path)
            item.Tag = cad_file
            self.list_view.Items.Add(item)
            
    def on_select_all_click(self, sender, e):
        """Handle Select All button click."""
        for item in self.list_view.Items:
            item.Checked = True
            
    def on_deselect_all_click(self, sender, e):
        """Handle Deselect All button click."""
        for item in self.list_view.Items:
            item.Checked = False
            
    def on_next_click(self, sender, e):
        """Handle Next button click."""
        # Update selection status
        selected_count = 0
        for item in self.list_view.Items:
            cad_file = item.Tag
            cad_file.selected = item.Checked
            if item.Checked:
                selected_count += 1
                
        if selected_count == 0:
            from pyrevit import forms
            forms.alert("Please select at least one CAD file to continue.", title="Selection Required")
            return
            
        self.DialogResult = DialogResult.OK
        self.Close()
        
    def on_cancel_click(self, sender, e):
        """Handle Cancel button click."""
        self.DialogResult = DialogResult.Cancel
        self.Close()

class EnhancedBatchLayerEditor(Form):
    """Enhanced batch editor for CAD layer management with intuitive UI."""

    def __init__(self, layers, line_patterns, line_weights):
        try:
            print("EnhancedBatchLayerEditor: Setting instance variables...")
            self.layers = layers
            self.all_layers = layers[:]  # Keep a copy of all layers for filtering
            self.line_patterns = line_patterns
            self.line_weights = line_weights

            # Track pending changes
            self.pending_changes = {}  # {layer_index: {'lw': value, 'lp': value}}

            logger.info("Initializing EnhancedBatchLayerEditor...")

            print("EnhancedBatchLayerEditor: Setting up form properties...")
            # Form setup
            self.Text = "Batch CAD Layer Editor"
            self.Size = Size(1200, 800)
            self.FormBorderStyle = FormBorderStyle.Sizable
            self.StartPosition = FormStartPosition.CenterScreen
            self.MinimumSize = Size(1000, 600)
            
            print("EnhancedBatchLayerEditor: Creating main layout...")
            # Create main layout with all panels
            self.create_main_layout()

            print("EnhancedBatchLayerEditor: Constructor completed successfully")
        except Exception as e:
            print("Error in EnhancedBatchLayerEditor constructor: {}".format(e))
            print("Error type: {}".format(type(e)))
            import traceback
            print("Traceback: {}".format(traceback.format_exc()))
            raise

    def create_main_layout(self):
        """Create the main layout with all panels."""

        # Quick presets panel (top)
        self.preset_panel = self.create_preset_panel()
        self.preset_panel.Dock = DockStyle.Top
        self.preset_panel.Height = 80

        # Filter panel
        self.filter_panel = self.create_filter_panel()
        self.filter_panel.Dock = DockStyle.Top
        self.filter_panel.Height = 40

        # Bottom panel (buttons)
        self.button_panel = self.create_button_panel()
        self.button_panel.Dock = DockStyle.Bottom
        self.button_panel.Height = 50

        # Preview panel (above buttons)
        self.preview_panel = self.create_preview_panel()
        self.preview_panel.Dock = DockStyle.Bottom
        self.preview_panel.Height = 100

        # Batch editor panel (bottom section)
        self.batch_editor_panel = self.create_batch_editor_panel()
        self.batch_editor_panel.Dock = DockStyle.Bottom
        self.batch_editor_panel.Height = 150

        # DataGridView (fills remaining space)
        self.grid_panel = self.create_grid_panel()
        self.grid_panel.Dock = DockStyle.Fill

        # Add controls in correct order (bottom-up for DockStyle.Bottom)
        self.Controls.Add(self.grid_panel)  # Adds last, fills middle
        self.Controls.Add(self.batch_editor_panel)
        self.Controls.Add(self.preview_panel)
        self.Controls.Add(self.button_panel)
        self.Controls.Add(self.filter_panel)
        self.Controls.Add(self.preset_panel)

    def create_preset_panel(self):
        """Create quick preset buttons panel."""
        panel = Panel()
        panel.BackColor = Color.FromArgb(240, 240, 240)

        # Title
        title = Label()
        title.Text = "QUICK PRESETS:"
        title.Font = Font("Segoe UI", 9, FontStyle.Bold)
        title.Location = Point(10, 10)
        title.AutoSize = True

        # Preset buttons - Row 1
        btn_solid_lw1 = Button()
        btn_solid_lw1.Text = "Solid + LW1"
        btn_solid_lw1.Size = Size(100, 25)
        btn_solid_lw1.Location = Point(10, 35)
        btn_solid_lw1.Click += lambda s, e: self.apply_preset("Solid", "1")

        btn_dashed_lw1 = Button()
        btn_dashed_lw1.Text = "Dashed + LW1"
        btn_dashed_lw1.Size = Size(100, 25)
        btn_dashed_lw1.Location = Point(120, 35)
        btn_dashed_lw1.Click += lambda s, e: self.apply_preset("Dashed", "1")

        btn_solid_lw2 = Button()
        btn_solid_lw2.Text = "Solid + LW2"
        btn_solid_lw2.Size = Size(100, 25)
        btn_solid_lw2.Location = Point(230, 35)
        btn_solid_lw2.Click += lambda s, e: self.apply_preset("Solid", "2")

        btn_lw1_only = Button()
        btn_lw1_only.Text = "LW1 Only"
        btn_lw1_only.Size = Size(100, 25)
        btn_lw1_only.Location = Point(340, 35)
        btn_lw1_only.Click += lambda s, e: self.apply_preset(None, "1")

        btn_lw2_only = Button()
        btn_lw2_only.Text = "LW2 Only"
        btn_lw2_only.Size = Size(100, 25)
        btn_lw2_only.Location = Point(450, 35)
        btn_lw2_only.Click += lambda s, e: self.apply_preset(None, "2")

        btn_reset = Button()
        btn_reset.Text = "Reset Selected"
        btn_reset.Size = Size(100, 25)
        btn_reset.Location = Point(560, 35)
        btn_reset.BackColor = Color.FromArgb(255, 230, 230)
        btn_reset.Click += self.reset_selected

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [title, btn_solid_lw1, btn_dashed_lw1,
                     btn_solid_lw2, btn_lw1_only, btn_lw2_only, btn_reset]:
            control_list.Add(ctrl)
        panel.Controls.AddRange(control_list.ToArray(Control))

        return panel

    def create_filter_panel(self):
        """Create filter panel."""
        panel = Panel()
        panel.BackColor = Color.White

        # Filter label
        lbl = Label()
        lbl.Text = "Filter:"
        lbl.Location = Point(10, 12)
        lbl.Size = Size(50, 20)

        # Search textbox
        self.txt_filter = TextBox()
        self.txt_filter.Location = Point(60, 10)
        self.txt_filter.Size = Size(200, 20)
        self.txt_filter.TextChanged += self.on_filter_changed

        # CAD file filter
        lbl_cad = Label()
        lbl_cad.Text = "CAD File:"
        lbl_cad.Location = Point(270, 12)
        lbl_cad.Size = Size(60, 20)

        self.cmb_cad_filter = ComboBox()
        self.cmb_cad_filter.Location = Point(330, 10)
        self.cmb_cad_filter.Size = Size(200, 20)
        self.cmb_cad_filter.DropDownStyle = ComboBoxStyle.DropDownList
        self.cmb_cad_filter.Items.Add("All CAD Files")

        # Populate unique CAD files
        unique_cads = set(layer.cad_link_name for layer in self.all_layers)
        for cad_name in sorted(unique_cads):
            self.cmb_cad_filter.Items.Add(cad_name)
        self.cmb_cad_filter.SelectedIndex = 0
        self.cmb_cad_filter.SelectedIndexChanged += self.on_filter_changed

        # Clear button
        btn_clear = Button()
        btn_clear.Text = "Clear Filter"
        btn_clear.Location = Point(540, 9)
        btn_clear.Size = Size(80, 22)
        btn_clear.Click += self.clear_filter

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [lbl, self.txt_filter, lbl_cad,
                     self.cmb_cad_filter, btn_clear]:
            control_list.Add(ctrl)
        panel.Controls.AddRange(control_list.ToArray(Control))

        return panel

    def create_grid_panel(self):
        """Create DataGridView panel."""
        panel = Panel()

        # Label
        lbl = Label()
        lbl.Text = "LAYERS (Select multiple with Ctrl/Shift click):"
        lbl.Dock = DockStyle.Top
        lbl.Height = 25
        lbl.Font = Font("Segoe UI", 9, FontStyle.Bold)
        lbl.Padding = Padding(5, 5, 0, 0)

        # DataGridView
        self.grid = DataGridView()
        self.grid.Dock = DockStyle.Fill
        self.grid.AutoGenerateColumns = False
        self.grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        self.grid.MultiSelect = True
        self.grid.AllowUserToAddRows = False
        self.grid.AllowUserToDeleteRows = False
        self.grid.ReadOnly = True
        self.grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
        self.grid.SelectionChanged += self.on_selection_changed

        # Columns
        col_layer = DataGridViewTextBoxColumn()
        col_layer.HeaderText = "Layer Name"
        col_layer.DataPropertyName = "name"
        col_layer.FillWeight = 30

        col_cad = DataGridViewTextBoxColumn()
        col_cad.HeaderText = "CAD File"
        col_cad.DataPropertyName = "cad_link_name"
        col_cad.FillWeight = 25

        col_cur_lw = DataGridViewTextBoxColumn()
        col_cur_lw.HeaderText = "Current LW"
        col_cur_lw.DataPropertyName = "line_weight"
        col_cur_lw.FillWeight = 15

        col_cur_lp = DataGridViewTextBoxColumn()
        col_cur_lp.HeaderText = "Current Pattern"
        col_cur_lp.DataPropertyName = "line_pattern"
        col_cur_lp.FillWeight = 20

        col_changes = DataGridViewTextBoxColumn()
        col_changes.HeaderText = "Pending Changes"
        col_changes.Name = "pending_changes"
        col_changes.FillWeight = 25

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import DataGridViewColumn
        column_list = ArrayList()
        for col in [col_layer, col_cad, col_cur_lw, col_cur_lp, col_changes]:
            column_list.Add(col)
        self.grid.Columns.AddRange(column_list.ToArray(DataGridViewColumn))

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [self.grid, lbl]:
            control_list.Add(ctrl)
        panel.Controls.AddRange(control_list.ToArray(Control))

        # Populate grid
        self.populate_grid()

        return panel

    def create_batch_editor_panel(self):
        """Create batch editor panel with radio buttons."""
        panel = Panel()
        panel.BackColor = Color.FromArgb(250, 250, 250)

        # Title
        self.lbl_batch_title = Label()
        self.lbl_batch_title.Text = "BATCH EDITOR (0 layers selected):"
        self.lbl_batch_title.Font = Font("Segoe UI", 9, FontStyle.Bold)
        self.lbl_batch_title.Location = Point(10, 10)
        self.lbl_batch_title.AutoSize = True

        # Line Weight Group
        grp_lw = GroupBox()
        grp_lw.Text = "Line Weight"
        grp_lw.Location = Point(10, 35)
        grp_lw.Size = Size(250, 100)

        self.radio_lw_no_change = RadioButton()
        self.radio_lw_no_change.Text = "No change"
        self.radio_lw_no_change.Location = Point(10, 20)
        self.radio_lw_no_change.Size = Size(200, 20)
        self.radio_lw_no_change.Checked = True

        self.radio_lw_change = RadioButton()
        self.radio_lw_change.Text = "Change to:"
        self.radio_lw_change.Location = Point(10, 45)
        self.radio_lw_change.Size = Size(80, 20)

        self.cmb_batch_lw = ComboBox()
        self.cmb_batch_lw.Location = Point(90, 43)
        self.cmb_batch_lw.Size = Size(60, 20)
        self.cmb_batch_lw.DropDownStyle = ComboBoxStyle.DropDownList
        for i in range(1, 17):
            self.cmb_batch_lw.Items.Add(str(i))
        self.cmb_batch_lw.SelectedIndex = 0

        btn_apply_lw = Button()
        btn_apply_lw.Text = "Apply to Selected"
        btn_apply_lw.Location = Point(10, 70)
        btn_apply_lw.Size = Size(120, 23)
        btn_apply_lw.Click += self.apply_batch_line_weight

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [self.radio_lw_no_change, self.radio_lw_change,
                     self.cmb_batch_lw, btn_apply_lw]:
            control_list.Add(ctrl)
        grp_lw.Controls.AddRange(control_list.ToArray(Control))

        # Line Pattern Group
        grp_lp = GroupBox()
        grp_lp.Text = "Line Pattern"
        grp_lp.Location = Point(270, 35)
        grp_lp.Size = Size(350, 100)

        self.radio_lp_no_change = RadioButton()
        self.radio_lp_no_change.Text = "No change"
        self.radio_lp_no_change.Location = Point(10, 20)
        self.radio_lp_no_change.Size = Size(200, 20)
        self.radio_lp_no_change.Checked = True

        self.radio_lp_change = RadioButton()
        self.radio_lp_change.Text = "Change to:"
        self.radio_lp_change.Location = Point(10, 45)
        self.radio_lp_change.Size = Size(80, 20)

        self.cmb_batch_lp = ComboBox()
        self.cmb_batch_lp.Location = Point(90, 43)
        self.cmb_batch_lp.Size = Size(150, 20)
        self.cmb_batch_lp.DropDownStyle = ComboBoxStyle.DropDownList

        # Populate line patterns
        for pattern in self.line_patterns.values():
            if pattern:
                self.cmb_batch_lp.Items.Add(pattern.Name)
        if self.cmb_batch_lp.Items.Count > 0:
            self.cmb_batch_lp.SelectedIndex = 0

        btn_apply_lp = Button()
        btn_apply_lp.Text = "Apply to Selected"
        btn_apply_lp.Location = Point(10, 70)
        btn_apply_lp.Size = Size(120, 23)
        btn_apply_lp.Click += self.apply_batch_line_pattern

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [self.radio_lp_no_change, self.radio_lp_change,
                     self.cmb_batch_lp, btn_apply_lp]:
            control_list.Add(ctrl)
        grp_lp.Controls.AddRange(control_list.ToArray(Control))

        # Apply Both Button
        btn_apply_both = Button()
        btn_apply_both.Text = "Apply Both to Selected"
        btn_apply_both.Location = Point(630, 75)
        btn_apply_both.Size = Size(150, 30)
        btn_apply_both.Font = Font("Segoe UI", 9, FontStyle.Bold)
        btn_apply_both.BackColor = Color.FromArgb(220, 240, 255)
        btn_apply_both.Click += self.apply_batch_both

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [self.lbl_batch_title, grp_lw, grp_lp, btn_apply_both]:
            control_list.Add(ctrl)
        panel.Controls.AddRange(control_list.ToArray(Control))

        return panel

    def create_preview_panel(self):
        """Create preview panel showing pending changes."""
        panel = Panel()
        panel.BackColor = Color.FromArgb(255, 255, 240)

        # Title
        lbl_title = Label()
        lbl_title.Text = "PREVIEW:"
        lbl_title.Font = Font("Segoe UI", 9, FontStyle.Bold)
        lbl_title.Location = Point(10, 10)
        lbl_title.AutoSize = True

        # Preview listbox
        self.lst_preview = ListBox()
        self.lst_preview.Location = Point(10, 35)
        self.lst_preview.Size = Size(760, 55)
        self.lst_preview.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [lbl_title, self.lst_preview]:
            control_list.Add(ctrl)
        panel.Controls.AddRange(control_list.ToArray(Control))

        return panel

    def create_button_panel(self):
        """Create bottom button panel."""
        panel = Panel()

        btn_back = Button()
        btn_back.Text = "← Back"
        btn_back.Location = Point(10, 10)
        btn_back.Size = Size(100, 30)
        btn_back.Click += lambda s, e: self.on_back()

        btn_clear_changes = Button()
        btn_clear_changes.Text = "Clear All Changes"
        btn_clear_changes.Location = Point(120, 10)
        btn_clear_changes.Size = Size(130, 30)
        btn_clear_changes.Click += self.clear_all_changes

        self.btn_apply = Button()
        self.btn_apply.Text = "Apply All Changes (0 items)"
        self.btn_apply.Location = Point(650, 10)
        self.btn_apply.Size = Size(180, 30)
        self.btn_apply.Anchor = AnchorStyles.Top | AnchorStyles.Right
        self.btn_apply.Font = Font("Segoe UI", 9, FontStyle.Bold)
        self.btn_apply.BackColor = Color.FromArgb(200, 255, 200)
        self.btn_apply.Click += self.apply_all_changes

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [btn_back, btn_clear_changes, self.btn_apply]:
            control_list.Add(ctrl)
        panel.Controls.AddRange(control_list.ToArray(Control))

        return panel

    def create_filter_panel(self):
        """Create filter panel for searching layers."""
        # Filter panel
        filter_panel = Panel()
        filter_panel.Dock = DockStyle.Top
        filter_panel.Height = 40

        # Filter label
        filter_label = Label()
        filter_label.Text = "Filter layers:"
        filter_label.Location = Point(10, 12)
        filter_label.Size = Size(80, 20)

        # Filter textbox
        self.filter_textbox = TextBox()
        self.filter_textbox.Location = Point(95, 10)
        self.filter_textbox.Size = Size(200, 20)
        self.filter_textbox.TextChanged += self.on_filter_text_changed

        # Clear filter button
        clear_filter_btn = Button()
        clear_filter_btn.Text = "Clear"
        clear_filter_btn.Location = Point(305, 9)
        clear_filter_btn.Size = Size(60, 22)
        clear_filter_btn.Click += self.on_clear_filter_click

        # Convert list to .NET Array for IronPython compatibility
        from System.Collections import ArrayList
        from System.Windows.Forms import Control
        control_list = ArrayList()
        for ctrl in [filter_label, self.filter_textbox, clear_filter_btn]:
            control_list.Add(ctrl)
        filter_panel.Controls.AddRange(control_list.ToArray(Control))

        return filter_panel
        
    def populate_grid(self):
        """Populate grid with layer data."""
        from System.Collections import ArrayList
        binding_list = ArrayList()
        for layer in self.layers:
            binding_list.Add(layer)
        self.grid.DataSource = binding_list
        self.update_pending_changes_column()

    def on_selection_changed(self, sender, e):
        """Handle selection changes."""
        selected_count = self.grid.SelectedRows.Count
        self.lbl_batch_title.Text = "BATCH EDITOR ({} layers selected):".format(selected_count)

    def on_filter_changed(self, sender, e):
        """Handle filter changes."""
        filter_text = self.txt_filter.Text.lower()
        cad_filter = self.cmb_cad_filter.SelectedItem

        filtered = []
        for layer in self.all_layers:
            # Text filter
            text_match = (filter_text in layer.name.lower() or
                         filter_text in layer.cad_link_name.lower())

            # CAD filter
            cad_match = (cad_filter == "All CAD Files" or
                        cad_filter == layer.cad_link_name)

            if text_match and cad_match:
                filtered.append(layer)

        self.layers = filtered
        self.populate_grid()

    def clear_filter(self, sender, e):
        """Clear all filters."""
        self.txt_filter.Text = ""
        self.cmb_cad_filter.SelectedIndex = 0

    def apply_preset(self, line_pattern, line_weight):
        """Apply preset to selected layers immediately."""
        selected_rows = self.grid.SelectedRows
        if selected_rows.Count == 0:
            from pyrevit import forms
            forms.alert("Please select layers first", title="No Selection")
            return

        from pyrevit import forms, revit, DB

        # Show confirmation
        preset_name = []
        if line_pattern:
            preset_name.append(line_pattern)
        if line_weight:
            preset_name.append("LW{}".format(line_weight))
        preset_desc = " + ".join(preset_name)

        confirm = forms.alert(
            "Apply '{}' preset to {} selected layers?".format(preset_desc, selected_rows.Count),
            title="Confirm Preset Application",
            ok=False,
            yes=True,
            no=True
        )

        if not confirm:
            return

        # Apply changes immediately
        applied_count = 0
        try:
            with revit.Transaction("Apply CAD Layer Preset"):
                for row in selected_rows:
                    layer_index = row.Index
                    if layer_index >= len(self.all_layers):
                        continue

                    layer = self.all_layers[layer_index]

                    # Apply line weight
                    if line_weight:
                        try:
                            layer.category.SetLineWeight(
                                int(line_weight),
                                DB.GraphicsStyleType.Projection
                            )
                            applied_count += 1
                        except Exception as ex:
                            logger.error("Failed to set line weight for {}: {}".format(layer.name, ex))

                    # Apply line pattern
                    if line_pattern:
                        pattern = next((p for p in self.line_patterns.values()
                                      if p and p.Name == line_pattern), None)
                        if pattern:
                            try:
                                layer.category.SetLinePatternId(
                                    pattern.Id,
                                    DB.GraphicsStyleType.Projection
                                )
                                applied_count += 1
                            except Exception as ex:
                                logger.error("Failed to set line pattern for {}: {}".format(layer.name, ex))

        except Exception as tx_ex:
            logger.error("Transaction failed: {}".format(tx_ex))
            forms.alert("Failed to apply preset. See log for details.", title="Error")
            return

        forms.alert("Successfully applied '{}' preset to {} layers!".format(preset_desc, applied_count), title="Success")
        logger.info("Preset applied successfully to {} layers".format(applied_count))

    def reset_selected(self, sender, e):
        """Reset selected layers to remove pending changes."""
        selected_rows = self.grid.SelectedRows
        for row in selected_rows:
            layer_index = row.Index
            if layer_index in self.pending_changes:
                del self.pending_changes[layer_index]

        self.update_preview()
        self.update_pending_changes_column()

    def apply_batch_line_weight(self, sender, e):
        """Apply batch line weight to selected layers."""
        if not self.radio_lw_change.Checked:
            from pyrevit import forms
            forms.alert("Please select 'Change to' option first", title="No Change Selected")
            return

        selected_rows = self.grid.SelectedRows
        if selected_rows.Count == 0:
            from pyrevit import forms
            forms.alert("Please select layers first", title="No Selection")
            return

        lw_value = self.cmb_batch_lw.SelectedItem

        for row in selected_rows:
            layer_index = row.Index
            if layer_index not in self.pending_changes:
                self.pending_changes[layer_index] = {}
            self.pending_changes[layer_index]['lw'] = str(lw_value)

        self.update_preview()
        self.update_pending_changes_column()

    def apply_batch_line_pattern(self, sender, e):
        """Apply batch line pattern to selected layers."""
        if not self.radio_lp_change.Checked:
            from pyrevit import forms
            forms.alert("Please select 'Change to' option first", title="No Change Selected")
            return

        selected_rows = self.grid.SelectedRows
        if selected_rows.Count == 0:
            from pyrevit import forms
            forms.alert("Please select layers first", title="No Selection")
            return

        lp_value = self.cmb_batch_lp.SelectedItem

        for row in selected_rows:
            layer_index = row.Index
            if layer_index not in self.pending_changes:
                self.pending_changes[layer_index] = {}
            self.pending_changes[layer_index]['lp'] = str(lp_value)

        self.update_preview()
        self.update_pending_changes_column()

    def apply_batch_both(self, sender, e):
        """Apply both line weight and pattern to selected layers."""
        selected_rows = self.grid.SelectedRows
        if selected_rows.Count == 0:
            from pyrevit import forms
            forms.alert("Please select layers first", title="No Selection")
            return

        for row in selected_rows:
            layer_index = row.Index
            if layer_index not in self.pending_changes:
                self.pending_changes[layer_index] = {}

            if self.radio_lw_change.Checked:
                self.pending_changes[layer_index]['lw'] = str(self.cmb_batch_lw.SelectedItem)

            if self.radio_lp_change.Checked:
                self.pending_changes[layer_index]['lp'] = str(self.cmb_batch_lp.SelectedItem)

        self.update_preview()
        self.update_pending_changes_column()

    def update_preview(self):
        """Update preview listbox with pending changes."""
        self.lst_preview.Items.Clear()

        if not self.pending_changes:
            self.lst_preview.Items.Add("No pending changes")
            self.btn_apply.Text = "Apply All Changes (0 items)"
            self.btn_apply.Enabled = False
            return

        # Count changes by type
        lw_changes = sum(1 for c in self.pending_changes.values() if 'lw' in c)
        lp_changes = sum(1 for c in self.pending_changes.values() if 'lp' in c)

        self.lst_preview.Items.Add("{} layers will be modified:".format(len(self.pending_changes)))
        if lw_changes > 0:
            self.lst_preview.Items.Add("  • {} layers - Line Weight changes".format(lw_changes))
        if lp_changes > 0:
            self.lst_preview.Items.Add("  • {} layers - Line Pattern changes".format(lp_changes))

        self.btn_apply.Text = "Apply All Changes ({} items)".format(len(self.pending_changes))
        self.btn_apply.Enabled = True

    def update_pending_changes_column(self):
        """Update the pending changes column in grid."""
        for i in range(self.grid.Rows.Count):
            row = self.grid.Rows[i]
            if i in self.pending_changes:
                changes = self.pending_changes[i]
                change_text = []
                if 'lw' in changes:
                    change_text.append("LW:{}".format(changes['lw']))
                if 'lp' in changes:
                    change_text.append("LP:{}".format(changes['lp']))
                row.Cells["pending_changes"].Value = " | ".join(change_text)
                row.DefaultCellStyle.BackColor = Color.FromArgb(255, 255, 200)
            else:
                row.Cells["pending_changes"].Value = ""
                row.DefaultCellStyle.BackColor = Color.White

    def clear_all_changes(self, sender, e):
        """Clear all pending changes."""
        self.pending_changes.clear()
        self.update_preview()
        self.update_pending_changes_column()

    def apply_all_changes(self, sender, e):
        """Apply all pending changes in one transaction."""
        if not self.pending_changes:
            from pyrevit import forms
            forms.alert("No changes to apply.", title="Info")
            return

        from pyrevit import forms, revit, DB

        # Debug: Log pending changes
        logger.info("Applying {} pending changes".format(len(self.pending_changes)))
        for idx, changes in self.pending_changes.items():
            logger.info("Layer {}: {}".format(idx, changes))

        # Show confirmation
        confirm = forms.alert(
            "Apply {} changes to layers?".format(len(self.pending_changes)),
            title="Confirm Changes",
            ok=False,
            yes=True,
            no=True
        )

        if not confirm:
            logger.info("User cancelled changes")
            return

        logger.info("Starting transaction...")

        # Apply changes in single transaction
        try:
            with revit.Transaction("Batch Edit CAD Layers"):
                applied_count = 0
                for layer_index, changes in self.pending_changes.items():
                    if layer_index >= len(self.all_layers):
                        logger.warning("Layer index {} out of range".format(layer_index))
                        continue

                    layer = self.all_layers[layer_index]
                    logger.info("Processing layer: {} (index {})".format(layer.name, layer_index))

                    # Apply line weight change
                    if 'lw' in changes:
                        try:
                            new_weight = int(changes['lw'])
                            logger.info("Setting line weight to {} for layer {}".format(new_weight, layer.name))
                            layer.category.SetLineWeight(
                                new_weight,
                                DB.GraphicsStyleType.Projection
                            )
                            applied_count += 1
                        except Exception as ex:
                            logger.error("Failed to set line weight for {}: {}".format(
                                layer.name, ex))

                    # Apply line pattern change
                    if 'lp' in changes:
                        pattern_name = changes['lp']
                        logger.info("Setting line pattern to '{}' for layer {}".format(pattern_name, layer.name))
                        pattern = next((p for p in self.line_patterns.values()
                                      if p and p.Name == pattern_name), None)
                        if pattern:
                            try:
                                layer.category.SetLinePatternId(
                                    pattern.Id,
                                    DB.GraphicsStyleType.Projection
                                )
                                applied_count += 1
                            except Exception as ex:
                                logger.error("Failed to set line pattern for {}: {}".format(
                                    layer.name, ex))
                        else:
                            logger.error("Pattern '{}' not found".format(pattern_name))

                logger.info("Applied {} changes successfully".format(applied_count))

        except Exception as tx_ex:
            logger.error("Transaction failed: {}".format(tx_ex))
            forms.alert("Failed to apply changes. See log for details.", title="Error")
            return

        # Clear all changes after applying
        self.pending_changes.clear()
        self.update_preview()
        self.update_pending_changes_column()

        forms.alert("Successfully applied {} changes to layers!".format(applied_count), title="Success")
        logger.info("Changes applied successfully")
        self.DialogResult = DialogResult.OK
        self.Close()

    def on_back(self):
        """Handle back button."""
        self.DialogResult = DialogResult.Retry
        self.Close()

    def populate_data(self):
        """Populate the DataGridView with layer data."""
        try:
            count = len(self.layers)
            logger.info("Populating DataGridView with {} layers".format(str(count)))
        except Exception as e:
            logger.info("Populating DataGridView with layers (count error)")

        # Add diagnostic logging for layer properties
        for i, layer in enumerate(self.layers):
            try:
                logger.info("Layer {}: name type={}, value={}".format(i, type(layer.name), layer.name))
                logger.info("Layer {}: cad_link_name type={}, value={}".format(i, type(layer.cad_link_name), layer.cad_link_name))
                logger.info("Layer {}: line_pattern type={}, value={}".format(i, type(layer.line_pattern), layer.line_pattern))
            except Exception as e:
                logger.error("Error checking layer {} properties: {}".format(i, e))

        # Fix for IronPython generic type issue - use simple list instead
        from System.Collections import ArrayList
        binding_list = ArrayList()

        for layer in self.layers:
            binding_list.Add(layer)
        self.grid.DataSource = binding_list


    def on_select_all_click(self, sender, e):
        """Handle Select All button click."""
        self.grid.SelectAll()

    def get_selected_layers(self):
        """Get currently selected rows as layers."""
        selected_rows = self.grid.SelectedRows
        selected_layers = []

        for row in selected_rows:
            if row.Index < len(self.layers):
                selected_layers.append(self.layers[row.Index])

        return selected_layers

    def on_cell_value_changed(self, sender, e):
        """Handle cell value changes for batch editing."""
        try:
            # Only handle changes to New Line Weight and New Line Pattern columns
            if e.ColumnIndex < 0 or e.RowIndex < 0:
                return

            column_name = self.grid.Columns[e.ColumnIndex].Name
            if column_name not in ["NewLW", "NewLP"]:
                return

            # Get the new value
            new_value = self.grid.Rows[e.RowIndex].Cells[e.ColumnIndex].Value
            if new_value is None:
                return

            # Get all selected layers
            selected_layers = self.get_selected_layers()

            # If multiple layers are selected, apply the change to all selected layers
            if len(selected_layers) > 1:
                for layer in selected_layers:
                    layer_index = self.layers.index(layer)
                    if column_name == "NewLW":
                        layer.new_line_weight = str(new_value)
                        self.grid.Rows[layer_index].Cells["NewLW"].Value = str(new_value)
                    elif column_name == "NewLP":
                        layer.new_line_pattern = str(new_value)
                        self.grid.Rows[layer_index].Cells["NewLP"].Value = str(new_value)

                # Refresh the grid to show all changes
                self.grid.Refresh()

        except Exception as ex:
            logger.error("Error in batch editing: {}".format(ex))

    def on_selection_changed(self, sender, e):
        """Handle selection changes to update UI feedback."""
        try:
            selected_count = self.grid.SelectedRows.Count
            self.lbl_batch_title.Text = "BATCH EDITOR ({} layers selected):".format(selected_count)
        except Exception as ex:
            logger.error("Error in selection changed: {}".format(ex))

    def on_cell_begin_edit(self, sender, e):
        """Handle cell begin edit to preserve selection."""
        try:
            # Store current selection before editing starts
            self._pre_edit_selection = []
            for row in self.grid.SelectedRows:
                self._pre_edit_selection.append(row.Index)
        except Exception as ex:
            logger.error("Error in cell begin edit: {}".format(ex))

    def on_cell_end_edit(self, sender, e):
        """Handle cell end edit to restore selection."""
        try:
            # Restore selection after editing
            if hasattr(self, '_pre_edit_selection') and self._pre_edit_selection:
                self.grid.ClearSelection()
                for row_index in self._pre_edit_selection:
                    if row_index < self.grid.Rows.Count:
                        self.grid.Rows[row_index].Selected = True
        except Exception as ex:
            logger.error("Error restoring selection after edit: {}".format(ex))

    def on_filter_text_changed(self, sender, e):
        """Handle filter text changes."""
        try:
            filter_text = self.filter_textbox.Text.lower()

            # Filter the layers based on the search text
            if not filter_text:
                # Show all layers if filter is empty
                filtered_layers = self.all_layers[:]
            else:
                # Filter layers that match the search criteria
                filtered_layers = []
                for layer in self.all_layers:
                    layer_name_match = filter_text in layer.name.lower()
                    cad_name_match = filter_text in layer.cad_link_name.lower()

                    if layer_name_match or cad_name_match:
                        filtered_layers.append(layer)

            # Update the current layers list and refresh the grid
            self.layers = filtered_layers
            self.refresh_grid()

        except Exception as ex:
            logger.error("Error in filter: {}".format(ex))

    def on_clear_filter_click(self, sender, e):
        """Handle clear filter button click."""
        try:
            self.filter_textbox.Text = ""
            # Reset to show all layers
            self.layers = self.all_layers[:]
            self.refresh_grid()
        except Exception as ex:
            logger.error("Error clearing filter: {}".format(ex))

    def refresh_grid(self):
        """Refresh the DataGridView with current layers."""
        try:
            # Create new data source with filtered layers
            from System.Collections import ArrayList
            binding_list = ArrayList()

            for layer in self.layers:
                binding_list.Add(layer)

            # Update the data source
            self.grid.DataSource = binding_list
            self.grid.Refresh()

        except Exception as ex:
            logger.error("Error refreshing grid: {}".format(ex))

    def on_back_click(self, sender, e):
        """Handle Back button click."""
        self.DialogResult = DialogResult.Retry # Using Retry to signify going back
        self.Close()

    def on_apply_click(self, sender, e):
        """Handle Apply button click."""
        from pyrevit import forms

        # Get selected layers from DataGridView selection
        selected_layers = self.get_selected_layers()

        changes = []
        # Check selected layers for changes
        for layer in selected_layers:
            if layer.new_line_weight != "Default" or layer.new_line_pattern != "Default":
                changes.append({
                    'layer': layer,
                    'new_lw': layer.new_line_weight,
                    'new_lp': layer.new_line_pattern
                })

        if not changes:
            forms.alert("No changes selected to apply.", title="Info")
            return

        # Show confirmation
        confirm_text = "Apply changes to {} layers?\n\n".format(len(changes))
        for change in changes[:10]: # Preview first 10 changes
            layer = change['layer']
            confirm_text += "• {} - {}: ".format(layer.cad_link_name, layer.name)
            if change['new_lw'] is not None:
                confirm_text += "LW {}→{} ".format(layer.line_weight, change['new_lw'])
            if change['new_lp'] is not None:
                confirm_text += "LP {}→{}".format(
                    layer.line_pattern if layer.line_pattern else "Default",
                    change['new_lp']
                )
            confirm_text += "\n"
        if len(changes) > 10:
            confirm_text += "\n...and {} more.".format(len(changes) - 10)


        confirm = forms.alert(confirm_text, title="Confirm Changes", ok=False, yes=True, no=True)
        if confirm:
            # Apply all changes in single transaction
            with revit.Transaction("Batch Edit CAD Link Styles"):
                for change in changes:
                    layer = change['layer']
                    if change['new_lw'] is not None and change['new_lw'] != "Default":
                        try:
                            layer.category.SetLineWeight(int(change['new_lw']), DB.GraphicsStyleType.Projection)
                        except Exception as ex:
                            logger.error("Failed to set line weight for layer {}: {}".format(layer.name, ex))
                    if change['new_lp'] is not None and change['new_lp'] != "Default":
                        pattern = next((p for p in self.line_patterns.values() if p and p.Name == change['new_lp']), None)
                        if pattern:
                            try:
                                layer.category.SetLinePatternId(pattern.Id, DB.GraphicsStyleType.Projection)
                            except Exception as ex:
                                logger.error("Failed to set line pattern for layer {}: {}".format(layer.name, ex))

            # Reset changes for all layers
            for layer in self.all_layers:
                layer.new_line_weight = "Default"
                layer.new_line_pattern = "Default"

            # Clear selection and refresh the current view
            self.grid.ClearSelection()
            self.refresh_grid()
            forms.alert("CAD link styles updated successfully!", title="Success")
            self.DialogResult = DialogResult.OK
            self.Close()

def get_linked_cad_files():
    """Get all linked CAD files from the document."""
    try:
        logger.info("Starting get_linked_cad_files...")
        cad_files = []
        cad_link_types = DB.FilteredElementCollector(doc).OfClass(DB.CADLinkType).ToElements()
        try:
            count = len(cad_link_types)
            logger.info("Found {} CAD link types".format(str(count)))
        except Exception as e:
            logger.info("Found CAD link types (count error)")
        
        # Using a dictionary to avoid duplicate CAD link types
        unique_cad_links = {}

        for i, link_type in enumerate(cad_link_types):
            try:
                logger.info("Processing CAD link type {}: {}".format(i, link_type.Id))
                # Find an instance of this link type to get the instance object
                collector = DB.FilteredElementCollector(doc).OfClass(DB.ImportInstance)
                instances = collector.WhereElementIsNotElementType().ToElements()
                
                for instance in instances:
                    if instance.IsLinked and instance.GetTypeId() == link_type.Id:
                        logger.info("Creating LinkedCADFile for type {}".format(link_type.Id))
                        unique_cad_links[link_type.Id.IntegerValue] = LinkedCADFile(instance, link_type)
                        break # Found an instance, no need to check others
            except Exception as e:
                logger.error("Error processing CAD link type {}: {}".format(i, e))
                logger.error("Error type: {}".format(type(e)))

        try:
            count = len(unique_cad_links)
            logger.info("Returning {} unique CAD links".format(str(count)))
        except Exception as e:
            logger.info("Returning unique CAD links (count error)")
        return list(unique_cad_links.values())
    except Exception as e:
        logger.error("Error in get_linked_cad_files: {}".format(e))
        logger.error("Error type: {}".format(type(e)))
        import traceback
        logger.error("Traceback: {}".format(traceback.format_exc()))
        raise


def get_layers_from_selected_cads(selected_cad_files):
    """Get all layers from selected CAD files."""
    layers = []
    
    for cad_file in selected_cad_files:
        if cad_file.selected:
            cad_link_type = cad_file.cad_link_type
            if cad_link_type:
                # Get categories (layers) from the CAD link type
                cat = cad_link_type.Category
                if cat and cat.SubCategories:
                    for sub_cat in cat.SubCategories:
                        # Ensure the subcategory is valid before creating a layer object
                        if sub_cat and sub_cat.Name:
                            layers.append(EnhancedCadLayer(cad_file.name, sub_cat, cad_file))

    return layers


def get_line_patterns():
    """Get all line patterns from the document."""
    line_patterns = {}
    collector = DB.FilteredElementCollector(doc).OfClass(DB.LinePatternElement)
    for pattern in collector:
        line_patterns[pattern.Id.IntegerValue] = pattern
    return line_patterns

def main():
    """Main execution function."""
    try:
        logger.info("Starting main function...")
        
        # Retrieve linked CAD files once at the beginning
        logger.info("Getting linked CAD files...")
        all_linked_cad_files = get_linked_cad_files()
        # Fix potential string formatting issue
        try:
            count = len(all_linked_cad_files)
            logger.info("Found {} linked CAD files".format(str(count)))
        except Exception as e:
            logger.info("Found linked CAD files (count error)")

        if not all_linked_cad_files:
            from pyrevit import forms
            forms.alert("No linked CAD files found in the document.", title="No CAD Files")
            return
    except Exception as e:
        logger.error("Error in main function start: {}".format(e))
        logger.error("Error type: {}".format(type(e)))
        import traceback
        logger.error("Traceback: {}".format(traceback.format_exc()))
        raise

    while True: # Loop to allow going back from layer manager to selection
        try:
            # Reset selection state for the loop
            print("Resetting selection state...")
            for f in all_linked_cad_files:
                f.selected = False

            # Step 1: Show CAD selection form
            print("Creating CADSelectionForm...")
            logger.info("Creating CADSelectionForm...")
            try:
                selection_form = CADSelectionForm(all_linked_cad_files)
                print("CADSelectionForm created successfully")
            except Exception as e:
                print("Error creating CADSelectionForm: {}".format(e))
                raise
                
            print("Showing CADSelectionForm...")
            logger.info("Showing CADSelectionForm...")
            try:
                result = selection_form.ShowDialog()
                print("CADSelectionForm ShowDialog completed")
            except Exception as e:
                print("Error showing CADSelectionForm: {}".format(e))
                raise
            
            print("About to log result...")
            try:
                result_str = "{}".format(result)
                print("Result formatted successfully: {}".format(result_str))
                logger.info("CADSelectionForm closed with result: {}".format(result_str))
                print("Logger call completed")
            except Exception as e:
                print("Error in result logging: {}".format(e))
                logger.info("CADSelectionForm closed with result (format error)")
 
            print("Checking dialog result...")
            if result != DialogResult.OK:
                print("User cancelled, returning...")
                return # Exit if user cancels

            # Step 2: Get layers from selected CAD files
            print("Getting layers from selected CADs...")
            try:
                layers = get_layers_from_selected_cads(all_linked_cad_files)
                print("Got {} layers".format(len(layers) if layers else 0))
            except Exception as e:
                print("Error getting layers: {}".format(e))
                raise

            print("Checking if layers is empty...")
            if not layers:
                print("No layers found, showing alert...")
                from pyrevit import forms
                forms.alert("No layers found in the selected CAD files. Please try a different selection.", title="No Layers Found")
                continue # Go back to selection

            # Step 3: Get line patterns and weights
            print("Getting line patterns...")
            try:
                line_patterns = get_line_patterns()
                print("Got {} line patterns".format(len(line_patterns) if line_patterns else 0))
            except Exception as e:
                print("Error getting line patterns: {}".format(e))
                raise
                
            print("Setting line weights...")
            line_weights = range(1, 17)

            # Step 4: Show enhanced batch layer editor form
            print("Creating EnhancedBatchLayerEditor...")
            logger.info("Creating EnhancedBatchLayerEditor...")
            try:
                layer_manager_form = EnhancedBatchLayerEditor(layers, line_patterns, line_weights)
                print("EnhancedBatchLayerEditor created successfully")
            except Exception as e:
                print("Error creating EnhancedBatchLayerEditor: {}".format(e))
                print("Error type: {}".format(type(e)))
                import traceback
                print("Traceback: {}".format(traceback.format_exc()))
                raise

            print("Showing EnhancedBatchLayerEditor...")
            logger.info("Showing EnhancedBatchLayerEditor...")
            try:
                layer_result = layer_manager_form.ShowDialog()
                print("EnhancedBatchLayerEditor ShowDialog completed")
            except Exception as e:
                print("Error showing EnhancedBatchLayerEditor: {}".format(e))
                raise
            try:
                result_str = "{}".format(layer_result)
                logger.info("EnhancedBatchLayerEditor closed with result: {}".format(result_str))
            except Exception as e:
                logger.info("EnhancedBatchLayerEditor closed with result (format error)")
 
            if layer_result == DialogResult.Retry:
                continue # Go back to the start of the loop (CAD selection)
            else:
                break # Exit on OK or Cancel

        except Exception as e:
            from pyrevit import forms
            logger.error("An unexpected error occurred: {}".format(e))
            forms.alert("An error occurred. See log for details.", title="Error")
            break

if __name__ == '__main__':
    try:
        # Add a simple test to see if we can even get to this point
        print("Script starting...")
        
        # Test logger with simple string first
        try:
            print("Testing logger with simple string...")
            logger.info("Test message")
            print("Logger test successful")
        except Exception as e:
            print("Error in logger test: {}".format(e))
            print("Error type: {}".format(type(e)))
            raise
        
        # Test the problematic string
        try:
            print("Testing problematic string...")
            test_msg = "Script main block reached"
            logger.info(test_msg)
            print("Problematic string test successful")
        except Exception as e:
            print("Error in problematic string test: {}".format(e))
            print("Error type: {}".format(type(e)))
            raise
        
        # Test main() call
        try:
            print("Calling main()...")
            main()
            print("main() completed successfully")
        except Exception as e:
            print("Error in main(): {}".format(e))
            print("Error type: {}".format(type(e)))
            import traceback
            print("Traceback: {}".format(traceback.format_exc()))
            raise
    except Exception as e:
        print("Error in __main__: {}".format(e))
        print("Error type: {}".format(type(e)))
        import traceback
        print("Traceback: {}".format(traceback.format_exc()))
        # Try to log if logger is available
        try:
            logger.error("Error in __main__: {}".format(e))
        except:
            pass
        raise