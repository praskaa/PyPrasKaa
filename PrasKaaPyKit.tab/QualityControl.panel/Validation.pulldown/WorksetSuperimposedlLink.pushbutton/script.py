# -*- coding: utf-8 -*-
"""
Workset Superimposed Management Script
Handles 3 scenarios:
1. File not workshared yet
2. File workshared but no "Superimposed" workset
3. File is a Central Model (linked directly)
"""
__title__ = 'Create Superimposed Workset'
__author__ = 'PrasKaa Team'
__doc__ = 'Opens a linked Revit file, enables worksharing if needed, creates "Superimposed" workset, and moves all elements from "Workset1" to it.'

import clr
from pyrevit import revit, DB, forms, script
import os

doc = revit.doc
app = doc.Application
uidoc = revit.uidoc

if doc.IsFamilyDocument:
    forms.alert('This script must be run in a project document.', title='Invalid Document Type')
    script.exit()

# ============================================================================
# STEP 1: Select linked model from project
# ============================================================================
link_types = DB.FilteredElementCollector(doc).OfClass(DB.RevitLinkType).ToElements()
if not link_types:
    forms.alert('No Revit links found in the current project.', title='No Links Found')
    script.exit()

link_dict = {}
for lt in link_types:
    try:
        ext_ref = lt.GetExternalFileReference()
        if ext_ref and ext_ref.GetAbsolutePath():
            model_path = ext_ref.GetAbsolutePath()
            path_str = DB.ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path)
            link_name = os.path.basename(path_str)
            link_dict[link_name] = {'type': lt, 'path': path_str, 'model_path': model_path}
    except:
        pass

if not link_dict:
    forms.alert('No valid Revit links found.', title='No Links Found')
    script.exit()

selected_link_name = forms.SelectFromList.show(
    sorted(link_dict.keys()),
    title='Select Linked Revit Model',
    button_name='Select Link'
)

if not selected_link_name:
    script.exit()

link_info = link_dict[selected_link_name]
selected_link_type = link_info['type']
file_path = link_info['path']
model_path = link_info['model_path']

if not os.path.exists(file_path):
    forms.alert('File not found: {}'.format(file_path), title='File Not Found')
    script.exit()

# Confirm with user
result = forms.alert(
    'File: {}\n\n'
    'This script handles:\n'
    '- Non-workshared files (will enable worksharing)\n'
    '- Workshared files without "Superimposed" workset\n'
    '- Central models (will save back to central)\n\n'
    'The link will be unloaded during this process.\n\n'
    'Continue?'.format(file_path),
    title='Confirm Operation',
    yes=True, no=True
)

if not result:
    script.exit()

# Check if document is modifiable
if doc.IsModifiable:
    forms.alert(
        'Cannot proceed - there is an active transaction.\n'
        'Please ensure no other operations are in progress.',
        title='Transaction Active'
    )
    script.exit()

# ============================================================================
# STEP 2: Unload the link
# ============================================================================
try:
    selected_link_type.Unload(None)
except Exception as e:
    forms.alert('Warning: Could not unload link: {}'.format(str(e)), title='Unload Warning')

# ============================================================================
# STEP 3: Open the file
# ============================================================================
linked_doc = None
was_workshared = False
is_central = False

try:
    open_options = DB.OpenOptions()
    # Don't detach - we want to work with the actual file
    open_options.DetachFromCentralOption = DB.DetachFromCentralOption.DoNotDetach
    
    try:
        workset_config = DB.WorksetConfiguration(DB.WorksetConfigurationOption.OpenAllWorksets)
        open_options.SetOpenWorksetsConfiguration(workset_config)
    except:
        pass
    
    linked_doc = app.OpenDocumentFile(model_path, open_options)
    
    # Check current state
    was_workshared = linked_doc.IsWorkshared
    
    # Check if this is a central model
    if was_workshared:
        central_path = linked_doc.GetWorksharingCentralModelPath()
        if central_path:
            central_path_str = DB.ModelPathUtils.ConvertModelPathToUserVisiblePath(central_path)
            # If central path equals file path, this IS the central model
            is_central = (central_path_str.lower() == file_path.lower())
        else:
            # No central path means this file IS the central (or standalone workshared)
            is_central = True
    
