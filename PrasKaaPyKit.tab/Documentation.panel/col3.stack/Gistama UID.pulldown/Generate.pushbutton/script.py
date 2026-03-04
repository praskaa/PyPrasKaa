# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Generates GIS_Element_UID for selected categories. Creates unique identifiers
for structural elements based on category prefix and sequential numbering.
_____________________________________________________________________
How-to:
1. Click "Generate UIDs"
2. Select categories to process
3. Choose mode: Generate Missing or Regenerate All
4. UIDs are generated and saved to registry database

Notes:
- Stores registry in Documents\PrasKaaPyKit\
- UIDs follow format: PREFIX-00001
- Updates existing UIDs if "Regenerate All" selected

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

__title__ = "Generate UIDs"
__author__ = "PrasKaa"

from Autodesk.Revit.DB import FilteredElementCollector, Transaction, BuiltInParameter
from pyrevit import revit, forms

# Import shared configuration and utilities
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME
from elements.element_names import get_type_name, get_family_name
from uid_registry import (
    get_database_path,
    load_registry,
    save_registry,
    generate_uid,
    get_all_model_uids
)

doc = revit.doc


def get_mark(element):
    """Get Mark parameter value from element."""
    try:
        mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if mark_param:
            return mark_param.AsString() or ""
    except:
        pass
    return ""


def main():
    # Validate parameter exists
    if not any(FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType().FirstElement()
               and FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType().FirstElement().LookupParameter(PARAM_NAME)
               for cat, _ in GIS_CATEGORIES.values()):
        forms.alert("Parameter '{}' tidak ditemukan.".format(PARAM_NAME))
        return

    # User input
    selected = forms.SelectFromList.show(sorted(GIS_CATEGORIES.keys()), title="Pilih Kategori", multiselect=True)
    if not selected:
        return

    overwrite = forms.alert("Mode:", options=["Generate Missing", "Regenerate All"]) == "Regenerate All"

    # Load existing registry
    db_path = get_database_path(doc)
    old_registry = load_registry(db_path)

    # Get all existing UIDs in model
    used_uids = get_all_model_uids(doc, GIS_CATEGORIES, PARAM_NAME)

    new_registry = {}
    generated = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with Transaction(doc, "Generate UIDs") as t:
        t.Start()

        for name in selected:
            cat_enum, prefix = GIS_CATEGORIES[name]
            for el in FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType():
                p = el.LookupParameter(PARAM_NAME)
                if not p or p.IsReadOnly:
                    continue

                elem_id = el.Id.IntegerValue
                current_uid = p.AsString()
                old_entry = old_registry.get(elem_id, {})
                type_name = get_type_name(el)
                family_name = get_family_name(el)
                mark = get_mark(el)

                # Determine if generate needed
                need_generate = overwrite or not current_uid

                if need_generate:
                    # Generate new UID
                    new_uid = generate_uid(prefix, used_uids)
                    p.Set(new_uid)
                    used_uids.add(new_uid)
                    generated += 1

                    new_registry[elem_id] = {
                        'ElementId': elem_id,
                        'GIS_Element_UID': new_uid,
                        'Mark': mark,
                        'Category': name,
                        'TypeName': type_name,
                        'FamilyName': family_name,
                        'Status': 'ACTIVE',
                        'Created': old_entry.get('Created', now),
                        'Modified': now
                    }
                else:
                    # Keep existing UID
                    if elem_id in old_registry:
                        # Update Mark if changed
                        entry = old_entry.copy()
                        if entry.get('Mark') != mark:
                            entry['Mark'] = mark
                            entry['Modified'] = now
                        new_registry[elem_id] = entry
                    else:
                        new_registry[elem_id] = {
                            'ElementId': elem_id,
                            'GIS_Element_UID': current_uid,
                            'Mark': mark,
                            'Category': name,
                            'TypeName': type_name,
                            'FamilyName': family_name,
                            'Status': 'ACTIVE',
                            'Created': now,
                            'Modified': now
                        }

        t.Commit()

    # Save registry
    save_registry(db_path, new_registry.values())

    print("Generated: {} | Total DB entries: {}".format(generated, len(new_registry)))
    print("DB: {}".format(db_path))


if __name__ == "__main__":
    from datetime import datetime
    main()
