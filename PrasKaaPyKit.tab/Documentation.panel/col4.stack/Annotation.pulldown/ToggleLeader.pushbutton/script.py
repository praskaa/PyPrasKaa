# -*- coding: utf-8 -*-
"""
Version: 1.0
Date    = 05.03.2026
_____________________________________________________________________
Description:
Toggle leader ON/OFF on selected IndependentTag elements. This tool
inverts the leader (arrow) status of the selected tags.

When enabled, the leader displays an arrow pointing to the referenced
element. This tool is useful for batch-modifying tag appearance without
needing to edit each tag individually.
_____________________________________________________________________
How-to:
1. Select the tags (IndependentTag) in the viewport to modify
2. Run this tool from the PrasKaaPyKit toolbar
3. The leader will be toggled (ON becomes OFF, OFF becomes ON)
4. No need to reselect - simply run again to toggle back

_____________________________________________________
Last update:
- 05.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""

__title__ = "Toggle\nLeader"
__doc__ = """Toggle leader ON/OFF on selected IndependentTag elements."""

from pyrevit import revit, DB, script

doc = revit.doc
uidoc = revit.uidoc

selection_ids = uidoc.Selection.GetElementIds()
if not selection_ids:
    script.exit()

tags = []
for eid in selection_ids:
    el = doc.GetElement(eid)
    if isinstance(el, DB.IndependentTag):
        tags.append(el)

if not tags:
    script.exit()

with revit.Transaction("Toggle Tag Leader"):
    for tag in tags:
        tag.HasLeader = not tag.HasLeader