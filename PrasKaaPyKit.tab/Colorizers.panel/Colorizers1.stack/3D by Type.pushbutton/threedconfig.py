from pyrevit import script, revit
from colorize import *
from database import *

overrides_config = script.get_config() #get colorizebyvalue config - to store override options

def get_overrides_config():
    return get_config(overrides_config, OVERRIDES_CONFIG_OPTION_NAME, default_override_options)


if __name__ == "__main__":
    config_overrides(overrides_config, OVERRIDES_CONFIG_OPTION_NAME)
    config_category_overrides(revit.doc)
