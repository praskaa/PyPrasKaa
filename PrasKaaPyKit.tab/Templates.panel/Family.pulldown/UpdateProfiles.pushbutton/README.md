# Family Profile Updater

## Overview

The **Family Profile Updater** is a powerful pyRevit tool designed to streamline the process of creating and updating multiple family types within a Revit family document using a CSV file. It features a user-friendly interface that allows for dynamic mapping between CSV columns and Revit family parameters, eliminating the need for hardcoded configurations.

This tool is ideal for BIM managers, content creators, and Revit users who need to manage large sets of family types efficiently and accurately.

## Features

- **Batch Creation/Update**: Process hundreds of family types from a single CSV file in one operation.
- **Dynamic Parameter Mapping**: An interactive utility maps your CSV column headers to the corresponding parameters in your Revit family, providing full flexibility.
- **Intelligent Mapping Suggestions**: The tool automatically suggests parameter mappings based on name similarity, speeding up the setup process.
- **Persistent Mappings**: Your parameter mappings are saved to a `parameter_mappings.json` file, so you only need to set them up once per CSV structure.
- **Unit Handling**: Automatically converts numeric values from millimeters in the CSV to the required internal units in Revit.
- **Error Reporting**: Provides a clear summary of successful and failed operations, with detailed console messages for easy troubleshooting.
- **IronPython Compatible**: Fully compatible with the IronPython environment used by pyRevit.

## How to Use

### Step 1: Prepare Your CSV File

Create a CSV file with the data for the family types you want to create.

- The first row must contain the column headers.
- One column must be named `Name` (case-sensitive) and contain the desired name for each family type.
- Other columns should contain the parameter values you want to set (e.g., `Width`, `Height`, `Thickness`). The names of these columns can be anything, as you will map them in the next step.
- All numeric parameter values should be in **millimeters (mm)**.

**Example CSV (`profiles.csv`):**

```csv
Name,Section_Width,Section_Height,Web_Thickness
L50x50x5,50,50,5
L60x60x6,60,60,6
L75x75x8,75,75,8
```

### Step 2: Open the Revit Family Document

Open the Revit family file (`.rfa`) where you want to create the new types. This tool is designed to be run from within a family document.

### Step 3: Run the Tool

1. In Revit, navigate to the **PrasKaaPyKit** tab.
2. In the **Family Tools** panel, click on the **Update Profiles** button.

### Step 4: Select the CSV File

A file dialog will appear. Locate and select the CSV file you prepared in Step 1.

### Step 5: Map Parameters (First-Time Setup)

If this is the first time you are using a CSV with this specific set of column headers, the **Parameter Mapper** will launch automatically.

1.  **Review Suggestions**: The tool will analyze your CSV headers and the parameters in your Revit family. If it finds a likely match, it will suggest it.
    -   Press `y` and `Enter` to accept a suggestion.
    -   Press `n` and `Enter` to reject it and map it manually.
    -   Press `q` and `Enter` to quit the mapping process.

2.  **Manual Mapping**: If no suggestion is made or you reject one, you will be prompted to select a parameter from a numbered list of all available family parameters.
    -   Enter the number corresponding to the correct Revit parameter and press `Enter`.
    -   Enter `s` to skip mapping for the current CSV column.
    -   Enter `q` to quit.

3.  **Mappings Saved**: Once you complete the process, your mappings will be saved in a `parameter_mappings.json` file in the same directory as the script. The next time you run the tool with a CSV file that has the same headers, it will use these saved mappings automatically.

### Step 6: Processing

The tool will begin processing the CSV file row by row.

- A transaction is used to create all family types, ensuring that the operation is efficient.
- The console will print real-time feedback, indicating which types were created successfully (`✅`) and which failed (`❌`), along with the reason for any failures.

### Step 7: Review the Summary

Once processing is complete, a summary dialog will appear showing:
- Total types processed.
- Number of successful creations.
- Number of errors.
- The overall success rate.

## Managing Mappings

The parameter mappings are stored in a `parameter_mappings.json` file located in the same directory as the tool script:
```
PrasKaaPyPyKit.tab\Family Tools.panel\UpdateProfiles.pushbutton\parameter_mappings.json
```

If you need to reset the mappings (for instance, if you've changed your CSV headers or made a mistake), simply delete this file. The tool will then prompt you to create new mappings the next time it is run.