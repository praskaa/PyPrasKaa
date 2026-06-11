# -*- coding: UTF-8 -*-
from datetime import datetime
from pyrevit.userconfig import user_config
import sys
import os

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from customOutput import def_syncLogPath

doc = __eventargs__.Document
filePath = doc.PathName

# getting local file name for tmp file name
try:
    lastBackslash = filePath.rindex("\\")
# for syncing detached central file
except:
    lastBackslash = filePath.rindex("/")
# just the file name without the extension
file_name = filePath[lastBackslash:][:-4]

fileExtension = filePath[-3:]

if fileExtension == "rvt":
    # getting timestamp string now in seconds
    start_time_string_seconds = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        try:
            # if parameter exists in config file
            try:
                syncLogPath = user_config.PrasKaaToolsSettings.syncLogPath
            # if parameter doesnt exist in config file
            except:
                syncLogPath = def_syncLogPath
            f = open(syncLogPath + "\\" +  file_name + "_Save.tmp", "w")
        except:
            f = open("\\\\Srv2\\Z\\customToolslogs\\syncTimeLogs\\"+ file_name + "_Save.tmp", "w")
        f.write(start_time_string_seconds + "\n")
        f.close()
    except:
         pass