---
id: "LOG-UTIL-PARAM-003"
version: "v1"
status: "active"
category: "utilities/parameters"
element_type: "Configuration"
operation: "persistence"
revit_versions: [2024, 2026]
tags: ["configuration", "persistence", "settings", "json", "file-storage"]
created: "2025-10-10"
updated: "2025-10-10"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton/script.py"
source_location: "Helper.panel/SmartTag.pushbutton"
---

# LOG-UTIL-PARAM-003-v1: Configuration Management and Persistence

## Problem Context

pyRevit scripts often need to remember user preferences, settings, and configuration between runs. Without a proper configuration management system, users have to reconfigure settings every time they use the tool, leading to frustration and inefficiency.

## Solution Summary

This pattern implements a JSON-based configuration management system that persists settings to a file in the script directory. It provides methods to load, save, and update configuration values with proper error handling and default fallbacks.

## Working Code

```python
import json
import os
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon

class ConfigurationManager:
    """Manages configuration persistence for pyRevit scripts"""

    def __init__(self, script_dir=None, config_filename="config.json"):
        self.script_dir = script_dir or os.path.dirname(__file__)
        self.config_filename = config_filename
        self.config_path = os.path.join(self.script_dir, config_filename)
        self.config = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default configuration
                self.config = self._get_default_config()
                self._save_config()
        except Exception as e:
            print("Warning: Could not load config file: {}".format(str(e)))
            # Use defaults if loading fails
            self.config = self._get_default_config()

    def _save_config(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print("Error: Could not save config file: {}".format(str(e)))
            MessageBox.Show(
                "Could not save configuration: {}".format(str(e)),
                "Configuration Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )

    def _get_default_config(self):
        """Get default configuration values"""
        return {
            'tag_mode': 'untagged_only',
            'categories': {
                'structural_framing': {
                    'enabled': True,
                    'offset_mm': 150
                },
                'structural_column': {
                    'enabled': True,
                    'offset_mm': 100
                },
                'walls': {
                    'enabled': True,
                    'offset_mm': 50
                }
            },
            'ui_settings': {
                'verbose_logging': False,
                'show_progress': True
            }
        }

    def get_value(self, key, default=None):
        """Get configuration value with optional default"""
        return self.config.get(key, default)

    def set_value(self, key, value):
        """Set configuration value and save"""
        self.config[key] = value
        self._save_config()

    def update_nested_value(self, keys, value):
        """Update nested configuration value (e.g., ['categories', 'walls', 'enabled'])"""
        try:
            current = self.config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
            self._save_config()
            return True
        except Exception as e:
            print("Error updating nested config: {}".format(str(e)))
            return False

    def get_nested_value(self, keys, default=None):
        """Get nested configuration value"""
        try:
            current = self.config
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    # Specific methods for common operations
    def get_tag_mode(self):
        """Get current tag mode"""
        return self.get_value('tag_mode', 'untagged_only')

    def update_tag_mode(self, mode):
        """Update tag mode"""
        if mode in ['untagged_only', 'retag_all']:
            self.set_value('tag_mode', mode)
            return True
        return False

    def get_all_categories(self):
        """Get all category configurations"""
        return self.get_value('categories', {})

    def get_category_config(self, category_key):
        """Get configuration for specific category"""
        categories = self.get_all_categories()
        return categories.get(category_key, {})

    def update_category_config(self, category_key, config_dict):
        """Update configuration for a category"""
        categories = self.get_all_categories()
        categories[category_key] = config_dict
        self.set_value('categories', categories)

    def is_category_enabled(self, category_key):
        """Check if category is enabled"""
        cat_config = self.get_category_config(category_key)
        return cat_config.get('enabled', True)

    def get_category_offset(self, category_key):
        """Get offset for category"""
        cat_config = self.get_category_config(category_key)
        return cat_config.get('offset_mm', 0)

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self._get_default_config()
        self._save_config()

    def export_config(self, export_path=None):
        """Export configuration to external file"""
        if not export_path:
            export_path = self.config_path.replace('.json', '_export.json')

        try:
            with open(export_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return export_path
        except Exception as e:
            print("Error exporting config: {}".format(str(e)))
            return None

    def import_config(self, import_path):
        """Import configuration from external file"""
        try:
            with open(import_path, 'r') as f:
                imported_config = json.load(f)

            # Validate imported config has required structure
            if self._validate_config(imported_config):
                self.config = imported_config
                self._save_config()
                return True
            else:
                print("Invalid configuration format")
                return False
        except Exception as e:
            print("Error importing config: {}".format(str(e)))
            return False

    def _validate_config(self, config):
        """Validate configuration structure"""
        required_keys = ['tag_mode', 'categories']
        for key in required_keys:
            if key not in config:
                return False
        return True
```

