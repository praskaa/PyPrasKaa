# -*- coding: utf-8 -*-
__title__   = "RVT Link: Organize"
__author__  = "PrasKaa"
__doc__ = """Version = 1.1
Date    = 06.05.2026
_____________________________________________________________________
Description:

Organize Revit Links attached to the current project.

Workflow (you choose):
  1. Report  — list selected links with path, load status, and
               attachment type (Overlay / Attachment).
  2. Copy + Relink — copy selected linked RVT files to a chosen
               folder, then optionally relink to the new location.
  3. Relink from Folder — point to a folder that already contains
               the RVT files; script matches by filename and relinks.
_____________________________________________________________________
How to use:

  1. Run the script.
  2. Choose an action.
  3. A checklist of all Revit Links in the project will appear.
     Select which links to include — you can pick one, some, or all.
  4. Proceed with the chosen action on selected links only.
_____________________________________________________________________
"""

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> IMPORTS
import os, shutil, traceback
import clr

clr.AddReference("System")
clr.AddReference("System.Windows.Forms")

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    RevitLinkType,
    RevitLinkInstance,
    ModelPathUtils,
    Element,
    LinkedFileStatus,
    WorksetConfiguration,
)
from pyrevit import revit, script, forms

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> VARIABLES
doc   = revit.doc
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application

output = script.get_output()

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> HELPERS

def normalize_unc(path):
    """
    Revit sometimes returns UNC paths with a single leading backslash.
    Fix to double backslash without breaking already-correct paths.
    """
    if path.startswith('\\\\'):
        return path
    if path.startswith('\\'):
        return '\\' + path
    return path


def get_link_path(link_type):
    """
    Safely resolve the user-visible file path of a RevitLinkType.
    Returns empty string if the link is embedded or path is unresolvable.
    """
    try:
        efr  = link_type.GetExternalFileReference()
        path = ModelPathUtils.ConvertModelPathToUserVisiblePath(efr.GetPath())
        return normalize_unc(path)
    except Exception:
        return ""


def get_link_name(link_type):
    """IronPython-safe name retrieval for RevitLinkType."""
    return Element.Name.GetValue(link_type)


def get_load_status(link_type):
    """Return a human-readable load status string."""
    try:
        status = link_type.GetLinkedFileStatus()
        mapping = {
            LinkedFileStatus.Loaded:            "Loaded",
            LinkedFileStatus.NotLoaded:         "Not Loaded",
            LinkedFileStatus.LocallyUnloaded:   "Locally Unloaded",
            LinkedFileStatus.Unresolved:        "Unresolved / Missing",
            LinkedFileStatus.InClosedWorkset:   "In Closed Workset",
            LinkedFileStatus.Unknown:           "Unknown",
        }
        return mapping.get(status, str(status))
    except Exception:
        return "Unknown"


def collect_link_types():
    """Return all RevitLinkType elements in the project (element types only)."""
    return (
        FilteredElementCollector(doc)
        .OfClass(RevitLinkType)
        .WhereElementIsElementType()
        .ToElements()
    )


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SELECTION HELPER

class LinkItem(object):
    """
    Wrapper around RevitLinkType used as the item in forms.SelectFromList.
    The __str__ label is what the user sees in the checklist.
    """
    def __init__(self, link_type):
        self.link_type = link_type
        self.name      = get_link_name(link_type)
        self.path      = get_link_path(link_type)
        self.status    = get_load_status(link_type)

    def __str__(self):
        filename = os.path.basename(self.path) if self.path else "(no path)"
        return "[{}]  {}  |  {}".format(self.status, self.name, filename)


def select_links(prompt="Select Revit Links to include:"):
    """
    Show a multi-select checklist of all RevitLinkTypes in the project.
    Returns a list of RevitLinkType elements for the user's selection.
    Exits the script if the user cancels or selects nothing.
    """
    all_link_types = collect_link_types()

    if not all_link_types:
        forms.alert("No Revit Links found in this project.", exitscript=True)

    items = [LinkItem(lt) for lt in all_link_types]

    selected = forms.SelectFromList.show(
        items,
        title=__title__,
        prompt=prompt,
        multiselect=True,
        button_name="Confirm Selection",
    )

    if not selected:
        script.exit()

    # Return the underlying RevitLinkType objects
    return [item.link_type for item in selected]


