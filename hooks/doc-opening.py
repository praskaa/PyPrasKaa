# -*- coding: UTF-8 -*-
from datetime import datetime
from pyrevit.userconfig import user_config
import sys
import os

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from customOutput import def_openingLogPath

filePath = __eventargs__.PathName

# runing only if file is workshared because of backslash in path
try:
    lastBackslash = filePath.rindex("\\")
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
                    openingLogPath = user_config.PrasKaaToolsSettings.openingLogPath
                # if parameter doesnt exist in config file
                except:
                    openingLogPath = def_openingLogPath

                # Ensure directory exists
                if not os.path.exists(openingLogPath):
                    os.makedirs(openingLogPath, exist_ok=True)

                f = open(openingLogPath + "\\"+ file_name + "_Open.tmp", "w")
                # f = open("L:\\customToolslogs\\openingTimeLogs\\"+ file_name + "_Open.tmp", "w")
            except:
                fallback_path = "F:\\1_STUDI\\_PrasKaa Python Kit\\PrasKaaToolsLogs\\openingTimeLogs"
                if not os.path.exists(fallback_path):
                    os.makedirs(fallback_path, exist_ok=True)
                f = open(fallback_path + "\\"+ file_name + "_Open.tmp", "w")
                
            f.write(start_time_string_seconds + "\n")
            f.close()
        except:
             pass
except:
    pass