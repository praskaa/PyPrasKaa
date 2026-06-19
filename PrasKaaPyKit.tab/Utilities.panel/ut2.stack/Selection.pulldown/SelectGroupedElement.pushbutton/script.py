# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Pick rectangle to select elements inside any Group (Detail or Model)
# Version: 1.0

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