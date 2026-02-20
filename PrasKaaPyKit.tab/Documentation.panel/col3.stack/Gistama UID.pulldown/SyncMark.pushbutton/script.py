# -*- coding: utf-8 -*-
__title__ = 'Sync Mark by UID'
__author__ = 'PrasKaa'

from Autodesk.Revit.DB import FilteredElementCollector, Transaction, RevitLinkInstance
from pyrevit import revit, forms

# Import centralized config
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME

doc = revit.doc
TARGET_PARAM = "Mark"


def main():
    # Select link
    links = {l.Name: l for l in FilteredElementCollector(doc).OfClass(RevitLinkInstance)}
    selected_link_name = forms.SelectFromList.show(
        sorted(links.keys()),
        title='Select Source Link (File A)',
        multiselect=False
    )
    if not selected_link_name: return
    
    selected_link = links[selected_link_name]
    link_doc = selected_link.GetLinkDocument()
    if not link_doc:
        forms.alert("Cannot access link document."); return
    
    # Select category
    selected_cat = forms.SelectFromList.show(
        sorted(GIS_CATEGORIES.keys()),
        title='Select Category',
        multiselect=False
    )
    if not selected_cat: return
    
    cat_enum, _ = GIS_CATEGORIES[selected_cat]
    
    # Select mode
    overwrite = forms.alert("Sync Mode:", options=["Update Empty Only", "Overwrite All"]) == "Overwrite All"
    
    # Build source map {UID: Mark}
    source_data = {}
    for el in FilteredElementCollector(link_doc).OfCategory(cat_enum).WhereElementIsNotElementType():
        uid_p = el.LookupParameter(PARAM_NAME)
        mark_p = el.LookupParameter(TARGET_PARAM)
        if uid_p and mark_p:
            uid = uid_p.AsString()
            mark = mark_p.AsString()
            if uid and mark:
                source_data[uid] = mark
    
    if not source_data:
        forms.alert("No UID+Mark data in source link."); return
    
    # Sync to host
    updated, skipped = 0, 0
    
    with Transaction(doc, "Sync Mark by UID") as t:
        t.Start()
        
        for el in FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType():
            uid_p = el.LookupParameter(PARAM_NAME)
            if not uid_p: continue
            
            uid = uid_p.AsString()
            if not uid or uid not in source_data: continue
            
            mark_p = el.LookupParameter(TARGET_PARAM)
            if not mark_p or mark_p.IsReadOnly: continue
            
            current = mark_p.AsString()
            new_mark = source_data[uid]
            
            if overwrite or not current:
                if current != new_mark:
                    mark_p.Set(new_mark)
                    updated += 1
                else:
                    skipped += 1
        
        t.Commit()
    
    print("Synced: {} | Skipped: {}".format(updated, skipped))
    forms.alert("Updated: {} elements".format(updated), title="Complete")


if __name__ == "__main__":
    main()
