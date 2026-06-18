# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Align viewport title positions - vertical (shared Y) and horizontal (centered per viewport)
# Version: 1.3

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
    try:
        t.Rollback()
    except Exception:
        pass
    forms.alert("Error: {}".format(str(e)), exitscript=True)

forms.alert("Done! {} viewport titles aligned.".format(len(viewports)))