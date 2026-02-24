#*-* coding:utf-8 *-*
from datetime import datetime
from Autodesk.Revit.DB import (BuiltInCategory, BuiltInParameter, ElementId, WorksharingUtils, FamilyInstance)

# Variables
sender  = __eventsender__
args    = __eventargs__

doc     = args.GetDocument()

# Get the modified, deleted and new elements
modified_el_ids = args.GetModifiedElementIds()
deleted_el_ids  = args.GetDeletedElementIds()
new_el_ids      = args.GetAddedElementIds()

modified_el = [doc.GetElement(e_id) for e_id in modified_el_ids]


# IUpdater - Modified Elements
allowed_cats =[
    ElementId(BuiltInCategory.OST_StructuralFraming),
    ElementId(BuiltInCategory.OST_StructuralColumns), 
    ElementId(BuiltInCategory.OST_StructuralFoundation), 
    ElementId(BuiltInCategory.OST_Walls), 
    ElementId(BuiltInCategory.OST_Floors),
    ElementId(BuiltInCategory.OST_Stairs)
]
for el in modified_el:

    if type(el) != FamilyInstance:
        continue

    # Check if element is in allowed categories
    if el.Category.Id in allowed_cats:

        try:
            # Get the last modified date
            timestamp = datetime.now()
            f_timestamp = timestamp.strftime(r"%a, %d %b %H:%M")

            wti = WorksharingUtils.GetWorksharingTooltipInfo(doc, el.Id)
            last = wti.LastChangedBy

            value   = "{} ({})".format(last, f_timestamp)

            p_last  = el.LookupParameter('LastModifiedBy')
            if p_last:
                p_last.Set(value)
 
        except:
            import traceback
            print(traceback.format_exc())