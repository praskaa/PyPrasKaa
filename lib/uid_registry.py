# -*- coding: utf-8 -*-
"""
UID Registry Management for GIS Element UID System.

Provides database operations for tracking ElementID → UID mapping.

Usage:
    from uid_registry import (
        get_database_path,
        load_registry,
        save_registry,
        generate_uid
    )
"""

import os
import csv
import uuid
from datetime import datetime

from Autodesk.Revit.DB import FilteredElementCollector


# Database folder path
DB_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaaPyKit", "UID_Registry")


def get_database_path(doc):
    """Get database file path for current project."""
    project_name = doc.ProjectInformation.Name if doc.ProjectInformation.Name else "Unnamed"
    safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '_', '-')).strip()
    return os.path.join(DB_FOLDER, "{}_UID_Registry.csv".format(safe_name))


def load_registry(db_path):
    """
    Load existing registry from CSV.
    
    Returns:
        dict: {ElementId: row_dict}
    """
    registry = {}
    if os.path.exists(db_path):
        with open(db_path, 'rb') as f:
            for row in csv.DictReader(f):
                try:
                    registry[int(row['ElementId'])] = row
                except:
                    pass
    return registry


def save_registry(db_path, rows):
    """
    Save registry to CSV.
    
    Args:
        db_path: Path to CSV file
        rows: List of row dictionaries
    """
    folder = os.path.dirname(db_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
    fieldnames = ['ElementId', 'GIS_Element_UID', 'Mark', 'Category',
                  'TypeName', 'FamilyName', 'Status', 'Created', 'Modified']
    with open(db_path, 'wb') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_all_model_uids(doc, GIS_CATEGORIES, PARAM_NAME):
    """
    Get all UIDs currently in model.
    
    Returns:
        set: All UID values found in model
    """
    uids = set()
    for cat_enum, _ in GIS_CATEGORIES.values():
        for el in FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType():
            p = el.LookupParameter(PARAM_NAME)
            if p and p.AsString():
                uids.add(p.AsString())
    return uids


def generate_uid(prefix, used_uids):
    """
    Generate unique UID.
    
    Args:
        prefix: UID prefix (e.g., 'WALL', 'BEAM')
        used_uids: Set of already-used UIDs to avoid duplicates
        
    Returns:
        str: New unique UID
    """
    while True:
        uid = "{}-{}".format(prefix, str(uuid.uuid4()).split('-')[0])
        if uid not in used_uids:
            return uid
