# -*- coding: UTF-8 -*-
"""
hook_translate.py - PrasKaa PyKit Hook Translation Module
Adapted from CustomTools for PrasKaa PyKit extension
"""

from pyrevit.userconfig import user_config

def lang():
    """
    Get the current language setting
    Returns:
        int: Language code (0 for English, 1 for other languages)
    """
    try:
        return user_config.PrasKaaToolsSettings.language
    except:
        return 0  # Default to English

# Translation dictionary for hook messages
hook_texts = {
    0: {  # English
        "Load Family": {
            "text": "You are trying to load a family larger than 1 MB.\n\nLarge families can slow down your project significantly.\n\nDo you want to continue?",
            "buttons": ["Cancel", "Load", "More Info"]
        },
        "Link CAD file in 3D": {
            "text": "You are trying to link a CAD file in 3D view.\n\nThis can cause performance issues and is not recommended.\n\nDo you want to continue?",
            "buttons": ["Cancel", "Continue", "More Info"]
        },
        "Link CAD file": {
            "text": "You are trying to link a CAD file.\n\nDo you want to continue?",
            "buttons": ["Cancel", "Continue", "More Info"]
        },
        "Link CAD": {
            "text": "You are trying to link a CAD file.\n\nDo you want to continue?",
            "buttons": ["Continue", "Cancel", "More Info"]
        },
        "Project Parameters": {
            "text": "You are about to modify Project Parameters.\n\nThis can affect the entire project and all users.\n\nWhat would you like to do?",
            "buttons": ["View Shared Parameters", "Edit Parameters", "Cancel"]
        },
        "Save List Of Opened Views": {
            "text": "You have multiple views open.\n\nWould you like to save a list of currently opened views before closing?",
            "buttons": ["Save List", "Skip", "More Info"]
        },
        "In Place Family": {
            "text": "You are about to create an In-Place Family.\n\nIn-Place Families can cause performance issues and are generally not recommended for production work.\n\nDo you want to continue?",
            "buttons": ["Create", "Cancel", "More Info"]
        }
    },
    1: {  # Indonesian/Other language
        "Load Family": {
            "text": "Anda mencoba memuat family yang berukuran lebih dari 1 MB.\n\nFamily besar dapat memperlambat proyek Anda secara signifikan.\n\nApakah Anda ingin melanjutkan?",
            "buttons": ["Batal", "Muat", "Info Lebih Lanjut"]
        },
        "Link CAD file in 3D": {
            "text": "Anda mencoba menghubungkan file CAD dalam tampilan 3D.\n\nHal ini dapat menyebabkan masalah performa dan tidak disarankan.\n\nApakah Anda ingin melanjutkan?",
            "buttons": ["Batal", "Lanjutkan", "Info Lebih Lanjut"]
        },
        "Link CAD file": {
            "text": "Anda mencoba menghubungkan file CAD.\n\nApakah Anda ingin melanjutkan?",
            "buttons": ["Lanjutkan", "Batal", "Info Lebih Lanjut"]
        },
        "Link CAD": {
            "text": "Anda mencoba menghubungkan file CAD.\n\nApakah Anda ingin melanjutkan?",
            "buttons": ["Batal", "Lanjutkan", "Info Lebih Lanjut"]
        },
        "Project Parameters": {
            "text": "Anda akan memodifikasi Parameter Proyek.\n\nHal ini dapat mempengaruhi seluruh proyek dan semua pengguna.\n\nApa yang ingin Anda lakukan?",
            "buttons": ["Lihat Shared Parameters", "Edit Parameters", "Batal"]
        },
        "Save List Of Opened Views": {
            "text": "Anda memiliki beberapa view yang terbuka.\n\nApakah Anda ingin menyimpan daftar view yang sedang terbuka sebelum menutup?",
            "buttons": ["Simpan Daftar", "Lewati", "Info Lebih Lanjut"]
        },
        "In Place Family": {
            "text": "Anda akan membuat In-Place Family.\n\nIn-Place Family dapat menyebabkan masalah performa dan umumnya tidak disarankan untuk pekerjaan produksi.\n\nApakah Anda ingin melanjutkan?",
            "buttons": ["Buat", "Batal", "Info Lebih Lanjut"]
        }
    }
}

def get_hook_text(hook_name, language=None):
    """
    Get translated text for a specific hook
    Args:
        hook_name (str): Name of the hook
        language (int): Language code (optional, will use config if not provided)
    Returns:
        dict: Dictionary containing text and buttons for the hook
    """
    if language is None:
        language = lang()
    
    try:
        return hook_texts[language][hook_name]
    except KeyError:
        # Fallback to English if translation not found
        try:
            return hook_texts[0][hook_name]
        except KeyError:
            # Ultimate fallback
            return {
                "text": "Hook message not found",
                "buttons": ["OK"]
            }

def add_hook_translation(hook_name, language, text, buttons):
    """
    Add or update a hook translation
    Args:
        hook_name (str): Name of the hook
        language (int): Language code
        text (str): The translated text
        buttons (list): List of button texts
    """
    if language not in hook_texts:
        hook_texts[language] = {}
    
    hook_texts[language][hook_name] = {
        "text": text,
        "buttons": buttons
    }