# -*- coding: utf-8 -*-
__title__ = "Quick Line Color"
__author__ = "PrasKaa"
__version__ = 'Version: 1.1'
__doc__ = """
10.03.2026
_____________________________________________________________________
Description:
Quickly overrides the Projection Line, Cut Line, and Cut Pattern colors of selected elements in the active view.

Does NOT apply surface patterns - only applies line colors and cut pattern colors to maintain existing surface fill appearance.
_____________________________________________________________________
How-to:
1. Select one or more elements in the active view
2. Click the button to apply the stored color
3. Color is stored in tool config (default: RGB 100,177,70 - green)
4. To change color, edit the color_code setting in config

_____________________________________________________
Last update:
- [10.03.2026] - 1.1 Added color picker function to script
- [10.03.2026] - 1.0 RELEASE
_____________________________________________________________________
Author:  PrasKaa"""

from pyrevit import script
from Autodesk.Revit.UI import ColorSelectionDialog
from graphicOverrides import setProjLines


# Config functions
def pick_color(my_config):
    """Open Revit color picker dialog and save selected color."""
    colorPickerDialog = ColorSelectionDialog()
    colorPickerDialog.Show()
    color = colorPickerDialog.SelectedColor

    # Generate color code
    color_code = str(color.Red) + "," + str(color.Green) + "," + str(color.Blue)

    # Setting parameter
    setattr(my_config, "color_code", color_code)
    script.save_config()


def read_color(my_config):
    """Read and print current color code from config."""
    new_color_code = getattr(my_config, "color_code")
    print(new_color_code)


# Main execution
my_config = script.get_config()

try:
    new_color_code = getattr(my_config, "color_code")
except:
    setattr(my_config, "color_code", "100,177,70")
    new_color_code = getattr(my_config, "color_code")
    script.save_config()

# Splitting color code to list of 3 strings
new_color_code_list = new_color_code.split(",")
# List of integers
new_color_list = [int(x) for x in new_color_code_list]

setProjLines(new_color_list[0], new_color_list[1], new_color_list[2], False)
