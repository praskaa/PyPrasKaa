# -*- coding: UTF-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction
from pyrevit import revit, EXEC_PARAMS

args = EXEC_PARAMS.event_args

# get IDs of modified elements
# mod_elems = __eventargs__.GetModifiedElementIds()
# print(mod_elems)

# get IDs of deleted elements
# del_elems = __eventargs__.GetDeletedElementIds()
# print(del_elems)