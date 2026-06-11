# -*- coding: utf-8 -*-
"""
Create a 3D view and isolate specific elements by Element ID.

This tool creates a new 3D isometric view and hides all elements
except the specified ones. Useful for inspecting specific elements from
error/warning lists or for focused element review.

Supported input formats:
- Newline separated: 2687043\n2687049\n2687057
- Comma separated: 2687043, 2687049, 2687057
- Space separated: 2687043 2687049 2687057
- Mixed formats: 2687043,2687049 2687057

CONTEXT: PyRevit UI tool - only runs from Revit interface
"""

__title__ = '3D View by ElementID'
__author__ = 'PrasKaa Team'
__version__ = '1.0'
__doc__ = """Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Creates a 3D isometric view and isolates specific elements by Element ID.
Useful for inspecting specific elements from error/warning lists or for
focused element review.

Supports multiple input formats:
- Newline separated: 2687043, 2687049, 2687057
- Comma separated: 2687043, 2687049, 2687057
- Space separated: 2687043 2687049 2687057
- Mixed formats

How-to:
1. Click the tool button to open the input dialog
2. Enter Element IDs (one per line or comma/space separated)
3. Click OK to create the isolated 3D view
4. The tool creates a new 3D view showing only selected elements

Notes:
- Element IDs must be valid integers
- Levels, grids, and other interfering categories are automatically hidden
- The new 3D view is automatically activated

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
"""

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from pyrevit import revit, DB, script
from Autodesk.Revit.DB import ElementId, FilteredElementCollector, ViewFamilyType, View3D, ViewFamily
from System.Windows.Forms import Form, TextBox, Button, Label, DialogResult, MessageBox, MessageBoxButtons, FormStartPosition, FormBorderStyle, ScrollBars
from System.Drawing import Font, ContentAlignment, Point, Size
from System.Collections.Generic import List


def parse_element_ids(input_text):
    """
    Parse Element IDs from text input.

    Supports multiple formats:
    - Newline separated
    - Comma separated
    - Space separated
    - Mixed

    Args:
        input_text: String containing Element IDs

    Returns:
        List of valid integer Element IDs
    """
    if not input_text or not input_text.strip():
        return []

    # Replace commas and newlines with spaces, then split by whitespace
    cleaned = input_text.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
    parts = cleaned.split()

    element_ids = []
    for part in parts:
        part = part.strip()
        if part:
            try:
                elem_id = int(part)
                if elem_id > 0:
                    element_ids.append(elem_id)
            except ValueError:
                pass

    return element_ids


def get_elements_from_ids(doc, element_id_integers):
    """
    Get Revit elements from integer Element IDs.
    """
    found_elements = []
    not_found_ids = []

    for elem_id_int in element_id_integers:
        elem_id = ElementId(elem_id_int)
        element = doc.GetElement(elem_id)
        if element is not None:
            found_elements.append(element)
        else:
            not_found_ids.append(elem_id_int)

    return found_elements, not_found_ids


def create_3d_view(doc, view_name):
    """
    Create a new 3D isometric view.
    """
    # Get 3D view type
    view_type_collector = FilteredElementCollector(doc).OfClass(ViewFamilyType)
    view_3d_types = [vt for vt in view_type_collector
                     if vt.ViewFamily == ViewFamily.ThreeDimensional]

    if not view_3d_types:
        MessageBox.Show("No 3D view type found in the project.", "Error")
        return None

    view_type_3d = view_3d_types[0]
    view_3d = View3D.CreateIsometric(doc, view_type_3d.Id)

    # Set view name with uniqueness check
    base_name = view_name
    for i in range(100):
        try:
            view_3d.Name = view_name
            break
        except Exception:
            view_name = "{} {}".format(base_name, i + 1)

    return view_3d


