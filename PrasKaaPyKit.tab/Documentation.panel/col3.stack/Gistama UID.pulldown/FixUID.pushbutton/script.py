# -*- coding: utf-8 -*-
__title__ = "Fix UIDs"
__author__ = "PrasKaa"

from Autodesk.Revit.DB import FilteredElementCollector, Transaction, BuiltInParameter, ElementId
from pyrevit import revit, forms
import os

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
    db_path = get_database_path(doc)

    if not os.path.exists(db_path):
        forms.alert("DB tidak ditemukan. Generate UIDs dulu.", exitscript=True)
        return

    # Load registry
    registry = load_registry(db_path)

    # Collect current state
    current_state = {}
    uid_usage = {}

    for cat_enum, _ in GIS_CATEGORIES.values():
        for el in FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType():
            p = el.LookupParameter(PARAM_NAME)
            if p and p.AsString():
                elem_id = el.Id.IntegerValue
                uid = p.AsString()
                mark = get_mark(el)
                current_state[elem_id] = {'uid': uid, 'mark': mark}
                uid_usage.setdefault(uid, []).append(elem_id)

    # Detect issues
    conflicts = []
    mark_changed = []
    duplicates = {uid: ids for uid, ids in uid_usage.items() if len(ids) > 1}
    orphans = [eid for eid in registry if eid not in current_state]
    new_elements = [eid for eid in current_state if eid not in registry]

    # Build list of elements to fix
    to_fix = []

    # Conflicts: Element has UID but doesn't match registry
    for elem_id, state in current_state.items():
        if elem_id in registry:
            expected_uid = registry[elem_id]['GIS_Element_UID']
            expected_mark = registry[elem_id].get('Mark', '')
            current_uid = state['uid']
            current_mark = state['mark']

            if current_uid != expected_uid:
                conflicts.append((elem_id, current_uid, expected_uid))
                to_fix.append(elem_id)
            elif current_mark != expected_mark:
                mark_changed.append((elem_id, expected_mark, current_mark))
                # Don't fix mark changes - just warn
        else:
            new_elements.append(elem_id)
            to_fix.append(elem_id)

    # Duplicates: Same UID used by multiple elements
    for uid, elem_ids in duplicates.items():
        # Keep first, fix the rest
        for elem_id in elem_ids[1:]:
            to_fix.append(elem_id)

    if not to_fix:
        forms.alert("Tidak ada masalah UID yang perlu diperbaiki.\n\n"
                    "Note: {} perubahan Mark terdeteksi.".format(len(mark_changed)),
                    title="OK")
        return

    # Confirm
    if not forms.alert(
        "Perbaiki {} element?\n\n"
        "Conflicts: {}\n"
        "Duplicates: {}\n"
        "New: {}\n\n"
        "Mark Changed: {} (tidak akan difix)".format(
            len(to_fix), len(conflicts), len(duplicates), len(new_elements), len(mark_changed)
        ),
        title="Konfirmasi",
        options=["Ya, Perbaiki", "Batal"]
    ):
        return

    # Get all existing UIDs
    used_uids = get_all_model_uids(doc, GIS_CATEGORIES, PARAM_NAME)

    fixed = 0
    new_registry = {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with Transaction(doc, "Fix UIDs") as t:
        t.Start()

        # Process all elements
        for cat_enum, _ in GIS_CATEGORIES.values():
            for el in FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType():
                p = el.LookupParameter(PARAM_NAME)
                if not p or p.IsReadOnly:
                    continue

                elem_id = el.Id.IntegerValue
                type_name = get_type_name(el)
                family_name = get_family_name(el)
                mark = get_mark(el)
                cat_name = next(k for k, v in GIS_CATEGORIES.items() if v[0] == cat_enum)

                if elem_id in to_fix:
                    # Generate new UID
                    _, prefix = GIS_CATEGORIES[cat_name]
                    new_uid = generate_uid(prefix, used_uids)
                    p.Set(new_uid)
                    used_uids.add(new_uid)
                    fixed += 1

                    new_registry[elem_id] = {
                        'ElementId': elem_id,
                        'GIS_Element_UID': new_uid,
                        'Mark': mark,
                        'Category': cat_name,
                        'TypeName': type_name,
                        'FamilyName': family_name,
                        'Status': 'ACTIVE',
                        'Created': now,
                        'Modified': now
                    }
                else:
                    # Keep existing
                    if elem_id in registry:
                        entry = registry[elem_id].copy()
                        # Update Mark if changed
                        if entry.get('Mark') != mark:
                            entry['Mark'] = mark
                            entry['Modified'] = now
                        new_registry[elem_id] = entry
                    else:
                        current_uid = p.AsString()
                        new_registry[elem_id] = {
                            'ElementId': elem_id,
                            'GIS_Element_UID': current_uid,
                            'Mark': mark,
                            'Category': cat_name,
                            'TypeName': type_name,
                            'FamilyName': family_name,
                            'Status': 'ACTIVE',
                            'Created': now,
                            'Modified': now
                        }

        # Mark orphans as DELETED
        for elem_id in orphans:
            if elem_id in registry:
                entry = registry[elem_id].copy()
                entry['Status'] = 'DELETED'
                entry['Modified'] = now
                new_registry[elem_id] = entry

        t.Commit()

    # Save registry
    save_registry(db_path, new_registry.values())

    print("Fixed: {} | DB entries: {}".format(fixed, len(new_registry)))
    if mark_changed:
        print("Mark Changed: {} (not fixed)".format(len(mark_changed)))

    forms.alert("Berhasil memperbaiki {} element.\n\n"
                "Mark Changed: {} (not modified)".format(fixed, len(mark_changed)),
                title="Complete")


if __name__ == "__main__":
    from datetime import datetime
    main()
