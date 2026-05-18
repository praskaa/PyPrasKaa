# -*- coding: utf-8 -*-
__title__   = "Image: Save/Relink"
__author__  = "PrasKaa"
__doc__ = """Version = 1.6
Date    = 07.05.2026
_____________________________________________________________________
Description:

Save all linked/imported image files (JPG, PNG, BMP, TIF, PDF)
in the project to a specified location.
Optionally relinks them all after saving.

For truly embedded images (empty Path, e.g. "Save to Project as Image"),
the script will ask for a source folder to locate the originals.

Supports Revit 2024, 2025, 2026.
_____________________________________________________________________
"""

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> IMPORTS
import os, shutil, re
from Autodesk.Revit.DB import (FilteredElementCollector,
                                ImageType,
                                ImageTypeOptions,
                                ImageTypeSource,
                                Transaction,
                                Element)
from pyrevit.forms import alert
from pyrevit import script

import clr
clr.AddReference("System")
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import (DialogResult,
                                  MessageBox,
                                  MessageBoxButtons,
                                  FolderBrowserDialog)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> VARIABLES
doc    = __revit__.ActiveUIDocument.Document
uidoc  = __revit__.ActiveUIDocument
app    = __revit__.Application
output = script.get_output()

_REVIT_VERSION = int(app.VersionNumber)


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> HELPERS
def normalize_unc(path):
    """Fix single-backslash UNC paths returned by Revit."""
    if path.startswith('\\\\'):
        return path
    if path.startswith('\\'):
        return '\\' + path
    return path


def unc_to_local_drive(path):
    """
    Convert UNC share path to local drive letter path.
    Handles the pattern where a network share exposes a local drive:
      \\server\D\foo\bar  ->  D:\\foo\\bar
    Returns path unchanged if it doesn't match the pattern or
    already has a drive letter.
    """
    # Already a local drive path
    if len(path) >= 2 and path[1] == ':':
        return path
    # Match \\server\DriveLetter\rest  (single letter share name = drive letter)
    match = re.match(r'^\\\\[^\\]+\\([A-Za-z])\\(.+)$', path)
    if match:
        drive = match.group(1).upper()
        rest  = match.group(2)
        return "{}:\\{}".format(drive, rest)
    # UNC path with non-drive share name — return as-is, cannot convert
    return path


def get_image_type_name(img_type):
    """Safe name retrieval for ImageType in IronPython."""
    try:
        return Element.Name.GetValue(img_type)
    except Exception:
        return str(img_type.Id)


