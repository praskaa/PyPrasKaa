# -*- coding: utf-8 -*-
'''
Version: 1.1
Date    = 13.06.2026
_____________________________________________________________________
Description:
Sets grid extent mode to 2D (ViewSpecific) for selected grids or all
visible grids in the active view. No toggle — always forces 2D extents.
_____________________________________________________________________
How-to:
1. Click "Set Grid to 2D Extents"
2. Select grids (or uses all visible grids in active view)
3. All targeted grids set to 2D (ViewSpecific) in the active view

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release as toggle
- 13.06.2026 - 1.1 Changed to non-toggle; always sets 2D extents
_____________________________________________________________________
Author:  PrasKaa Team
'''

__title__ = "Set Grid to 2D Extents"
__author__ = "PrasKaa Team"
__version__ = "1.1"

from pyrevit import revit, DB, forms

uidoc = revit.uidoc
doc = revit.doc
aview = doc.ActiveView

def get_target_grids():
    sel_ids = list(uidoc.Selection.GetElementIds())
    if sel_ids:
        elems = [doc.GetElement(eid) for eid in sel_ids]
        grids = [e for e in elems if isinstance(e, DB.Grid)]
        if grids:
            return grids
    col = DB.FilteredElementCollector(doc, aview.Id)\
            .OfCategory(DB.BuiltInCategory.OST_Grids)\
            .WhereElementIsNotElementType()
    grids = [g for g in col if isinstance(g, DB.Grid)]
    return grids

def set_grid_to_2d(grid, view):
    ends = [DB.DatumEnds.End0, DB.DatumEnds.End1]
    for end in ends:
        try:
            grid.SetDatumExtentType(end, view, DB.DatumExtentType.ViewSpecific)
        except Exception:
            try:
                grid.SetDatumExtentType(view, DB.DatumExtentType.ViewSpecific)
            except Exception:
                pass

def main():
    grids = get_target_grids()
    if not grids:
        forms.alert("Tidak ada Grid ditemukan di active view atau seleksi.", exitscript=True)

    count = 0
    with revit.Transaction("Set Grid to 2D Extents"):
        for g in grids:
            set_grid_to_2d(g, aview)
            count += 1

    msg = "Grid berhasil di-set ke 2D: {}".format(count)
    forms.toast(msg, title="Set Grid 2D Extents", appid="PrasKaaPyKit")

if __name__ == "__main__":
    main()