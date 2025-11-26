# -*- coding: UTF-8 -*-

from pyrevit import EXEC_PARAMS
from pyrevit import forms, script, revit
from Autodesk.Revit.DB.Document import GetElement
from pyrevit.userconfig import user_config

# pylint: skip-file
import os.path as op
import sys
import os

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from hooksScripts import hookTurnOff

# showing of dialog box with warning
def dialogBox():
  from hook_translate import hook_texts, lang

  cadLinkId = __eventargs__.ImportedInstanceId
  doc = __eventargs__.Document
  cadLinkElement = doc.GetElement(cadLinkId)
  twoD = cadLinkElement.ViewSpecific
  docName = doc.PathName
  fileExtension = docName[-3:]

  title = "Link CAD file in 3D"
  # the language value is read from pyrevit config file
  current_lang = lang()

  # if ViewSpecific or not revit project (or not saved hence does not have .rvt extension)
  # because imports in revit families doesn't have Viewspecific Yes Value
  if twoD or fileExtension!="rvt":
    pass
  else:
    # WARNING WINDOW
    res = forms.alert(hook_texts[current_lang][title]["text"],
                    options = hook_texts[current_lang][title]["buttons"],
                    title = title,
                    footer = "PrasKaa PyKit Hooks")
    # BUTTONS
    # Continue, DWG in 3D
    if res  == hook_texts[current_lang][title]["buttons"][1]:
        pass
        # logging to server - cannot access active document
        from hooksScripts import hooksLogger
        hooksLogger("Link DWG in 3D" , doc)
    # Cancel
    elif res  == hook_texts[current_lang][title]["buttons"][0]:
        #run command UNDO
        from Autodesk.Revit.UI import UIApplication, RevitCommandId, PostableCommand

        Command_ID=RevitCommandId.LookupPostableCommandId(PostableCommand.Undo)
        uiapp = UIApplication(doc.Application)
        uiapp.PostCommand(Command_ID)
    # More info
    elif res  == hook_texts[current_lang][title]["buttons"][2]:
        wiki_url = user_config.PrasKaaToolsSettings.wiki
        # if current_lang == "SK":
        if len(wiki_url) > 0:
            url = wiki_url + '/wiki/Linknutie_DWG_s%C3%BAboru_do_Revitu#HLAVN.C3.89_Z.C3.81SADY'
        else:
            url = 'https://praskaapykit.notion.site/Procedures-to-be-avoided'
        #run command UNDO
        from Autodesk.Revit.UI import UIApplication, RevitCommandId, PostableCommand

        Command_ID=RevitCommandId.LookupPostableCommandId(PostableCommand.Undo)
        uiapp = UIApplication(doc.Application)
        uiapp.PostCommand(Command_ID)
        script.open_url(url)
    else:
        pass

# try to find config file for people who dont want to see the hook
hookTurnOff(dialogBox,4)