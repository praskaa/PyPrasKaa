# -*- coding: utf-8 -*-
"""
CSV Processor
This module handles reading, parsing, and validating CSV files based on
the selected profile configuration.
"""

import csv

class CSVProcessor:
    """
    A class to process and validate CSV data for family profiles.
    """
    def __init__(self, profile_config):
        """
        Initializes the CSVProcessor with a specific profile configuration.
        
        Args:
            profile_config (dict): The configuration dictionary for a specific profile type.
        """
        self.config = profile_config
        self.data = []
        self.errors = []

    def read_and_validate(self, file_path):
        """
        Reads and validates the CSV file.
        
        Args:
            file_path (str): The path to the CSV file.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                if not self._validate_header(header):
                    return False
                
                for i, row in enumerate(reader):
                    if not row: continue # Skip empty rows
                    self._validate_row(row, i + 2) # +2 for header and 1-based index
            
            return not self.errors

        except IOError as e:
            self.errors.append("Error reading file: {}".format(e))
            return False
        except Exception as e:
            self.errors.append("An unexpected error occurred during CSV processing: {}".format(e))
            return False

    def _validate_header(self, header):
        """Validates the CSV header."""
        expected_headers = self.config['csv_headers']
        if header != expected_headers:
            self.errors.append(
                "CSV header mismatch.\nExpected: {}\nFound: {}".format(
                    ', '.join(expected_headers), ', '.join(header)
                )
            )
            return False
        return True

    def _validate_row(self, row, line_number):
        """Validates a single row of data."""
        expected_col_count = len(self.config['csv_headers'])
        if len(row) != expected_col_count:
            self.errors.append("Line {}: Incorrect number of columns. Expected {}, found {}.".format(line_number, expected_col_count, len(row)))
            return

        profile_data = {}
        for i, header in enumerate(self.config['csv_headers']):
            value = row[i]
            # Basic validation: check if required fields are not empty
            if header in self.config['required_headers'] and not value.strip():
                self.errors.append("Line {}: Required field '{}' is empty.".format(line_number, header))
                continue
            
            # More advanced validation can be added here based on validation_rules
            # For now, we just store the data
            profile_data[header] = value
        
        self.data.append(profile_data)

    def get_data(self):
        """Returns the processed data."""
        return self.data

    def get_errors(self):
        """Returns a list of validation errors."""
        return self.errors