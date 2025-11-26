# -*- coding: UTF-8 -*-
import os
import subprocess
from pyrevit.userconfig import user_config
import sys
import os

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from hooksScripts import versionLogger, releasedVersion, snapshot
from customOutput import ct_icon, mass_message_url
from customOutput import def_hookLogs, def_revitBuildLogs, def_revitBuilds, def_massMessagePath
from customOutput import def_syncLogPath, def_openingLogPath, def_dashboardsPath, def_language
from customOutput import def_doorUnflipped, def_doorFlipped, def_windowUnflipped, def_windowFlipped
from customOutput import def_wiki, def_standardWorksets
from customOutput import company_conf


# reading custom tools company config file if it does exist
# config_values are stored as dictionary
config_values = company_conf()

# Force update user config with converted Documents paths
try:
    print("Updating user config with new Documents paths...")
    if 'hookLogs' in config_values:
        user_config.PrasKaaToolsSettings.hookLogs = config_values['hookLogs']
        print("hookLogs updated: {}".format(config_values['hookLogs']))
    if 'syncLogPath' in config_values:
        user_config.PrasKaaToolsSettings.syncLogPath = config_values['syncLogPath']
        print("syncLogPath updated: {}".format(config_values['syncLogPath']))
    if 'openingLogPath' in config_values:
        user_config.PrasKaaToolsSettings.openingLogPath = config_values['openingLogPath']
        print("openingLogPath updated: {}".format(config_values['openingLogPath']))
    if 'familyloadLogPath' in config_values:
        user_config.PrasKaaToolsSettings.familyloadLogPath = config_values['familyloadLogPath']
        print("familyloadLogPath updated: {}".format(config_values['familyloadLogPath']))
    if 'revitBuildLogs' in config_values:
        user_config.PrasKaaToolsSettings.revitBuildLogs = config_values['revitBuildLogs']
    if 'dashboardsPath' in config_values:
        user_config.PrasKaaToolsSettings.dashboardsPath = config_values['dashboardsPath']
    user_config.save_changes()
    print("User config successfully updated with Documents paths!")
except Exception as e:
    print("Warning: Failed to update user config: {}".format(str(e)))

# creating sections in pyRevit_config.ini if it does not exist
try:
    user_config.add_section('PrasKaaToolsSettings')
except:
    pass
# if parameter does not exist create one in pyRevit_config.ini

# hookLogs
try:
    try:
        # if there is ct_config.ini present reset the values from company config
        user_config.PrasKaaToolsSettings.hookLogs = config_values['hookLogs']
    except: 
        user_config.PrasKaaToolsSettings.hookLogs
except:
    user_config.PrasKaaToolsSettings.hookLogs = def_hookLogs

# revitBuildLogs
try:
    try:
        user_config.PrasKaaToolsSettings.revitBuildLogs = config_values['revitBuildLogs']
    except:
        user_config.PrasKaaToolsSettings.revitBuildLogs
except:
    user_config.PrasKaaToolsSettings.revitBuildLogs = def_revitBuildLogs

# revitBuilds
try:
    try:
        user_config.PrasKaaToolsSettings.revitBuilds = config_values['revitBuilds']
    except:
        user_config.PrasKaaToolsSettings.revitBuilds
except:
    user_config.PrasKaaToolsSettings.revitBuilds = def_revitBuilds

# massMessagePath
try:
    try:
        user_config.PrasKaaToolsSettings.massMessagePath = config_values['massMessagePath']
    except:
        user_config.PrasKaaToolsSettings.massMessagePath
except:
    user_config.PrasKaaToolsSettings.massMessagePath = def_massMessagePath

# syncLogPath
try:
    try:
        user_config.PrasKaaToolsSettings.syncLogPath = config_values['syncLogPath']
    except:
        user_config.PrasKaaToolsSettings.syncLogPath
except:
    user_config.PrasKaaToolsSettings.syncLogPath = def_syncLogPath

# openingLogPath
try:
    try:
        user_config.PrasKaaToolsSettings.openingLogPath = config_values['openingLogPath']
    except:
        user_config.PrasKaaToolsSettings.openingLogPath
