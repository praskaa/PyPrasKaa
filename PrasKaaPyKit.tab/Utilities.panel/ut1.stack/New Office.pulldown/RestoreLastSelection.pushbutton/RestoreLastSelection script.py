# -*- coding: utf-8 -*-
'''
Version: 1.1
Date    = 13.06.2026
_____________________________________________________________________
Description:
Restores element selection from last auto-saved state. Useful after
accidental Esc that clears Revit selection.

Reads serialized file (pickle) written by command-before-exec hooks,
verifies elements still exist in document, then restores selection.
Skips elements removed after last auto-save.
_____________________________________________________________________
How-to:
1. Run Move/Copy/Delete/Rotate (selection auto-saved by hook)
2. Accidentally press Esc — selection cleared
3. Run this tool
4. Selection restored to pre-command state
_____________________________________________________
Last update:
- 13.06.2026 - 1.1 Faster: batch GetElement via ElementMulticlassFilter
- 13.06.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

__title__ = "Restore Last Selection"

import pickle
from pyrevit import script, revit, forms
import Autodesk.Revit.DB as DB
from System.Collections.Generic import List

# ── runtime objects ────────────────────────────────────────────────
doc       = revit.doc
selection = revit.get_selection()
logger    = script.get_logger()

# ── data file written by command-before-exec hooks ─────────────────
# Key must match exactly what the hooks write ("LastAutoSel")
datafile = script.get_document_data_file("LastAutoSel", "pym")

# ──────────────────────────────────────────────────────────────────
def make_element_id(int_str):
    """
    Convert string integer → ElementId.
    ElementId(int) works on 2024-2025.
    2026 changed the constructor to accept long — fallback handles it.
    """
    val = int(int_str)
    try:
        return DB.ElementId(val)        # Revit 2024-2025
    except TypeError:
        return DB.ElementId(long(val))  # Revit 2026 fallback

# ──────────────────────────────────────────────────────────────────
def build_valid_ids(saved_str_ids):
    """
    Convert saved string IDs → valid ElementIds that still exist in doc.

    Speed optimisation vs one-by-one GetElement:
      Build a .NET List[ElementId] first, then run a single
      FilteredElementCollector with an ElementIdSetFilter.
      One DB round-trip instead of N individual GetElement calls.

    Returns (valid_id_list, missing_count).
    """
    # --- step 1: convert strings → ElementId objects ---------------
    candidate_ids = List[DB.ElementId]()
    parse_errors  = 0
    for s in saved_str_ids:
        try:
            candidate_ids.Add(make_element_id(s))
        except Exception:
            parse_errors += 1

    if candidate_ids.Count == 0:
        return [], parse_errors

    # --- step 2: single collector pass to filter existing elements --
    # ElementIdSetFilter returns only IDs that still exist in the doc.
    # Much faster than looping doc.GetElement() for large selections.
    id_filter    = DB.ElementIdSetFilter(candidate_ids)
    existing_ids = (
        DB.FilteredElementCollector(doc)
          .WherePasses(id_filter)
          .ToElementIds()          # returns ICollection[ElementId]
    )

    valid   = list(existing_ids)
    missing = candidate_ids.Count - len(valid) + parse_errors

    return valid, missing

# ══════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════
try:
    # --- load pickle -----------------------------------------------
    with open(datafile, "rb") as f:
        saved_ids = pickle.load(f)

    if not saved_ids:
        forms.alert("No auto-saved selection found.\n"
                    "Run a Move/Copy/Delete first.", exitscript=True)

    # --- validate against live document ----------------------------
    valid_ids, missing = build_valid_ids(saved_ids)

    if not valid_ids:
        forms.alert("All saved elements no longer exist in document.",
                    exitscript=True)

    # --- restore ---------------------------------------------------
    selection.set_to(valid_ids)

    # Lightweight status — print() goes to pyRevit output bar (no popup)
    # msg = "Restored {} elements.".format(len(valid_ids))
    # if missing:
        # msg += "  ({} no longer exist, skipped.)".format(missing)
    # print(msg)

except IOError:
    # File doesn't exist yet — no hook has fired this session
    forms.alert("No saved selection found.\n"
                "Run a Move/Copy/Delete/Rotate command first.",
                exitscript=True)

except Exception as e:
    logger.debug("RestoreLastSel failed: %s" % e)
    forms.alert("Unexpected error: {}".format(str(e)), exitscript=True)
