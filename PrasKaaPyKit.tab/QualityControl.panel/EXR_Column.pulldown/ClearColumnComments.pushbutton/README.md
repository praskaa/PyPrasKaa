# Clear Column Comments

## Overview
This script removes all comment parameters that were set by the Check Column Dimensions script. It clears the following comment values: "Approved", "Dimension to be checked", "Unmatched".

## Process
1. Collect all structural column elements from the host model
2. Check each column's comment parameter
3. Clear comments that match the validation results
4. Report how many comments were cleared

## Requirements
- Revit environment with pyRevit extension
- Host model with structural column elements

## Comments Cleared
The script specifically clears these exact comment values:
- "Approved"
- "Dimension to be checked"
- "Unmatched"

## Usage
1. Run the script from the pyRevit toolbar
2. Wait for processing to complete
3. Comments will be cleared from all columns

## Safety Features
- Only clears comments that exactly match the validation script's output
- Safe to run multiple times - will only clear matching comments
- Does not affect other comment values that may be set by other scripts

## Related Scripts
- **Check Column Dimensions**: Sets validation comments on columns
- **Matching Column**: Transfers column types based on geometry intersection

## Troubleshooting
- **No columns found**: Ensure you have structural columns in the model
- **No comments cleared**: Columns may not have validation comments set, or comments may have different text