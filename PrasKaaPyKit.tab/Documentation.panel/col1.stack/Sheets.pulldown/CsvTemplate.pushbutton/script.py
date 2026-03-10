# -*- coding: utf-8 -*-
__title__ = "Open CSV Template"
__author__ = "PrasKaa"
__version__ = 'Version: 1.1'
__doc__ ="""Version: 1.1
Date    = 09.03.2026
_____________________________________________________________________
Description:
Opens the Excel template file for creating sheets from CSV. The template
provides a format for entering sheet numbers and names that can be imported
using the "Create Sheets from CSV" tool.
_____________________________________________________________________
How-to:
1. Click "CSV Template"
2. Excel template will open automatically
3. Save As CSV to a new location
4. Fill in sheet numbers and names
5. Use "Sheets from CSV" tool to import

Notes:
- First column: Sheet Number
- Second column: Sheet Name
- Do not modify the header row

_____________________________________________________
Last update:
- 09.03.2026 - 1.1 Fixed path calculation, removed unused imports, fixed logic
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""

# Standard library
import os

# pyRevit libraries
from pyrevit import forms, script


def main():
    """Open the CSV template file."""
    # Get script path and calculate extension root
    # Path structure: .../PrasKaaPyKitv2.extension/PrasKaaPyKit.tab/.../CsvTemplate.pushbutton/script.py
    script_path = script.get_script_path()
    extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_path)))))
    
    # Build template path using os.path.join for cross-platform compatibility
    template_path = os.path.join(extension_root, 'bin', 'Templates', 'PrasKaa Import Sheets.xlsx')
    
    # Check if template exists
    if not os.path.exists(template_path):
        forms.alert(
            "Template file not found at:\n{}".format(template_path),
            title="Error",
            warn_icon=True
        )
        return
    
    # Show instructions to user
    form_message = (
        "1. Excel template will open automatically.\n"
        "2. Save As CSV to another location.\n"
        "3. Populate with sheet numbers and names.\n"
        "4. Run the import sheets tool."
    )
    forms.alert(form_message, title="Instructions", warn_icon=False)
    
    # Open the template file
    os.startfile(template_path)


if __name__ == '__main__':
    main()
