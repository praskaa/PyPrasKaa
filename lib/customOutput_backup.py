# -*- coding: utf-8 -*- 
from pyrevit import coreutils
from pyrevit import output

# colors for chart.js graphs
colors = 10*["#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb",
            "#4d4d4d","#000000","#fff0f2","#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#e97800","#a6c844",
            "#4d4d4d","#fff0d9","#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#4d4d4d","#e97800","#a6c844",
            "#fff0e6","#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#4d4d4d","#fff0e6","#e97800","#a6c844",
            "#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#4d4d4d","#9988bb","#4d4d4d","#e97800","#a6c844",
            "#4d4d4d","#fff0d9","#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#4d4d4d","#e97800","#a6c844",
            "#4d4d4d","#fff0d9","#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#4d4d4d","#e97800","#a6c844",
            "#4d4d4d","#fff0d9","#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#4d4d4d","#e97800","#a6c844",
            "#4d4d4d","#fff0d9","#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#4d4d4d","#e97800","#a6c844",
            "#4d4d4d","#fff0d9","#ffc299","#ff751a","#cc5200","#ff6666","#ffd480","#b33c00","#ff884d","#d9d9d9","#9988bb","#4d4d4d","#e97800","#a6c844",]

# list of Warnings rated as critical
criticalWarnings = ['Elements have duplicate "Type Mark" values',
    'There are identical instances in the same place',
    'Room Tag is outside of its Room',
    'Multiple Rooms are in the same enclosed region',
    'Multiple Areas are in the same enclosed region',
    'One element is completely inside another',
    'Room is not in a properly enclosed region',
    'Room separation line is slightly off axis and may cause inaccuracies',
    'Area is not in a properly enclosed region',
    "Rectangular opening doesn't cut its host",
    'Elements have duplicate "Number" values',]

# List Type Mark warnings as critical

typemarkWarning = ['Elements have duplicate "Type Mark" values']

# default paths for settings - updated for PrasKaa PyKit
# this can be overriden by user in customToolsSettings.py
# or by company config file
def_hookLogs = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\hooksLogs"
def_revitBuildLogs = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\versions.log"
# Updated revit builds for PrasKaa PyKit
def_revitBuilds = "20240814_1400(x64), 20220520_1515(x64), 20201116_1100(x64), 20240408_1515(x64), This is not a software bug. Install the update please :) Your BIM manager"
def_massMessagePath = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaPyKit.extension\mass_message\mass_message.html"
def_syncLogPath = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\syncTimeLogs"
def_openingLogPath = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\openingTimeLogs"
def_dashboardsPath = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\powerBI"
def_language = 0
def_doorUnflipped = "L"
def_doorFlipped = "R"
def_windowUnflipped = "0"
def_windowFlipped = "1"
def_wiki = "https://www.yourinternalwiki.com"
def_standardWorksets = "Shared Levels & Grids, Workset1, Hidden, 3DtextRoomData"
def_familyloadLogPath = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\FamilyLoad"

# read the company config file if it does exist
def company_conf():
    import os
    config_values = {}
    # Updated path for PrasKaa PyKit extension
    # Use dynamic path instead of hardcoded D: drive
    extension_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(extension_path, 'config', 'ct_config.ini')
    
    try:
        with open(config_path, "r") as company_config_file:
            configSetting = company_config_file.readlines()
            for line in configSetting:
                # separating values from lines
                if " = " in line:
                    keys = line.split(" = ", 1)
                    # remove new lines - enter
                    keys[1] = keys[1].strip()
                    
                    # Update paths to use PrasKaaToolsLogs
                    value = keys[1]
                    if 'customToolslogs' in value:
                        value = value.replace('L:\\customToolslogs', r'D:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs')
                    elif 'customToolsLogs' in value:
                        value = value.replace('L:\\customToolsLogs', r'D:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs')
                    elif value.startswith('L:\\_i\\CTmassMessage'):
                        value = def_massMessagePath
                    elif value.startswith('L:\\powerBI'):
                        value = def_dashboardsPath
                    
                    # add values to dictionary
                    config_values.update({keys[0].strip(): value})
    except IOError:
        # If the file doesn't exist, return empty config
        pass
    return config_values

# formating time in seconts to HHMMSS format
def hmsTimer(timerSeconds):
    # for treating formating of pyrevit timer function
    from math import floor
    seconds = round(timerSeconds,2)
    if seconds<60:
        hms = str(seconds)+" seconds"
    elif seconds<3600:
        minutes = int(floor(seconds//60))
        seconds = seconds%60
        hms = str(minutes)+" min "+str(seconds)+" seconds"
    else:
        hours = seconds//3600
        minutes = int((seconds%3600)//60)
        seconds = seconds%60
        if minutes ==0:
            hms = str(hours)+" h "+str(seconds)+" seconds"
        else:
            hms = str(hours)+" h "+str(minutes)+" min "+str(seconds)+" seconds"
    claim = "Transaction took "+hms
    return claim

# gets name of the current document
def file_name_getter(doc):
    file_path = doc.PathName
    # trying all cases, for worshared, not worshared and detached files
    try:
        file_name = file_path[file_path.rindex("/"):]
    except:
        try:
            file_name = file_path[file_path.rindex("\\")+1:]
        except:
            file_name = file_path
    return(file_name)

# setting icon for output window
def ct_icon(output):
    import os
    # Updated path for PrasKaa PyKit extension
    # Use dynamic path instead of hardcoded D: drive
    extension_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    iconPath = os.path.join(extension_path, 'hooks', 'icon-s.png')
    try:
        output.set_icon(iconPath)
    except:
        # Fallback if icon doesn't exist
        pass

# creating mass message url
def mass_message_url(output):
    from pyrevit.userconfig import user_config
    from os import path
    import os
    
    # server version of massmessage
    # if parameter exists in config file
    try:
        url = user_config.PrasKaaToolsSettings.massMessagePath
    # if parameter doesnt exist in config file
    except:
        url = def_massMessagePath

    if path.exists(url):
        return url
    # offline hardcoded version of massmessage - updated for PrasKaa PyKit
    else:
        # offline content of mass message
        # Use dynamic path instead of hardcoded D: drive
        extension_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(extension_path, 'mass_message', 'mass_message.html')

# highlights text using html string with css
def text_highligter(a):
    content = str(a)
    html_code = "<p class='elementlink'>"+content+"</p>"
    return coreutils.prepare_html_str(html_code)

# makes mailto link in output window
def mailto(a):
    content = str(a)
    html_code = '<a href=mailto:"'+ content +'" target="_blank" style="text-decoration: none; color: black; font-weight: bold;">'+ content +'</a>'
    # html_code = '<a href=mailto:"'+ content +'" target="_blank">'+ content +'</a>'
    return coreutils.prepare_html_str(html_code)

# makes html link tag
def linkMaker(a,title):
    content = str(a)
    html_code = '<a href="'+content+'">'+ title +'</a>'
    return coreutils.prepare_html_str(html_code)

# views image in output window
def imageViewer(html_code):
    # sample_code = "<img src='https://i.ytimg.com/vi/SfLV8hD7zX4/maxresdefault.jpg' width=50%>"
    print(coreutils.prepare_html_str(html_code))

# heading in html
def heading(text, size):
    # sample_code = "<h2>Heading</h2>"
    size_str = str(size)
    html_code = "<h" + size_str +">" + text + "</h" + size_str +">"
    print(coreutils.prepare_html_str(html_code))