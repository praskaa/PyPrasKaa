# -*- coding: UTF-8 -*-
"""
log_sender.py  —  PrasKaaPyKit v2
Shared module untuk mengirim log hook ke Google Sheets via Apps Script.

Letakkan file ini di:
    PrasKaaPyKitv2/lib/log_sender.py
"""

import os
import json

# ── KONFIGURASI ───────────────────────────────────────────────
LOG_SENDER_URL = "https://script.google.com/macros/s/AKfycbzHIH-CIt5ibUQHShpT9pLZVqZOF7VR70vhi3fpXKKTAb6s1_iKWm7ziM0rxXhM2tkg2w/exec"
LOG_SENDER_ENABLED = True
# ─────────────────────────────────────────────────────────────


def _get_revit_version(doc):
    try:
        return str(doc.Application.VersionNumber)
    except Exception:
        return ""


def _get_machine_name():
    try:
        import System
        return System.Environment.MachineName
    except Exception:
        return os.environ.get("COMPUTERNAME", "")


def _get_file_name(doc):
    try:
        p = doc.PathName
        sep = "\\" if "\\" in p else "/"
        name = p.split(sep)[-1]
        return name[:-4] if name.endswith(".rvt") else name
    except Exception:
        return ""


def _get_central_path(doc):
    try:
        from pyrevit import revit
        cp = revit.query.get_central_path(doc)
        return cp if cp else doc.PathName
    except Exception:
        return doc.PathName


def _timedelta_to_seconds(td):
    if td is None:
        return None
    try:
        return td.days * 86400.0 + td.seconds + td.microseconds / 1e6
    except AttributeError:
        pass
    try:
        return float(td)
    except (TypeError, ValueError):
        pass
    try:
        s = str(td).strip()
        parts = s.split(":")
        if len(parts) == 3:
            h, m, sec = parts
            return int(h) * 3600 + int(m) * 60 + float(sec)
    except Exception:
        pass
    return None


def _post_json(url, json_str):
    """
    POST JSON ke URL menggunakan .NET HttpClient.
    Google Apps Script melakukan redirect 302 dari script.google.com
    ke script.googleusercontent.com — HttpClient follow redirect tapi
    mengubah method jadi GET. Solusi: disable redirect, ambil Location
    header, lalu POST langsung ke URL tujuan.
    """
    import clr
    clr.AddReference("System.Net.Http")
    import System
    from System.Net.Http import HttpClient, HttpClientHandler, StringContent

    # Step 1: POST ke URL awal tanpa follow redirect
    handler1 = HttpClientHandler()
    handler1.AllowAutoRedirect = False
    client1 = HttpClient(handler1)
    client1.DefaultRequestHeaders.Add("User-Agent", "PrasKaaPyKit/2.0")

    content1 = StringContent(json_str, System.Text.Encoding.UTF8, "application/json")
    response1 = client1.PostAsync(url, content1).Result
    client1.Dispose()

    status_code = int(response1.StatusCode)

    # Step 2: Jika redirect (301/302/307/308), ambil Location dan POST lagi
    if status_code in (301, 302, 303, 307, 308):
        location = str(response1.Headers.Location)
        if not location.startswith("http"):
            # Relative URL — jarang terjadi tapi handle saja
            return

        handler2 = HttpClientHandler()
        handler2.AllowAutoRedirect = False
        client2 = HttpClient(handler2)
        client2.DefaultRequestHeaders.Add("User-Agent", "PrasKaaPyKit/2.0")

        content2 = StringContent(json_str, System.Text.Encoding.UTF8, "application/json")
        response2 = client2.PostAsync(location, content2).Result
        client2.Dispose()


def send_log(event_type, doc, duration_s=None, extra_info=""):
    """
    Kirim satu baris log ke Google Sheets.

    Args:
        event_type  (str) : "doc-synced", "doc-saved", "doc-opened", dst
        doc               : Revit Document object
        duration_s        : timedelta, float (detik), atau string "H:MM:SS"
        extra_info  (str) : info tambahan opsional
    """
    if not LOG_SENDER_ENABLED:
        return

    try:
        from datetime import datetime

        duration_float = _timedelta_to_seconds(duration_s)

        payload = {
            "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event_type":    event_type,
            "username":      doc.Application.Username,
            "file_name":     _get_file_name(doc),
            "central_path":  _get_central_path(doc),
            "duration_s":    round(duration_float, 1) if duration_float is not None else None,
            "revit_version": _get_revit_version(doc),
            "machine_name":  _get_machine_name(),
            "extra_info":    extra_info or "",
        }

        _post_json(LOG_SENDER_URL, json.dumps(payload))

    except Exception:
        # Silent fail — jangan sampai log sender crash Revit
        pass


def send_family_log(family_name, family_path, file_size_bytes, doc, load_type="manual"):
    """
    Kirim log family loading ke sheet 'Family Load' di Google Sheets.

    Args:
        family_name      (str) : nama family tanpa ekstensi
        family_path      (str) : direktori lokasi file .rfa
        file_size_bytes  (int) : ukuran file dalam bytes (0 jika tidak diketahui)
        doc                    : Revit Document object
        load_type        (str) : "manual" atau "auto" (default: "manual")
    """
    if not LOG_SENDER_ENABLED:
        return

    try:
        from datetime import datetime

        payload = {
            "event_type":    "family-loading",
            "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username":      doc.Application.Username,
            "family_name":   family_name or "",
            "family_path":   family_path or "",
            "file_size_kb":  round(file_size_bytes / 1024.0, 1) if file_size_bytes else 0,
            "project_title": doc.Title if doc else "",
            "machine_name":  _get_machine_name(),
            "revit_version": _get_revit_version(doc),
            "load_type":     load_type,
        }

        _post_json(LOG_SENDER_URL, json.dumps(payload))

    except Exception:
        pass