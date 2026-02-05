# -*- coding: utf-8 -*-
"""
Linked Element Selection Tool

Only allows selection of elements from linked Revit models.
Similar to pyRevit's "Pick Model Elements" but specifically for linked elements.

Usage:
- Click button
- Select elements using window/box selection
- Only linked elements will be selected
- Press ESC to cancel

Benefits:
- No need for hover + tab + tab... to select linked elements
- Window selection works on linked elements
- Filter by category if needed
"""

from pyrevit import revit, DB, UI, forms
import clr

clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import (
    Form, Button, CheckBox, Label, ListBox,
    FormBorderStyle, DockStyle, AnchorStyles, 
    FormStartPosition, DialogResult, MessageBox,
    MessageBoxButtons, MessageBoxIcon, Point, Size
)
from System.Drawing import Font, FontStyle, Color

doc = revit.doc
uidoc = revit.uidoc


class LinkedElementFilter(UI.Selection.ISelectionFilter):
    """
    Selection filter that only allows elements from linked models.
    """
    
    def __init__(self, include_categories=None):
        """
        Args:
            include_categories: List of BuiltInCategory to include, None = all
        """
        self.include_categories = include_categories or []
    
    def AllowElement(self, element):
        """Check if element should be allowed."""
        if not element:
            return False
        
        # Must be view-specific (shown in current view)
        if not element.ViewSpecific:
            return False
        
        # Must be from a linked model
        if not self.is_from_linked_model(element):
            return False
        
        # Category filter if specified
        if self.include_categories:
            if not element.Category:
                return False
            if element.Category.BuiltInCategory not in self.include_categories:
                return False
        
        return True
    
    def AllowReference(self, refer, point):
        """Don't allow references, only elements."""
        return False
    
    def is_from_linked_model(self, element):
        """Check if element is from a linked model."""
        # Get the document of the element
        elem_doc = element.Document
        
        # If same as current doc, not linked
        if elem_doc.Equals(doc):
            return False
        
        # Check if it's from a linked model
        try:
            link_instances = DB.FilteredElementCollector(doc).OfClass(
                DB.RevitLinkInstance
            ).ToElements()
            
            for link in link_instances:
                if link.GetLinkDocument().Equals(elem_doc):
                    return True
        except:
            pass
        
        return False


class LinkedElementSelectionForm(Form):
    """Dialog for linked element selection options."""
    
    def __init__(self):
        self.selected_categories = []
        self.selection_mode = 'window'  # 'window' or 'single'
        self.InitializeComponent()
    
    def InitializeComponent(self):
        self.Text = "Select Linked Elements"
        self.Size = Size(350, 250)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        y_pos = 20
        
        # Title
        title = Label()
        title.Text = "Linked Element Selection"
        title.Location = Point(20, y_pos)
        title.Size = Size(310, 25)
        title.Font = Font("Segoe UI", 12, FontStyle.Bold)
        self.Controls.Add(title)
        
        y_pos += 40
        
        # Instructions
        info = Label()
        info.Text = "Select elements from linked models only.\nNo need for hover + tab + tab..."
        info.Location = Point(20, y_pos)
        info.Size = Size(310, 40)
        info.Font = Font("Segoe UI", 9)
        info.ForeColor = Color.Gray
        self.Controls.Add(info)
        
        y_pos += 50
        
        # Selection mode
        mode_label = Label()
        mode_label.Text = "Selection Mode:"
        mode_label.Location = Point(20, y_pos)
        mode_label.Size = Size(310, 20)
        mode_label.Font = Font("Segoe UI", 10, FontStyle.Bold)
        self.Controls.Add(mode_label)
        
        y_pos += 25
        
        # Window selection button
        window_btn = Button()
        window_btn.Text = "Window Selection"
        window_btn.Location = Point(20, y_pos)
        window_btn.Size = Size(140, 35)
        window_btn.Click += self.on_window_select
        self.Controls.Add(window_btn)
        
        # Single element button
        single_btn = Button()
        single_btn.Text = "Pick Single Element"
        single_btn.Location = Point(170, y_pos)
        single_btn.Size = Size(140, 35)
        single_btn.Click += self.on_single_select
        self.Controls.Add(single_btn)
        
        y_pos += 50
        
        # Help text
        help_text = Label()
        help_text.Text = "Tip: After selection, selected elements\nwill be highlighted in Revit."
        help_text.Location = Point(20, y_pos)
        help_text.Size = Size(310, 40)
        help_text.Font = Font("Segoe UI", 8)
        help_text.ForeColor = Color.Gray
        self.Controls.Add(help_text)
        
        # Cancel button
        cancel_btn = Button()
        cancel_btn.Text = "Cancel"
        cancel_btn.Location = Point(230, y_pos + 30)
        cancel_btn.Size = Size(80, 30)
        cancel_btn.Click += lambda s, a: self.Close()
        self.Controls.Add(cancel_btn)
    
    def on_window_select(self, sender, args):
        """Handle window selection mode."""
        self.selection_mode = 'window'
        self.DialogResult = DialogResult.OK
        self.Close()
    
    def on_single_select(self, sender, args):
        """Handle single element selection mode."""
        self.selection_mode = 'single'
        self.DialogResult = DialogResult.OK
        self.Close()


