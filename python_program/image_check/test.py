import glob
import os
import sys
import datetime
import numpy as np
import pandas as pd

def find_consecutive_ranges(lst):
    if not lst:
        return []
    
    ranges = []
    start = lst[0]
    
    for i in range(1, len(lst)):
        if lst[i] != lst[i - 1] + 1:
            ranges.append([start, lst[i - 1]])
            start = lst[i]
    
    ranges.append([start, lst[-1]])  # Append the last range
    
    return ranges

output_IM_folder_path = "./optical/"
report_path = "./report/"
os.makedirs(output_IM_folder_path,exist_ok=True)
os.makedirs(report_path,exist_ok=True)
files = glob.glob('./raw_data/*.bin')
files.sort()
if len(sys.argv)<2:
    file_name = files[-1]
else:
    file_name = f'./raw_data/{sys.argv[1]}'
    
print(f'Raw data file: {file_name}')