# -*- coding: UTF-8 -*-
from pyrevit import EXEC_PARAMS
from pyrevit import forms, script
from pyrevit.userconfig import user_config
from pyrevit import revit
import sys
import os

# Add lib directory to Python path
lib_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from hooksScripts import hookTurnOff

import os.path as op
import os
import datetime
import getpass
import uuid

# JSON Logging Configuration
ENABLE_JSON_LOGGING = False
JSON_LOG_FILENAME = "family_load_log.json"
TEXT_LOG_FILENAME = "family_load_log.txt"

# Log Rotation Configuration
MAX_LOG_FILE_SIZE_MB = 10
MAX_BACKUP_FILES = 5
ENABLE_LOG_COMPRESSION = False  # Set to False for IronPython compatibility

# Session Management - Generate once per Revit session
SESSION_ID = str(uuid.uuid4())

# JSON Serialization Functions
def safe_json_dumps(data):
    """
    Safe JSON serialization compatible with IronPython
    """
    try:
        import json
        return json.dumps(data, separators=(',', ':'))
    except ImportError:
        # Fallback manual JSON creation for IronPython
        return manual_json_serialize(data)
    except Exception:
        return None

def manual_json_serialize(data):
    """
    Manual JSON serialization as fallback
    """
    if isinstance(data, dict):
        items = []
        for key, value in data.items():
            key_str = '"{0}"'.format(str(key))
            value_str = manual_json_serialize(value)
            items.append('{0}:{1}'.format(key_str, value_str))
        return '{{{0}}}'.format(','.join(items))
    elif isinstance(data, (list, tuple)):
        items = [manual_json_serialize(item) for item in data]
        return '[{0}]'.format(','.join(items))
    elif isinstance(data, str):
        # Escape quotes and backslashes
        escaped = data.replace('\\', '\\\\').replace('"', '\\"')
        return '"{0}"'.format(escaped)
    elif isinstance(data, bool):
        return 'true' if data else 'false'
    elif data is None:
        return 'null'
    else:
        return str(data)

# Log Rotation Functions
def get_log_file_size_mb(file_path):
    """
    Get log file size in MB
    """
    try:
        if op.exists(file_path):
            size_bytes = op.getsize(file_path)
            return size_bytes / (1024.0 * 1024.0)
        return 0
    except:
        return 0

def rotate_log_files(log_file_path):
    """
    Rotate log files when size limit exceeded
    """
    try:
        if not op.exists(log_file_path):
            return True
        
        # Get base name and extension
        base_name = op.splitext(log_file_path)[0]
        extension = op.splitext(log_file_path)[1]
        
        # Rotate existing backup files
        for i in range(MAX_BACKUP_FILES - 1, 0, -1):
            old_backup = "{0}.{1}{2}".format(base_name, i, extension)
            new_backup = "{0}.{1}{2}".format(base_name, i + 1, extension)
            
            if op.exists(old_backup):
                if i + 1 <= MAX_BACKUP_FILES:
                    # Move to next backup number
                    if op.exists(new_backup):
                        os.remove(new_backup)
                    os.rename(old_backup, new_backup)
                else:
                    # Delete if exceeds max backups
                    os.remove(old_backup)
        
        # Move current log to .1 backup
        first_backup = "{0}.1{1}".format(base_name, extension)
        if op.exists(first_backup):
            os.remove(first_backup)
        os.rename(log_file_path, first_backup)
        
        return True
        
    except Exception as e:
        # Silently handle rotation errors
        return False

def check_and_rotate_log(log_file_path):
    """
    Check if log rotation is needed and perform it
    """
    try:
        current_size_mb = get_log_file_size_mb(log_file_path)
        if current_size_mb > MAX_LOG_FILE_SIZE_MB:
            return rotate_log_files(log_file_path)
        return True
    except:
        return True  # Continue even if rotation check fails

# Function to get project log directory
def get_project_log_directory(document):
    """
    Get the directory where project logs should be saved.
    Returns project directory if document is saved, otherwise Documents folder.
    """
    try:
        if document and document.PathName:
            # Document is saved, use its directory
            project_path = document.PathName
            project_dir = op.dirname(project_path)
            return project_dir
        else:
            # Document not saved, fallback to Documents folder
            import System
            return System.Environment.GetFolderPath(System.Environment.SpecialFolder.MyDocuments)
    except:
        # Error handling - fallback to Documents folder
        import System
        return System.Environment.GetFolderPath(System.Environment.SpecialFolder.MyDocuments)


