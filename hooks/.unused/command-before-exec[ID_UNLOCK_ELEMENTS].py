# -*- coding: UTF-8 -*-
from pyrevit import EXEC_PARAMS
from pyrevit import forms, script
from hooksScripts import hookTurnOff
from pyrevit.userconfig import user_config

def dialogBox():
    from hook_translate import hook_texts, lang

    title = "Unpin"
    # the language value is read from pyrevit config file
    lang = lang()

    # WARNING WINDOW
    res = forms.alert(hook_texts[lang][title]["text"],
                    options = hook_texts[lang][title]["buttons"],
                    title = title,
                    footer = "CustomTools Hooks")
    # BUTTONS
    # Unpin
    if res  == hook_texts[lang][title]["buttons"][0]:
      EXEC_PARAMS.event_args.Cancel = False
    # Cancel
    elif res  == hook_texts[lang][title]["buttons"][1]:
      EXEC_PARAMS.event_args.Cancel = True
    # More info
    elif res  == hook_texts[lang][title]["buttons"][2]:
      EXEC_PARAMS.event_args.Cancel = True
      wiki_url = user_config.CustomToolsSettings.wiki
      # if lang == "SK":
      if len(wiki_url) > 0:
        url = wiki_url + '/w/index.php?search=unpin&title=Špeciálne%3AHľadanie&go=Ísť+na'
      else:
        url = 'https://customtools.notion.site/Procedures-to-be-avoided-e6e4ce335d544040acee210943afa237'  
      script.open_url(url)
    else:
      EXEC_PARAMS.event_args.Cancel = True

hookTurnOff(dialogBox,10)