except Exception as e:
    try:
        selected_link_type.Reload()
    except:
        pass
    forms.alert('Failed to open the linked file: {}'.format(str(e)), title='File Open Error')
    script.exit()

# Log scenario for debugging
scenario = ""
if not was_workshared:
    scenario = "Scenario 1: File not workshared"
elif was_workshared and is_central:
    scenario = "Scenario 3: File is Central Model"
else:
    scenario = "Scenario 2: File is workshared (local copy)"

# ============================================================================
# STEP 4: Enable worksharing if needed (Scenario 1)
# ============================================================================
if not was_workshared:
    try:
        t = DB.Transaction(linked_doc, 'Enable Worksharing')
        t.Start()
        linked_doc.EnableWorksharing("Workset1", "Shared Levels and Grids")
        t.Commit()
    except Exception as e:
        try:
            if t.HasStarted():
                t.RollBack()
        except:
            pass
        forms.alert('Failed to enable worksharing: {}'.format(str(e)), title='Worksharing Error')
        linked_doc.Close(False)
        try:
            selected_link_type.Reload()
        except:
            pass
        script.exit()

# ============================================================================
# STEP 5: Find Workset1
# ============================================================================
workset1 = None
for ws in DB.FilteredWorksetCollector(linked_doc).OfKind(DB.WorksetKind.UserWorkset):
    if ws.Name == "Workset1":
        workset1 = ws
        break

if not workset1:
    forms.alert('Workset1 not found in the linked file.', title='Workset Not Found')
    linked_doc.Close(False)
    try:
        selected_link_type.Reload()
    except:
        pass
    script.exit()

# ============================================================================
# STEP 6: Find or create Superimposed workset
# ============================================================================
superimposed_workset = None
for ws in DB.FilteredWorksetCollector(linked_doc).OfKind(DB.WorksetKind.UserWorkset):
    if ws.Name == "Superimposed":
        superimposed_workset = ws
        break

if not superimposed_workset:
    try:
        t = DB.Transaction(linked_doc, 'Create Superimposed Workset')
        t.Start()
        superimposed_workset = DB.Workset.Create(linked_doc, "Superimposed")
        t.Commit()
    except Exception as e:
        try:
            if t.HasStarted():
                t.RollBack()
        except:
            pass
        forms.alert('Failed to create Superimposed workset: {}'.format(str(e)), title='Workset Creation Error')
        linked_doc.Close(False)
        try:
            selected_link_type.Reload()
        except:
            pass
        script.exit()

# ============================================================================
# STEP 7: Move elements from Workset1 to Superimposed
# ============================================================================
moved_count = 0
skipped_count = 0
t = None

try:
    collector = DB.FilteredElementCollector(linked_doc)
    workset_filter = DB.ElementWorksetFilter(workset1.Id)
    elements_in_workset1 = list(collector.WherePasses(workset_filter).ToElements())

    if not elements_in_workset1:
        forms.alert('No elements found in Workset1.', title='No Elements')
        linked_doc.Close(False)
        try:
            selected_link_type.Reload()
        except:
            pass
        script.exit()

    t = DB.Transaction(linked_doc, 'Move Elements to Superimposed')
    t.Start()
    for elem in elements_in_workset1:
        try:
            param = elem.get_Parameter(DB.BuiltInParameter.ELEM_PARTITION_PARAM)
            if param and not param.IsReadOnly:
                param.Set(superimposed_workset.Id.IntegerValue)
                moved_count += 1
            else:
                skipped_count += 1
        except:
            skipped_count += 1
    t.Commit()
    t = None

except Exception as e:
    if t and t.HasStarted():
        t.RollBack()
    forms.alert('Error during element movement: {}'.format(str(e)), title='Operation Failed')
    linked_doc.Close(False)
    try:
        selected_link_type.Reload()
    except:
        pass
    script.exit()

