# -*- coding: utf-8 -*-
__title__ = "Validate UIDs"
__author__ = "PrasKaa"

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter
from pyrevit import revit, forms
import os

# Import shared configuration and utilities
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME
from uid_registry import get_database_path, load_registry

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

    # Check issues
    conflicts = []
    mark_changed = []
    duplicates = {uid: ids for uid, ids in uid_usage.items() if len(ids) > 1}
    orphans = [eid for eid in registry if eid not in current_state]
    new_elements = [eid for eid in current_state if eid not in registry]

    # Find conflicts and mark changes
    for elem_id, state in current_state.items():
        if elem_id in registry:
            expected_uid = registry[elem_id]['GIS_Element_UID']
            expected_mark = registry[elem_id].get('Mark', '')
            current_uid = state['uid']
            current_mark = state['mark']

            if current_uid != expected_uid:
                conflicts.append((elem_id, current_uid, expected_uid))
            elif current_mark != expected_mark:
                mark_changed.append((elem_id, expected_mark, current_mark))
        else:
            new_elements.append(elem_id)

    # Report
    print("=" * 50)
    print("UID VALIDATION")
    print("=" * 50)
    print("DB: {}".format(db_path))
    print("-" * 50)
    print("Conflicts (copy-paste): {}".format(len(conflicts)))
    print("Mark Changed (revisi): {}".format(len(mark_changed)))
    print("Duplicates (same UID): {}".format(len(duplicates)))
    print("New (not in DB): {}".format(len(new_elements)))
    print("Orphans (deleted): {}".format(len(orphans)))
    print("=" * 50)

    if conflicts:
        print("\nCONFLICTS:")
        for elem_id, curr, exp in conflicts[:5]:
            print("  ID {}: '{}' != '{}'".format(elem_id, curr, exp))

    if mark_changed:
        print("\nMARK CHANGED (perubahan terdeteksi):")
        for elem_id, old_mark, new_mark in mark_changed[:5]:
            print("  ID {}: '{}' -> '{}'".format(elem_id, old_mark, new_mark))

    if duplicates:
        print("\nDUPLICATES:")
        for uid, ids in list(duplicates.items())[:5]:
            print("  '{}' -> {}".format(uid, ids))

    # Alert summary
    issues = len(conflicts) + len(duplicates)
    warnings = len(mark_changed)

    if issues > 0:
        forms.alert(
            "ISSUES (harus diperbaiki):\n\n"
            "Conflicts: {}\n"
            "Duplicates: {}\n\n"
            "WARNINGS (revisi terdeteksi):\n"
            "Mark Changed: {}\n\n"
            "Run 'Fix UIDs' untuk issues.".format(
                len(conflicts), len(duplicates), len(mark_changed)
            ),
            title="Validation Failed"
        )
    elif warnings > 0:
        forms.alert(
            "WARNINGS (perubahan terdeteksi):\n\n"
            "Mark Changed: {}\n\n"
            "Periksa apakah perubahan ini authorized.".format(len(mark_changed)),
            title="Warnings Found"
        )
    else:
        forms.alert("All UIDs valid!", title="OK")


if __name__ == "__main__":
    main()
