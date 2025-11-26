# CAD Line Styles Manager - UI Improvement Plan

## Current Pain Points
1. **Checkbox Selection**: Users must manually click checkboxes for each layer, which is unintuitive
2. **Broken Batch Selection**: Shift-click selection disappears when dropdown is opened
3. **Non-Standard UI**: Doesn't follow Windows UI conventions for multi-selection
4. **Inefficient Workflow**: Requires two separate actions (select + modify) for each layer

## Proposed Solution: Direct Row Selection

### Key Improvements
1. **Remove Checkbox Column**: Replace checkbox-based selection with native DataGridView row selection
2. **Native Windows Selection**: Implement shift-click, ctrl-click, and standard click behavior
3. **Visual Indicators**: Highlight selected rows with different background color
4. **Preserve Selection**: Ensure dropdown interactions don't clear row selection
5. **Direct Editing**: Allow immediate editing of selected rows without separate selection step

### Technical Implementation Plan

#### 1. Remove Checkbox Column
- Remove `DataGridViewCheckBoxColumn` from columns
- Remove "Select" header and related logic
- Update `EnhancedCadLayer` class to remove `selected` property

#### 2. Enable Native Row Selection
```python
# Set selection mode for multi-row selection
self.data_grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect
self.data_grid.MultiSelect = True
```

#### 3. Add Selection Event Handlers
```python
# Handle selection changes
self.data_grid.SelectionChanged += self.on_selection_changed

# Handle keyboard shortcuts
self.data_grid.KeyDown += self.on_key_down
```

#### 4. Update Batch Editing Logic
```python
def get_selected_layers(self):
    """Get currently selected rows as layers"""
    selected_rows = self.data_grid.SelectedRows
    selected_layers = []
    
    for row in selected_rows:
        if row.Index < len(self.layers):
            selected_layers.append(self.layers[row.Index])
    
    return selected_layers

def on_cell_value_changed(self, sender, e):
    """Apply changes to all selected layers when dropdown value changes"""
    # Get all selected layers
    selected_layers = self.get_selected_layers()
    
    # Apply change to all selected layers (including current)
    for layer in selected_layers:
        if column_name == "NewLW":
            layer.new_line_weight = str(new_value)
        elif column_name == "NewLP":
            layer.new_line_pattern = str(new_value)
```

#### 5. Fix Dropdown Interaction
- Override dropdown close behavior to preserve selection
- Use `CellEnter` event to maintain focus on selected rows
- Prevent selection clearing on dropdown open/close

#### 6. Add Visual Feedback
```python
def on_selection_changed(self, sender, e):
    """Update visual feedback for selected rows"""
    # Highlight selected rows
    # Update status bar showing selection count
    # Enable/disable batch operation buttons based on selection
```

### New User Workflow
1. **Select Layers**: Use shift-click, ctrl-click, or drag to select multiple rows
2. **Direct Editing**: Click dropdown in any selected row to change value
3. **Batch Application**: Changes apply to all selected rows automatically
4. **Apply Changes**: Click "Apply Changes" to commit all modifications

### Benefits
- **Intuitive**: Follows standard Windows selection patterns
- **Efficient**: No separate selection step required
- **Visual**: Clear indication of selected rows
- **Preserved**: Selection maintained during dropdown interaction
- **Flexible**: Supports all standard multi-selection techniques

### Implementation Tasks
1. Remove checkbox column and related properties
2. Implement native DataGridView selection
3. Update batch editing logic to use selected rows
4. Add visual feedback for selection state
5. Fix dropdown interaction to preserve selection
6. Test all selection scenarios (single, multi, shift-click, ctrl-click)
7. Update apply logic to work with new selection model

This approach will provide a much more intuitive and efficient user experience that aligns with Windows UI standards.