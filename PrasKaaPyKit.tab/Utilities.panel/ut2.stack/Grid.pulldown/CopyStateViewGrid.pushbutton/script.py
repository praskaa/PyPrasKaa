# -*- coding: utf-8 -*-
"""Sync Grid Visibility: match which Grids are visible in Source View into Target View(s)"""

__title__ = "Sync Grid Visibility"
__author__ = "PrasKaa Team"

from pyrevit import revit, DB, forms
from System.Collections.Generic import List

doc   = revit.doc
uidoc = __revit__.ActiveUIDocument

# --- helpers ----------------------------------------------------------------
VIEW_TYPES = {
    DB.ViewType.FloorPlan,
    DB.ViewType.EngineeringPlan,
    DB.ViewType.CeilingPlan,
    DB.ViewType.Section,
    DB.ViewType.Elevation,
    DB.ViewType.AreaPlan
}

def candidate_views():
    vs = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
    return [v for v in vs if not v.IsTemplate and v.ViewType in VIEW_TYPES]

def get_visible_grids_in_view(view):
    # Collector berbasis view otomatis menghitung visibilitas aktual (kategori, filter, hide, crop)
    col = (DB.FilteredElementCollector(doc, view.Id)
           .OfCategory(DB.BuiltInCategory.OST_Grids)
           .WhereElementIsNotElementType())
    return set(col.ToElementIds())

def ensure_grid_category_visible(view):
    # Jika mau menampilkan grid (unhide), pastikan kategori Grid tidak disembunyikan
    try:
        cat = DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Grids)
        if cat and view.CanCategoryBeHidden(cat.Id):
            try:
                # Revit modern
                if view.GetCategoryHidden(cat.Id):
                    view.SetCategoryHidden(cat.Id, False)
            except:
                # Revit lama: langsung set visible (akan no-op jika sudah visible)
                try:
                    view.SetCategoryHidden(cat.Id, False)
                except:
                    pass
    except:
        pass

def hide_in_view(view, ids_iter):
    idlist = List[DB.ElementId]()
    for eid in ids_iter:
        idlist.Add(eid)
    if idlist.Count:
        try:
            view.HideElements(idlist)
        except Exception as e:
            forms.alert("Gagal HideElements di view '{}':\n{}".format(view.Name, e))

def unhide_in_view(view, ids_iter):
    idlist = List[DB.ElementId]()
    for eid in ids_iter:
        idlist.Add(eid)
    if idlist.Count:
        try:
            view.UnhideElements(idlist)
        except Exception as e:
            forms.alert("Gagal UnhideElements di view '{}':\n{}".format(view.Name, e))

# --- pick views --------------------------------------------------------------
views = candidate_views()
if not views:
    forms.alert("Tidak ada view kandidat (plan/section/elevation) ditemukan.", exitscript=True)

src_view = forms.SelectFromList.show(
    sorted(views, key=lambda v: v.Name),
    name_attr='Name',
    title="Pilih SOURCE View (acuan grid yang TAMPIL)",
    multiselect=False
)
if not src_view:
    forms.alert("Source view tidak dipilih.", exitscript=True)

targets = [v for v in views if v.Id != src_view.Id]
tgt_pick = forms.SelectFromList.show(
    sorted(targets, key=lambda v: v.Name),
    name_attr='Name',
    title="Pilih TARGET View(s) untuk disinkronkan",
    multiselect=True
)
if not tgt_pick:
    forms.alert("Target view tidak dipilih.", exitscript=True)

# --- compute & apply ---------------------------------------------------------
src_visible = get_visible_grids_in_view(src_view)

with revit.Transaction("Sync Grid Visibility (by Source View)"):
    total_sync = 0
    for tv in tgt_pick:
        tgt_visible = get_visible_grids_in_view(tv)

        # Set hasil akhir di Target = src_visible
        to_show = src_visible.difference(tgt_visible)   # harus dimunculkan di Target
        to_hide = tgt_visible.difference(src_visible)   # harus disembunyikan di Target

        # Pastikan kategori Grid terlihat jika ada yang perlu di-show
        if to_show:
            ensure_grid_category_visible(tv)
            unhide_in_view(tv, to_show)

        if to_hide:
            hide_in_view(tv, to_hide)

        total_sync += 1
        forms.toast(
            "View: {}\nShow: {}\nHide: {}".format(tv.Name, len(to_show), len(to_hide)),
            title="Sync Grid Visibility",
            appid="PrasKaaPyKit"
        )

forms.toast("Sync selesai untuk {} view target.".format(total_sync),
            title="Sync Grid Visibility", appid="PrasKaaPyKit")
