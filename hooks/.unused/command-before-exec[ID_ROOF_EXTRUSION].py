# -*- coding: UTF-8 -*-

from pyrevit import EXEC_PARAMS
from pyrevit import forms, script
import sys
import os

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from hooksScripts import hookTurnOff
from pyrevit.userconfig import user_config

doc = __revit__.ActiveUIDocument.Document

# showing of dialog box with warning
def dialogBox():
   from hook_translate import hook_texts, lang

   title = "Roof by Extrusion"
   # the language value is read from pyrevit config file
   lang = lang()

   # WARNING WINDOW
   res = forms.alert(hook_texts[lang][title]["text"],
                    options = hook_texts[lang][title]["buttons"],
                    title = title,
                    footer = "PrasKaa PyKit Hooks")
   # BUTTONS
   # Create
   if res  == hook_texts[lang][title]["buttons"][0]:
      EXEC_PARAMS.event_args.Cancel = False
      # logging to server
      from hooksScripts import hooksLogger
      hooksLogger(title, doc)
   # Cancel
   elif res  == hook_texts[lang][title]["buttons"][1]:
      EXEC_PARAMS.event_args.Cancel = True
   # More info
   elif res  == hook_texts[lang][title]["buttons"][2]:
      EXEC_PARAMS.event_args.Cancel = True
      wiki_url = user_config.PrasKaaToolsSettings.wiki
      # if lang == "SK":
      if len(wiki_url) > 0:
         url = wiki_url + '/wiki/Postupy,_ktor%C3%BDm_je_potrebn%C3%A9_sa_vyhn%C3%BA%C5%A5_-_Revit#Roofs'
      else:
         url = 'https://customtools.notion.site/Procedures-to-be-avoided-e6e4ce335d544040acee210943afa237'
      script.open_url(url)
   else:
      EXEC_PARAMS.event_args.Cancel = True

# try to find config file for people who dont want to see the hook
hookTurnOff(dialogBox,8)