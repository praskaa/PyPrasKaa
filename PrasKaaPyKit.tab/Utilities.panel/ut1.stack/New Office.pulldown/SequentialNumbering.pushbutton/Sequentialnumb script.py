# -*- coding: utf-8 -*-
'''
Version: 1.1
Date    = 21.06.2026
_____________________________________________________________________
Description:
Click TextNotes one by one to assign sequential numbered labels (e.g. 1FS-1,
1FS-2, ...). Each click assigns the next number in sequence and advances the
counter. Press ESC to finish.
_____________________________________________________________________
How-to:
1. Click the button and enter a label prefix (e.g. "1FS-")
2. Enter the starting number
3. Click each TextNote to assign sequential labels
4. Press ESC to finish when done
_____________________________________________________
Last update:
- 21.06.2026 - 1.1 Added rollback guard on error
- 13.06.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

from pyrevit import revit, DB, forms, script
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.Exceptions import OperationCanceledException

doc = revit.doc
uidoc = revit.uidoc


class TextNoteSelectionFilter(ISelectionFilter):
    def AllowElement(self, element):
        return isinstance(element, DB.TextNote)

    def AllowReference(self, reference, point):
        return False


# --- Ask prefix and start number ---
prefix = forms.ask_for_string(
    prompt="Enter label prefix (e.g. '1FS-')",
    title="Sequential Numbering",
    default="1FS-"
)
if not prefix:
    script.exit()

start_str = forms.ask_for_string(
    prompt="Enter starting number",
    title="Sequential Numbering",
    default="1"
)
if not start_str:
    script.exit()

try:
    counter = int(start_str.strip())
except ValueError:
    forms.alert("Starting number must be an integer.", exitscript=True)

sel_filter = TextNoteSelectionFilter()
count = 0

# --- Pick loop ---
while True:
    try:
        ref = uidoc.Selection.PickObject(
            ObjectType.Element,
            sel_filter,
            "Click TextNote to assign [{}{}] — ESC to finish".format(prefix, counter)
        )
    except OperationCanceledException:
        break

    element = doc.GetElement(ref.ElementId)
    label = "{}{}".format(prefix, counter)

    t = DB.Transaction(doc, "Number TextNote: {}".format(label))
    t.Start()
    try:
        element.Text = label
        t.Commit()
        counter += 1
        count += 1
    except Exception as e:
        t.RollbackIfPending()
        forms.alert("Failed on [{}]: {}".format(label, str(e)))

# --- Minimal summary ---
if count > 0:
    forms.alert("{} TextNote(s) numbered.\nLast: {}{}".format(count, prefix, counter - 1))