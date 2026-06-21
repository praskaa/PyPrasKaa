# -*- coding: utf-8 -*-
'''
Version: 1.4
Date    = 21.06.2026
_____________________________________________________________________
Description:
Aligns viewport title labels on a sheet to share the same Y position (vertical
alignment) while each label remains horizontally centered within its respective
viewport. Uses the lowest viewport bottom edge as the baseline, offset by a
user-specified mm value.

Requires 2+ viewports selected on the active sheet.
_____________________________________________________________________
How-to:
1. Select 2 or more viewports on a sheet
2. Click the button and enter Y offset in mm
   (positive = title below viewport, negative = above)
3. All selected viewport titles will be aligned to the same Y position
4. Each title stays horizontally centered within its viewport
_____________________________________________________
Last update:
- 21.06.2026 - 1.4 Added rollback guard and improved error handling
- 17.06.2026 - 1.3 Initial release with viewport title alignment
_____________________________________________________________________
Author:  PrasKaa
'''

from pyrevit import revit, DB, forms, script

doc = revit.doc
uidoc = revit.uidoc

# --- 1. Get pre-selected viewports on active sheet ---
selection_ids = uidoc.Selection.GetElementIds()
if not selection_ids:
    forms.alert("No elements selected.", exitscript=True)

viewports = []
for eid in selection_ids:
    el = doc.GetElement(eid)
    if isinstance(el, DB.Viewport):
        viewports.append(el)

if not viewports:
    forms.alert("No Viewports found in selection.", exitscript=True)

if len(viewports) < 2:
    forms.alert("Please select at least 2 viewports.", exitscript=True)

# --- 2. User input: Y offset (in mm, converted to feet) ---
offset_str = forms.ask_for_string(
    prompt="Enter Y offset from bottom edge of viewport (mm):\n(positive = title below viewport, negative = above)",
    title="Viewport Title Alignment",
    default="5"
)
if offset_str is None:
    script.exit()

try:
    offset_mm = float(offset_str)
except ValueError:
    forms.alert("Invalid input. Please enter a number.", exitscript=True)

offset_ft = offset_mm / 304.8

# --- 3. Find lowest bottom edge among all selected viewports ---
min_y = None
for vp in viewports:
    box_outline = vp.GetBoxOutline()
    bottom_y = box_outline.MinimumPoint.Y
    if min_y is None or bottom_y < min_y:
        min_y = bottom_y

target_y = min_y - offset_ft

# --- 4. Apply LabelOffset per viewport ---
t = DB.Transaction(doc, "Align Viewport Titles")
t.Start()
try:
    for vp in viewports:
        label_outline = vp.GetLabelOutline()
        if label_outline is None:
            continue

        # Current label center (absolute sheet coords)
        cur_label_cx = (label_outline.MinimumPoint.X + label_outline.MaximumPoint.X) / 2.0
        cur_label_cy = (label_outline.MinimumPoint.Y + label_outline.MaximumPoint.Y) / 2.0

        # Current offset
        cur_offset = vp.LabelOffset

        # Back-calculate default label center (absolute, before any offset)
        default_label_cx = cur_label_cx - cur_offset.X
        default_label_cy = cur_label_cy - cur_offset.Y

        # Target X: center of this viewport's box
        target_x = vp.GetBoxCenter().X

        # New offset = target_absolute - default_label_position
        new_offset_x = target_x - default_label_cx
        new_offset_y = target_y - default_label_cy

        vp.LabelOffset = DB.XYZ(new_offset_x, new_offset_y, 0.0)

    t.Commit()
except Exception as e:
    if t.HasStarted() and not t.HasEnded():
        t.RollbackIfPending()
    forms.alert("Error: {}".format(str(e)), exitscript=True)

forms.alert("Done! {} viewport titles aligned.".format(len(viewports)))