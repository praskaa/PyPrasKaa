# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Toggles grid bubble visibility in the active view. If one end is visible,
it switches to the other end. If both are visible or both hidden, it skips.
Useful for quickly adjusting grid bubble display orientation.
_____________________________________________________________________
How-to:
1. Click "Toggle Grid Bubble"
2. Select grids in the view (or pick from selection)
3. Grid bubbles will toggle from one end to the other

Notes:
- Only toggles if exactly one end is visible
- Works on selected grids or allows picking grids
- Shows toast with count of toggled and skipped grids

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
'''

__title__ = "Toggle Grid Bubble"
__author__ = "PrasKaa Team"
__version__ = "1.0"

from Autodesk.Revit.DB import Transaction, Grid, DatumEnds
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from pyrevit import revit, forms

uidoc = revit.uidoc
doc = revit.doc
active_view = doc.ActiveView

class GridFilter(ISelectionFilter):
    def AllowElement(self, e):
        return isinstance(e, Grid)
    def AllowReference(self, ref, point):
        return False

def pick_grids():
    sel_ids = list(uidoc.Selection.GetElementIds())
    grids = []
    if sel_ids:
        for eid in sel_ids:
            el = doc.GetElement(eid)
            if isinstance(el, Grid):
                grids.append(el)
    if not grids:
        try:
            refs = uidoc.Selection.PickObjects(ObjectType.Element, GridFilter(), "Pilih grid")
            for r in refs:
                el = doc.GetElement(r.ElementId)
                if isinstance(el, Grid):
                    grids.append(el)
        except:
            pass
    return grids

def toggle_bubbles(grids):
    end0 = DatumEnds.End0
    end1 = DatumEnds.End1
    changed = 0
    skipped = 0

    t = Transaction(doc, "Toggle Grid Bubbles (Instance)")
    t.Start()
    try:
        for g in grids:
            try:
                v0 = g.IsBubbleVisibleInView(end0, active_view)
                v1 = g.IsBubbleVisibleInView(end1, active_view)

                # Hanya toggle kalau persis satu sisi ON
                if v0 and not v1:
                    g.HideBubbleInView(end0, active_view)
                    g.ShowBubbleInView(end1, active_view)
                    changed += 1
                elif v1 and not v0:
                    g.HideBubbleInView(end1, active_view)
                    g.ShowBubbleInView(end0, active_view)
                    changed += 1
                else:
                    skipped += 1
            except:
                skipped += 1
        t.Commit()
    except:
        t.RollBack()
        raise
    return changed, skipped

def main():
    grids = pick_grids()
    if not grids:
        forms.alert("Tidak ada Grid yang dipilih.", title="Toggle Grid Bubbles", warn_icon=True)
        return
    changed, skipped = toggle_bubbles(forms.toast(
        "Grid diproses: {} | Di-toggle: {} | Dilewati: {}".format(len(grids), changed, skipped),
        title="Toggle Grid Bubbles (Instance)",
        appid="PrasKaaPyKit"
    ))

if __name__ == "__main__":
    main()