def get_instance_attachment(link_type_id):
    """
    Attachment type (Overlay/Attachment) lives on RevitLinkInstance, not the type.
    Return the attachment type string of the first instance found for this type,
    or 'N/A' if no instance exists.
    """
    instances = (
        FilteredElementCollector(doc)
        .OfClass(RevitLinkInstance)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    for inst in instances:
        if inst.GetTypeId() == link_type_id:
            try:
                attach = inst.AttachmentType
                # AttachmentType enum: Overlay=0, Attachment=1
                return "Overlay" if str(attach) == "Overlay" else "Attachment"
            except Exception:
                return "N/A"
    return "N/A"


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ACTIONS

def action_report():
    """Print a report of the selected Revit Links."""
    link_types = select_links("Select links to include in the report:")

    if not link_types:
        output.print_html("<p><b>No links selected.</b></p>")
        return

    output.print_html("<h2>Revit Link Report</h2>")
    output.print_html(
        "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;width:100%;'>"
        "<tr style='background:#444;color:#fff;'>"
        "<th>#</th><th>Link Name</th><th>Status</th><th>Attachment</th><th>File Exists</th><th>Path</th>"
        "</tr>"
    )

    for i, lt in enumerate(link_types, 1):
        name       = get_link_name(lt)
        status     = get_load_status(lt)
        attach     = get_instance_attachment(lt.Id)
        path       = get_link_path(lt)
        file_ok    = "Yes" if (path and os.path.exists(path)) else ("No path" if not path else "Missing")
        row_color  = "" if i % 2 == 0 else "background:#f9f9f9;"
        status_color = "color:green;" if status == "Loaded" else "color:red;"

        output.print_html(
            "<tr style='{rc}'>"
            "<td>{i}</td>"
            "<td>{name}</td>"
            "<td style='{sc}'>{status}</td>"
            "<td>{attach}</td>"
            "<td>{fok}</td>"
            "<td style='font-size:11px;'>{path}</td>"
            "</tr>".format(
                rc=row_color, i=i, name=name,
                sc=status_color, status=status,
                attach=attach, fok=file_ok,
                path=path if path else "(embedded or unresolved)"
            )
        )

    output.print_html("</table>")
    output.print_html("<p>Total links: <b>{}</b></p>".format(len(link_types)))


def action_copy_relink():
    """
    Copy all linked RVT files to a chosen folder.
    Optionally relink all to the new location.
    """
    from System.Windows.Forms import (
        FolderBrowserDialog, MessageBox, MessageBoxButtons, DialogResult
    )

    # ---- Pick destination folder ----
    dlg             = FolderBrowserDialog()
    dlg.Description = "Select destination folder for RVT link files."
    result          = dlg.ShowDialog()

    if str(result) != "OK" or not dlg.SelectedPath:
        forms.alert("No folder selected. Operation cancelled.", exitscript=True)

    dest_folder = dlg.SelectedPath
    rvt_dir     = os.path.join(dest_folder, "RevitLinks")
    if not os.path.exists(rvt_dir):
        os.makedirs(rvt_dir)

    # ---- Select which links to copy ----
    link_types   = select_links("Select links to copy and relink:")
    copied_map   = {}  # filename -> new_full_path

    output.print_html("<h2>Copy Revit Links</h2>")

    for lt in link_types:
        name = get_link_name(lt)
        path = get_link_path(lt)

        if not path:
            output.print_html("<p>&#x26A0; <b>{}</b> — embedded or unresolvable, skipped.</p>".format(name))
            continue

        if not os.path.exists(path):
            output.print_html("<p>&#x274C; <b>{}</b> — source file not found:<br/><code>{}</code></p>".format(name, path))
            continue

        filename = os.path.basename(path)
        new_path = os.path.join(rvt_dir, filename)

        if os.path.normcase(path) == os.path.normcase(new_path):
            output.print_html("<p>&#x2139; <b>{}</b> — source and destination are the same, skipped.</p>".format(name))
            continue

        try:
            shutil.copyfile(path, new_path)
            output.print_html("<p>&#x2705; Copied: <code>{}</code></p>".format(new_path))
            copied_map[filename] = new_path
        except IOError as e:
            output.print_html("<p>&#x274C; Failed to copy <b>{}</b>: {}</p>".format(name, str(e)))

    if not copied_map:
        output.print_html("<p>No files were copied.</p>")
        return

    # ---- Ask whether to relink ----
    ask = MessageBox.Show(
        "Copied {} file(s) to:\n{}\n\nRelink all matched links to this new location?".format(
            len(copied_map), rvt_dir),
        "Relink?",
        MessageBoxButtons.YesNo
    )

    if ask == DialogResult.Yes:
        _relink_from_map(link_types, copied_map)


def action_relink_from_folder():
    """
    Pick a folder. Match linked RVT files by filename.
    Relink matched ones to the new location.
    """
    from System.Windows.Forms import FolderBrowserDialog

    dlg             = FolderBrowserDialog()
    dlg.Description = "Select folder containing the RVT link files."
    result          = dlg.ShowDialog()

    if str(result) != "OK" or not dlg.SelectedPath:
        forms.alert("No folder selected. Operation cancelled.", exitscript=True)

    folder     = dlg.SelectedPath
    link_types = select_links("Select links to relink from this folder:")

    # Build filename -> full path map from folder contents
    folder_map = {}
    for fname in os.listdir(folder):
        if fname.lower().endswith(".rvt"):
            folder_map[fname.lower()] = os.path.join(folder, fname)

    if not folder_map:
        forms.alert("No .rvt files found in the selected folder.", exitscript=True)

    # Match by filename
    matched_map = {}
    for lt in link_types:
        path = get_link_path(lt)
        if not path:
            continue
        fname = os.path.basename(path)
        if fname.lower() in folder_map:
            matched_map[fname] = folder_map[fname.lower()]

    output.print_html("<h2>Relink from Folder</h2>")
    output.print_html("<p>Folder: <code>{}</code></p>".format(folder))
    output.print_html("<p>Files in folder: {} | Matches found: {}</p>".format(
        len(folder_map), len(matched_map)))

    if not matched_map:
        output.print_html("<p>&#x274C; No matching link files found by filename. No changes made.</p>")
        return

    _relink_from_map(link_types, matched_map)


def _relink_from_map(link_types, file_map):
    """
    Core relink logic. file_map = {filename: new_full_path}.
    LoadFrom manages its own internal transaction — must NOT be wrapped
    inside an external Transaction or it will fail.
    """
    output.print_html("<h3>Relink Results</h3>")

    for lt in link_types:
        name = get_link_name(lt)
        path = get_link_path(lt)
        if not path:
            output.print_html("<p>&#x2796; <b>{}</b> — no path, skipped.</p>".format(name))
            continue

        filename = os.path.basename(path)
        if filename not in file_map:
            output.print_html("<p>&#x2796; <b>{}</b> — no match in map, skipped.</p>".format(name))
            continue

        new_path = file_map[filename]
        try:
            model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(new_path)
            lt.LoadFrom(model_path, WorksetConfiguration())
            output.print_html("<p>&#x2705; Relinked: <b>{}</b><br/><code>{}</code></p>".format(
                name, new_path))
        except Exception as e:
            err_str = str(e)
            if "loaded into multiple documents" in err_str:
                output.print_html(
                    "<p>&#x26A0; <b>{}</b> — file is open in another tab. "
                    "Close it first, then rerun.</p>".format(name))
            else:
                output.print_html("<p>&#x274C; Failed to relink <b>{}</b>: {}</p>".format(
                    name, err_str))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> MAIN

if __name__ == '__main__':
    # --- Action selection ---
    actions = [
        "1. Report — list all links with status and path",
        "2. Copy + Relink — copy RVT files to a folder, then relink",
        "3. Relink from Folder — match by filename, relink to new location",
    ]

    chosen = forms.ask_for_one_item(
        actions,
        prompt="Select an action:",
        title=__title__
    )

    if not chosen:
        script.exit()

    if chosen.startswith("1"):
        action_report()
    elif chosen.startswith("2"):
        action_copy_relink()
    elif chosen.startswith("3"):
        action_relink_from_folder()