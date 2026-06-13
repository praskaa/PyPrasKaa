# -*- coding: utf-8 -*-
# Author:  PrasKaa
# Version: 1.0
# Date:    13.06.2026
#
# HOOK: command-before-exec[ID_EDIT_MOVE_COPY].py
#
# Duplicate this file and rename for other commands:
#   command-before-exec[ID_EDIT_MOVE].py
#   command-before-exec[ID_EDIT_COPY].py
#   command-before-exec[ID_EDIT_DELETE].py
#   command-before-exec[ID_EDIT_ROTATE].py
#   command-before-exec[ID_EDIT_MIRROR_PICK].py
#   command-before-exec[ID_EDIT_MIRROR_DM].py
#   command-before-exec[ID_EDIT_ARRAY].py
#
# HOW IT WORKS:
#   pyRevit fires this script BEFORE the named Revit command executes.
#   At that moment the user's selection is still intact — we snapshot
#   it to a per-document pickle file so RestoreLastSel can reload it
#   after an accidental Esc wipes the selection.
#
# DATA FILE:
#   Written to pyRevit's appdata folder, keyed to the active document.
#   Example path:
#     %APPDATA%\pyRevit\<ver>\pyRevit_<ver>_LastAutoSel_<docname>.pym
#   Key "LastAutoSel" must match exactly what RestoreLastSel reads.
#
# PERFORMANCE:
#   Hook runs synchronously before every matched command.
#   Kept intentionally minimal — no imports beyond what's needed,
#   no validation loops, single file write.

import pickle
from pyrevit import script, revit
from pyrevit.compat import get_elementid_value_func

logger = script.get_logger()

def main():
    selection = revit.get_selection()

    # Nothing selected → nothing worth saving
    if not selection.element_ids:
        logger.debug("PrasKaa hook: empty selection, skip")
        return

    # Convert ElementId objects → plain strings for pickle portability
    # (ElementId is a .NET object; storing raw ints as strings is safer
    #  across IronPython sessions and avoids serialisation edge cases)
    get_id_value  = get_elementid_value_func()
    ids_to_save   = {str(get_id_value(eid)) for eid in selection.element_ids}

    # Write to per-document slot — overwrites previous snapshot
    # One slot only: we only need to recover from the *last* command
    datafile = script.get_document_data_file("LastAutoSel", "pym")
    try:
        with open(datafile, "wb") as f:
            pickle.dump(ids_to_save, f)
        logger.debug("PrasKaa hook: saved {} IDs → {}".format(
            len(ids_to_save), datafile))
    except Exception as e:
        # Non-fatal — user just won't be able to restore this time
        logger.debug("PrasKaa hook: write failed — {}".format(str(e)))

main()