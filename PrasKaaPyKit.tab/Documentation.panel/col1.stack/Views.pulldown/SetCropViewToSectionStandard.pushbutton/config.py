# Configuration file for Crop View Line Settings
# Modify these values to change the default behavior

CONFIG = {
    # Line settings
    'line_weight': 6,
    'line_pattern_name': 'Dash dot',
      # View type filter - set to None to include all view types
    # Available options: 'Section', 'Elevation', 'Plan', 'Detail', etc.
    'allowed_view_types': ['Section', 'Detail'],
    
    # Undo functionality
    'enable_undo': True,
    'store_original_settings': True,
    
    # UI settings
    'show_progress_bar': True,
    'show_detailed_results': True
}

# Advanced settings (modify with caution)
ADVANCED_CONFIG = {
    'transaction_group_name': 'Set Crop View Line Settings',
    'backup_file_prefix': 'crop_view_backup_',
    'max_backup_files': 5
}