def get_linked_categories():
    """Get list of categories that exist in linked models."""
    linked_categories = set()
    
    try:
        # Get all link instances
        link_instances = DB.FilteredElementCollector(doc).OfClass(
            DB.RevitLinkInstance
        ).ToElements()
        
        for link in link_instances:
            link_doc = link.GetLinkDocument()
            if link_doc:
                # Get all elements in linked doc
                elements = DB.FilteredElementCollector(link_doc).WhereElementIsNotElementType().ToElements()
                
                for elem in elements:
                    if elem.Category:
                        linked_categories.add(elem.Category.BuiltInCategory)
    
    except Exception as e:
        forms.alert("Error getting linked categories: {}".format(str(e)))
    
    return list(linked_categories)


def perform_window_selection():
    """Perform window selection for linked elements."""
    # Show category filter dialog
    dialog = LinkedElementSelectionForm()
    result = dialog.ShowDialog()
    
    if result != DialogResult.OK:
        return
    
    # Create filter - include all categories from linked models
    linked_categories = get_linked_categories()
    
    if not linked_categories:
        forms.alert("No linked models found in current project.", exitscript=True)
        return
    
    # Filter for linked elements only
    msfilter = LinkedElementFilter(include_categories=linked_categories)
    
    try:
        # Pick elements using rectangle/box selection
        selection_list = revit.pick_rectangle(pick_filter=msfilter)
        
        if not selection_list:
            forms.alert("No linked elements selected.", exitscript=True)
            return
        
        # Convert to element IDs and set selection
        selection_ids = [el.Id for el in selection_list]
        selection = revit.get_selection()
        selection.set_to(selection_ids)
        
        # Refresh view
        uidoc.RefreshActiveView()
        
        # Show results
        forms.alert(
            "Selected {} linked element(s).".format(len(selection_ids)),
            title="Selection Complete"
        )
        
    except Exception as e:
        if "cancelled" in str(e).lower() or "escape" in str(e).lower():
            pass  # User cancelled
        else:
            forms.alert("Error during selection: {}".format(str(e)))


def perform_single_selection():
    """Perform single element selection for linked elements."""
    linked_categories = get_linked_categories()
    
    if not linked_categories:
        forms.alert("No linked models found in current project.", exitscript=True)
        return
    
    # Create filter
    msfilter = LinkedElementFilter(include_categories=linked_categories)
    
    try:
        # Pick single element
        ref = uidoc.Selection.PickObject(
            UI.Selection.ObjectType.Element,
            msfilter,
            "Select a linked element (press ESC to cancel)"
        )
        
        # Get element
        element = doc.GetElement(ref.ElementId)
        
        if element:
            selection = revit.get_selection()
            selection.set_to([element.Id])
            
            uidoc.RefreshActiveView()
            
            forms.alert(
                "Selected: {}".format(element.Name or element.Id),
                title="Selection Complete"
            )
    
    except Exception as e:
        if "cancelled" in str(e).lower() or "escape" in str(e).lower():
            pass  # User cancelled
        else:
            forms.alert("Error during selection: {}".format(str(e)))


def main():
    """Main execution."""
    # Check if there are any linked models
    link_count = DB.FilteredElementCollector(doc).OfClass(
        DB.RevitLinkInstance
    ).ToElements().Count
    
    if link_count == 0:
        forms.alert(
            "No linked Revit models found in current project.\n"
            "Please link a Revit model first.",
            title="No Linked Models"
        )
        return
    
    # Show selection dialog
    dialog = LinkedElementSelectionForm()
    result = dialog.ShowDialog()
    
    if result != DialogResult.OK:
        return
    
    # Perform selection based on mode
    if dialog.selection_mode == 'window':
        perform_window_selection()
    else:
        perform_single_selection()


if __name__ == '__main__':
    main()
