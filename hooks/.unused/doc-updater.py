# -*- coding: UTF-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, \
        Transaction, Document, BuiltInParameter
from pyrevit import revit, EXEC_PARAMS
from pyrevit.userconfig import user_config
import sys
import os

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from customOutput import def_doorUnflipped, def_doorFlipped
from customOutput import def_windowUnflipped, def_windowFlipped

doc = EXEC_PARAMS.event_doc

# read config file
try:
    # door mirror flip states
    left = user_config.PrasKaaToolsSettings.doorUnflipped # L
    right = user_config.PrasKaaToolsSettings.doorFlipped # R
    # window mirror flip states
    unflipped = user_config.PrasKaaToolsSettings.windowUnflipped # 0
    flipped = user_config.PrasKaaToolsSettings.windowFlipped # 1

# if config is not available
except:
    # door mirror flip states
    left = def_doorUnflipped # L
    right = def_doorFlipped # R

    # window mirror flip states
    unflipped = def_windowUnflipped # 0
    flipped = def_windowFlipped # 1


# # door mirror flip states
# left = "L"
# right = "P"

# # window mirror flip states
# flipped = "1"
# unflipped = "0"


def door_swing_setter(doc):
    # Auto Door flip setter
    doors = FilteredElementCollector(doc) \
            .OfCategory(BuiltInCategory.OST_Doors) \
            .WhereElementIsNotElementType()
    param_name = 'Door Swing'
    with revit.Transaction('Auto Door Flip Setter'):
        for d in doors:
            param = d.LookupParameter(param_name)
            if param:
                # # default door is Left
                if d.Mirrored:
                    param.Set(right)
                else:
                    param.Set(left)

def win_swing_setter(doc):
    # Auto Window flip setter
    windows = FilteredElementCollector(doc) \
            .OfCategory(BuiltInCategory.OST_Windows) \
            .WhereElementIsNotElementType()
    param_name = 'Window Flip'
    param_name_obsolete = 'Window Swing'

    with revit.Transaction('Auto Window Flip Setter'):
        for w in windows:
            w_type_Id = w.GetTypeId()
            w_type = Document.GetElement(doc,w_type_Id)
            # skipping all windows without Type (e.g. DirectShape)
            if w_type:
                # skipping the wall penetration modelled in the window category
                filterp = w_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
                if filterp and filterp.AsString() != "stavebne upravy":
                    param = w.LookupParameter(param_name)
                    if param:
                        # default window is unflipped
                        if w.Mirrored:
                            param.Set(flipped)
                        else:
                            param.Set(unflipped)
                    # Obsolete parameter name for backward compatibility. 
                    # This is not going to be supported in the future.
                    # The parameter name should ne changed to "Window Flip".
                    param = w.LookupParameter(param_name_obsolete)
                    if param:
                        # default window is unflipped
                        if w.Mirrored:
                            param.Set(flipped)
                        else:
                            param.Set(unflipped)


if not doc.IsFamilyDocument:
    # WINDOWS
    # getting project info
    # if there is shared parameter NOT checked, script is not triggered
    win_settings = doc.ProjectInformation.LookupParameter("ctWindowSwingSetterOFF")
    try:
        # if parameter is turned on
        if not win_settings or win_settings.AsInteger() == 0:
            win_swing_setter(doc)
    except AttributeError:
        # if parameter doesn't exist
        if not win_settings:
            win_swing_setter(doc)

    # DOORS
    # getting project info
    # if there is shared parameter NOT checked, script is not triggered
    door_settings = doc.ProjectInformation.LookupParameter("ctDoorSwingSetterOFF")
    try:
        # if parameter is nurned on
        if not door_settings or door_settings.AsInteger() == 0:
            door_swing_setter(doc)
    except AttributeError:
        # if parameter doesn't exist
        if not door_settings:
            door_swing_setter(doc)