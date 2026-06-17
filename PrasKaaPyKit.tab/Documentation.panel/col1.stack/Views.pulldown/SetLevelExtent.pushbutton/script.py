# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Set horizontal extent of level lines in section/detail/elevation views
# Version: 1.0

from pyrevit import revit, DB, forms, script

doc    = revit.doc
uidoc  = revit.uidoc
output = script.get_output()

MM_TO_FT = 1.0 / 304.8

# ─────────────────────────────────────────────────────────────
# 1. Helpers
# ─────────────────────────────────────────────────────────────
def is_section_like(view):
    """Check if view is section, detail, or elevation (all ViewSection subclasses)."""
    try:
        return isinstance(view, DB.ViewSection) and not view.IsTemplate
    except Exception:
        return False


def get_eligible_views():
    """Collect all non-template section/detail/elevation views."""
    all_views = DB.FilteredElementCollector(doc)\
                  .OfClass(DB.View)\
                  .WhereElementIsNotElementType()\
                  .ToElements()
    return [v for v in all_views if is_section_like(v)]


def get_preselected_views():
    """Extract views from preselected elements (views or viewports)."""
    sel_ids = uidoc.Selection.GetElementIds()
    if not sel_ids:
        return None

    views = []
    for eid in sel_ids:
        el = doc.GetElement(eid)
        if isinstance(el, DB.Viewport):
            view = doc.GetElement(el.ViewId)
            if is_section_like(view):
                views.append(view)
        elif isinstance(el, DB.View) and is_section_like(el):
            views.append(el)
    return views if views else None


def get_levels_in_view(view):
    """Get all levels that have datum extents in the given view."""
    all_levels = DB.FilteredElementCollector(doc)\
                   .OfClass(DB.Level)\
                   .WhereElementIsNotElementType()\
                   .ToElements()
    result = []
    for lvl in all_levels:
        try:
            # Check if level appears in this view
            extent0 = lvl.GetDatumExtentTypeInView(DB.DatumEnds.End0, view)
            result.append(lvl)
        except Exception:
            pass
    return result


def format_mm(val_in_ft):
    """Format feet value to mm string."""
    return "{:.0f} mm".format(val_in_ft * 304.8)


# ─────────────────────────────────────────────────────────────
# 2. Pre-selection check
# ─────────────────────────────────────────────────────────────
preselected = get_preselected_views()
if preselected:
    names = "\n".join("  - " + v.Name for v in preselected)
    msg = "Found {} pre-selected view(s):\n{}\n\nUse these views?".format(
        len(preselected), names)
    use_sel = forms.alert(msg, title="Pre-selected Views", yes=True, no=True)
    target_views = preselected if use_sel else None
else:
    target_views = None

# ─────────────────────────────────────────────────────────────
# 3. Select target views (if not pre-selected)
# ─────────────────────────────────────────────────────────────
if not target_views:
    eligible = get_eligible_views()
    if not eligible:
        forms.alert("No section/detail/elevation views found.", exitscript=True)

    chosen = forms.SelectFromList.show(
        sorted(eligible, key=lambda v: v.Name),
        button_name="Select Views",
        multiselect=True,
        name_attr="Name"
    )
    if not chosen:
        script.exit()
    target_views = chosen

# ─────────────────────────────────────────────────────────────
# 4. Select levels to adjust
# ─────────────────────────────────────────────────────────────
all_levels = DB.FilteredElementCollector(doc)\
               .OfClass(DB.Level)\
               .WhereElementIsNotElementType()\
               .ToElements()
if not all_levels:
    forms.alert("No levels found in project.", exitscript=True)

level_names = sorted([l.Name for l in all_levels])
chosen_levels = forms.SelectFromList.show(
    level_names,
    button_name="Select Levels",
    multiselect=True,
    title="Select Levels to Adjust"
)
if not chosen_levels:
    script.exit()

# Build lookup from name to avoid duplicates
level_lookup = {}
for lvl in all_levels:
    level_lookup[lvl.Name] = lvl

selected_levels = [level_lookup[n] for n in chosen_levels]

# ─────────────────────────────────────────────────────────────
# 5. Ask for offset values
# ─────────────────────────────────────────────────────────────
# Show sample info from first view + first level
sample_view = target_views[0]
sample_cb = sample_view.CropBox
sample_width_mm = (sample_cb.Max.X - sample_cb.Min.X) * 304.8
sample_level = selected_levels[0]

