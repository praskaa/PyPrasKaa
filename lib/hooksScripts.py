# -*- coding: UTF-8 -*-
"""
hooksScripts.py - PrasKaa PyKit Hooks Scripts Module
Adapted from CustomTools for PrasKaa PyKit extension
"""

import os
import datetime
import getpass
import sys

# Add lib directory to Python path if not already there
lib_path = os.path.dirname(os.path.abspath(__file__))
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from customOutput import def_hookLogs, def_revitBuildLogs

# Version information for PrasKaa PyKit
releasedVersion = "1.0.0"
snapshot = "PrasKaa PyKit"

def get_extension_path():
    """Get the current extension path"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to get the extension root
        extension_path = os.path.dirname(script_dir)
        return extension_path
    except:
        return r"F:\1_STUDI\_PrasKaa Python Kit\PrasKaaPyKit.extension"

def hookTurnOff(function, hook_id):
    """
    Check if hook should be turned off based on config file
    Args:
        function: The function to execute if hook is enabled
        hook_id: The ID of the hook to check
    """
    try:
        extension_path = get_extension_path()
        config_file_path = os.path.join(extension_path, "config", "hooksConfig.txt")
        
        # Check if config file exists
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as config_file:
                content = config_file.read()
                # Read the first line which contains the hook enable/disable flags
                lines = content.split('\n')
                if len(lines) > 0:
                    hook_flags = lines[0].strip()
                    # Check if the hook_id position has '1' (enabled) or '0' (disabled)
                    if len(hook_flags) > hook_id - 1:
                        if hook_flags[hook_id - 1] == '1':
                            # Hook is enabled, execute the function
                            function()
                        # If '0', hook is disabled, do nothing
                    else:
                        # If config is shorter than expected, enable by default
                        function()
                else:
                    # If config file is empty, enable by default
                    function()
        else:
            # If config file doesn't exist, enable by default
            function()
    except Exception as e:
        # If any error occurs, enable by default to avoid breaking functionality
        function()

def hooksLogger(message, doc):
    """
    Log hook events to server/file
    Args:
        message: The message to log
        doc: The Revit document
    """
    try:
        # Create log entry
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        
        # Get document info
        doc_title = "Unknown"
        doc_path = "Unknown"
        if doc:
            try:
                doc_title = doc.Title
                doc_path = doc.PathName if doc.PathName else "Unsaved"
            except:
                pass
        
        # Create log entry
        log_entry = "{0} | {1} | {2} | {3} | {4}".format(
            timestamp, username, message, doc_title, doc_path
        )
        
        # Write to log file
        try:
            from pyrevit.userconfig import user_config
            try:
                logs_path = user_config.PrasKaaToolsSettings.hookLogs
            except:
                logs_path = def_hookLogs
        except:
            logs_path = def_hookLogs
            
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
        
        log_file_path = os.path.join(logs_path, "hooks_log.txt")
        with open(log_file_path, "a") as log_file:
            log_file.write(log_entry + "\n")
            
    except Exception as e:
        # Silently handle logging errors to avoid breaking hooks
        pass

def versionLogger(version, snapshot):
    """
    Log version information and check Revit build
    Args:
        version: The version string
        snapshot: The snapshot/build info
    """
    try:
        from pyrevit import HOST_APP
        from pyrevit.userconfig import user_config
        
        # Get Revit build info
        revit_build = "Unknown"
        try:
            revit_build = HOST_APP.build
        except:
            pass
        
        # Create log entry
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = getpass.getuser()
        
        log_entry = "{0} | {1} | {2} | {3} | {4}".format(
            timestamp, username, version, snapshot, revit_build
        )
        
        # Write to version log file
        try:
            try:
                revit_build_logs = user_config.PrasKaaToolsSettings.revitBuildLogs
            except:
                revit_build_logs = def_revitBuildLogs
        except:
            revit_build_logs = def_revitBuildLogs
            
        # Get directory from the full log file path
        logs_path = os.path.dirname(revit_build_logs)
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
        
        log_file_path = revit_build_logs
        with open(log_file_path, "a") as log_file:
            log_file.write(log_entry + "\n")
        
        # Check if Revit build is supported
        try:
            supported_builds = user_config.PrasKaaToolsSettings.revitBuilds
        except:
            # Default supported builds
            supported_builds = "20240814_1400(x64), 20220520_1515(x64), 20201116_1100(x64), 20240408_1515(x64)"
        
        # Show warning if build is not supported (optional)
        if str(revit_build) not in supported_builds:
            # Could show a warning dialog here if needed
            pass
            
    except Exception as e:
        # Silently handle logging errors
        pass

def ensure_log_directories():
    """
    Ensure all required log directories exist
    """
    try:
        from customOutput import def_syncLogPath, def_openingLogPath, def_dashboardsPath
        
        # Use configured paths or defaults
        try:
            from pyrevit.userconfig import user_config
            try:
                hook_logs = user_config.PrasKaaToolsSettings.hookLogs
            except:
                hook_logs = def_hookLogs
            try:
                sync_logs = user_config.PrasKaaToolsSettings.syncLogPath
            except:
                sync_logs = def_syncLogPath
            try:
                opening_logs = user_config.PrasKaaToolsSettings.openingLogPath
            except:
                opening_logs = def_openingLogPath
            try:
                dashboards_path = user_config.PrasKaaToolsSettings.dashboardsPath
            except:
                dashboards_path = def_dashboardsPath
            try:
                revit_logs = user_config.PrasKaaToolsSettings.revitBuildLogs
                base_path = os.path.dirname(revit_logs)
            except:
                base_path = os.path.dirname(def_revitBuildLogs)
        except:
            hook_logs = def_hookLogs
            sync_logs = def_syncLogPath
            opening_logs = def_openingLogPath
            dashboards_path = def_dashboardsPath
            base_path = os.path.dirname(def_revitBuildLogs)
        
        directories = [
            base_path,
            hook_logs,
            sync_logs,
            opening_logs,
            os.path.join(base_path, "toolsLogs"),
            dashboards_path
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                
    except Exception as e:
        # Silently handle directory creation errors
        pass

# Initialize log directories when module is imported
ensure_log_directories()