# Enhanced Log Entry Creation
def create_json_log_entry(family_path, family_name, document, load_context=None):
    """
    Create structured JSON log entry
    """
    try:
        timestamp = datetime.datetime.now()
        iso_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+07:00"
        
        # Calculate file size
        full_path = op.join(family_path, family_name + ".rfa")
        file_size = 0
        if op.exists(full_path):
            file_size = op.getsize(full_path)
        
        # Get document information
        doc_title = "Unknown"
        doc_path = "Unknown"
        if document:
            doc_title = document.Title
            try:
                doc_path = document.PathName if document.PathName else "Unsaved"
            except:
                doc_path = "Unknown"
        
        # Get Revit username (if available)
        revit_username = "Unknown"
        try:
            from Autodesk.Revit.ApplicationServices import Application
            app = document.Application if document else None
            if app and hasattr(app, 'Username'):
                revit_username = app.Username
        except:
            pass
        
        # Create structured log entry
        log_entry = {
            "timestamp": iso_timestamp,
            "event_type": "family_load",
            "user": {
                "windows_username": getpass.getuser(),
                "revit_username": revit_username
            },
            "family": {
                "name": family_name,
                "path": full_path,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024.0 * 1024.0), 2)
            },
            "document": {
                "title": doc_title,
                "path": doc_path
            },
            "load_context": load_context or {
                "trigger": "hook",
                "size_warning": file_size > 1048576,
                "load_approved": True
            },
            "session_id": SESSION_ID
        }
        
        return log_entry
        
    except Exception as e:
        # Return minimal entry on error
        return {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "event_type": "family_load",
            "family_name": family_name,
            "error": "Failed to create full log entry",
            "session_id": SESSION_ID
        }

# Enhanced Logging Function
def log_family_load_enhanced(family_path, family_name, document, load_context=None):
    """
    Enhanced family loading logger with JSON support and rotation
    """
    try:
        # Get log file paths - using configured family load log path
        log_directory = get_familyload_log_path(document)
        json_log_path = op.join(log_directory, JSON_LOG_FILENAME)
        text_log_path = op.join(log_directory, TEXT_LOG_FILENAME)
        
        # Check and rotate logs if needed
        if ENABLE_JSON_LOGGING:
            check_and_rotate_log(json_log_path)
        check_and_rotate_log(text_log_path)
        
        # Create log entries
        success = False
        
        # Try JSON logging first
        if ENABLE_JSON_LOGGING:
            try:
                json_entry = create_json_log_entry(family_path, family_name, document, load_context)
                json_string = safe_json_dumps(json_entry)
                
                if json_string:
                    with open(json_log_path, "a") as json_file:
                        json_file.write(json_string + "\n")
                    success = True
            except Exception as e:
                pass  # Fall back to text logging
        
        # Always create text log entry as backup
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username = getpass.getuser()
            
            # Calculate file size
            full_path = op.join(family_path, family_name + ".rfa")
            file_size = 0
            if op.exists(full_path):
                file_size = op.getsize(full_path)
            
            # Get document title safely
            doc_title = "Unknown"
            if document:
                doc_title = document.Title
            
            # Create text log entry
            text_entry = "{0} | {1} | {2} | {3} | {4} bytes | {5} | {6}".format(
                timestamp, username, family_name, family_path, file_size, doc_title, SESSION_ID
            )
            
            with open(text_log_path, "a") as text_file:
                text_file.write(text_entry + "\n")
                
        except Exception as e:
            pass  # Silently handle text logging errors
            
    except Exception as e:
        # Ultimate fallback - try original simple logging
        try:
            log_family_load(family_path, family_name, document)
        except:
            pass  # Silently handle all logging errors to avoid breaking the hook

