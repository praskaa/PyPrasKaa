from pyrevit import script
from graphicOverrides import setProjLines

__title__ = "Line & Pattern Color"
__doc__ = 'Quicker override Projection Line, Cut Line & Pattern Color of Elements.'
__author__ = "David Vadkerti"

my_config = script.get_config()

try:
    # my_config.color_code
    new_color_code = getattr(my_config, "color_code")
except:
    setattr(my_config, "color_code", "100,177,70")
    new_color_code = getattr(my_config, "color_code")
    script.save_config()

# spliting color code to list of 3 strings
new_color_code_list = new_color_code.split(",")
# list of integers
new_color_list = [int(x) for x in new_color_code_list]


setProjLines(new_color_list[0], new_color_list[1], new_color_list[2], True)