## Key Techniques

1. **JSON Persistence**: Configuration stored as human-readable JSON files
2. **Default Fallbacks**: Robust defaults when configuration is missing or corrupted
3. **Nested Access**: Support for hierarchical configuration structures
4. **Error Handling**: Graceful handling of file I/O errors
5. **Validation**: Configuration structure validation for imports

## Revit API Compatibility

- **File System Access**: Uses standard Python file operations
- **No Revit API Dependencies**: Pure configuration management
- **Cross-platform**: Works on Windows (Revit's platform)

## Performance Notes

- **Execution Time**: Fast file operations, typically < 0.1s
- **Memory Usage**: Lightweight JSON structure storage
- **File Size**: Small configuration files, minimal disk impact

## Usage Examples

### Basic Configuration Setup
```python
# Initialize configuration manager
config = ConfigurationManager()

# Get current tag mode
current_mode = config.get_tag_mode()  # Returns 'untagged_only' or 'retag_all'

# Update tag mode
config.update_tag_mode('retag_all')

# Check category status
if config.is_category_enabled('structural_framing'):
    offset = config.get_category_offset('structural_framing')
    # Use offset for processing
```

### Category Management
```python
# Get all category configurations
categories = config.get_all_categories()

# Update specific category
config.update_category_config('walls', {
    'enabled': True,
    'offset_mm': 75
})

# Check individual category settings
for cat_key, cat_config in categories.items():
    if cat_config.get('enabled', True):
        print("{}: {}mm offset".format(cat_key, cat_config.get('offset_mm', 0)))
```

### Advanced Configuration Operations
```python
# Export configuration for backup
backup_path = config.export_config()
print("Configuration exported to: {}".format(backup_path))

# Reset to defaults
config.reset_to_defaults()

# Import from backup
if config.import_config(backup_path):
    print("Configuration restored successfully")
```

### Integration with Script Logic
```python
def execute_with_config():
    config = ConfigurationManager()

    # Get processing mode from config
    tag_mode = config.get_tag_mode()

    # Get enabled categories
    enabled_categories = []
    for cat_key in ['structural_framing', 'structural_column', 'walls']:
        if config.is_category_enabled(cat_key):
            enabled_categories.append(cat_key)

    # Process based on configuration
    for category in enabled_categories:
        offset = config.get_category_offset(category)
        process_category_elements(category, tag_mode, offset)
```

## Common Pitfalls

1. **File Permissions**: Ensure write access to script directory
2. **JSON Encoding**: Handle special characters in configuration values
3. **Concurrent Access**: Avoid simultaneous file access from multiple instances
4. **Version Compatibility**: Handle configuration format changes between versions

## Related Logic Entries

- [LOG-STRUCT-PARAM-001-v1-category-based-parameter-management](LOG-STRUCT-PARAM-001-v1-category-based-parameter-management.md) - Category configuration usage
- [LOG-STRUCT-PARAM-002-v1-tag-mode-management](LOG-STRUCT-PARAM-002-v1-tag-mode-management.md) - Tag mode persistence

## Optimization History

*This is the initial version (v1) with no optimizations yet.*