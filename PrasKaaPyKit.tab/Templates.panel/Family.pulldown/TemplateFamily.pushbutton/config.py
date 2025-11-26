# -*- coding: utf-8 -*-
"""Configuration for Family Repository"""

# Template project name patterns
TEMPLATE_PATTERNS = [
    "TEMPLATE",
    "STD",
    "STANDARD",
    "_TPL",
    "_TEMPLATE"
]

# Template project paths on different machines
TEMPLATE_PROJECT_PATHS = [
    r"I:\1_STUDI\Revit_Template\SL_Template_Structural_vers.6.0_v2024.rte",  # Main template
    r"F:\1_STUDI\Revit_Template\SL_Template_Structural_vers.6.0_v2024.rte",  # Backup 1  
    r"D:\1_STUDI\Revit_Template\SL_Template_Structural_vers.6.0_v2024.rte",  # Backup 1  
]

# Status colors
COLORS = {
    'NEW': '#D7EDFF',      # Light blue - family only in template
    'EXISTS': '#FFD700',    # Gold - family exists in current doc
    'SYNCED': '#90EE90',   # Light green - family was just synced
    'ERROR': '#FFB6C1',    # Light red - sync failed
}

# Status text
STATUS = {
    'NEW': 'Available',      # Family is in template but not in current doc
    'EXISTS': 'Exists',      # Family already exists in current doc
    'SYNCED': 'Synced',      # Family was just synced from template
    'ERROR': 'Error',        # Error occurred during sync
}
