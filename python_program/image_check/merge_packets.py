'''
This script is used to read the re-downloaded missing packets (MP) and merge them with the original raw data (OP).
It reads the MP files, identifies which OPs they belong to, and merges them with the OPs.
The output will be the image data (opt_frame_n_Fname.bin).
'''

import glob
import sys
import os
import numpy as np
import pandas as pd

