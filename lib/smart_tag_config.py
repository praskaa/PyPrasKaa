# -*- coding: utf-8 -*-
"""Smart Tag System - Configuration Management"""

import json
import os
from collections import OrderedDict

class SmartTagConfig:
    """Manages configuration for Smart Tag System"""
    
    def __init__(self):
        self.config_file = self._get_config_path()
        self.default_config = self._get_default_config()
        self.config = self.load_config()
    
    def _get_config_path(self):
        """Get configuration file path"""
        # Config will be stored in pyRevit extension folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, 'smart_tag_config.json')
    
    def _get_default_config(self):
        """Default configuration values"""
        return OrderedDict([
            ('structural_framing', {
                'tag_type_name': 'Structural Framing Tag',
                'offset_mm': 150,
                'enabled': True
            }),
            ('structural_column', {
                'tag_type_name': 'Structural Column Tag',
                'offset_mm': 200,
                'enabled': True
            }),
            ('walls', {
                'tag_type_name': 'Wall Tag',
                'offset_mm': 100,
                'enabled': True
            }),
            ('tag_mode', 'untagged_only')  # or 'retag_all'
        ])
    
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f, object_pairs_hook=OrderedDict)
                    # Merge with defaults to ensure all keys exist
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
            except Exception as e:
                print("Error loading config: {}".format(e))
                return self.default_config.copy()
        else:
            # Create default config file
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print("Error saving config: {}".format(e))
            return False
    
    def get_category_config(self, category_key):
        """Get configuration for specific category"""
        return self.config.get(category_key, {})
    
    def get_tag_mode(self):
        """Get current tag mode"""
        return self.config.get('tag_mode', 'untagged_only')
    
    def update_category_config(self, category_key, tag_type_name, offset_mm, enabled):
        """Update configuration for a category"""
        self.config[category_key] = {
            'tag_type_name': tag_type_name,
            'offset_mm': offset_mm,
            'enabled': enabled
        }
        return self.save_config()
    
    def update_tag_mode(self, mode):
        """Update tag mode"""
        self.config['tag_mode'] = mode
        return self.save_config()
    
    def get_all_categories(self):
        """Get all category configurations"""
        categories = OrderedDict()
        for key in ['structural_framing', 'structural_column', 'walls']:
            categories[key] = self.config.get(key, {})
        return categories