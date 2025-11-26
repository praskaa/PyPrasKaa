# -*- coding: utf-8 -*-
"""
Profile Configurations
This file contains the configuration data for each supported profile type.
The configuration includes display name, CSV headers, parameter mappings,
validation rules, and other metadata.
"""

PROFILE_CONFIGS = {
    "ANGLE": {
        "display_name": "Angle Profile (L Siku)",
        "description": "Equal and unequal angle structural sections.",
        "csv_headers": ["Name", "H", "B", "t", "r1", "r2", "A", "WEIGHT"],
        "required_headers": ["Name", "H", "B", "t"],
        "optional_headers": ["r1", "r2", "A", "WEIGHT"],
        "parameter_mapping": {
            "H": {"revit_param": "d", "type": "length", "unit_conversion": True},
            "B": {"revit_param": "b", "type": "length", "unit_conversion": True},
            "t": {"revit_param": "t", "type": "length", "unit_conversion": True},
            "r1": {"revit_param": "r1", "type": "length", "unit_conversion": True},
            "r2": {"revit_param": "r2", "type": "length", "unit_conversion": True},
            "A": {"revit_param": "A", "type": "area", "unit_conversion": False},
            "WEIGHT": {"revit_param": "W", "type": "number", "unit_conversion": False}
        },
        "validation_rules": {
            "H": {"min": 20, "max": 300, "type": "float"},
            "B": {"min": 20, "max": 300, "type": "float"},
            "t": {"min": 3, "max": 35, "type": "float"},
            "r1": {"min": 2, "max": 24, "type": "float"},
            "r2": {"min": 2, "max": 24, "type": "float"},
            "A": {"min": 1, "max": 200, "type": "float"},
            "WEIGHT": {"min": 0.5, "max": 200, "type": "float"}
        },
        "sample_data": "L50x50x5,50,50,5,6.5,3,4.802,3.77",
        "template_file": "Angle_template.csv"
    },
    # --- Add other profile configurations below ---
    # "RHS": { ... },
    # "C-CHANNEL": { ... },
}