# -*- coding: utf-8 -*-
"""Toggle 2D/3D Extents for Grids in Active View
Works on selected Grids (if any), else all visible Grids in the active view.
"""

__title__ = "Toggle Grid 2D/3D Extents"
__author__ = "PrasKaa Team"

from pyrevit import revit, DB, forms

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document
aview = uidoc.ActiveView

def get_target_grids():
    sel_ids = list(uidoc.Selection.GetElementIds())
    if sel_ids:
        elems = [doc.GetElement(eid) for eid in sel_ids]
        grids = [e for e in elems if isinstance(e, DB.Grid)]
        if grids:
            return grids
        # Jika yang terseleksi bukan Grid, fallback ke visible-in-view
    # Ambil semua Grid yang muncul di active view
    col = DB.FilteredElementCollector(doc, aview.Id)\
            .OfCategory(DB.BuiltInCategory.OST_Grids)\
            .WhereElementIsNotElementType()
    grids = [g for g in col if isinstance(g, DB.Grid)]
    return grids

def grid_is_any_end_2d(grid, view):
    # Cek apakah salah satu ujung (End0/End1) dalam mode 2D (ViewSpecific)
    ends = [DB.DatumEnds.End0, DB.DatumEnds.End1]
    try:
        for end in ends:
            if grid.GetDatumExtentType(end, view) == DB.DatumExtentType.ViewSpecific:
                return True
        return False
    except Exception:
        # Fallback untuk API lama (jarang diperlukan, tapi berjaga-jaga)
        # Beberapa versi punya overload tanpa 'end' (level tertentu).
        # Kalau gagal, anggap not 2D agar set jadi 2D.
        return False

def set_grid_extents(grid, view, to_viewspecific):
    ends = [DB.DatumEnds.End0, DB.DatumEnds.End1]
    target_type = DB.DatumExtentType.ViewSpecific if to_viewspecific else DB.DatumExtentType.Model
    for end in ends:
        # Untuk safety: bungkus tiap set dalam try agar grid melengkung/khusus tetap lanjut.
        try:
            grid.SetDatumExtentType(end, view, target_type)
        except Exception:
            # API overload berbeda di beberapa versi — coba tanpa 'end' jika tersedia
            try:
                # WARNING: tidak semua versi punya method ini; diamkan jika gagal.
                grid.SetDatumExtentType(view, target_type)
            except Exception:
                pass

def main():
    grids = get_target_grids()
    if not grids:
        forms.alert("Tidak ada Grid ditemukan di active view atau seleksi.", exitscript=True)

    toggled_to_2d = 0
    toggled_to_3d = 0

    with revit.Transaction("Toggle Grid 2D/3D Extents"):
        for g in grids:
            # Jika salah satu ujung sudah 2D → jadikan 3D; else jadikan 2D
            if grid_is_any_end_2d(g, aview):
                set_grid_extents(g, aview, to_viewspecific=False)  # ke 3D (Model)
                toggled_to_3d += 1
            else:
                set_grid_extents(g, aview, to_viewspecific=True)   # ke 2D (ViewSpecific)
                toggled_to_2d += 1

    total = len(grids)
    msg = "Grid diproses: {}\n→ ke 2D: {}\n→ ke 3D: {}".format(total, toggled_to_2d, toggled_to_3d)
    forms.toast(msg, title="Toggle Grid 2D/3D", appid="PrasKaaPyKit")

if __name__ == "__main__":
    main()
