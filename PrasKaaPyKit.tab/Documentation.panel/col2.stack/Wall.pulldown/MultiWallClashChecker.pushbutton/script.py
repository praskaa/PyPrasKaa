# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Wall clash check across multiple views (pre-selection or dialog picker)
# Version: 1.0

__title__ = 'Wall Clash\nMulti-View'
__doc__ = ('Check wall geometry clashes across multiple views.\n'
           'Pre-select views or viewports, or pick from dialog.')

from pyrevit import revit, DB, forms, script
from System.Collections.Generic import List

doc  = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# ─── Constants ─────────────────────────────────────────────────────────────────

ALLOWED_VIEW_TYPES = [
    DB.ViewType.FloorPlan,
    DB.ViewType.Elevation,
    DB.ViewType.Section,
    DB.ViewType.Detail,
]

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

# ─── Helpers ───────────────────────────────────────────────────────────────────

def eid_value(element_id):
    """Cross-version ElementId integer value (2024-2026)."""
    try:
        return element_id.Value
    except AttributeError:
        return element_id.IntegerValue


def get_category_int(element):
    try:
        cat = element.Category
        return eid_value(cat.Id) if cat is not None else None
    except Exception:
        return None


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
    try:
        result = DB.BooleanOperationsUtils.ExecuteBooleanOperation(
            solid_a, solid_b,
            DB.BooleanOperationsType.Intersect
        )
        return result is not None and result.Volume > 1e-9
    except Exception:
        return False


def element_clashes_with_wall(wall_solids, other_element):
    for ws in wall_solids:
        for os in get_solids(other_element):
            if solids_clash(ws, os):
                return True
    return False

# ─── View wrapper for dialog display ───────────────────────────────────────────

class ViewItem(object):
    def __init__(self, view):
        self.view = view
        # Build display label: "ViewType | Level | Name"
        level_name = ""
        level_param = view.get_Parameter(DB.BuiltInParameter.PLAN_VIEW_LEVEL)
        if level_param and level_param.HasValue:
            level_name = level_param.AsString()
        type_label = str(view.ViewType).replace("FloorPlan", "Floor Plan")
        if level_name:
            self.label = "[{}]  {}  —  {}".format(type_label, level_name, view.Name)
        else:
            self.label = "[{}]  {}".format(type_label, view.Name)

    def __str__(self):
        return self.label

# ─── Step 1: Resolve target views ──────────────────────────────────────────────

def resolve_preselection():
    """Extract valid views from current Revit selection (Views + Viewports)."""
    sel_ids = uidoc.Selection.GetElementIds()
    resolved = []
    seen_ids = set()
    for eid in sel_ids:
        el = doc.GetElement(eid)
        view = None
        if isinstance(el, DB.View):
            view = el
        elif isinstance(el, DB.Viewport):
            view = doc.GetElement(el.ViewId)
        if view is None:
            continue
        if view.ViewType not in ALLOWED_VIEW_TYPES:
            continue
        vid = eid_value(view.Id)
        if vid in seen_ids:
            continue
        seen_ids.add(vid)
        resolved.append(view)
    return resolved


def pick_views_from_dialog():
    """Show SelectFromList dialog with all allowed views in the model."""
    all_views = list(
        DB.FilteredElementCollector(doc)
          .OfClass(DB.View)
          .WhereElementIsNotElementType()
          .ToElements()
    )
    items = []
    for v in all_views:
        if v.ViewType not in ALLOWED_VIEW_TYPES:
            continue
        if v.IsTemplate:
            continue
        items.append(ViewItem(v))

    if not items:
        forms.alert("No valid views found in model.", exitscript=True)

    # Sort: by type then name
    items.sort(key=lambda x: x.label)

    chosen = forms.SelectFromList.show(
        items,
        title="Select Views for Clash Check",
        button_name="Run Check",
        multiselect=True
    )
    if not chosen:
        script.exit()
    return [item.view for item in chosen]


# Try pre-selection first
target_views = resolve_preselection()

if target_views:
    # Inform user how many views were picked from selection
    pass  # silently proceed
else:
    target_views = pick_views_from_dialog()

