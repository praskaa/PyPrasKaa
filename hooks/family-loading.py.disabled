# -*- coding: UTF-8 -*-
"""
Family Loading Hook for pyRevit
Logs all family loading events to track which families are loaded into projects.

Author: PrasKaa Team
Version: 2.1.0
"""

from pyrevit import revit
from pyrevit.userconfig import user_config
import sys
import os
import os.path as op
import datetime

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from hooksScripts import hookTurnOff
from log_sender import send_family_log

# ── Helpers ───────────────────────────────────────────────────

def _get_central_file_name(document):
    """Ambil nama file central tanpa ekstensi."""
    try:
        central_path = revit.query.get_central_path(document)
        p = central_path if central_path else document.PathName
        sep = "/" if "/" in str(p) else "\\"
        name = str(p).split(sep)[-1]
        return name[:-4] if name.endswith(".rvt") else name
    except Exception:
        return "Unknown"


def _detect_load_type(family_path):
    """
    Deteksi apakah family load ini automated (oleh Revit/plugin)
    atau manual (oleh user).

    Automated load biasanya berasal dari path system Autodesk:
      - C:\\ProgramData\\Autodesk\\...
      - C:\\Users\\...\\AppData\\...\\Autodesk\\...

    Returns:
        str: "auto" atau "manual"
    """
    try:
        p = family_path.lower().replace("/", "\\")
        auto_indicators = [
            "programdata\\autodesk",
            "appdata\\autodesk",
            "appdata\\local\\autodesk",
            "appdata\\roaming\\autodesk",
        ]
        for indicator in auto_indicators:
            if indicator in p:
                return "auto"
    except Exception:
        pass
    return "manual"


def _get_familyload_log_path(document):
    """Ambil direktori log family load dari config atau fallback."""
    try:
        return user_config.PrasKaaToolsSettings.familyloadLogPath
    except Exception:
        pass
    try:
        from customOutput import def_familyloadLogPath
        if def_familyloadLogPath and os.path.isabs(def_familyloadLogPath):
            return def_familyloadLogPath
    except Exception:
        pass
    import System
    docs = System.Environment.GetFolderPath(System.Environment.SpecialFolder.MyDocuments)
    return System.IO.Path.Combine(docs, "PrasKaaPyKit", "FamilyLoad")


def _detect_load_type(family_path):
    """
    Deteksi apakah family load ini dilakukan otomatis oleh Revit/plugin
    atau secara manual oleh user.

    Auto indicators:
    - Path dari system library Autodesk (ProgramData\\Autodesk)
    - Path dari AppData Autodesk (internal Revit temp)
    - Path mengandung 'Family Templates' (template bawaan Revit/plugin)
    - Path mengandung 'Revit Steel Connections' (steel connection auto-load)

    Returns:
        str: "auto" atau "manual"
    """
    try:
        p = str(family_path).lower()
        auto_indicators = [
            "programdata\\autodesk",
            "programdata/autodesk",
            "appdata\\autodesk",
            "appdata/autodesk",
            "family templates",
            "revit steel connections",
        ]
        for indicator in auto_indicators:
            if indicator in p:
                return "auto"
    except Exception:
        pass
    return "manual"


def _log_to_file(family_path, family_name, file_size, doc_title, log_path, load_type, load_context=None):
    """Tulis log ke file lokal."""
    try:
        central_name = _get_central_file_name(__eventargs__.Document)
        safe_name = central_name.replace("\\", "_").replace("/", "_").strip() or "Unknown_Project"
        log_file_path = op.join(log_path, safe_name + "_FamilyLoad.log")

        if not op.exists(log_path):
            os.makedirs(log_path)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sep = "\t"
        entry = sep.join([timestamp, family_name, family_path, str(file_size), doc_title, load_type])
        if load_context:
            entry += sep + str(load_context)

        with open(log_file_path, "a") as f:
            f.write(entry + "\n")
    except Exception:
        pass


# ── Main hook function ────────────────────────────────────────

def dialogBox():
    doc      = __eventargs__.Document
    fam_path = __eventargs__.FamilyPath
    fam_name = __eventargs__.FamilyName

    try:
        full_path  = op.join(fam_path, fam_name + ".rfa")
        file_size  = op.getsize(full_path) if op.exists(full_path) else 0
        size_mb    = round(file_size / (1024.0 * 1024.0), 2)
        load_type  = _detect_load_type(fam_path)
        doc_title  = doc.Title if doc else "Unknown"
        log_path   = _get_familyload_log_path(doc)

        load_context = {
            "size_warning":  file_size > 1048576,
            "file_size_mb":  size_mb,
            "load_approved": True,
            "load_type":     load_type,
        }

        _log_to_file(fam_path, fam_name, file_size, doc_title, log_path, load_type, load_context)

        try:
            send_family_log(
                family_name=fam_name,
                family_path=fam_path,
                file_size_bytes=file_size,
                load_type=load_type,
                doc=doc
            )
        except Exception:
            pass

    except Exception:
        pass


hookTurnOff(dialogBox, 7)