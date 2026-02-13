from pyrevit import revit, DB, forms

view = revit.active_view
doc = revit.doc

view_filter_ids = view.GetFilters()




if view_filter_ids:
    filter_ids_dict = {}
    # collect filters and get their names for the form
    for filter_id in view_filter_ids:
        filter_ids_dict[doc.GetElement(filter_id).Name] = filter_id
    # ask which filters to override
    selected_filter_names = forms.SelectFromList.show(sorted(filter_ids_dict,
                       ),
                                                 message="Select View Filters",
                                                 multiselect="True",
                                                 width=400)
    if selected_filter_names:
        with revit.Transaction ("Remove Filter Overrides"):
            for filter_name in selected_filter_names:
                filter=filter_ids_dict[filter_name]
                overrides = DB.OverrideGraphicSettings()
                view.SetFilterOverrides(filter, overrides)


