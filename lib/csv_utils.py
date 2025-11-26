# -*- coding: UTF-8 -*-

# CSV utility class
import csv
import os

class csvUtils():
    def __init__(self, lstData, filepath):
        self.lstData = lstData
        self.filepath = filepath

    def csvUtils_import(self, wsName=None, col=0, row=0):
        if not os.path.exists(self.filepath):
            return [[], False]

        try:
            dataOut = []
            with open(self.filepath, 'r') as f:
                reader = csv.reader(f)
                row_count = 0
                for row_data in reader:
                    if row == 0 or row_count < row:
                        if col == 0:
                            dataOut.append(row_data)
                        else:
                            dataOut.append(row_data[:col])
                        row_count += 1
                    else:
                        break
            return [dataOut, True]
        except Exception as e:
            print("CSV Read Error: " + str(e))
            return [[], False]