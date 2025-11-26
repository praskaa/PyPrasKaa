#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import Testing Script for PrasKaaPyKit
Test critical imports to ensure architecture compliance

Usage:
    python test_imports.py
    # or run from pyRevit console
"""

import sys
import os

def test_import(module_path, function_name=None, description=""):
    """
    Test if import works correctly.

    Args:
        module_path (str): Module path to test
        function_name (str, optional): Specific function to test
        description (str): Description of what this import does

    Returns:
        bool: True if import successful, False otherwise
    """
    try:
        module = __import__(module_path, fromlist=[function_name] if function_name else [])
        if function_name:
            func = getattr(module, function_name)
            print(f"✅ {module_path}.{function_name} - OK")
            if description:
                print(f"   {description}")
            return True
        else:
            print(f"✅ {module_path} - OK")
            if description:
                print(f"   {description}")
            return True
    except ImportError as e:
        print(f"❌ {module_path} - FAILED: {e}")
        if function_name:
            print(f"   Expected function: {function_name}")
        return False
    except Exception as e:
        print(f"⚠️  {module_path} - ERROR: {e}")
        return False

def main():
    """Main testing function"""
    print("=" * 60)
    print("🧪 PrasKaaPyKit Import Testing")
    print("=" * 60)
    print()

    # Add current directory to path for testing
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Test critical imports
    tests = [
        # Core lib imports
        ('Snippets.smart_selection', 'get_filtered_selection', 'Smart element selection utility'),
        ('wall_orientation_logic', 'WallOrientationHandler', 'Wall orientation detection'),
        ('parameters.framework', 'find_parameter_element', 'Parameter finding utilities'),
        ('graphicOverrides', 'setProjLines', 'Graphic override utilities'),

        # Snippets utilities
        ('Snippets._selection', 'get_selected_elements', 'Basic selection utilities'),
        ('Snippets._convert', None, 'Unit conversion utilities'),

        # Parameter utilities
        ('parameters.validators', None, 'Parameter validation'),
        ('parameters.framework', None, 'Parameter framework'),

        # UI utilities
        ('ui.base_window', None, 'Base WPF window classes'),
        ('ui.ui_utils', None, 'UI utility functions'),
    ]

    print("Testing Core Library Imports...")
    print("-" * 40)

    passed = 0
    total = len(tests)

    for module, func, desc in tests:
        if test_import(module, func, desc):
            passed += 1
        print()

    print("=" * 60)
    print(f"📊 RESULTS: {passed}/{total} imports working")

    if passed == total:
        print("🎉 All imports successful! Architecture is compliant.")
    else:
        print("⚠️  Some imports failed. Check architecture compliance.")
        print("   - Ensure files are in lib/ folder")
        print("   - Check __init__.py files exist")
        print("   - Verify import paths are correct")

    print()
    print("🔍 For debugging:")
    print("   - Check lib/ folder structure")
    print("   - Verify __init__.py files")
    print("   - Read IMPORT_GUIDELINES.md")
    print("   - Check ARCHITECTURE_GUIDE.md")
    print("=" * 60)

    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)