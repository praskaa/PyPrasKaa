# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 21.06.2026
_____________________________________________________________________
Description:
Pick rectangle to select all elements that belong to any Group (Detail or
Model) within the picked area. The tool filters elements by checking if
they have a valid GroupId, then sets the selection to those grouped elements.

This is useful for quickly selecting all members of nested groups without
manually picking each element individually.
_____________________________________________________________________
How-to:
1. Click the button to activate the selection tool
2. Draw a rectangle (pick rectangle) in the viewport to define the area
3. All elements within the rectangle that belong to a group will be selected
4. Selection can include elements from multiple groups (both Detail and Model)

Note: Elements outside groups within the rectangle will be excluded.
_____________________________________________________
Last update:
- 21.06.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

from pyrevit import revit, UI

selection = revit.get_selection()

class GroupMemberSelectionFilter(UI.Selection.ISelectionFilter):
    def AllowElement(self, element):
        # Allow any element that belongs to a group (GroupId is valid)
        # Works across multiple groups in the same pick rectangle
        invalid_id = element.GroupId.InvalidElementId
        return element.GroupId != invalid_id

    def AllowReference(self, refer, point):
        return False

try:
    gfilter = GroupMemberSelectionFilter()
    selection_list = revit.pick_rectangle(pick_filter=gfilter)
    filtered_ids = [el.Id for el in selection_list]
    selection.set_to(filtered_ids)
    revit.uidoc.RefreshActiveView()
except Exception:
    pass