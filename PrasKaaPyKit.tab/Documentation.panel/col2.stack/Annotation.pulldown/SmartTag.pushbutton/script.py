# -*- coding: utf-8 -*-
"""Smart Tag System - Main Script"""

__title__ = "Smart Tag"
__author__ = "Your Name"
__doc__ = "Intelligently tag structural elements across multiple views"

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import (
    Form, Button, CheckBox, RadioButton, Label,
    ListView, View, ColumnHeader, ListViewItem, ColumnHeaderStyle, HorizontalAlignment,
    FormBorderStyle, DockStyle, AnchorStyles, FormStartPosition, DialogResult,
    MessageBox, MessageBoxButtons, MessageBoxIcon,
    ProgressBar, TextBox
)
from System.Drawing import Point, Size, Font, FontStyle, Color

from pyrevit import revit, DB, forms
import sys
import os
import time

# Add lib folder to path
script_dir = os.path.dirname(__file__)
lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from smart_tag_config import SmartTagConfig
from smart_tag_engine import SmartTagEngine

doc = revit.doc
uidoc = revit.uidoc

class SmartTagDialog(Form):
    """Main dialog for Smart Tag System"""
    
    def __init__(self, views, config):
        self.views = views
        self.config = config
        self.selected_views = []
        self.tag_mode = config.get_tag_mode()
        self.filtered_views = views[:]  # Initialize with all views

        self.InitializeComponent()
    
    def InitializeComponent(self):
        """Initialize UI components"""
        self.Text = "Smart Tag System - Structural"
        self.Size = Size(500, 650)  # Increased height for search components
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        y_pos = 20

        # Search section
        search_label = Label()
        search_label.Text = "Search views:"
        search_label.Location = Point(20, y_pos)
        search_label.Size = Size(80, 20)
        search_label.Font = Font("Segoe UI", 9, FontStyle.Regular)
        self.Controls.Add(search_label)

        self.search_box = TextBox()
        self.search_box.Location = Point(100, y_pos)
        self.search_box.Size = Size(200, 20)
        self.search_box.TextChanged += self.on_search_text_changed
        self.Controls.Add(self.search_box)

        clear_btn = Button()
        clear_btn.Text = "Clear"
        clear_btn.Location = Point(310, y_pos)
        clear_btn.Size = Size(50, 25)
        clear_btn.Click += self.on_clear_search
        self.Controls.Add(clear_btn)

        y_pos += 25

        # Search tip
        search_tip = Label()
        search_tip.Text = "Tip: Type 'L1' for L10-L19, 'struct' for structural views"
        search_tip.Location = Point(20, y_pos)
        search_tip.Size = Size(400, 15)
        search_tip.Font = Font("Segoe UI", 8, FontStyle.Italic)
        search_tip.ForeColor = Color.Gray
        self.Controls.Add(search_tip)

        y_pos += 20
        
        # Title label
        title_label = Label()
        title_label.Text = "Select Views to Tag:"
        title_label.Location = Point(20, y_pos)
        title_label.Size = Size(460, 20)
        title_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
        self.Controls.Add(title_label)
        
        y_pos += 30
        
        # Views list with checkboxes (View.Details with hidden headers)
        self.views_list = ListView()
        self.views_list.Location = Point(20, y_pos)
        self.views_list.Size = Size(460, 200)
        self.views_list.View = View.Details
        self.views_list.CheckBoxes = True
        self.views_list.MultiSelect = True
        self.views_list.FullRowSelect = True
        self.views_list.GridLines = False

        # Hide headers by setting to non-clickable (minimal appearance)
        self.views_list.HeaderStyle = ColumnHeaderStyle.Nonclickable

        # Add column with empty header
        self.views_list.Columns.Add("", 440, HorizontalAlignment.Left)

        # Populate with view items
        for view in self.views:
            item = ListViewItem(view.Name)
            item.Tag = view  # Store view object
            self.views_list.Items.Add(item)

        self.Controls.Add(self.views_list)
        
        y_pos += 210
        
        # Select All / Deselect All buttons
        select_all_btn = Button()
        select_all_btn.Text = "Select All"
        select_all_btn.Location = Point(20, y_pos)
        select_all_btn.Size = Size(100, 25)
        select_all_btn.Click += self.on_select_all
        self.Controls.Add(select_all_btn)
        
        deselect_all_btn = Button()
        deselect_all_btn.Text = "Deselect All"
        deselect_all_btn.Location = Point(130, y_pos)
        deselect_all_btn.Size = Size(100, 25)
        deselect_all_btn.Click += self.on_deselect_all
        self.Controls.Add(deselect_all_btn)
        
        y_pos += 40
        
        # Tag Mode section
        mode_label = Label()
        mode_label.Text = "Tag Mode:"
        mode_label.Location = Point(20, y_pos)
        mode_label.Size = Size(460, 20)
        mode_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
        self.Controls.Add(mode_label)
        
        y_pos += 25
        
        self.radio_untagged = RadioButton()
        self.radio_untagged.Text = "Tag untagged elements only"
        self.radio_untagged.Location = Point(40, y_pos)
        self.radio_untagged.Size = Size(400, 20)
        self.radio_untagged.Checked = (self.tag_mode == 'untagged_only')
        self.Controls.Add(self.radio_untagged)
        
        y_pos += 25
        
        self.radio_retag = RadioButton()
        self.radio_retag.Text = "Retag all elements"
        self.radio_retag.Location = Point(40, y_pos)
        self.radio_retag.Size = Size(400, 20)
        self.radio_retag.Checked = (self.tag_mode == 'retag_all')
        self.Controls.Add(self.radio_retag)
        
        y_pos += 35
        
        # Categories section
        cat_label = Label()
        cat_label.Text = "Categories (from configuration):"
        cat_label.Location = Point(20, y_pos)
        cat_label.Size = Size(460, 20)
        cat_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
        self.Controls.Add(cat_label)
        
        y_pos += 25
        
        # Display category info
        categories = self.config.get_all_categories()
        
        for key, cat_config in categories.items():
            if key == 'structural_framing':
                display_name = "Structural Framing"
            elif key == 'structural_column':
                display_name = "Structural Columns"
            elif key == 'walls':
                display_name = "Walls"
            else:
                display_name = key
            
            enabled = cat_config.get('enabled', True)
            offset = cat_config.get('offset_mm', 0)
            
            cat_info = Label()
            cat_info.Text = u"{} {} (offset: {}mm)".format(
                u"☑" if enabled else u"☐",
                display_name,
                offset
            )
            cat_info.Location = Point(40, y_pos)
            cat_info.Size = Size(400, 20)
            cat_info.ForeColor = Color.Green if enabled else Color.Gray
            self.Controls.Add(cat_info)
            
            y_pos += 22
        
        y_pos += 20
        
        # Buttons 
        execute_btn = Button()
        execute_btn.Text = "Execute"
        execute_btn.Location = Point(200, y_pos)  # Centered: (500 - 100) / 2 = 200
        execute_btn.Size = Size(100, 30)
        execute_btn.Click += self.on_execute_click
        self.Controls.Add(execute_btn)
    
    def on_select_all(self, sender, args):
        """Select all currently visible/filtered views"""
        for item in self.views_list.Items:
            item.Checked = True

    def on_deselect_all(self, sender, args):
        """Deselect all currently visible/filtered views"""
        for item in self.views_list.Items:
            item.Checked = False
    
    def on_settings_click(self, sender, args):
        """Open settings dialog"""
        from System.Diagnostics import Process
        MessageBox.Show(
            "Settings dialog will open the configuration.\nPlease use the 'Smart Tag Settings' button to modify configuration.",
            "Info",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )

    def on_search_text_changed(self, sender, args):
        """Filter views based on search text."""
        search_text = self.search_box.Text.lower().strip()

        if not search_text:
            # Show all views
            self.views_list.Items.Clear()
            for view in self.views:
                item = ListViewItem(view.Name)
                item.Tag = view
                self.views_list.Items.Add(item)
            self.filtered_views = self.views[:]
        else:
            # Filter views
            self.views_list.Items.Clear()
            self.filtered_views = []

            for view in self.views:
                view_name = view.Name.lower()
                if search_text in view_name:
                    item = ListViewItem(view.Name)
                    item.Tag = view
                    self.views_list.Items.Add(item)
                    self.filtered_views.append(view)

    def on_clear_search(self, sender, args):
        """Clear search and show all views."""
        self.search_box.Text = ""
        # on_search_text_changed will be triggered automatically
    
    def on_execute_click(self, sender, args):
        """Execute tagging"""
        # Get selected views from checked items
        self.selected_views = []
        for item in self.views_list.CheckedItems:
            view = item.Tag  # Get view object from Tag
            self.selected_views.append(view)
        
        if not self.selected_views:
            MessageBox.Show(
                "Please select at least one view to tag.",
                "No Views Selected",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return
        
        # Get tag mode
        if self.radio_untagged.Checked:
            self.tag_mode = 'untagged_only'
        else:
            self.tag_mode = 'retag_all'
        
        self.DialogResult = DialogResult.OK
        self.Close()


def show_summary(stats, view_count):
    """Show summary dialog"""
    total = stats['framing'] + stats['columns'] + stats['walls']
    
    message = "Tagging Complete!\n\n"
    message += "Total Views Processed: {}\n\n".format(view_count)
    message += "Structural Framing: {} tagged\n".format(stats['framing'])
    message += "Structural Columns: {} tagged\n".format(stats['columns'])
    message += "Walls: {} tagged\n\n".format(stats['walls'])
    message += "Total Elements Tagged: {}\n".format(total)
    
    if stats['errors']:
        message += "\nWarnings: {} (check output window for details)".format(len(stats['errors']))
    
    MessageBox.Show(
        message,
        "Smart Tag System - Complete",
        MessageBoxButtons.OK,
        MessageBoxIcon.Information
    )
    
    # Print errors to output
    if stats['errors']:
        print("\n=== ERRORS/WARNINGS ===")
        for error in stats['errors']:
            print(error)


def execute_settings():
    """Execute the SmartTagSettings script"""
    try:
        # Settings script is now in the same folder
        settings_script_path = os.path.join(
            os.path.dirname(__file__),
            'settings.py'
        )

        # Execute settings script by importing and running its main
        import sys
        settings_dir = os.path.dirname(settings_script_path)
        if settings_dir not in sys.path:
            sys.path.append(settings_dir)

        # Import settings module and execute
        import imp
        settings_module = imp.load_source('settings_script', settings_script_path)
        settings_module.main()

    except Exception as e:
        forms.alert("Failed to open settings: {}".format(str(e)))


def execute_main_tagging():
    """Execute the main tagging workflow"""
    # Initialize config and engine
    config_manager = SmartTagConfig()
    engine = SmartTagEngine(doc)
    engine.reset_cache()  # Reset cache for fresh run

    # Check for verbose mode (Ctrl+Click for verbose output)
    import System.Windows.Forms as WinForms
    verbose = (WinForms.Control.ModifierKeys == WinForms.Keys.Control)  # Ctrl+Click for verbose

    if verbose:
        print("Smart Tag: VERBOSE MODE ENABLED")
        engine.set_debug(True)  # Enable debug logging
    else:
        # Quiet mode: completely silent, no console output
        engine.set_debug(False)  # Disable debug logging

    # Get structural plan views
    views = engine.get_structural_plans()

    if not views:
        forms.alert("No structural plan views found in the project.", exitscript=True)

    # Show dialog
    dialog = SmartTagDialog(views, config_manager)
    result = dialog.ShowDialog()

    if result != DialogResult.OK:
        return

    # Get selections
    selected_views = dialog.selected_views
    tag_mode = dialog.tag_mode

    # Update tag mode in config
    config_manager.update_tag_mode(tag_mode)

    # Process views quietly (no console spam)
    total_views = len(selected_views)
    total_time = 0

    for idx, view in enumerate(selected_views):
        # Start timer for this view
        view_start = time.time()

        # Tag elements in view
        engine.tag_elements_in_view(
            view,
            config_manager.config,
            tag_mode
        )

        # Accumulate total time
        view_time = time.time() - view_start
        total_time += view_time

    # Show summary
    stats = engine.get_statistics()
    show_summary(stats, total_views)

    # Performance summary (only in verbose mode)
    if verbose:
        print("\n=== PERFORMANCE SUMMARY ===")
        print("Total views processed: {}".format(total_views))
        print("Total processing time: {:.2f}s".format(total_time))
        if total_views > 0:
            print("Average time per view: {:.2f}s".format(total_time / total_views))
        print("Tag mode: {}".format(tag_mode))
        print("Elements tagged - Framing: {}, Columns: {}, Walls: {}".format(
            stats['framing'], stats['columns'], stats['walls']))


def main():
    """Main execution with modifier key support"""
    import System.Windows.Forms as WinForms

    # Check modifier keys
    if WinForms.Control.ModifierKeys == WinForms.Keys.Shift:
        # Shift+Click: Open settings
        execute_settings()
    else:
        # Normal/Ctrl+Click: Execute main tagging
        execute_main_tagging()


if __name__ == '__main__':
    main()