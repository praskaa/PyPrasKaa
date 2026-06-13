# -*- coding: utf-8 -*-
__title__ = "Copy Grid\nState"
__author__ = "PrasKaa"
__doc__ = """
Version: 1.2
Date    = 13.06.2026
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
2. The source view is automatically taken from the active view (if it contains grids).
   If the active view has no grids, select the SOURCE view manually from the list.
3. Select one or more TARGET views (views to receive the grid state)
4. Review the output report showing successful, skipped, and failed grids

Note: Grids that don't exist in target views are skipped. Grids must have matching
names or Element IDs in both source and target.
_____________________________________________________
Last update:
- 13.06.2026 - 1.2 Improved output formatting
- 12.03.2026 - 1.1 Source view automatically taken from active view if it has grids
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
    curve = (
        get_curve_safe(grid, DB.DatumExtentType.ViewSpecific, view) or
        get_curve_safe(grid, DB.DatumExtentType.Model, view)
    )
    if curve:
        return curve.GetEndPoint(0).Z
    return 0.0


def get_param_on_infinite_line(infinite_line, point):
    origin    = infinite_line.Origin
    direction = infinite_line.Direction.Normalize()
    vec       = point.Subtract(origin)
    return vec.DotProduct(direction)


def rebuild_point(infinite_line, param, z):
    origin    = infinite_line.Origin
    direction = infinite_line.Direction.Normalize()
    pt        = origin.Add(direction.Multiply(param))
    return DB.XYZ(pt.X, pt.Y, z)


# ══════════════════════════════════════════════
#  STEP 1 — CAPTURE from source view
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
#  STEP 2 — APPLY to a single grid
# ══════════════════════════════════════════════

def apply_single_grid(grid, target_view, state):
    grid.SetDatumExtentType(DB.DatumEnds.End0, target_view, state["extent_end0"])
    grid.SetDatumExtentType(DB.DatumEnds.End1, target_view, state["extent_end1"])

    any_view_specific = (
        state["extent_end0"] == DB.DatumExtentType.ViewSpecific or
        state["extent_end1"] == DB.DatumExtentType.ViewSpecific
    )

    if not any_view_specific:
        return

    if state["param0"] is None or state["param1"] is None:
        return

    z = get_view_elevation_z(grid, target_view)

    pt0 = rebuild_point(grid.Curve, state["param0"], z)
    pt1 = rebuild_point(grid.Curve, state["param1"], z)

    if pt0.DistanceTo(pt1) < 1e-6:
        return

    new_curve = DB.Line.CreateBound(pt0, pt1)
    grid.SetCurveInView(DB.DatumExtentType.ViewSpecific, target_view, new_curve)


# ══════════════════════════════════════════════
#  STEP 3 — APPLY to all targets (1 transaction)
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
                    skipped_list.append((target_view.Name, state["grid_name"], None,target_view.Id))
                    continue

                try:
                    apply_single_grid(target_grid, target_view, state)
                    ok_list.append((target_view.Name, state["grid_name"], target_grid.Id))
                except Exception as e:
                    error_list.append((target_view.Name, state["grid_name"], target_grid.Id, str(e),target_view.Id))

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
#  REPORT HELPER
# ══════════════════════════════════════════════

def print_report(source_view, active_has_grids, selected_target_names, states,
                 ok_list, skipped_list, error_list):

    output.set_title("Copy Grid State — {}".format(doc.Title))
    output.resize(820, 680)

    # ── Header ────────────────────────────────────────────────────────
    output.print_md("# Copy Grid State")
    output.print_html(
        "<table style='width:100%;border-collapse:collapse;font-size:13px;"
        "background:#f8f9fa;border:1px solid #dee2e6;border-radius:4px;margin-bottom:8px'>"
        "<tr>"
        "<td style='padding:6px 12px;width:30%;color:#6c757d;font-weight:600'>SOURCE</td>"
        "<td style='padding:6px 12px'><code>{src}</code>{tag}</td>"
        "</tr>"
        "<tr style='border-top:1px solid #dee2e6'>"
        "<td style='padding:6px 12px;color:#6c757d;font-weight:600'>TARGET</td>"
        "<td style='padding:6px 12px'>{targets}</td>"
        "</tr>"
        "<tr style='border-top:1px solid #dee2e6'>"
        "<td style='padding:6px 12px;color:#6c757d;font-weight:600'>GRIDS CAPTURED</td>"
        "<td style='padding:6px 12px'><strong>{count}</strong> grids</td>"
        "</tr>"
        "</table>".format(
            src     = source_view.Name,
            tag     = "&nbsp;&nbsp;<span style='background:#d1ecf1;color:#0c5460;padding:2px 6px;"
                      "border-radius:3px;font-size:11px'>active view</span>" if active_has_grids else "",
            targets = ", ".join("<code>{}</code>".format(n) for n in selected_target_names),
            count   = len(states),
        )
    )

    # ── Summary bar ───────────────────────────────────────────────────
    output.print_html(
        "<div style='display:flex;gap:8px;margin:8px 0 12px'>"
        "<div style='flex:1;padding:10px;background:#d4edda;border-radius:4px;text-align:center'>"
        "<div style='font-size:24px;font-weight:700;color:#155724'>{ok}</div>"
        "<div style='font-size:11px;color:#155724;margin-top:2px'>&#10003; Applied</div>"
        "</div>"
        "<div style='flex:1;padding:10px;background:#fff3cd;border-radius:4px;text-align:center'>"
        "<div style='font-size:24px;font-weight:700;color:#856404'>{sk}</div>"
        "<div style='font-size:11px;color:#856404;margin-top:2px'>&#9654; Skipped</div>"
        "</div>"
        "<div style='flex:1;padding:10px;background:#f8d7da;border-radius:4px;text-align:center'>"
        "<div style='font-size:24px;font-weight:700;color:#721c24'>{er}</div>"
        "<div style='font-size:11px;color:#721c24;margin-top:2px'>&#10007; Errors</div>"
        "</div>"
        "</div>".format(ok=len(ok_list), sk=len(skipped_list), er=len(error_list))
    )

    output.insert_divider()

    # ── Helper: build a simple HTML table ────────────────────────────
    def html_table(columns, rows):
        th_style = ("padding:6px 10px;text-align:left;background:#e9ecef;"
                    "border-bottom:2px solid #dee2e6;font-size:12px;color:#495057")
        td_style = "padding:5px 10px;font-size:12px;border-bottom:1px solid #f0f0f0"
        tr_alt   = "background:#f8f9fa"

        head = "".join("<th style='{}'>{}</th>".format(th_style, c) for c in columns)
        body = ""
        for i, row in enumerate(rows):
            bg   = " style='{}'".format(tr_alt) if i % 2 == 1 else ""
            cols = "".join("<td style='{}'>{}</td>".format(td_style, cell) for cell in row)
            body += "<tr{}>{}</tr>".format(bg, cols)

        return (
            "<table style='width:100%;border-collapse:collapse;"
            "border:1px solid #dee2e6;margin-bottom:12px'>"
            "<thead><tr>{}</tr></thead>"
            "<tbody>{}</tbody>"
            "</table>".format(head, body)
        )

    # ── Applied ───────────────────────────────────────────────────────
    if ok_list:
        output.print_md("### ✅ Applied ({})".format(len(ok_list)))
        rows = []
        for view_name, grid_name, grid_id in ok_list:
            link = output.linkify(grid_id, title=grid_name) if grid_id else "—"
            rows.append([view_name, link])
        output.print_html(html_table(["Target View", "Select Grid"], rows))

    # ── Skipped ───────────────────────────────────────────────────────
    if skipped_list:
        output.print_md("### ⏭ Skipped — not found in target ({})".format(len(skipped_list)))
        rows = []
        for v, g, _, view_id in skipped_list:
            view_link = output.linkify(view_id, title=v) if view_id else v
            rows.append([view_link, g])
        output.print_html(html_table(["Target View", "Grid"], rows))

    # ── Errors ────────────────────────────────────────────────────────
    if error_list:
        output.print_md("### ❌ Errors ({})".format(len(error_list)))
        rows = []
        for view_name, grid_name, grid_id, err, view_id in error_list:
            view_link = output.linkify(view_id, title=view_name) if view_id else view_name
            grid_link = output.linkify(grid_id, title=grid_name) if grid_id else "—"
            rows.append([
                view_link,
                grid_link,
                "<span style='color:#dc3545;font-family:monospace'>{}</span>".format(err)
            ])
        output.print_html(html_table(["Target View", "Select Grid", "Error"], rows))
    
    # ── Log panel ─────────────────────────────────────────────────────
    if error_list:
        output.log_error("{} error(s) — check table above".format(len(error_list)))
    if skipped_list:
        output.log_warning("{} grid(s) skipped (not found in target)".format(len(skipped_list)))
    if ok_list:
        output.log_success("Done — {ok} applied across {views} view(s)".format(
            ok    = len(ok_list),
            views = len(set(v for v, _, _ in ok_list)),
        ))

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main():
    all_views     = get_selectable_views()
    view_name_map = {v.Name: v for v in all_views}
    view_names    = sorted(view_name_map.keys())

    if not view_names:
        forms.alert("No views available.", exitscript=True)

    # ── Check active view first ───────────────────────────────────────
    active_view      = revit.active_view
    active_has_grids = bool(active_view and get_grids_in_view(active_view))

    if active_has_grids:
        source_view          = active_view
        selected_source_name = source_view.Name
    else:
        if active_view:
            forms.alert(
                "Active view '{}' has no grids.\n"
                "Please select a SOURCE view manually.".format(active_view.Name)
            )

        selected_source_name = forms.SelectFromList.show(
            view_names,
            title       = "Select SOURCE View",
            prompt      = "View whose grid state will be copied:",
            multiselect = False,
        )
        if not selected_source_name:
            script.exit()

        source_view = view_name_map[selected_source_name]

        if not get_grids_in_view(source_view):
            forms.alert(
                "No grids found in view '{}'.".format(source_view.Name),
                exitscript=True
            )

    # ── Select TARGET view(s) ─────────────────────────────────────────
    target_view_names = sorted([n for n in view_names if n != selected_source_name])

    selected_target_names = forms.SelectFromList.show(
        target_view_names,
        title       = "Select TARGET View(s)",
        prompt      = "Destination views (multiple selection allowed):",
        multiselect = True,
    )
    if not selected_target_names:
        script.exit()

    target_views = [view_name_map[n] for n in selected_target_names]

    # ── Capture + Apply ───────────────────────────────────────────────
    states                            = capture_grid_states(source_view)
    ok_list, skipped_list, error_list = apply_grid_states(states, target_views)

    # ── Report ────────────────────────────────────────────────────────
    print_report(
        source_view          = source_view,
        active_has_grids     = active_has_grids,
        selected_target_names= selected_target_names,
        states               = states,
        ok_list              = ok_list,
        skipped_list         = skipped_list,
        error_list           = error_list,
    )


main()