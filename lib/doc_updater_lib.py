#*-* coding:utf-8 *-*
"""
Doc Updater Hook - IUpdater Implementation

This hook tracks changes to Structural Framing elements (beams, columns, etc.)
and automatically updates the 'LastModifiedBy' parameter with user info and timestamp.

NOTE: This is an IUpdater implementation. For pyRevit hooks, import doesn't work
across hook files. Embed this code directly in doc-opened.py and doc-closing.py.

The code below provides:
1. ElementModificationUpdater - IUpdater class
2. register_updater() - Register function
3. unregister_updater() - Unregister function
"""

from datetime import datetime
from Autodesk.Revit.DB import (
    IUpdater,
    UpdaterId,
    UpdaterRegistry,
    BuiltInCategory,
    ElementId,
    ElementCategoryFilter,
    Transaction,
    FilteredElementCollector,
    LogicalOrFilter
)
from pyrevit import script

# Global storage for updater ID (to allow unregistration)
_updater_id = None


# ============================================
# 1. IUpdater Implementation
# ============================================
class ElementModificationUpdater(IUpdater):
    """
    IUpdater that tracks element modifications and updates LastModifiedBy parameter.
    """
    
    def __init__(self, updater_id, doc):
        self.updater_id = updater_id
        self.doc = doc
        self.logger = script.get_logger()
    
    def Execute(self, updater_data):
        """Main execution method - called when tracked elements are modified."""
        doc = updater_data.GetDocument()
        
        # Get modified element IDs
        modified_ids = updater_data.GetModifiedElementIds()
        
        if not modified_ids:
            return
        
        # Define allowed categories
        allowed_cats = [
            ElementId(BuiltInCategory.OST_StructuralFraming),
            ElementId(BuiltInCategory.OST_StructuralColumns),
            ElementId(BuiltInCategory.OST_StructuralFoundation),
        ]
        
        # Collect elements that need updating
        elements_to_update = []
        
        for elem_id in modified_ids:
            elem = doc.GetElement(elem_id)
            
            # Safety check
            if elem is None or elem.Category is None:
                continue
            
            if elem.Category.Id in allowed_cats:
                elements_to_update.append(elem)
        
        if not elements_to_update:
            return
        
        # Perform update within a transaction
        t = Transaction(doc, "Update LastModifiedBy")
        t.Start()
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for elem in elements_to_update:
                try:
                    param = elem.LookupParameter('LastModifiedBy')
                    
                    if param and not param.IsReadOnly:
                        # Get username
                        try:
                            from Autodesk.Revit.DB import WorksharingUtils
                            wti = WorksharingUtils.WorksharingTooltipInfo(doc, elem.Id)
                            username = wti.LastChangedBy if wti.LastChangedBy else "Unknown"
                        except:
                            username = "User"
                        
                        value = "{} (at {})".format(username, timestamp)
                        param.Set(value)
                        
                except Exception as e:
                    self.logger.debug("Error updating element {}: {}".format(elem.Id, str(e)))
            
            t.Commit()
            
        except Exception as e:
            t.RollBack()
            self.logger.error("Transaction failed: {}".format(str(e)))
    
    def GetAdditionalInformation(self):
        return "Automatically updates LastModifiedBy parameter for structural elements"
    
    def GetUpdaterId(self):
        return self.updater_id
    
    def GetUpdaterName(self):
        return "PrasKaa Element Modification Updater"
    
    def GetUpdaterDescription(self):
        return "Updates LastModifiedBy parameter when structural framing elements are modified"


# ============================================
# 2. Registration Function
# ============================================
def register_updater(doc):
    """
    Register the IUpdater with the document.
    Call this from doc-opened.py when document opens.
    """
    global _updater_id
    
    # Create unique UpdaterId
    updater_id = UpdaterId(
        "PrasKaaPyKit",
        "ElementModificationUpdater_v1"
    )
    
    # Create updater instance
    updater = ElementModificationUpdater(updater_id, doc)
    
    try:
        # Register the updater (is_automatic=True means it runs automatically)
        UpdaterRegistry.RegisterUpdater(updater, doc, True)
        
        # Create filters for structural categories
        filter_stframing = ElementCategoryFilter(BuiltInCategory.OST_StructuralFraming)
        filter_structcol = ElementCategoryFilter(BuiltInCategory.OST_StructuralColumns)
        filter_structfound = ElementCategoryFilter(BuiltInCategory.OST_StructuralFoundation)
        
        # Combine filters using Or logic
        combined_filter = LogicalOrFilter([filter_stframing, filter_structcol, filter_structfound])
        
        # Add trigger - use category ElementId as trigger
        # This triggers on any modification to elements in these categories
        trigger_ids = [
            ElementId(BuiltInCategory.OST_StructuralFraming),
            ElementId(BuiltInCategory.OST_StructuralColumns),
            ElementId(BuiltInCategory.OST_StructuralFoundation),
        ]
        
        # Add triggers for each category
        for trigger_id in trigger_ids:
            UpdaterRegistry.AddTrigger(updater.GetUpdaterId(), trigger_id, combined_filter)
        
        # Store updater ID for unregistration
        _updater_id = updater_id
        
        # Log success
        logger = script.get_logger()
        logger.info("ElementModificationUpdater registered successfully")
        
        return updater_id
        
    except Exception as e:
        logger = script.get_logger()
        logger.error("Failed to register updater: {}".format(str(e)))
        return None


def unregister_updater(doc):
    """
    Unregister the IUpdater from the document.
    Call this from doc-closing.py when document closes.
    """
    global _updater_id
    
    if _updater_id is None:
        return
    
    try:
        UpdaterRegistry.UnregisterUpdater(_updater_id, doc)
        _updater_id = None
        
        logger = script.get_logger()
        logger.info("ElementModificationUpdater unregistered successfully")
        
    except Exception as e:
        logger = script.get_logger()
        logger.error("Failed to unregister updater: {}".format(str(e)))
