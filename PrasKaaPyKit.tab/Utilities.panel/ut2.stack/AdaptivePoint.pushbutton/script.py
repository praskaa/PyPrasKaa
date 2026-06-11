# -*- coding: utf-8 -*-
'''
Version: 1.4
Date    = 18.03.2026
Author:  PrasKaa Team
'''
__title__ = "Hide Adaptive Points"
__author__ = "PrasKaa Team"
__version__ = "1.4"

from pyrevit import revit, DB, forms

def get_views_on_sheets():
    all_sheets = DB.FilteredElementCollector(revit.doc)\
                   .OfCategory(DB.BuiltInCategory.OST_Sheets)\
                   .WhereElementIsNotElementType()\
                   .ToElements()

    view_ids = set()
    for sheet in all_sheets:
        for vp_id in sheet.GetAllViewports():
            vp = revit.doc.GetElement(vp_id)
            if vp:
                view_ids.add(vp.ViewId)

    views = []
    for vid in view_ids:
        v = revit.doc.GetElement(vid)
        if v:
            views.append(v)
    return views

def get_adaptive_category():
    return revit.doc.Settings.Categories.get_Item(
        DB.BuiltInCategory.OST_AdaptivePoints_Points
    )

def try_set_category_hidden(view_or_template, category):
    try:
        if not view_or_template.CanCategoryBeHidden(category.Id):
            return False
        view_or_template.SetCategoryHidden(category.Id, True)
        return True
    except Exception:
        return False

@revit.carryout('Hide Adaptive Points Subcategory')
def main():
    category = get_adaptive_category()
    if category is None:
        forms.alert('Category OST_AdaptivePoints_Points not found.', title='Hide Adaptive Points')
        return

    sheet_views = get_views_on_sheets()
    invalid_id  = DB.ElementId.InvalidElementId
    template_ids = set()

    for view in sheet_views:
        tid = view.ViewTemplateId
        if tid != invalid_id:
            template_ids.add(tid)
        else:
            try_set_category_hidden(view, category)

    for tid in template_ids:
        tmpl = revit.doc.GetElement(tid)
        if tmpl:
            try_set_category_hidden(tmpl, category)

main()