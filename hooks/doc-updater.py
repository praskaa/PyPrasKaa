# -*- coding: utf-8 -*-
from datetime import datetime
from Autodesk.Revit.DB import (
    BuiltInCategory, ElementId,
    WorksharingUtils, FamilyInstance,
    Viewport
)

sender = __eventsender__
args   = __eventargs__
doc    = args.GetDocument()

modified_el_ids = args.GetModifiedElementIds()
modified_el     = [doc.GetElement(e_id) for e_id in modified_el_ids]

allowed_cats = [
    ElementId(BuiltInCategory.OST_StructuralFraming),
    ElementId(BuiltInCategory.OST_StructuralColumns),
    ElementId(BuiltInCategory.OST_StructuralFoundation),
    ElementId(BuiltInCategory.OST_Walls),
    ElementId(BuiltInCategory.OST_Floors),
    ElementId(BuiltInCategory.OST_Stairs),
    ElementId(BuiltInCategory.OST_Viewports),
    ElementId(BuiltInCategory.OST_Sheets),  
]

for el in modified_el:
    if el is None:
        continue

    is_family   = isinstance(el, FamilyInstance)
    is_viewport = isinstance(el, Viewport)

    if not (is_family or is_viewport):
        continue

    el_cat         = el.Category
    in_allowed_cat = el_cat is not None and el_cat.Id in allowed_cats
    if not in_allowed_cat:
        continue

    try:
        timestamp   = datetime.now()
        f_timestamp = timestamp.strftime(r"%a, %d %b %H:%M")
        wti         = WorksharingUtils.GetWorksharingTooltipInfo(doc, el.Id)
        last        = wti.LastChangedBy
        if not last or last.strip() == "":
            last = doc.Application.Username
        value  = "{} ({})".format(last, f_timestamp)
        p_last = el.LookupParameter('LastModifiedBy')
        if p_last and not p_last.IsReadOnly:
            p_last.Set(value)
    except:
        import traceback
        print(traceback.format_exc())