def name_to_filename(img_name):
    """
    Strip Revit's ' - <page>' suffix from multi-page PDF names.
    e.g. 'SONDIR.pdf - 4'  ->  'SONDIR.pdf'
    """
    match = re.match(r'^(.+\.pdf)\s*-\s*\d+$', img_name.strip(), re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return img_name.strip()


def get_page_number(img_name):
    """
    Extract 1-based page number from ' - <N>' suffix.
    ImageTypeOptions.PageNumber is 1-based.
    e.g. 'SONDIR.pdf - 4' -> 4.  No suffix -> 1.
    """
    match = re.match(r'^.+\.pdf\s*-\s*(\d+)$', img_name.strip(), re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 1


def get_image_path(img_type):
    """
    Get stored file path using ImageType.Path property (Revit 2024+).
    Resolves relative paths against project location.
    Returns normalized absolute path string, or None if truly embedded.
    """
    try:
        path = img_type.Path
        if path:
            if not os.path.isabs(path):
                project_dir = os.path.dirname(doc.PathName)
                path = os.path.normpath(os.path.join(project_dir, path))
            return normalize_unc(path)
    except Exception:
        pass
    return None


def get_id_value(element_id):
    """Cross-version ElementId integer extraction."""
    try:
        return element_id.Value           # Revit 2026+
    except AttributeError:
        return element_id.IntegerValue    # Revit 2024-2025


def make_image_options(local_path, page_num):
    """
    Build ImageTypeOptions for ReloadFrom.
    - Always uses Link (preserves external reference, keeps path in Manage Links)
    - local_path must be a local drive letter path (not UNC)
    - page_num is 1-based
    """
    opts = ImageTypeOptions(local_path, False, ImageTypeSource.Link)
    opts.PageNumber = page_num
    return opts


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CLASS
class SaveImages:
    def __init__(self):
        dir_backup = self.dialog_dir_backup()
        if not dir_backup:
            return

        # Convert UNC backup dir to local drive path for Revit compatibility
        img_dir = unc_to_local_drive(os.path.join(dir_backup, "Images"))

        all_img_types = (FilteredElementCollector(doc)
                         .OfClass(ImageType)
                         .WhereElementIsElementType()
                         .ToElements())

        if not all_img_types:
            output.print_html("<p>No image types found in project.</p>")
            return

        # Classify: has stored path vs truly embedded (empty Path)
        with_path = []   # list of (img_type, src_path)
        embedded  = []   # list of img_type — no path stored

        for img_type in all_img_types:
            path = get_image_path(img_type)
            if path:
                with_path.append((img_type, path))
            else:
                embedded.append(img_type)

        output.print_html("<p>Found: <b>{}</b> with stored path, "
                          "<b>{}</b> truly embedded.</p>".format(
                              len(with_path), len(embedded)))

        all_resolved = {}

        if with_path:
            all_resolved.update(self.save_images(img_dir, with_path))

        if embedded:
            all_resolved.update(self.locate_embedded(img_dir, embedded))

        if all_resolved:
            self.relink_images(all_resolved)
        else:
            output.print_html("<p>Nothing to relink.</p>")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIALOG
    def dialog_dir_backup(self):
        try:
            if os.path.exists(doc.PathName):
                result = MessageBox.Show(
                    "Save image files in the same folder as the current Revit file?\n\n"
                    "Current file: {}".format(doc.PathName),
                    __title__,
                    MessageBoxButtons.YesNo)
                if result == DialogResult.Yes:
                    return os.path.dirname(doc.PathName)

            dlg             = FolderBrowserDialog()
            dlg.Description = "Select destination folder for saving image files."
            dlg.ShowDialog()

            if not dlg.SelectedPath:
                alert("No folder selected. Script cancelled.",
                      title=__title__, exitscript=True)
            return dlg.SelectedPath
        except Exception:
            return None

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SAVE
    def save_images(self, dest_dir, img_list):
        """
        Copy source files to dest_dir (already converted to local drive path).
        Returns {eid_val: (dest_path, page_number)} dict.
        page_number is 1-based (ImageTypeOptions.PageNumber).
        """
        saved = {}
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        output.print_html("<h4>Saving images:</h4>")
        for img_type, src_path in img_list:
            img_name  = get_image_type_name(img_type)
            # Convert source UNC to local drive for file copy
            src_local = unc_to_local_drive(src_path)
            file_name = os.path.basename(src_local)
            dst_path  = os.path.join(dest_dir, file_name)
            page_num  = get_page_number(img_name)

            try:
                if not os.path.exists(src_local):
                    output.print_html(
                        "<p>- Source not found, skipping: {}</p>".format(src_local))
                    continue

                if os.path.normcase(src_local) != os.path.normcase(dst_path):
                    shutil.copyfile(src_local, dst_path)
                    output.print_html("<p>- Saved: {}</p>".format(dst_path))
                else:
                    output.print_html(
                        "<p>- Same location, skipping copy: {}</p>".format(dst_path))

                eid_val = get_id_value(img_type.Id)
                saved[eid_val] = (dst_path, page_num)

            except Exception as e:
                output.print_html(
                    "<p>- Error saving {}: {}</p>".format(img_name, str(e)))

        return saved

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> LOCATE EMBEDDED
    def locate_embedded(self, dest_dir, embedded_types):
        """
        For truly embedded images (empty Path):
        user picks source folder, match files by name.
        """
        output.print_html("<h4>Truly embedded images (no stored path):</h4>")
        for img_type in embedded_types:
            output.print_html(
                "<p>- {}</p>".format(get_image_type_name(img_type)))

        confirm = MessageBox.Show(
            "{} truly embedded image(s) found.\n\n"
            "These have no file path stored in Revit.\n"
            "Select the folder where the original files are located "
            "to copy and relink them.".format(len(embedded_types)),
            "Embedded Images",
            MessageBoxButtons.OKCancel)

        if confirm != DialogResult.OK:
            output.print_html("<p>Embedded image relinking skipped.</p>")
            return {}

        dlg             = FolderBrowserDialog()
        dlg.Description = "Select folder containing original image/PDF files."
        dlg.ShowDialog()

        if not dlg.SelectedPath:
            output.print_html("<p>No folder selected. Skipped.</p>")
            return {}

        src_folder = unc_to_local_drive(dlg.SelectedPath)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        resolved = {}
        output.print_html("<h4>Embedded images resolved:</h4>")

        for img_type in embedded_types:
            img_name  = get_image_type_name(img_type)
            file_name = name_to_filename(img_name)
            page_num  = get_page_number(img_name)
            src_path  = os.path.join(src_folder, file_name)
            dst_path  = os.path.join(dest_dir, file_name)

            if not os.path.exists(src_path):
                output.print_html(
                    "<p>- Not found in source folder: {}</p>".format(file_name))
                continue

            try:
                if not os.path.exists(dst_path):
                    shutil.copyfile(src_path, dst_path)
                output.print_html(
                    "<p>- Resolved: {} (page {})</p>".format(file_name, page_num))

                eid_val = get_id_value(img_type.Id)
                resolved[eid_val] = (dst_path, page_num)

            except Exception as e:
                output.print_html(
                    "<p>- Error: {}: {}</p>".format(file_name, str(e)))

        return resolved

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> RELINK
    def relink_images(self, resolved_dict):
        result = MessageBox.Show(
            "Relink {} image(s) to their saved locations?".format(len(resolved_dict)),
            "Relink Images?",
            MessageBoxButtons.YesNo)

        if result != DialogResult.Yes:
            output.print_html("<p>Images were not relinked.</p>")
            return

        all_img_types = (FilteredElementCollector(doc)
                         .OfClass(ImageType)
                         .WhereElementIsElementType()
                         .ToElements())

        output.print_html("<h4>Relink results:</h4>")

        t = Transaction(doc, "Relink Images")
        t.Start()
        try:
            for img_type in all_img_types:
                eid_val = get_id_value(img_type.Id)
                if eid_val not in resolved_dict:
                    continue

                dest_path, page_num = resolved_dict[eid_val]
                img_name = get_image_type_name(img_type)

                try:
                    # dest_path is already a local drive letter path
                    opts = make_image_options(dest_path, page_num)
                    img_type.ReloadFrom(opts)
                    output.print_html("<p>- Relinked: {} -> {}</p>".format(
                        img_name, dest_path))

                except Exception as e:
                    output.print_html(
                        "<p>- Failed: {}: {}</p>".format(img_name, str(e)))

            t.Commit()
            output.print_html("<p><b>Done.</b></p>")

        except Exception as e:
            t.RollBack()
            output.print_html(
                "<p><b>Transaction rolled back: {}</b></p>".format(str(e)))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> MAIN
if __name__ == '__main__':
    SaveImages()