info_msg = (
    "View: {}\n"
    "Crop width: {:.0f} mm\n"
    "Level: {} at elev {:.0f} mm\n\n"
    "Enter horizontal extension length (mm) "
    "from crop box edge.\n"
    "Example: Left=500, Right=500 means"
    " level line extends 500 mm beyond each side."
).format(
    sample_view.Name,
    sample_width_mm,
    sample_level.Name,
    sample_level.Elevation * 304.8
)
forms.alert(info_msg, title="Current State")

left_str = forms.ask_for_string(
    prompt="Left extension beyond crop box (mm):",
    title="Left Offset",
    default="500"
)
if not left_str:
    script.exit()

right_str = forms.ask_for_string(
    prompt="Right extension beyond crop box (mm):",
    title="Right Offset",
    default="500"
)
if not right_str:
    script.exit()

try:
    left_offset_ft = float(left_str.replace(",", ".")) * MM_TO_FT
    right_offset_ft = float(right_str.replace(",", ".")) * MM_TO_FT
except ValueError:
    forms.alert("Invalid number entered.", exitscript=True)

# ─────────────────────────────────────────────────────────────
# 6. Apply
# ─────────────────────────────────────────────────────────────
output.print_html("<h3>Set Level Extent Results</h3>")
output.print_html(
    "<p>Offset: Left = <b>{}</b>, Right = <b>{}</b></p>".format(
        format_mm(left_offset_ft), format_mm(right_offset_ft)))

success_count = 0
fail_list = []

with revit.Transaction("Set Level Extent in Section Views", doc=doc):
    for view in target_views:
        view_name = view.Name
        try:
            cb = view.CropBox
            crop_left_x = cb.Min.X
            crop_right_x = cb.Max.X

            for lvl in selected_levels:
                # Read existing datum curve in this view — guaranteed to be on datum plane
                try:
                    existing_curve = lvl.GetCurveInView(
                        DB.DatumExtentType.ViewSpecific, view)
                except Exception:
                    # Level may not have datum curve in this view yet
                    existing_curve = None

                if existing_curve is None:
                    # Level not shown or has no curve — set a default from crop box
                    elev_z = lvl.Elevation
                    start_pt = DB.XYZ(crop_left_x - left_offset_ft, 0.0, elev_z)
                    end_pt = DB.XYZ(crop_right_x + right_offset_ft, 0.0, elev_z)
                    if start_pt.X > end_pt.X:
                        start_pt, end_pt = end_pt, start_pt
                    new_line = DB.Line.CreateBound(start_pt, end_pt)
                else:
                    if not isinstance(existing_curve, DB.Line):
                        continue  # skip non-linear datum curves

                    # Extend existing curve along its own direction
                    orig_start = existing_curve.GetEndPoint(0)
                    orig_end = existing_curve.GetEndPoint(1)
                    direction = (orig_end - orig_start).Normalize()

                    new_start = orig_start - direction * left_offset_ft
                    new_end = orig_end + direction * right_offset_ft
                    new_line = DB.Line.CreateBound(new_start, new_end)

                # Ensure extent type is ViewSpecific for both ends
                try:
                    ex0 = lvl.GetDatumExtentTypeInView(DB.DatumEnds.End0, view)
                    ex1 = lvl.GetDatumExtentTypeInView(DB.DatumEnds.End1, view)
                except Exception:
                    # GetDatumExtentTypeInView may fail if level not visible
                    continue

                if ex0 != DB.DatumExtentType.ViewSpecific:
                    lvl.SetDatumExtentType(
                        DB.DatumEnds.End0, view, DB.DatumExtentType.ViewSpecific)
                if ex1 != DB.DatumExtentType.ViewSpecific:
                    lvl.SetDatumExtentType(
                        DB.DatumEnds.End1, view, DB.DatumExtentType.ViewSpecific)

                try:
                    lvl.SetCurveInView(
                        DB.DatumExtentType.ViewSpecific, view, new_line)
                except Exception as lvl_ex:
                    fail_list.append("{} - Level '{}': {}".format(
                        view_name, lvl.Name, str(lvl_ex)))

            success_count += 1

        except Exception as ex:
            fail_list.append("{}: {}".format(view_name, str(ex)))

# ─────────────────────────────────────────────────────────────
# 7. Report
# ─────────────────────────────────────────────────────────────
if success_count:
    output.print_html(
        "<p style='color:green'>Successfully updated {} view(s)</p>".format(
            success_count))

if fail_list:
    output.print_html("<details><summary>Failed ({})</summary>".format(
        len(fail_list)))
    for msg in fail_list:
        output.print_html("<p>{}</p>".format(msg))
    output.print_html("</details>")

forms.alert(
    "Done! {} view(s) updated.\n{} failure(s). Check output for details.".format(
        success_count, len(fail_list)),
    title="Set Level Extent Complete"
)
