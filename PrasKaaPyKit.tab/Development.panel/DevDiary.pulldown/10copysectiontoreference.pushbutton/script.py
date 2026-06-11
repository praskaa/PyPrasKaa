# -*- coding: utf-8 -*-
__title__ = 'Section → Reference'
__author__ = 'PrasKaa'
__version__ = 'Version: 1.0'
__doc__ ="""Version: 1.0
Date    = 11.03.2026
_____________________________________________________________________
Description:
Creates reference sections in the active view by copying selected
section, elevation, or callout markers. Reads the referenced view
name from each marker and creates a corresponding reference section
that displays that view's geometry.

Automatically handles section direction (flipping) issues and
auto-selects the newly created markers for repositioning.
_____________________________________________________________________
How-to:
1. Select one or more section/elevation/callout markers in the view
2. Run this script
3. The script creates reference sections referencing the same views
4. New markers are auto-selected - move them to desired location

Tip: Use Ctrl+click to select multiple markers at once.
_____________________________________________________
Last update:
- 11.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""

import clr
clr.AddReference("System")
from System.Collections.Generic import List

from pyrevit import revit, DB, forms

doc   = revit.doc
uidoc = revit.uidoc


def get_view_name_from_marker(marker):
    for pname in ["View Name", "Title on Sheet"]:
        p = marker.LookupParameter(pname)
        if p and p.AsString():
            return p.AsString()
    return None


def get_view_by_name(name):
    for v in DB.FilteredElementCollector(doc)\
                .OfClass(DB.View)\
                .WhereElementIsNotElementType()\
                .ToElements():
        if v.Name == name:
            return v
    return None


def get_active_view_z(view):
    try:
        return doc.GetElement(view.GenLevel.Id).Elevation
    except:
        pass
    try:
        return view.Origin.Z
    except:
        pass
    return 0.0


def get_viewers_in_view(view):
    return set(
        e.Id.IntegerValue for e in
        DB.FilteredElementCollector(doc, view.Id)
          .WhereElementIsNotElementType()
          .OfCategory(DB.BuiltInCategory.OST_Viewers)
          .ToElements()
    )


def main():
    active_view = uidoc.ActiveView

    # ── 1. Pre-selection ──────────────────────────────────────────────────────
    sel_ids = list(uidoc.Selection.GetElementIds())
    if not sel_ids:
        forms.alert(
            "No elements selected.\n\n"
            "How to use:\n"
            "1. Click (or Ctrl+click) section / callout / elevation markers\n"
            "2. Run this script",
            title="Select Elements First"
        )
        return

    view_z = get_active_view_z(active_view)

    # ── 2. Prepare ────────────────────────────────────────────────────────────
    prepared = []
    skipped  = []

    for eid in sel_ids:
        marker    = doc.GetElement(eid)
        view_name = get_view_name_from_marker(marker)
        if not view_name:
            skipped.append(("?", "Could not read view name"))
            continue

        ref_view = get_view_by_name(view_name)
        if ref_view is None:
            skipped.append((view_name, "View not found"))
            continue

        try:
            crop         = ref_view.CropBox
            t            = crop.Transform
            origin       = t.Origin
            basis_x      = t.BasisX
            ref_view_dir = ref_view.ViewDirection
            pt_h    = origin + basis_x * crop.Min.X
            pt_t    = origin + basis_x * crop.Max.X
            head_pt = DB.XYZ(pt_h.X, pt_h.Y, view_z)
            tail_pt = DB.XYZ(pt_t.X, pt_t.Y, view_z)
        except Exception as ex:
            skipped.append((view_name, "CropBox error: {}".format(ex)))
            continue

        prepared.append((view_name, ref_view, head_pt, tail_pt, ref_view_dir))

    if not prepared:
        forms.alert("No valid markers.", title="Nothing to Process")
        return

    # ── 3. Snapshot before transaction ───────────────────────────────────────
    viewers_before = get_viewers_in_view(active_view)

    # ── 4. Single transaction ─────────────────────────────────────────────────
    results_ok   = []  # list of view_name strings
    results_fail = []  # list of (view_name, error) tuples

    with revit.Transaction("Create Referenced Sections"):
        for item in prepared:
            view_name, ref_view, head_pt, tail_pt, ref_view_dir = item
            try:
                DB.ViewSection.CreateReferenceSection(
                    doc, active_view.Id, ref_view.Id, head_pt, tail_pt)
                results_ok.append(view_name)
            except Exception as ex:
                results_fail.append((view_name, str(ex)))

    # ── 5. Find new markers via OST_Viewers diff ──────────────────────────────
    viewers_after  = get_viewers_in_view(active_view)
    new_viewer_ids = viewers_after - viewers_before

    # ── 6. Flip check ─────────────────────────────────────────────────────────
    viewers_to_delete = []
    flip_recreates    = []

    for viewer_id in new_viewer_ids:
        viewer = doc.GetElement(DB.ElementId(viewer_id))
        try:
            p = viewer.get_Parameter(DB.BuiltInParameter.ID_PARAM)
            if not p:
                continue
            linked_view_id = p.AsElementId()
            linked_view    = None
            for v in DB.FilteredElementCollector(doc)\
                        .OfClass(DB.View)\
                        .WhereElementIsNotElementType()\
                        .ToElements():
                if v.Id == linked_view_id:
                    linked_view = v
                    break
            if linked_view is None:
                continue

            for item in prepared:
                view_name, ref_view, head_pt, tail_pt, ref_view_dir = item
                if ref_view.Id == linked_view_id:
                    if ref_view_dir.DotProduct(linked_view.ViewDirection) < 0:
                        viewers_to_delete.append(viewer_id)
                        flip_recreates.append((ref_view, tail_pt, head_pt))
                    break
        except:
            pass

    if viewers_to_delete:
        with revit.Transaction("Fix Flipped Sections"):
            for vid in viewers_to_delete:
                doc.Delete(DB.ElementId(vid))
            for ref_view, tail_pt, head_pt in flip_recreates:
                try:
                    DB.ViewSection.CreateReferenceSection(
                        doc, active_view.Id, ref_view.Id, tail_pt, head_pt)
                except:
                    pass

        viewers_after  = get_viewers_in_view(active_view)
        new_viewer_ids = viewers_after - viewers_before

    # ── 7. Auto-select new markers ────────────────────────────────────────────
    all_new_ids = [DB.ElementId(i) for i in new_viewer_ids]

    if all_new_ids:
        try:
            id_list = List[DB.ElementId]()
            for eid in all_new_ids:
                id_list.Add(eid)
            uidoc.Selection.SetElementIds(id_list)
        except Exception as ex:
            print("Selection failed: {}".format(ex))

    # ── 8. Summary ────────────────────────────────────────────────────────────
    msg_parts = []

    if results_ok:
        msg_parts.append(u"\u2705 Created ({}):\n{}".format(
            len(results_ok),
            "\n".join(u"  - {}".format(n) for n in results_ok)
        ))

    if results_fail or skipped:
        all_fail = results_fail + skipped
        msg_parts.append(u"\u274C Failed ({}):\n{}".format(
            len(all_fail),
            "\n".join(u"  - {}: {}".format(n, e) for n, e in all_fail)
        ))

    if all_new_ids:
        msg_parts.append(u"\u27A1 {} marker(s) selected \u2014 move them to the desired location.".format(
            len(all_new_ids)
        ))

    forms.alert("\n\n".join(msg_parts), title="Done")


if __name__ == "__main__":
    main()