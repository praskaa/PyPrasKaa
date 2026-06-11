# from graphicOverrides import setProjLines

__title__ = "."
__doc__ = 'Quicker override Projection Line Color of Elements.'
__author__ = "David Vadkerti"

# setProjLines(255,0,255)



from pyrevit import revit, DB, forms
try:
    selection = revit.get_selection()
    if len(selection)>0:
        with revit.Transaction('Line Color'):
        	# erase overrides
            src_style = DB.OverrideGraphicSettings().Dispose()
            # get clear graphics without overrides
            src_style = DB.OverrideGraphicSettings()
            for element in selection:
                revit.active_view.SetElementOverrides(element.Id, src_style)
    else:
        forms.alert('You must select at least one element.', exitscript=True)
except:
    pass