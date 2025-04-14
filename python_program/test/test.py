import time 
import datetime
import os 
import subprocess
import glob
import sys

import numpy as np
import pandas as pd
import binascii
import csv
from astropy.io import fits

import psutil
def print_memory():
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 * 1024)  # Memory in MB
    print(f"[Memory] {mem:.2f} MB")

log_folder = "./log/"
os.makedirs(log_folder, exist_ok=True)
os.makedirs("./test_fold/", exist_ok=True)

time_now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
nfiles = len(glob.glob(log_folder + "*.log"))
log_file = log_folder + f"log_{nfiles}_{time_now}.log"
# print(os.getcwd())
# os.system("touch ./log/log_test2.txt")
with open('./log/log_test3.log', "a"):
    pass

# print(os.getuid())
# os.system(f"touch {log_file}")
print(len(glob.glob(log_folder + "*.log")))
os.system('rm ./log/log_test3.log')

# result = subprocess.run(['touch', 'file_test'], capture_output=True, text=True)
# print("stdout:", result.stdout)
# print("stderr:", result.stderr)
# print("return code:", result.returncode)


print_memory()

try:
    result = subprocess.run(['touch', './log/file_test_subpro'], check=True)
    print_memory()
    print("Touch succeeded.")
except subprocess.CalledProcessError as e:
    print("Touch failed:", e)