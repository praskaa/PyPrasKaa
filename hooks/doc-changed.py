# -*- coding: UTF-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction
from pyrevit import revit, EXEC_PARAMS

# Guard: document bisa invalid saat CopyElements atau operasi besar lainnya selesai.
# Kalau GetDocument() gagal, skip hook ini dengan aman.
try:
    args = EXEC_PARAMS.event_args

    # Pastikan document masih valid sebelum lanjut
    _doc = args.GetDocument()
    if _doc is None or not _doc.IsValidObject:
        import sys
        sys.exit(0)

except Exception:
    import sys
    sys.exit(0)

# get IDs of modified elements
# mod_elems = args.GetModifiedElementIds()
# print(mod_elems)

# get IDs of deleted elements
# del_elems = args.GetDeletedElementIds()
# print(del_elems)