def hide_other_elements(view_3d, elements_to_show, doc):
    """
    Hide all elements except the ones to show.
    """
    if not elements_to_show:
        return False
    
    # First, hide some categories that often cause issues
    from Autodesk.Revit.DB import BuiltInCategory, ElementId as EID
    try:
        view_3d.SetCategoryHidden(EID(BuiltInCategory.OST_Levels), True)
        view_3d.SetCategoryHidden(EID(BuiltInCategory.OST_Grids), True)
        view_3d.SetCategoryHidden(EID(BuiltInCategory.OST_VolumeOfInterest), True)
        view_3d.SetCategoryHidden(EID(BuiltInCategory.OST_SectionBox), True)
    except Exception:
        pass
    
    # Get element IDs to show
    target_ids = [el.Id for el in elements_to_show]
    target_id_set = set(target_ids)
    
    # Get all element IDs in the view - only get elements that CAN be hidden
    all_elements = FilteredElementCollector(doc, view_3d.Id)\
        .WhereElementIsNotElementType()\
        .ToElements()
    
    # Find elements to hide (all elements minus target elements)
    # Only include elements that can be hidden
    elements_to_hide = []
    for el in all_elements:
        if el.Id not in target_id_set:
            try:
                if el.CanBeHidden(view_3d):
                    elements_to_hide.append(el.Id)
            except Exception:
                pass
    
    # Hide elements
    if elements_to_hide:
        view_3d.HideElements(List[ElementId](elements_to_hide))
    
    return True


def ask_for_element_ids():
    """Show a simple input dialog to get Element IDs."""
    form = Form()
    form.Width = 500
    form.Height = 300
    form.Text = "Enter Element IDs"
    form.StartPosition = FormStartPosition.CenterScreen
    form.FormBorderStyle = FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False

    label = Label()
    label.Text = "Enter Element IDs (one per line or comma/space separated):\n\nExample:\n2687043\n2687049\n2687057"
    label.Location = Point(10, 10)
    label.Width = 460
    label.Height = 70
    form.Controls.Add(label)

    textBox = TextBox()
    textBox.Location = Point(10, 85)
    textBox.Width = 460
    textBox.Height = 100
    textBox.Multiline = True
    textBox.ScrollBars = ScrollBars.Vertical
    textBox.AcceptsReturn = True
    form.Controls.Add(textBox)

    okButton = Button()
    okButton.Text = "OK"
    okButton.Location = Point(300, 220)
    okButton.Width = 80
    okButton.Height = 30
    okButton.DialogResult = DialogResult.OK
    form.Controls.Add(okButton)

    cancelButton = Button()
    cancelButton.Text = "Cancel"
    cancelButton.Location = Point(390, 220)
    cancelButton.Width = 80
    cancelButton.Height = 30
    cancelButton.DialogResult = DialogResult.Cancel
    form.Controls.Add(cancelButton)

    form.AcceptButton = okButton
    form.CancelButton = cancelButton

    result = form.ShowDialog()

    if result == DialogResult.OK:
        return textBox.Text
    return None


def main():
    """Main function for the tool."""
    doc = revit.doc
    uidoc = revit.uidoc

    # Show input dialog
    input_text = ask_for_element_ids()

    if not input_text:
        script.exit()

    # Parse Element IDs
    element_id_integers = parse_element_ids(input_text)

    if not element_id_integers:
        MessageBox.Show(
            "No valid Element IDs found in input.\n\n"
            "Please enter valid Element IDs (positive integers).",
            "Invalid Input"
        )
        script.exit()

    # Get elements from document
    found_elements, not_found_ids = get_elements_from_ids(doc, element_id_integers)

    if not found_elements:
        MessageBox.Show(
            "None of the specified Element IDs exist in the current document.\n\n"
            "Please verify the Element IDs are correct.",
            "Elements Not Found"
        )
        script.exit()

    # Show warning about not found elements
    if not_found_ids:
        MessageBox.Show(
            "Warning: {} Element ID(s) not found in document: {}\n\n"
            "The view will be created with {} element(s) that were found.".format(
                len(not_found_ids),
                ", ".join(str(x) for x in not_found_ids[:10]) +
                ("..." if len(not_found_ids) > 10 else ""),
                len(found_elements)
            ),
            "Some Elements Not Found"
        )

    # Create 3D view with transaction
    with revit.Transaction("Create 3D View with Isolated Elements"):
        # Create view name
        view_name = "Isolated_Elements_{}-{}".format(
            element_id_integers[0],
            element_id_integers[-1] if len(element_id_integers) > 1 else ""
        )

        view_3d = create_3d_view(doc, view_name)

        if view_3d is None:
            script.exit()

        # Hide other elements (show only target elements)
        hide_other_elements(view_3d, found_elements, doc)

    # Activate the new view
    uidoc.ActiveView = view_3d

    # Show success message
    print("=" * 60)
    print("3D View Created Successfully!")
    print("=" * 60)
    print("View Name: {}".format(view_3d.Name))
    print("Elements Visible: {}".format(len(found_elements)))
    print("Elements Not Found: {}".format(len(not_found_ids)))
    print("=" * 60)


if __name__ == '__main__':
    main()
