# -*- coding: utf-8 -*-
__title__ = "Copy Crop\nView"
__author__ = "PrasKaa"
__doc__ = """
Version: 1.0
Date    = 10.03.2026
_____________________________________________________________________
Description:
Copy crop box and split region settings from a source view to one or more target views.
The tool captures the crop box boundaries, visibility settings, and horizontal split
regions (if present) from the source and applies them to selected target views.

Useful for applying consistent crop boundaries across related plan, section, or detail views.
_____________________________________________________________________
How-to:
1. Run the tool from pyRevit toolbar
2. Select a SOURCE view (must have an active Crop Region enabled)
3. Select one or more TARGET views from the list
4. Click "Apply Crop" to apply settings
5. Review the output report

Note: If the source has split regions, a manual adjustment step may be required
to position the right region correctly in target views.
_____________________________________________________
Last update:
- 10.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""

from pyrevit import revit, DB, forms, script

doc    = revit.doc
uidoc  = revit.uidoc
output = script.get_output()

FT_TO_MM = 304.8

# ─────────────────────────────────────────────────────────────
# 1. Get source view
# ─────────────────────────────────────────────────────────────
def get_source_view():
    selection = uidoc.Selection.GetElementIds()
    for eid in selection:
        el = doc.GetElement(eid)
        if isinstance(el, DB.Viewport):
            return doc.GetElement(el.ViewId)
        if isinstance(el, DB.View):
            return el
    return uidoc.ActiveView

source_view = get_source_view()

if not source_view or not isinstance(source_view, DB.View):
    forms.alert("No valid source view found. Select a view or viewport first.", exitscript=True)

if not source_view.CropBoxActive:
    forms.alert(
        "Source view '{}' does not have an active Crop Region.".format(source_view.Name),
        exitscript=True
    )

output.print_md("**Source View:** `{}` | Id: {}".format(
    source_view.Name, source_view.Id.IntegerValue))

# ─────────────────────────────────────────────────────────────
# 2. Read CropBox + Split Regions from source
# ─────────────────────────────────────────────────────────────
crop_box = source_view.CropBox
mgr_src  = source_view.GetCropRegionShapeManager()

split_regions = []
for i in range(20):
    try:
        split_regions.append({
            'index'  : i,
            'minimum': mgr_src.GetSplitRegionMinimum(i),
            'maximum': mgr_src.GetSplitRegionMaximum(i),
            'offset' : mgr_src.GetSplitRegionOffset(i),
        })
    except Exception:
        break

has_split = len(split_regions) > 1

src_cb_min   = crop_box.Min.X
src_cb_max   = crop_box.Max.X
src_cb_width = src_cb_max - src_cb_min

if has_split:
    src_r0_max   = split_regions[0]['maximum']
    src_r1_min   = split_regions[1]['minimum']
    src_r1_max   = split_regions[1]['maximum']
    src_offset_x = split_regions[1]['offset'].X

    gap_left_world  = src_cb_min + (src_r0_max * src_cb_width)
    gap_right_world = src_cb_min + (src_r1_min * src_cb_width) + src_offset_x
    gap_size_mm     = (gap_right_world - gap_left_world) * FT_TO_MM
    region0_mm      = (src_r0_max * src_cb_width) * FT_TO_MM
    region1_mm      = ((src_r1_max - src_r1_min) * src_cb_width) * FT_TO_MM

    output.print_md("**Split Region detected:** {} regions".format(len(split_regions)))
    output.print_md("  - Left region : {:.1f} mm".format(region0_mm))
    output.print_md("  - Gap         : {:.1f} mm".format(gap_size_mm))
    output.print_md("  - Right region: {:.1f} mm".format(region1_mm))
else:
    output.print_md("**Split Region:** none (standard crop box)")

# ─────────────────────────────────────────────────────────────
# 3. Collect target views
# ─────────────────────────────────────────────────────────────
all_views = DB.FilteredElementCollector(doc)\
    .OfClass(DB.View)\
    .WhereElementIsNotElementType()\
    .ToElements()

ALLOWED_TYPES = (
    DB.ViewType.FloorPlan,
    DB.ViewType.CeilingPlan,
    DB.ViewType.Elevation,
    DB.ViewType.Section,
    DB.ViewType.Detail,
    DB.ViewType.DraftingView,
    DB.ViewType.AreaPlan,
    DB.ViewType.EngineeringPlan,
)

eligible_views = [
    v for v in all_views
    if not v.IsTemplate
    and v.Id != source_view.Id
    and v.ViewType in ALLOWED_TYPES
]

if not eligible_views:
    forms.alert("No eligible target views found.", exitscript=True)

# Handle duplicate names
view_dict = {}
for v in eligible_views:
    base_name    = u"{} [{}]".format(v.Name, v.ViewType)
    display_name = base_name
    if display_name in view_dict:
        old = view_dict.pop(base_name)
        view_dict[u"{} <id:{}>".format(base_name, old.Id.IntegerValue)] = old
        display_name = u"{} <id:{}>".format(base_name, v.Id.IntegerValue)
    view_dict[display_name] = v

# ─────────────────────────────────────────────────────────────
# 4. Target view selection dialog
# ─────────────────────────────────────────────────────────────
selected_names = forms.SelectFromList.show(
    sorted(view_dict.keys()),
    title="Select Target Views",
    multiselect=True,
    button_name="Apply Crop"
)

if not selected_names:
    script.exit()

target_views = [view_dict[n] for n in selected_names]

# ─────────────────────────────────────────────────────────────
# 5. Copy crop + split function
# ─────────────────────────────────────────────────────────────
def copy_crop_and_split(source_v, target_v):
    target_v.CropBoxActive  = True
    target_v.CropBoxVisible = source_v.CropBoxVisible
    target_v.CropBox        = crop_box

    if not has_split:
        output.print_md(u"  OK  Crop box applied to `{}`".format(target_v.Name))
        return

    mgr_tgt = target_v.GetCropRegionShapeManager()

    # Remove existing splits on target
    existing = []
    for i in range(20):
        try:
            mgr_tgt.GetSplitRegionMinimum(i)
            existing.append(i)
        except Exception:
            break
    for i in range(len(existing) - 1, 0, -1):
        try:
            mgr_tgt.RemoveSplit(i - 1)
        except Exception:
            pass

    try:
        cb_now   = target_v.CropBox
        cb_min_x = cb_now.Min.X
        cb_max_x = cb_now.Max.X
        cb_width = cb_max_x - cb_min_x

        left_part  = (gap_left_world  - cb_min_x) / cb_width
        right_part = (cb_max_x - gap_right_world) / cb_width
        left_part  = max(0.01, min(0.98, left_part))
        right_part = max(0.01, min(0.98, right_part))

        if left_part + right_part >= 1.0:
            output.print_md(u"  WARNING  leftPart + rightPart >= 1.0 — split skipped")
            return

        mgr_tgt.SplitRegionHorizontally(0, left_part, right_part)
        output.print_md(u"  OK  Crop + Split applied to `{}`".format(target_v.Name))
        output.print_md(u"  >>  Manual step: drag right region left to world X = {:.1f} mm  (gap = {:.1f} mm)".format(
            gap_right_world * FT_TO_MM, gap_size_mm))

    except Exception as e:
        output.print_md(u"  WARNING  Failed to apply split to `{}`: {}".format(target_v.Name, str(e)))


# ─────────────────────────────────────────────────────────────
# 6. Execute in single Transaction
# ─────────────────────────────────────────────────────────────
output.print_md("\n**Applying to {} target view(s)...**".format(len(target_views)))

with revit.Transaction("Copy Crop + Split Region"):
    for tv in target_views:
        copy_crop_and_split(source_view, tv)

output.print_md("\n---\n**Done.** {} view(s) updated.".format(len(target_views)))

if has_split:
    output.print_md("\n**Manual step required (right region offset):**")
    output.print_md("1. Open the target view and enable Crop Region display")
    output.print_md("2. Click the crop frame and select the right region")
    output.print_md("3. Drag the grip left until world X = **{:.1f} mm**".format(gap_right_world * FT_TO_MM))
    output.print_md("   *(desired gap = {:.1f} mm)*".format(gap_size_mm))