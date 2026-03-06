from pyrevit import script
from Autodesk.Revit.UI import ColorSelectionDialog

my_config = script.get_config()

def pick_color():
    # color pick GUI
    colorPickerDialog = ColorSelectionDialog()
    colorPickerDialog.Show()
    color = colorPickerDialog.SelectedColor

    # generate color code  
    color_code = str(color.Red)+","+str(color.Green)+","+str(color.Blue)
    # print(color_code)

    # setting parameter 
    setattr(my_config, "color_code", color_code)
    script.save_config()

def read_color():
    new_color_code = getattr(my_config, "color_code")
    print(new_color_code)

if __name__ == "__main__":
    pick_color()
    # read_color()