except:
    user_config.PrasKaaToolsSettings.openingLogPath = def_openingLogPath

# dashboardsPath
try:
    try:
        user_config.PrasKaaToolsSettings.dashboardsPath = config_values['dashboardsPath']
    except:
        user_config.PrasKaaToolsSettings.dashboardsPath
except:
    user_config.PrasKaaToolsSettings.dashboardsPath = def_dashboardsPath

# language
try:
    try:
        # language is a number stored as string - it must be converted to integer
        user_config.PrasKaaToolsSettings.language = int(config_values['language'])
    except:
        user_config.PrasKaaToolsSettings.language
except:
    # user_config.PrasKaaToolsSettings.language = str(def_language)
    user_config.PrasKaaToolsSettings.language = def_language

# doorUnflipped
try:
    try:
        user_config.PrasKaaToolsSettings.doorUnflipped = config_values['doorUnflipped']
    except:
        user_config.PrasKaaToolsSettings.doorUnflipped
except:
    user_config.PrasKaaToolsSettings.doorUnflipped = def_doorUnflipped

# doorFlipped
try:
    try:
        user_config.PrasKaaToolsSettings.doorFlipped = config_values['doorFlipped']
    except:
        user_config.PrasKaaToolsSettings.doorFlipped
except:
    user_config.PrasKaaToolsSettings.doorFlipped = def_doorFlipped

# windowUnflipped
try:
    try:
        user_config.PrasKaaToolsSettings.windowUnflipped = config_values['windowUnflipped']
    except:
        user_config.PrasKaaToolsSettings.windowUnflipped
except:
    user_config.PrasKaaToolsSettings.windowUnflipped = def_windowUnflipped

# windowFlipped
try:
    try:
        user_config.PrasKaaToolsSettings.windowFlipped = config_values['windowFlipped']
    except:
        user_config.PrasKaaToolsSettings.windowFlipped
except:
    user_config.PrasKaaToolsSettings.windowFlipped = def_windowFlipped

# pyrevit telemetry path
try:
    # try to read telemetry path from the customtools config file
    # cmd_command = 'cmd /c PowerShell pyrevit configs telemetry file "' + company_conf()['pyrevitTelemetry'] + '"'
    user_config.telemetry.telemetry_file_dir = config_values['pyrevitTelemetry']
except:
    # if there is no telemetry path present in the config file
    # cmd_command = 'cmd /c PowerShell pyrevit configs telemetry file "F:\\1_STUDI\\_PrasKaa Python Kit\\PrasKaaToolsLogs\\toolsLogs"'
    user_config.telemetry.telemetry_file_dir = "F:\\1_STUDI\\_PrasKaa Python Kit\\PrasKaaToolsLogs\\toolsLogs"
# os.system(cmd_command)

# wiki
try:
    try:
        user_config.PrasKaaToolsSettings.wiki = config_values['wiki']
    except:
        user_config.PrasKaaToolsSettings.wiki
except:
    user_config.PrasKaaToolsSettings.windowFlipped = def_wiki

# standardWorksets
try:
    try:
        user_config.PrasKaaToolsSettings.standardWorksets = config_values['standardWorksets']
    except:
        user_config.PrasKaaToolsSettings.standardWorksets
except:
    user_config.PrasKaaToolsSettings.standardWorksets = def_standardWorksets

user_config.save_changes()

# write log with revit build, username, CTversion and timestamp
# check revit build and show warning window if it's wrong
versionLogger(releasedVersion,snapshot)

# PrasKaa PyKit update at revit startup (disabled for now)
try:
    # Extension path for PrasKaa PyKit
    # Use dynamic path instead of hardcoded D: drive
    import os
    extension_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Update scripts can be added here if needed
    # updaterPath = os.path.join(extension_path, 'hooks', 'InitUpdate.cmd')
    # p = subprocess.Popen([updaterPath])
    pass
except:
    pass

"""TEASER."""
#prints heading and links offline version of mass message
from pyrevit import script
output = script.get_output()
output.set_height(700)
output.set_title("Mass Message")
# changing icon
ct_icon(output)

# server version of massmessage
output.open_page(mass_message_url(output))