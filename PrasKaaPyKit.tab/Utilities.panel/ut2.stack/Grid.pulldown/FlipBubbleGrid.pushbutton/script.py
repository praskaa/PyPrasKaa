# -*- coding: utf-8 -*-
"""Toggle bubble Grid di Active View: kalau salah satu sisi ON, balikkan ke sisi lain
Kalau keduanya ON atau keduanya OFF -> diabaikan
"""

__title__ = "Toggle Grid Bubble"
__author__ = "PrasKaa Team"

from Autodesk.Revit.DB import Transaction, Grid, DatumEnds
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from pyrevit import revit, forms

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
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
    changed, skipped = toggle_bubbles(grids)
    forms.toast(
        "Grid diproses: {} | Di-toggle: {} | Dilewati: {}".format(len(grids), changed, skipped),
        title="Toggle Grid Bubbles (Instance)",
        appid="PrasKaaPyKit"
    )

if __name__ == "__main__":
    main()