# Function to log family loading details
def log_family_load(family_path, family_name, document):
    """
    Log family loading details to a log file
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        
        # Calculate file size
        full_path = op.join(family_path, family_name + ".rfa")
        file_size = 0
        if op.exists(full_path):
            file_size = op.getsize(full_path)
        
        # Get document title safely
        doc_title = "Unknown"
        if document:
            doc_title = document.Title
        
        # Create log entry using string formatting compatible with IronPython
        log_entry = "{0} | {1} | {2} | {3} | {4} bytes | {5}".format(
            timestamp, username, family_name, family_path, file_size, doc_title
        )
        
        # Write to log file - using configured family load log path
        log_directory = get_familyload_log_path(document)
        log_file_path = op.join(log_directory, "family_load_log.txt")
        
        # Create/append to log file
        with open(log_file_path, "a") as log_file:
            log_file.write(log_entry + "\n")
            
    except:
        # Silently handle logging errors to avoid breaking the hook
        pass

def get_central_file_name(document):
    """
    Get central file name from document, similar to doc-opened.py
    """
    try:
        debug_log("=== START get_central_file_name ===")
        if not document:
            debug_log("No document provided")
            return "Unknown"
            
        file_path = document.PathName
        debug_log("Document path: {}".format(str(file_path)))
        if not file_path:
            debug_log("Empty file path")
            return "Unknown"
            
        # getting central file name for log name
        try:
            central_path = revit.query.get_central_path(document)
            debug_log("Central path: {}".format(str(central_path)))
            
            # Handle None or empty central path
            if not central_path or central_path == "None":
                debug_log("Central path is None, using file path")
                central_path = file_path
                
        except Exception as e:
            debug_log("Error getting central path: {}".format(str(e)))
            central_path = file_path
        
        try:
            # Handle both forward and backward slashes
            if "/" in str(central_path):
                lastBackslash_C = central_path.rindex("/")
            elif "\\" in str(central_path):
                lastBackslash_C = central_path.rindex("\\")
            else:
                # No slashes, use full path
                lastBackslash_C = -1
                
            # just the file name without the extension
            if lastBackslash_C >= 0:
                central_file_name = central_path[lastBackslash_C+1:][:-4]
            else:
                central_file_name = central_path[:-4]
                
            debug_log("Extracted central file name: {}".format(str(central_file_name)))
            
            # Clean up any leading slashes/backslashes
            central_file_name = central_file_name.strip("\\/")
            if not central_file_name:
                central_file_name = "Unknown"
                
        except Exception as e:
            debug_log("Error extracting from central path: {}".format(str(e)))
            # fallback to local file name
            try:
                if "\\" in str(file_path):
                    lastBackslash_L = file_path.rindex("\\")
                    central_file_name = file_path[lastBackslash_L+1:][:-4]
                elif "/" in str(file_path):
                    lastBackslash_L = file_path.rindex("/")
                    central_file_name = file_path[lastBackslash_L+1:][:-4]
                else:
                    central_file_name = file_path[:-4]
                    
                central_file_name = central_file_name.strip("\\/")
                debug_log("Fallback central file name: {}".format(str(central_file_name)))
                
            except Exception as e2:
                debug_log("ERROR in fallback: {}".format(str(e2)))
                central_file_name = "Unknown"
            
        return central_file_name
        
    except Exception as e:
        debug_log("ERROR in get_central_file_name: {}".format(str(e)))
        return "Unknown"

def get_familyload_log_path(document):
    """
    Get family load log path from configuration, similar to doc-opened.py
    """
    try:
        debug_log("=== START get_familyload_log_path ===")
        from pyrevit.userconfig import user_config
        
        # Try to get path from user config
        try:
            familyloadLogPath = user_config.PrasKaaToolsSettings.familyloadLogPath
            debug_log("Got path from user config: {}".format(str(familyloadLogPath)))
        except Exception as e:
            debug_log("Error getting from user config: {}".format(str(e)))
            # Fallback to default path
            try:
                from customOutput import def_familyloadLogPath
                familyloadLogPath = def_familyloadLogPath
                debug_log("Using default path: {}".format(str(familyloadLogPath)))
            except Exception as e2:
                debug_log("Error getting default path: {}".format(str(e2)))
                familyloadLogPath = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\FamilyLoad"
        
        # Ensure path is absolute and valid
        if not familyloadLogPath or not os.path.isabs(familyloadLogPath):
            familyloadLogPath = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\FamilyLoad"
            debug_log("Using absolute fallback path: {}".format(str(familyloadLogPath)))
            
        return familyloadLogPath
        
    except Exception as e:
        debug_log("ERROR in get_familyload_log_path: {}".format(str(e)))
        # Ultimate fallback
        return r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\FamilyLoad"

def debug_log(message):
    """
    Debug logging function to track issues
    """
    DEBUG_MODE = False  # Set to False to disable debug logging
    if not DEBUG_MODE:
        return
        
    try:
        debug_log_path = r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaToolsLogs\FamilyLoad\debug.log"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(debug_log_path, "a") as debug_file:
            debug_file.write("[{}] {}\n".format(timestamp, str(message)))
    except:
        pass

def log_family_load_new(family_path, family_name, document, load_context=None):
    """
    New family loading logger similar to doc-opened.py pattern
    """
    try:
        debug_log("=== START log_family_load_new ===")
        debug_log("family_path: {}".format(str(family_path)))
        debug_log("family_name: {}".format(str(family_name)))
        
        if not document:
            debug_log("ERROR: No document provided")
            return
            
        # Get central file name for log file name
        debug_log("Getting central file name...")
        central_file_name = get_central_file_name(document)
        debug_log("Central file name: {}".format(str(central_file_name)))
        
        # Get log path
        debug_log("Getting log path...")
        log_path = get_familyload_log_path(document)
        debug_log("Log path: {}".format(str(log_path)))
        
        # Create log file path - ensure proper path construction
        safe_file_name = str(central_file_name).replace("\\", "_").replace("/", "_").strip()
        if not safe_file_name or safe_file_name == "Unknown":
            safe_file_name = "Unknown_Project"
            
        log_file_path = op.join(log_path, safe_file_name + "_FamilyLoad.log")
        debug_log("Log file path: {}".format(str(log_file_path)))
        
        # Validate path construction
        debug_log("Full path validation - log_path: {}".format(str(log_path)))
        debug_log("Full path validation - safe_file_name: {}".format(str(safe_file_name)))
        debug_log("Full path validation - final path: {}".format(str(log_file_path)))
        
        # Ensure directory exists
        if not op.exists(log_path):
            debug_log("Directory does not exist, creating...")
            try:
                os.makedirs(log_path)
                debug_log("Directory created successfully")
            except Exception as e:
                debug_log("ERROR creating directory: {}".format(str(e)))
                pass
        
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        
        # Calculate file size
        full_path = op.join(family_path, family_name + ".rfa")
        file_size = 0
        if op.exists(full_path):
            file_size = op.getsize(full_path)
        
        # Get document title
        doc_title = "Unknown"
        if document:
            doc_title = document.Title
        
        # Create log entry
        separator = "\t"
        log_entry = timestamp + separator + username + separator + family_name + separator + family_path + separator + str(file_size) + separator + doc_title
        
        # Add load context if provided
        if load_context:
            log_entry += separator + str(load_context)
        
        debug_log("Log entry: {}".format(str(log_entry)))
        
        # Write to log file
        debug_log("Writing to log file...")
        with open(log_file_path, "a") as log_file:
            log_file.write(log_entry + "\n")
        debug_log("Log written successfully")
            
    except Exception as e:
        debug_log("ERROR in log_family_load_new: {}".format(str(e)))
        debug_log("Exception type: {}".format(type(e).__name__))
        import traceback
        try:
            debug_log("Traceback: {}".format(str(traceback.format_exc())))
        except:
            pass

# showing of dialog box with warning
def dialogBox():
    doc = __eventargs__.Document

    # if family is saved
    try:
        fam_path = __eventargs__.FamilyPath
        fam_name = __eventargs__.FamilyName
        famSize = op.getsize(fam_path + fam_name + ".rfa")

        # checking if family is larger than 1 megabyte 
        if famSize > 1048576:
            from hook_translate import hook_texts, lang

            title = "Load Family"
            # the language value is read from pyrevit config file
            current_lang = lang()

            # WARNING WINDOW
            res = forms.alert(hook_texts[current_lang][title]["text"],
                             options = hook_texts[current_lang][title]["buttons"],
                             title = title,
                             footer = "PrasKaa PyKit Hooks")
            # BUTTONS
            # Load
            if res  == hook_texts[current_lang][title]["buttons"][1]:
                # Log family loading details with new logging system
                load_context = {
                    "trigger": "user_dialog",
                    "size_warning": True,
                    "load_approved": True,
                    "file_size_mb": round(famSize / (1024.0 * 1024.0), 2)
                }
                log_family_load_new(fam_path, fam_name, doc, load_context)
                
                # logging to server - cannot access active document
                from hooksScripts import hooksLogger
                hooksLogger("Family loading over 1 MB", doc)
            # Cancel
            elif res  == hook_texts[current_lang][title]["buttons"][0]:
                EXEC_PARAMS.event_args.Cancel()
            # More info
            elif res  == hook_texts[current_lang][title]["buttons"][2]:
                wiki_url = user_config.PrasKaaToolsSettings.wiki
                # if lang == "SK":
                if len(wiki_url) > 0:
                    url = wiki_url + '/wiki/Chyby_vo_families_Revitu#Ve.C4.BEkos.C5.A5_Family'
                else:
                    url = 'https://customtools.notion.site/Procedures-to-be-avoided-e6e4ce335d544040acee210943afa237'
                script.open_url(url)
                EXEC_PARAMS.event_args.Cancel()
            else:
                EXEC_PARAMS.event_args.Cancel()
        else:
            # Log family loading details for small families too
            load_context = {
                "trigger": "automatic",
                "size_warning": False,
                "load_approved": True,
                "file_size_mb": round(famSize / (1024.0 * 1024.0), 2)
            }
            log_family_load_new(fam_path, fam_name, doc, load_context)
    # if family is not saved yet famSize does not exist
    except:
        # Log family loading details even if size can't be determined
        try:
            fam_path = __eventargs__.FamilyPath
            fam_name = __eventargs__.FamilyName
            load_context = {
                "trigger": "exception_handler",
                "size_warning": False,
                "load_approved": True,
                "error": "Could not determine file size"
            }
            log_family_load_new(fam_path, fam_name, doc, load_context)
        except:
            pass


# try to find config file for people who dont want to see the hook
hookTurnOff(dialogBox,7)