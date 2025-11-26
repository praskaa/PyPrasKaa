# -*- coding: utf-8 -*-
"""
Shared Configuration for Matching Scripts (Framing & Column)
Centralized configuration to maintain consistency across scripts.
Uses same Documents path detection as hooks for consistency.
"""

import os

# Dynamic Documents path detection (same as hooks)
try:
    import System
    documents_path = System.Environment.GetFolderPath(System.Environment.SpecialFolder.MyDocuments)
except:
    # Fallback for systems without .NET
    documents_path = os.path.expanduser('~/Documents')

# Processing Configuration
BATCH_SIZE = 150  # Elements per batch to prevent memory overload
ENABLE_PROGRESS_DETAIL = True  # Detailed progress reporting (False for cleaner output)
CLEANUP_GEOMETRY_CACHE = True  # Clear geometry cache after processing
DISABLE_JOINS = False  # Disable auto-joins for performance

# Output Configuration
MAX_TABLE_ROWS = 50  # Maximum rows to display in output window
EXPORT_RESULTS_TO_CSV = True  # Export full results to CSV file

# CSV Output Configuration - Now uses full Documents path like hooks
CSV_BASE_DIR = os.path.join(documents_path, "PrasKaaPyKit")  # Full path to base folder
CSV_CREATE_FOLDERS = True  # Auto-create folders if they don't exist