# ============================================================================
# STEP 8: Prepare for save (no regenerate needed)
# ============================================================================
# Note: Regenerate() requires transaction and is not critical for this operation
# The document will be regenerated automatically when saved

# ============================================================================
# STEP 9: Save the document based on scenario
# ============================================================================
save_success = False
save_message = ""

try:
    if not was_workshared:
        # SCENARIO 1: Was not workshared, now it is - save as new central
        save_options = DB.SaveAsOptions()
        save_options.OverwriteExistingFile = True
        
        ws_save_options = DB.WorksharingSaveAsOptions()
        ws_save_options.SaveAsCentral = True
        save_options.SetWorksharingOptions(ws_save_options)
        
        linked_doc.SaveAs(file_path, save_options)
        save_success = True
        save_message = "Saved as new Central Model"
        
    elif is_central:
        # SCENARIO 3: This IS the central model - use SynchronizeWithCentral
        # First relinquish ownership, then sync
        try:
            # Relinquish all
            relinquish_opts = DB.RelinquishOptions(True)
            trans_opts = DB.TransactWithCentralOptions()
            DB.WorksharingUtils.RelinquishOwnership(linked_doc, relinquish_opts, trans_opts)
        except:
            pass
        
        # Save as central (overwrite)
        save_options = DB.SaveAsOptions()
        save_options.OverwriteExistingFile = True
        
        ws_save_options = DB.WorksharingSaveAsOptions()
        ws_save_options.SaveAsCentral = True
        save_options.SetWorksharingOptions(ws_save_options)
        
        linked_doc.SaveAs(file_path, save_options)
        save_success = True
        save_message = "Saved to Central Model"
        
    else:
        # SCENARIO 2: This is a local copy - sync with central
        trans_opts = DB.TransactWithCentralOptions()
        sync_opts = DB.SynchronizeWithCentralOptions()
        relinquish_opts = DB.RelinquishOptions(True)
        sync_opts.SetRelinquishOptions(relinquish_opts)
        sync_opts.SaveLocalAfter = True
        sync_opts.Comment = "pyRevit: Moved elements to Superimposed workset"
        
        linked_doc.SynchronizeWithCentral(trans_opts, sync_opts)
        save_success = True
        save_message = "Synchronized with Central"

except Exception as e:
    save_message = "Save failed: {}".format(str(e))
    
    # Fallback: try simple SaveAs
    try:
        save_options = DB.SaveAsOptions()
        save_options.OverwriteExistingFile = True
        
        if linked_doc.IsWorkshared:
            ws_save_options = DB.WorksharingSaveAsOptions()
            ws_save_options.SaveAsCentral = True
            save_options.SetWorksharingOptions(ws_save_options)
        
        linked_doc.SaveAs(file_path, save_options)
        save_success = True
        save_message = "Saved with fallback method"
    except Exception as e2:
        save_message = "All save methods failed: {}".format(str(e2))

# ============================================================================
# STEP 10: Close the document
# ============================================================================
try:
    linked_doc.Close(False)
except Exception as e:
    pass

# ============================================================================
# STEP 11: Reload the link
# ============================================================================
reload_success = False
try:
    selected_link_type.Reload()
    reload_success = True
except Exception as e:
    pass

# ============================================================================
# STEP 12: Final report
# ============================================================================
separator = '-' * 40
final_message = (
    'Operation Summary\n'
    '{}\n\n'
    '{}\n\n'
    'Elements moved: {}\n'
    'Elements skipped: {}\n\n'
    'Save status: {}\n'
    'Link reload: {}'
).format(
    separator,
    scenario,
    moved_count,
    skipped_count,
    save_message if save_success else "FAILED - " + save_message,
    "Success" if reload_success else "FAILED - Please reload manually"
)

if save_success:
    forms.alert(final_message, title='Operation Complete')
else:
    forms.alert(final_message, title='Completed with Errors')