if not target_views:
    forms.alert("No views to process.", exitscript=True)

# ─── Step 2: Run clash check per view ──────────────────────────────────────────

output.set_title("Wall Clash — Multi-View Report")
output.resize(980, 700)
output.close_others()

output.print_md("# Wall Clash — Multi-View Report")
output.print_md("**Views processed:** {}".format(len(target_views)))
output.insert_divider()

total_clash_count = 0
all_clashing_ids  = []   # flat list of ElementIds across all views (for final selection)

for view_idx, view in enumerate(target_views):

    output.print_md("## {} / {}  —  `{}`".format(
        view_idx + 1, len(target_views), view.Name
    ))

    # Collect walls in this view
    walls = list(
        DB.FilteredElementCollector(doc, view.Id)
          .OfClass(DB.Wall)
          .WhereElementIsNotElementType()
          .ToElements()
    )

    if not walls:
        output.print_md("> _No walls found in this view — skipped._")
        output.insert_divider()
        continue

    # Collect wall IDs for exclusion
    wall_id_set = set(eid_value(w.Id) for w in walls)

    # Collect other elements in this view
    other_elements = []
    for el in DB.FilteredElementCollector(doc, view.Id)\
                 .WhereElementIsNotElementType()\
                 .ToElements():
        if eid_value(el.Id) in wall_id_set:
            continue
        if get_category_int(el) in SKIP_CATEGORIES:
            continue
        other_elements.append(el)

    output.print_md("Walls: **{}**  |  Other elements: **{}**".format(
        len(walls), len(other_elements)
    ))

    # Progress bar scoped to this view
    total_pairs = len(walls) * max(len(other_elements), 1)
    pair_idx    = 0
    clash_rows  = []

    output.freeze()

    for wall in walls:
        wall_solids = get_solids(wall)
        if not wall_solids:
            pair_idx += len(other_elements)
            output.update_progress(pair_idx, total_pairs)
            continue

        for other in other_elements:
            pair_idx += 1
            output.update_progress(pair_idx, total_pairs)

            if not element_clashes_with_wall(wall_solids, other):
                continue

            other_cat  = other.Category.Name if other.Category else "Unknown"
            try:
                other_name = other.Name
            except Exception:
                other_name = "-"

            clash_rows.append([
                output.linkify(wall.Id),
                str(eid_value(wall.Id)),
                output.linkify(other.Id),
                other_cat,
                other_name,
                str(eid_value(other.Id)),
            ])
            all_clashing_ids.append(wall.Id)
            all_clashing_ids.append(other.Id)

    output.hide_progress()
    output.unfreeze()

    if clash_rows:
        output.print_html_table(
            table_data=clash_rows,
            title="Clashes in: {}".format(view.Name),
            columns=["Wall", "Wall ID", "Clashing Element", "Category", "Name", "Elem ID"],
            column_widths=["70px", "80px", "90px", "150px", "200px", "80px"],
            col_data_align_styles=["center", "center", "center", "left", "left", "center"],
            row_striping=True,
            table_width_style="width:100%"
        )
        output.log_warning("  {} clash(es) in '{}'".format(len(clash_rows), view.Name))
        total_clash_count += len(clash_rows)
    else:
        output.print_md("> ✅ _No clashes found in this view._")

    output.insert_divider()

# ─── Step 3: Summary ───────────────────────────────────────────────────────────

output.print_md("## Summary")
output.print_md("| | |")
output.print_md("|---|---|")
output.print_md("| Views checked | **{}** |".format(len(target_views)))
output.print_md("| Total clashes | **{}** |".format(total_clash_count))

if total_clash_count > 0:
    # Deduplicate and select all clashing elements
    unique_ids = list({
        eid_value(eid): eid for eid in all_clashing_ids
    }.values())
    id_list = List[DB.ElementId]()
    for eid in unique_ids:
        id_list.Add(eid)
    uidoc.Selection.SetElementIds(id_list)
    output.log_warning("Total {} clash(es) across all views. All elements selected.".format(
        total_clash_count
    ))
else:
    output.log_success("All clear — no clashes found across {} view(s).".format(len(target_views)))