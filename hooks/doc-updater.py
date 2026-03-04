# -*- coding: utf-8 -*-
from datetime import datetime
from Autodesk.Revit.DB import (
    BuiltInCategory, BuiltInParameter, ElementId,
    WorksharingUtils, FamilyInstance,
    ViewSheet, View  # ← tambahkan import ini
)

sender         = __eventsender__
args           = __eventargs__
doc            = args.GetDocument()

modified_el_ids = args.GetModifiedElementIds()
modified_el     = [doc.GetElement(e_id) for e_id in modified_el_ids]

allowed_cats = [
    ElementId(BuiltInCategory.OST_StructuralFraming),
    ElementId(BuiltInCategory.OST_StructuralColumns),
    ElementId(BuiltInCategory.OST_StructuralFoundation),
    ElementId(BuiltInCategory.OST_Walls),
    ElementId(BuiltInCategory.OST_Floors),
    ElementId(BuiltInCategory.OST_Stairs),
    ElementId(BuiltInCategory.OST_Sheets),  # ← Sheet
    ElementId(BuiltInCategory.OST_Views),   # ← View
]

for el in modified_el:
    # Ganti filter: izinkan FamilyInstance ATAU ViewSheet ATAU View
    is_family   = isinstance(el, FamilyInstance)
    is_sheet    = isinstance(el, ViewSheet)
    is_view     = isinstance(el, View) and not isinstance(el, ViewSheet)

    if not (is_family or is_sheet or is_view):
        continue

    # Cek kategori (opsional untuk sheet/view karena sudah dicek tipenya)
    el_cat = el.Category
    in_allowed_cat = el_cat is not None and el_cat.Id in allowed_cats

    if not (in_allowed_cat or is_sheet or is_view):
        continue

    try:
        timestamp   = datetime.now()
        f_timestamp = timestamp.strftime(r"%a, %d %b %H:%M")
        wti         = WorksharingUtils.GetWorksharingTooltipInfo(doc, el.Id)
        last        = wti.LastChangedBy
        value       = "{} ({})".format(last, f_timestamp)

        p_last = el.LookupParameter('LastModifiedBy')
        if p_last and not p_last.IsReadOnly:
            p_last.Set(value)

    except:
        import traceback
        print(traceback.format_exc())