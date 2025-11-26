# -*- coding: UTF-8 -*-
from datetime import datetime
from os import path, remove
from pyrevit import revit
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

# getting central file name for log name
central_path = revit.query.get_central_path(doc)
try:
    try:
        # for rvt server
        lastBackslash_C = central_path.rindex("/")
    except:
        # for other locations
        lastBackslash_C = central_path.rindex("\\")
    # just the file name without the extension
    file_name = central_path[lastBackslash_C:][:-4]
# for files without worksharing
except:
    lastBackslash_C = filePath.rindex("\\")
    # just the file name without the extension
    file_name = filePath[lastBackslash_C:][:-4]


# getting local file name for tmp file name
try:
    lastBackslash_L = filePath.rindex("\\")
# for syncing detached central file
except:
    lastBackslash_L = filePath.rindex("/")
# just the file name without the extension
local_file_name = filePath[lastBackslash_L:][:-4]


fileExtension = filePath[-3:]

if fileExtension == "rvt":
    # tabulator between data to separte columns of the schedule
    separator = "\t" 
    try:
        # reading timestamp from tmp file
        try:
            # if parameter exists in config file
            try:
                syncLogPath = user_config.PrasKaaToolsSettings.syncLogPath
            # if parameter doesnt exist in config file
            except:
                syncLogPath = def_syncLogPath

            # Ensure directory exists
            if not os.path.exists(syncLogPath):
                os.makedirs(syncLogPath, exist_ok=True)

            tmp_file_path = syncLogPath + "\\"+ local_file_name + "_Save.tmp"
            # tmp_file_path = "L:\\customToolslogs\\syncTimeLogs\\"+ local_file_name + "_Save.tmp"
        except:
            tmp_file_path = "\\\\Srv2\\Z\\customToolslogs\\syncTimeLogs\\"+ local_file_name + "_Save.tmp"
        tmp_file = open(tmp_file_path, "r")
        start_time_string = tmp_file.read()
        # converting string to datetime
        start_time = datetime.strptime(start_time_string,"%Y-%m-%d %H:%M:%S")
        tmp_file.close()

        if path.exists(tmp_file_path):
            remove(tmp_file_path)

        # end time in seconds
        # round datetime to seconds (converting to string and then back to datetime object with correct)
        end_time_string_seconds = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time_string_seconds,"%Y-%m-%d %H:%M:%S")


        timeDelta = end_time - start_time
        # print timeDelta

        user_name = doc.Application.Username

        # writing time to log file
        # if syncLogPath exists
        try:
            log_file_path = syncLogPath + "\\"+ file_name + "_Save.log"
            # Ensure directory exists before writing
            log_dir = os.path.dirname(log_file_path)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            log_file = open(log_file_path, "a")
            # log_file = open("L:\\customToolslogs\\syncTimeLogs\\"+ file_name + "_Save.log", "a")
        # unc file path
        except:
            log_file_path = "\\\\Srv2\\Z\\customToolslogs\\syncTimeLogs\\"+ file_name + "_Save.log"
            log_dir = os.path.dirname(log_file_path)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            log_file = open(log_file_path, "a")
        log_file.write(end_time_string_seconds + separator + str(timeDelta) + separator + user_name + "\n")
        log_file.close()
    except:
         pass