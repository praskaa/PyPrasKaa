"""
pyRevit Script Template - IronPython Compatible
Safe template for pyRevit scripts that avoids common compatibility issues
"""

__title__ = "Your Script\nTitle"
__author__ = "Your Name"
__doc__ = "Description of what this script does"

# ========================================
# IMPORTS - Follow this exact order
# ========================================
import clr
import sys
import os

# Add .NET references BEFORE importing modules
clr.AddReference('System.Windows.Forms')  # For UI dialogs
clr.AddReference('RevitAPI') 
clr.AddReference('RevitAPIUI')

# Import after adding references
from System.Windows.Forms import MessageBox, SaveFileDialog, OpenFileDialog, DialogResult
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

# Get document using pyRevit method
from pyrevit import revit
doc = revit.doc
uidoc = revit.uidoc

# ========================================
# COMMON COMPATIBILITY RULES
# ========================================

def safe_string_format(template, *args, **kwargs):
    """
    Use this instead of f-strings for IronPython compatibility
    Example: safe_string_format("Hello {0}, you have {1} items", name, count)
    """
    return template.format(*args, **kwargs)

def safe_file_write(file_path, content):
    """
    Safe file writing for IronPython
    Avoids encoding and newline issues
    """
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        MessageBox.Show("Error writing file: {}".format(str(e)), "File Error")
        return False

def safe_csv_write(file_path, headers, rows, delimiter=';'):
    """
    Manual CSV writing for IronPython compatibility
    Avoids csv module issues
    """
    try:
        with open(file_path, 'w') as f:
            # Write header
            f.write(delimiter.join(headers) + '\n')
            
            # Write rows
            for row in rows:
                f.write(delimiter.join([str(cell) for cell in row]) + '\n')
        return True
    except Exception as e:
        MessageBox.Show("Error writing CSV: {}".format(str(e)), "CSV Error")
        return False

def get_desktop_path():
    """Get desktop path safely across different Windows versions"""
    try:
        return os.path.join(os.path.expanduser('~'), 'Desktop')
    except:
        return os.path.expanduser('~')

def show_file_dialog(title="Select File", filter_str="All files (*.*)|*.*", save_mode=True):
    """
    Standardized file dialog that works consistently
    """
    try:
        if save_mode:
            dialog = SaveFileDialog()
        else:
            dialog = OpenFileDialog()
            
        dialog.Title = title
        dialog.Filter = filter_str
        dialog.InitialDirectory = get_desktop_path()
        dialog.RestoreDirectory = True
        
        if dialog.ShowDialog() == DialogResult.OK:
            return dialog.FileName
        return None
    except Exception as e:
        MessageBox.Show("Dialog error: {}".format(str(e)), "Error")
        return None

# ========================================
# YOUR MAIN FUNCTION GOES HERE
# ========================================

def main():
    """Main script function"""
    try:
        # Your script logic here
        MessageBox.Show("Script template loaded successfully!", "Success")
        
        # Example: Get all view templates
        collector = FilteredElementCollector(doc).OfClass(View)
        templates = [view for view in collector if view.IsTemplate]
        
        MessageBox.Show(
            safe_string_format("Found {0} view templates", len(templates)),
            "Template Count"
        )
        
    except Exception as e:
        MessageBox.Show(
            safe_string_format("Script error: {0}", str(e)), 
            "Error"
        )

# ========================================
# SCRIPT EXECUTION
# ========================================
if __name__ == '__main__':
    main()
