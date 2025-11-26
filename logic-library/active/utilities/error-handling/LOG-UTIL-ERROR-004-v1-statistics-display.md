---
id: "LOG-UTIL-ERROR-004"
version: "v1"
status: "active"
category: "utilities/error-handling"
element_type: "UserFeedback"
operation: "display"
revit_versions: [2024, 2026]
tags: ["ui", "feedback", "statistics", "performance", "summary"]
created: "2025-10-10"
updated: "2025-10-10"
confidence: "high"
performance: "fast"
source_file: "PrasKaaPyKit.tab/Helper.panel/SmartTag.pushbutton/script.py"
source_location: "Helper.panel/SmartTag.pushbutton"
---

# LOG-UTIL-ERROR-004-v1: Operation Statistics and Summary Display

## Problem Context

Long-running operations in Revit need to provide users with feedback about what was accomplished, any errors that occurred, and performance metrics. Without proper summary displays, users don't know if operations completed successfully or how long they took.

## Solution Summary

This pattern collects operation statistics during execution, tracks timing information, and displays a comprehensive summary dialog showing results, errors, and performance metrics. It handles both successful operations and error conditions gracefully.

## Working Code

```python
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon
import time

class OperationStatistics:
    """Class to track operation statistics"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.framing = 0
        self.columns = 0
        self.walls = 0
        self.errors = []
        self.start_time = None
        self.end_time = None

    def start_operation(self):
        """Mark the start of operation"""
        self.start_time = time.time()

    def end_operation(self):
        """Mark the end of operation"""
        self.end_time = time.time()

    def add_error(self, error_message):
        """Add an error message"""
        self.errors.append(str(error_message))

    def get_duration(self):
        """Get operation duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def get_total_processed(self):
        """Get total items processed"""
        return self.framing + self.columns + self.walls

def show_operation_summary(stats, operation_count, operation_name="Operation"):
    """Display comprehensive operation summary"""
    duration = stats.get_duration()
    total_processed = stats.get_total_processed()

    # Build summary message
    message = "{} Complete!\n\n".format(operation_name)
    message += "Total Items Processed: {}\n".format(operation_count)
    message += "Duration: {:.2f} seconds\n\n".format(duration)

    if hasattr(stats, 'framing') and stats.framing > 0:
        message += "Structural Framing: {} processed\n".format(stats.framing)
    if hasattr(stats, 'columns') and stats.columns > 0:
        message += "Structural Columns: {} processed\n".format(stats.columns)
    if hasattr(stats, 'walls') and stats.walls > 0:
        message += "Walls: {} processed\n".format(stats.walls)

    message += "Total Elements: {}\n".format(total_processed)

    # Add performance info
    if operation_count > 0:
        avg_time = duration / operation_count
        message += "Average time per item: {:.3f}s\n".format(avg_time)

    # Add error information
    if stats.errors:
        message += "\nWarnings/Errors: {} found".format(len(stats.errors))
        message += "\n(Check output window for details)"

    # Determine icon based on results
    icon = MessageBoxIcon.Information
    if stats.errors:
        icon = MessageBoxIcon.Warning
    if total_processed == 0 and not stats.errors:
        icon = MessageBoxIcon.Exclamation

    # Show dialog
    MessageBox.Show(
        message,
        "{} - Summary".format(operation_name),
        MessageBoxButtons.OK,
        icon
    )

    # Print detailed errors to console
    if stats.errors:
        print("\n=== ERRORS/WARNINGS ===")
        for i, error in enumerate(stats.errors, 1):
            print("{}. {}".format(i, error))

def execute_with_statistics(operation_func, *args, **kwargs):
    """Execute operation with automatic statistics collection"""
    stats = OperationStatistics()
    stats.start_operation()

    try:
        # Execute the operation
        result = operation_func(stats, *args, **kwargs)
        stats.end_operation()

        # Show summary
        show_operation_summary(stats, 1, "Operation")

        return result

    except Exception as e:
        stats.end_operation()
        stats.add_error("Operation failed: {}".format(str(e)))

        # Show error summary
        show_operation_summary(stats, 1, "Operation")

        raise  # Re-raise the exception
```

## Key Techniques

1. **Statistics Collection**: Dedicated class to track multiple metrics during operation
2. **Timing Measurement**: Precise timing using `time.time()` for performance metrics
3. **Error Accumulation**: Collect multiple errors without stopping execution
4. **Comprehensive Display**: Single dialog showing all relevant information
5. **Console Logging**: Detailed error output to Revit output window

## Revit API Compatibility

- **Windows Forms**: Uses `MessageBox` for user feedback
- **No Revit API Dependencies**: Pure UI/statistics pattern
- **Console Output**: Uses standard `print()` for detailed logs

## Performance Notes

- **Execution Time**: Instant display, minimal overhead
- **Memory Usage**: Low - stores error strings and counters
- **Scalability**: Handles large error lists efficiently

## Usage Examples

### Basic Operation with Statistics
```python
def process_elements():
    stats = OperationStatistics()
    stats.start_operation()

    try:
        # Process elements
        for element in elements:
            try:
                process_single_element(element)
                stats.framing += 1  # or appropriate counter
            except Exception as e:
                stats.add_error("Failed to process {}: {}".format(element.Name, str(e)))

        stats.end_operation()

        # Show summary
        show_operation_summary(stats, len(elements), "Element Processing")

    except Exception as e:
        stats.end_operation()
        stats.add_error("Critical error: {}".format(str(e)))
        show_operation_summary(stats, len(elements), "Element Processing")
        raise
```

### Batch Operation Timing
```python
def process_multiple_views(views):
    stats = OperationStatistics()
    total_time = 0

    for i, view in enumerate(views):
        view_start = time.time()

        try:
            process_view(view, stats)
        except Exception as e:
            stats.add_error("View {}: {}".format(view.Name, str(e)))

        view_time = time.time() - view_start
        total_time += view_time
        print("View {}: {:.2f}s".format(view.Name, view_time))

    # Show performance summary
    if views:
        avg_time = total_time / len(views)
        print("Average time per view: {:.2f}s".format(avg_time))

    show_operation_summary(stats, len(views), "Batch View Processing")
```

### Integration with Progress Tracking
```python
def execute_with_progress_feedback(items, process_func):
    stats = OperationStatistics()
    stats.start_operation()

    for i, item in enumerate(items):
        try:
            process_func(item)
            # Update appropriate counter
            stats.framing += 1
        except Exception as e:
            stats.add_error(str(e))

        # Optional: show progress
        if (i + 1) % 10 == 0:
            print("Processed {}/{}".format(i + 1, len(items)))

    stats.end_operation()
    show_operation_summary(stats, len(items), "Batch Processing")
```

## Common Pitfalls

1. **Exception Handling**: Always wrap operations in try-catch for error collection
2. **Timing Accuracy**: Call `start_operation()` and `end_operation()` at correct points
3. **Counter Updates**: Update appropriate counters (framing, columns, walls) based on element type
4. **Error Messages**: Provide meaningful error messages with context

## Related Logic Entries

- [LOG-UTIL-ERROR-001-v1-graceful-api-failures](LOG-UTIL-ERROR-001-v1-graceful-api-failures.md) - Error handling patterns
- [LOG-UTIL-ERROR-002-v1-user-friendly-messages](LOG-UTIL-ERROR-002-v1-user-friendly-messages.md) - User messaging

## Optimization History

*This is the initial version (v1) with no optimizations yet.*