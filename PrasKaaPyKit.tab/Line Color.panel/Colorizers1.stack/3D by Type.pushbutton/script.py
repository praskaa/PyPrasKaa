from collections import defaultdict
from pyrevit import HOST_APP
from pyrevit import forms
from pyrevit import revit, DB
from pyrevit import script
import random
import threedconfig
from database import get_solid_fill_pat, get_3Dviewtype_id, remove_viewtemplate
from colorize import get_colours, set_colour_overrides_by_option, get_categories_config
from pyrevit.framework import List


logger = script.get_logger()
BIC = DB.BuiltInCategory
doc = revit.doc
overrides_option = threedconfig.get_overrides_config()
solid_fill_pattern = get_solid_fill_pat(doc=doc)

categories_for_selection = get_categories_config(doc)
sorted_cats = sorted(categories_for_selection.keys(), key=lambda x: x)


selected_cat = forms.CommandSwitchWindow.show(sorted_cats, message="Select Category to Colorize", width = 400)
if selected_cat == None:
    script.exit()

chosen_bic = [categories_for_selection[selected_cat]]
if selected_cat in ["Curtain Wall Panels", "Curtain Wall Mullions"]: # not so elegant way to support curtain panels by adding walls category
    chosen_bic.append(BIC.OST_Walls)

# get all element categories and return a list of all categories except chosen BIC
all_cats = doc.Settings.Categories
chosen_category = [all_cats.get_Item(i) for i in chosen_bic]
hide_categories_except = [c for c in all_cats if c.Id not in [i.Id for i in chosen_category]]

# First, try to find any existing view with this name
# We'll handle deletion inside the transaction
existing_view_name = "Colorize {} by Type".format(selected_cat)

# Collect view elements BEFORE the transaction
get_view_elements = DB.FilteredElementCollector(doc) \
    .OfCategory(chosen_bic[0]) \
    .WhereElementIsNotElementType() \
    .ToElements()

# Build the types dictionary before transaction
types_dict = defaultdict(set)
for el in get_view_elements:
    # discard nested shared - group under the parent family
    if selected_cat in ["Floors", "Walls", "Roofs", "Ceilings"]:
        type_id = el.GetTypeId()
    else:
        try:
            type_id = el.SuperComponent.GetTypeId()
        except:
            type_id = el.GetTypeId()
    types_dict[type_id].add(el.Id)

# colour dictionary
n = len(types_dict)
revit_colours = get_colours(n)

# Collect non-curtain wall elements BEFORE the transaction
get_wall_elements = None
if selected_cat in ["Curtain Wall Panels", "Curtain Wall Mullions"]:
    get_wall_elements = DB.FilteredElementCollector(doc)\
                        .OfCategory(BIC.OST_Walls) \
                        .WhereElementIsNotElementType() \
                        .ToElements()

# ALL operations in ONE transaction
view = None
try:
    with revit.Transaction("Create and Colorize 3D View"):
        # First, check and delete existing view with same name
        for v in DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements():
            if v.Name == existing_view_name:
                # Check if this is the active view
                current_active = doc.ActiveView
                if current_active and current_active.Id == v.Id:
                    forms.alert('The view "{}" is currently active. Please close it and run the tool again.'.format(v.Name))
                    script.exit()
                # Delete the existing view
                doc.Delete(v.Id)
                break
        
        # Create new 3D view
        viewtype_id = get_3Dviewtype_id(doc=doc)
        remove_viewtemplate(viewtype_id, doc=doc)
        view = DB.View3D.CreateIsometric(doc, viewtype_id)
        view.Name = existing_view_name
        
        # Hide other categories
        for cat in hide_categories_except:
            if view.CanCategoryBeHidden(cat.Id):
                view.SetCategoryHidden(cat.Id, True)
        
        # Hide non-curtain walls
        if get_wall_elements:
            not_cw_elements = List[DB.ElementId]([w.Id for w in get_wall_elements if w.WallType.Kind != DB.WallKind.Curtain ])
            view.HideElements(not_cw_elements)
        
        # Apply color overrides
        for type_id, colour in zip(types_dict.keys(), revit_colours):
            type_instance = types_dict[type_id]
            override = set_colour_overrides_by_option(overrides_option, colour, doc)
            for inst in type_instance:
                view.SetElementOverrides(inst, override)
except Exception as e:
    logger.error("Error creating colorized 3D view: {}".format(str(e)))
    forms.alert("Failed to create colorized 3D view: {}".format(str(e)))
    script.exit()

# Check if view was created successfully
if not view:
    forms.alert('Could not create the 3D view.')
    script.exit()

logger.info("Successfully created and colorized 3D view: {} with {} types".format(view.Name, len(types_dict)))
