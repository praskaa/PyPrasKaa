# -*- coding: utf-8 -*-
__title__ = "Copy Grid\nState"
__author__ = "PrasKaa"
__doc__ = """
Version: 1.0
Date    = 10.03.2026
_____________________________________________________________________
Description:
Copy grid extent states (2D/3D mode and endpoint positions) from a source view to one or
more target views. The tool captures grid visibility, extent type, and curve positions
from the source view and applies them to selected target views.

Useful for synchronizing grid display across multiple drawings or maintaining consistent
grid setups in related views.
_____________________________________________________________________
How-to:
1. Run the tool from pyRevit toolbar
2. Select the SOURCE view (the view whose grid state will be copied)
3. Select one or more TARGET views (views to receive the grid state)
4. Review the output report showing successful, skipped, and failed grids

Note: Grids that don't exist in target views are skipped. Grids must have matching
names or Element IDs in both source and target.
_____________________________________________________
Last update:
- 10.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""

from pyrevit import revit, DB, forms, script

doc    = revit.doc
output = script.get_output()


# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

def get_curve_safe(grid, extent_type, view):
    try:
        curves = grid.GetCurvesInView(extent_type, view)
        return curves[0] if curves and len(curves) > 0 else None
    except Exception:
        return None


def get_grids_in_view(view):
    return (
        DB.FilteredElementCollector(doc, view.Id)
        .OfClass(DB.Grid)
        .ToElements()
    )


def get_view_elevation_z(grid, view):
    """
    Ambil Z elevation yang dipakai kurva grid di view ini.
    Caranya: baca dari kurva existing (ViewSpecific atau Model).
    Setiap view punya Z berbeda sesuai cut plane / elevation-nya.
    """
    curve = (
        get_curve_safe(grid, DB.DatumExtentType.ViewSpecific, view) or
        get_curve_safe(grid, DB.DatumExtentType.Model, view)
    )
    if curve:
        return curve.GetEndPoint(0).Z
    return 0.0


def get_param_on_infinite_line(infinite_line, point):
    """
    Hitung parameter posisi titik pada infinite line (dot product).
    Orientation-independent: bekerja untuk semua arah grid.
    """
    origin    = infinite_line.Origin
    direction = infinite_line.Direction.Normalize()
    vec       = point.Subtract(origin)
    return vec.DotProduct(direction)


def rebuild_point(infinite_line, param, z):
    """
    Rebuild XYZ dari parameter di atas infinite line,
    dengan Z diganti sesuai view target.
    Ini PASTI coincident dengan grid di target view.
    """
    origin    = infinite_line.Origin
    direction = infinite_line.Direction.Normalize()
    pt        = origin.Add(direction.Multiply(param))
    return DB.XYZ(pt.X, pt.Y, z)


# ══════════════════════════════════════════════
#  STEP 1 — CAPTURE dari source view
# ══════════════════════════════════════════════

def capture_grid_states(source_view):
    states = []
    grids  = get_grids_in_view(source_view)

    for grid in grids:
        extent_end0 = grid.GetDatumExtentTypeInView(DB.DatumEnds.End0, source_view)
        extent_end1 = grid.GetDatumExtentTypeInView(DB.DatumEnds.End1, source_view)

        curve = (
            get_curve_safe(grid, DB.DatumExtentType.ViewSpecific, source_view) or
            get_curve_safe(grid, DB.DatumExtentType.Model,         source_view)
        )

        param0 = None
        param1 = None

        if curve:
            infinite = grid.Curve
            param0   = get_param_on_infinite_line(infinite, curve.GetEndPoint(0))
            param1   = get_param_on_infinite_line(infinite, curve.GetEndPoint(1))

        states.append({
            "grid_id"    : grid.Id,
            "grid_name"  : grid.Name,
            "extent_end0": extent_end0,
            "extent_end1": extent_end1,
            "param0"     : param0,
            "param1"     : param1,
        })

    return states


# ══════════════════════════════════════════════
#  STEP 2 — APPLY ke satu grid
# ══════════════════════════════════════════════

def apply_single_grid(grid, target_view, state):
    # Wajib set extent type DULU sebelum SetCurveInView
    grid.SetDatumExtentType(DB.DatumEnds.End0, target_view, state["extent_end0"])
    grid.SetDatumExtentType(DB.DatumEnds.End1, target_view, state["extent_end1"])

    any_view_specific = (
        state["extent_end0"] == DB.DatumExtentType.ViewSpecific or
        state["extent_end1"] == DB.DatumExtentType.ViewSpecific
    )

    if not any_view_specific:
        return  # Mode 3D → Revit atur sendiri

    if state["param0"] is None or state["param1"] is None:
        return

    # ── Kunci fix: ambil Z dari TARGET view, bukan source ──
    z = get_view_elevation_z(grid, target_view)

    # Rebuild titik di atas infinite line grid dengan Z target
    pt0 = rebuild_point(grid.Curve, state["param0"], z)
    pt1 = rebuild_point(grid.Curve, state["param1"], z)

    if pt0.DistanceTo(pt1) < 1e-6:
        return

    new_curve = DB.Line.CreateBound(pt0, pt1)
    grid.SetCurveInView(DB.DatumExtentType.ViewSpecific, target_view, new_curve)


# ══════════════════════════════════════════════
#  STEP 3 — APPLY ke semua target (1 transaction)
# ══════════════════════════════════════════════

def apply_grid_states(states, target_views):
    ok_list      = []
    skipped_list = []
    error_list   = []

    with DB.Transaction(doc, "Copy Grid States") as tx:
        tx.Start()

        for target_view in target_views:
            grids_in_target = get_grids_in_view(target_view)
            by_id           = {g.Id  : g for g in grids_in_target}
            by_name         = {g.Name: g for g in grids_in_target}

            for state in states:
                target_grid = by_id.get(state["grid_id"]) or by_name.get(state["grid_name"])

                if target_grid is None:
                    skipped_list.append((target_view.Name, state["grid_name"]))
                    continue

                try:
                    apply_single_grid(target_grid, target_view, state)
                    ok_list.append((target_view.Name, state["grid_name"]))
                except Exception as e:
                    error_list.append((target_view.Name, state["grid_name"], str(e)))

        tx.Commit()

    return ok_list, skipped_list, error_list


# ══════════════════════════════════════════════
#  VIEW SELECTOR
# ══════════════════════════════════════════════

def get_selectable_views():
    excluded_types = [
        DB.ViewType.Schedule,
        DB.ViewType.ProjectBrowser,
        DB.ViewType.SystemBrowser,
        DB.ViewType.Undefined,
        DB.ViewType.DrawingSheet,
        DB.ViewType.Report,
        DB.ViewType.Legend,
    ]
    all_views = (
        DB.FilteredElementCollector(doc)
        .OfClass(DB.View)
        .ToElements()
    )
    return [
        v for v in all_views
        if not v.IsTemplate and v.ViewType not in excluded_types
    ]


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main():
    all_views     = get_selectable_views()
    view_name_map = {v.Name: v for v in all_views}
    view_names    = sorted(view_name_map.keys())

    if not view_names:
        forms.alert("Tidak ada view yang tersedia.", exitscript=True)

    # Pilih SOURCE view
    selected_source_name = forms.SelectFromList.show(
        view_names,
        title       = "Pilih SOURCE View",
        prompt      = "View yang akan di-COPY state grid-nya:",
        multiselect = False,
    )
    if not selected_source_name:
        script.exit()

    source_view = view_name_map[selected_source_name]

    if not get_grids_in_view(source_view):
        forms.alert(
            "Tidak ada grid di view '{}'.".format(source_view.Name),
            exitscript=True
        )

    # Pilih TARGET view(s)
    target_view_names = sorted([n for n in view_names if n != selected_source_name])

    selected_target_names = forms.SelectFromList.show(
        target_view_names,
        title       = "Pilih TARGET View",
        prompt      = "View tujuan (bisa pilih lebih dari 1):",
        multiselect = True,
    )
    if not selected_target_names:
        script.exit()

    target_views = [view_name_map[n] for n in selected_target_names]

    # Capture + Apply
    states                            = capture_grid_states(source_view)
    ok_list, skipped_list, error_list = apply_grid_states(states, target_views)

    # ── Laporan ────────────────────────────────
    output.print_md("# Copy Grid States")
    output.print_md("**Source :** `{}`".format(source_view.Name))
    output.print_md("**Target :** {}".format(
        ", ".join("`{}`".format(n) for n in selected_target_names)
    ))
    output.print_md("**Grid di source :** {}".format(len(states)))
    output.print_md("---")

    output.print_md("## ✅ Berhasil ({})".format(len(ok_list)))
    if ok_list:
        for view_name, grid_name in ok_list:
            output.print_md("- [{}] Grid **{}**".format(view_name, grid_name))
    else:
        output.print_md("_Tidak ada_")

    output.print_md("## ⏭ Di-skip — tidak ada di target ({})".format(len(skipped_list)))
    if skipped_list:
        for view_name, grid_name in skipped_list:
            output.print_md("- [{}] Grid **{}**".format(view_name, grid_name))
    else:
        output.print_md("_Tidak ada_")

    output.print_md("## ❌ Error ({})".format(len(error_list)))
    if error_list:
        for view_name, grid_name, err in error_list:
            output.print_md("- [{}] Grid **{}**: `{}`".format(view_name, grid_name, err))
    else:
        output.print_md("_Tidak ada_")

    output.print_md("---\n**Selesai!**")


main()