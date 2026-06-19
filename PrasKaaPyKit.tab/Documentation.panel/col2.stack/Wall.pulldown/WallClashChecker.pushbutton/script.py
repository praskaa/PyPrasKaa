# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Check geometry clash between walls and other elements in active view
# Version: 1.0

__title__ = 'Wall Clash\nCheck'
__doc__ = 'Check if walls in active view have geometry clash with other elements.'

from pyrevit import revit, DB, forms, script
from System.Collections.Generic import List

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# ─── Solid extraction ──────────────────────────────────────────────────────────

def get_solids(element):
    """Return list of non-empty solids from element geometry."""
    solids = []
    opt = DB.Options()
    opt.ComputeReferences = False
    opt.IncludeNonVisibleObjects = False
    try:
        geom = element.get_Geometry(opt)
        if geom is None:
            return solids
        for g in geom:
            if isinstance(g, DB.Solid) and g.Volume > 1e-9:
                solids.append(g)
            elif isinstance(g, DB.GeometryInstance):
                for sg in g.GetInstanceGeometry():
                    if isinstance(sg, DB.Solid) and sg.Volume > 1e-9:
                        solids.append(sg)
    except Exception:
        pass
    return solids


def solids_clash(solid_a, solid_b):
    """Return True if two solids intersect (volume > 0)."""
    try:
        result = DB.BooleanOperationsUtils.ExecuteBooleanOperation(
            solid_a, solid_b,
            DB.BooleanOperationsType.Intersect
        )
        return result is not None and result.Volume > 1e-9
    except Exception:
        return False


def element_clashes_with_wall(wall_solids, other_element):
    """Check if any solid of other_element clashes with any wall solid."""
    other_solids = get_solids(other_element)
    for ws in wall_solids:
        for os in other_solids:
            if solids_clash(ws, os):
                return True
    return False

# ─── Category skip list ────────────────────────────────────────────────────────
# Skip annotation, detail, and non-solid categories
SKIP_CATEGORIES = {
    int(DB.BuiltInCategory.OST_Dimensions),
    int(DB.BuiltInCategory.OST_TextNotes),
    int(DB.BuiltInCategory.OST_Tags),
    int(DB.BuiltInCategory.OST_Lines),
    int(DB.BuiltInCategory.OST_DetailComponents),
    int(DB.BuiltInCategory.OST_GenericAnnotation),
    int(DB.BuiltInCategory.OST_Grids),
    int(DB.BuiltInCategory.OST_Levels),
    int(DB.BuiltInCategory.OST_Cameras),
    int(DB.BuiltInCategory.OST_Views),
}

def get_category_int(element):
    try:
        cat = element.Category
        if cat is None:
            return None
        # Cross-version ElementId value
        try:
            return cat.Id.Value
        except AttributeError:
            return cat.Id.IntegerValue
    except Exception:
        return None

# ─── Main ──────────────────────────────────────────────────────────────────────

active_view = uidoc.ActiveView

# Only run on views that show 3D model elements
allowed_view_types = [
    DB.ViewType.FloorPlan,
    DB.ViewType.CeilingPlan,
    DB.ViewType.Elevation,
    DB.ViewType.Section,
    DB.ViewType.Detail,
    DB.ViewType.ThreeD,
]
if active_view.ViewType not in allowed_view_types:
    forms.alert("Run this script from a plan, elevation, section, or 3D view.", exitscript=True)

# Collect walls in active view
walls = list(
    DB.FilteredElementCollector(doc, active_view.Id)
      .OfClass(DB.Wall)
      .WhereElementIsNotElementType()
      .ToElements()
)

if not walls:
    forms.alert("No walls found in active view.", exitscript=True)

# Collect all other model elements in active view (excluding walls themselves)
wall_ids_set = set()
for w in walls:
    try:
        wall_ids_set.add(w.Id.Value)
    except AttributeError:
        wall_ids_set.add(w.Id.IntegerValue)

all_elements = list(
    DB.FilteredElementCollector(doc, active_view.Id)
      .WhereElementIsNotElementType()
      .ToElements()
)

other_elements = []
for el in all_elements:
    try:
        el_id_val = el.Id.Value
    except AttributeError:
        el_id_val = el.Id.IntegerValue

    if el_id_val in wall_ids_set:
        continue
    cat_int = get_category_int(el)
    if cat_int in SKIP_CATEGORIES:
        continue
    other_elements.append(el)

# ─── Output setup ──────────────────────────────────────────────────────────────

output.set_title("Wall Clash Check — {}".format(active_view.Name))
output.resize(900, 650)
output.close_others()

output.print_md("# Wall Clash Check")
output.print_md("**View:** `{}`".format(active_view.Name))
output.print_md("**Walls checked:** {}  |  **Other elements:** {}".format(
    len(walls), len(other_elements)
))
output.insert_divider()

# ─── Check loop ────────────────────────────────────────────────────────────────

clash_data   = []   # rows for output table
clashing_ids = []   # ElementIds to highlight

total_pairs = len(walls) * max(len(other_elements), 1)
pair_idx = 0

output.freeze()

for wall in walls:
    wall_solids = get_solids(wall)
    if not wall_solids:
        pair_idx += len(other_elements)
        output.update_progress(pair_idx, total_pairs)
        continue

    wall_link = output.linkify(wall.Id)

    for other in other_elements:
        pair_idx += 1
        output.update_progress(pair_idx, total_pairs)

        if not element_clashes_with_wall(wall_solids, other):
            continue

        # Build a readable name for the other element
        other_cat = other.Category.Name if other.Category else "Unknown"
        try:
            other_name = other.Name
        except Exception:
            other_name = "-"

        try:
            other_id_val = other.Id.Value
        except AttributeError:
            other_id_val = other.Id.IntegerValue

        other_link = output.linkify(other.Id)

        try:
            wall_id_val = wall.Id.Value
        except AttributeError:
            wall_id_val = wall.Id.IntegerValue

        clash_data.append([
            wall_link,
            str(wall_id_val),
            other_link,
            other_cat,
            other_name,
            str(other_id_val),
        ])

        clashing_ids.append(wall.Id)
        clashing_ids.append(other.Id)

output.hide_progress()
output.unfreeze()

# ─── Results ───────────────────────────────────────────────────────────────────

if clash_data:
    output.print_md("## ⚠ Clashes Found: {}".format(len(clash_data)))
    output.print_html_table(
        table_data=clash_data,
        title="Clash Report",
        columns=["Wall", "Wall ID", "Clashing Element", "Category", "Name", "Elem ID"],
        column_widths=["80px", "80px", "100px", "150px", "200px", "80px"],
        col_data_align_styles=["center", "center", "center", "left", "left", "center"],
        row_striping=True,
        repeat_head_as_foot=False,
        table_width_style="width:100%"
    )

    # Select clashing elements in Revit
    unique_ids = list({
        (eid.Value if hasattr(eid, 'Value') else eid.IntegerValue): eid
        for eid in clashing_ids
    }.values())

    id_list = List[DB.ElementId]()
    for eid in unique_ids:
        id_list.Add(eid)
    uidoc.Selection.SetElementIds(id_list)

    output.log_warning("{} clash(es) detected. Elements selected in view.".format(len(clash_data)))
else:
    output.print_md("## ✅ No Clashes Found")
    output.print_md("All walls in **{}** are clear of geometry conflicts.".format(active_view.Name))
    output.log_success("No clashes detected for {} wall(s).".format(len(walls)))