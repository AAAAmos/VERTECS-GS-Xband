'''
This script reads the raw data, checks completeness of the data, and the data quality.
------Parameters------
1. file_name: the name of the raw data file to be checked. If no input, the last file in the raw_data folder will be checked.
2. mode: "detail" or no input for normal mode
------Output------
1. If mode is "detail", the script will output a txt file that contains the header information of the packets.
2. If mode is "normal", the script will write the report to the last report file (.csv) in the report folder.:
    - If there is no missing image packets, the script will save the image data to the optical folder.
    - If there are missing image packets, the script will save the incomplete image data to the tmp folder.
'''

import glob
import os
import sys
import datetime
import numpy as np
import pandas as pd

def find_consecutive_ranges(lst):
    
    '''
    Find the consecutive ranges in a list of integers.
    Input:
        lst: a list of integers
    Output:
        ranges: a list of lists, each sublist contains the start and end of a consecutive range
    '''
    
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
# get the file name to be checked
files = glob.glob('./raw_data/*.bin')
files.sort()
if len(sys.argv)<2:
    file_name = files[-1]
else:
    file_name = f'./raw_data/{sys.argv[1]}'
    
reports = glob.glob('./report/*.csv')
reports.sort()

# read the raw data, split the data into packets using sync bytes
with open(file_name, 'rb') as f:
    mpduPackets = f.read().split(b'\x1A\xCF\xFC\x1D')[1:]

if (len(sys.argv)>2) and (sys.argv[2] == "detail"):
    # output file that contains the header information of the packets
    # fout_name = f'./DQ_check/{'/'.join(file_name.split('/')[2:])}'
    fout_name = f'./{file_name.split('/')[-1]}'
    fout_name = fout_name.replace('.bin', '_header.txt')
    print(f'Detail output: {fout_name}')
    fout = open(fout_name, 'w')
else:
    dt_now = datetime.datetime.now()
    time_now = dt_now.strftime('%d_%H%M%S')
    print(f'Raw data file: {file_name}')
    if len(reports) == 0:
        print('No report file found, create a new one.')
        fout_name = f'{report_path}report_0000_{time_now}.csv'
        with open(fout_name, 'w') as f:
            f.write('Filename,Type,Start_Packet_number,End_Packet_number,Incompleteness(100*missing/16621)\n')
    else:
        fout_name = reports[-1]
        if os.path.getsize(fout_name) > 10000:
            print('The last report file is too large, create a new one.')
            fout_name = f'{report_path}report_{str(len(reports)).zfill(4)}_{time_now}.csv'
            with open(fout_name, 'w') as f:
                f.write('Filename,Type,Start_Packet_number,End_Packet_number,Incompleteness(100*missing/16621)\n')
        else:
            print(f'Write to the last report file: {fout_name}')
            
headers = [[], [], [], []]
hk = []

# loop through all the packets
if (len(sys.argv)>2) and (sys.argv[2] == "detail"):
    for k, packet in enumerate(mpduPackets):
        # classify the packets by the VCDU header
        if packet[28:30] == b'\x55\x40':
            headers[0].append('IM')
        elif packet[28:30] == b'\x40\x3F':
            headers[0].append('HK')
            hk.append(packet.hex())
        else:
            headers[0].append('UnClassified')
        
        headers[1].append(int.from_bytes(packet[30:33], 'big'))
        headers[2].append(packet[34])
        headers[3].append(packet[1])
        fout.write(
            f'{headers[0][-1]}, {headers[1][-1]}, {headers[2][-1]}, {headers[3][-1]}\n'
        )
    fout.write(f'Number of Packets: {len(mpduPackets)}\n')
    fout.close()
else:
    for k, packet in enumerate(mpduPackets):
        # classify the packets by the VCDU header
        if packet[28:30] == b'\x55\x40':
            headers[0].append('IM')
        elif packet[28:30] == b'\x40\x3F':
            headers[0].append('HK')
            hk.append(packet.hex())
        else:
            headers[0].append('UnClassified')
        
        headers[1].append(int.from_bytes(packet[30:33], 'big'))
        headers[2].append(packet[34])
        headers[3].append(packet[1])
        # *** save hk data somewhere ***

try:
    headerDF = pd.DataFrame(np.array(headers).T, columns=['VCDU', 'PSC', 'IB', 'DQ'])
    IM, HK = headerDF[headerDF['VCDU'] == 'IM']['PSC'].astype(int), headerDF[headerDF['VCDU'] == 'HK']['PSC'].astype(int)
    bad_IM, bad_HK = headerDF[headerDF['DQ'] != '0']['PSC'].astype(int), headerDF[headerDF['DQ'] != '0']['PSC'].astype(int)
    IM_range = set(range(0, 16620))
    max_HK = HK[HK < 10000].max()
    HK_range = set(range(int(min(HK)), int(max_HK)+1))
    missing_IM = IM_range - set(IM)
    missing_HK = HK_range - set(HK)
    missing_IM = sorted(list(missing_IM))
    missing_HK = sorted(list(missing_HK))
    # request_IM = set(IM) | set(bad_IM)
    # request_HK = set(HK) | set(bad_HK)
    missing_rate_IM = (len(missing_IM)/16621)*100
    missing_segment_IM = find_consecutive_ranges(list(missing_IM))
    missing_segment_HK = find_consecutive_ranges(list(missing_HK))
    
    if (len(sys.argv)>2) and (sys.argv[2] == "detail"):
        fout = open(fout_name, 'a')
        fout.write(f'Total Image Packets: {headerDF[headerDF['VCDU'] == 'IM'].shape[0]}\n')
        fout.write(f'UnClassified Packets: {headerDF[headerDF['VCDU'] == 'UnClassified'].shape[0]}\n')
        fout.write(f'Sequence number of Missing Image Packets: {missing_IM}\n')
        fout.write(f'Number of Missing Image Packets: {len(missing_IM)}\n')
        fout.write(f'Sequence number of Missing HK Packets: {missing_HK}\n')
        fout.write(f'Number of bad quality Image Packets: {len(bad_IM)}\n')
        fout.write(f'Number of Missing HK Packets: {len(missing_HK)}\n')
        fout.write(f'Number of bad quality HK Packets: {len(bad_HK)}\n')
        fout.write(f'Total missing packets: {len(missing_IM)+len(missing_HK)}\n')
        fout.write(f'Segment of request image packets: {missing_segment_IM}\n')
        fout.write(f'Segment of request HK packets: {missing_segment_HK}\n')
        fout.write(f'Request image packets rate (missing image/Image packet %): {missing_rate_IM}\n')
        fout.close()

    else:
        nfiles = len(glob.glob(output_IM_folder_path+'*.bin'))
        nfiles = str(nfiles).zfill(4)
        imgData = bytes()
        
        if missing_rate_IM == 0:
            for k, packet in enumerate(mpduPackets):
                if packet[28:30] == b'\x55\x40':
                    imgData += packet[56:-160]
            imgData = imgData.rstrip(b'\0')
            # no missing packets, save the image data
            with open(f'./optical/opt_frame_{nfiles}_{file_name.split('/')[-1]}', 'wb') as f:
                f.write(imgData)
            # output the report
            with open(fout_name, 'a') as f:
                f.write(f'{file_name.split('/')[-1]},IM,0,0,0\n')
        else:
            # remove the bad quality image packets, and store the incomplete image packets
            for k, packet in enumerate(mpduPackets):
                if packet[28:30] == b'\x55\x40':
                    # check data quality
                    if packet[1] != '0':
                        continue
                    imgData += packet[56:-160]
            imgData = imgData.rstrip(b'\0')
            # save the incomplete image data
            with open(f'./tmp/opt_frame_{nfiles}_{file_name.split('/')[-1]}', 'wb') as f:
                f.write(imgData)
            # output the report for the missing packets
            with open(fout_name, 'a') as f:
                for segment in missing_segment_IM:
                    f.write(f'{file_name.split('/')[-1]},IM,{segment[0]},{segment[1]},{missing_rate_IM}\n')
                for segment in missing_segment_HK:
                    f.write(f'{file_name.split('/')[-1]},HK,{segment[0]},{segment[1]},-1\n')

except Exception as e:
    # report for unreadable files
    with open(fout_name, 'a') as f:
        f.write(f'{file_name.split('/')[-1]},Error,-1,-1,-1\n')
    # print(f'Error in {file_name}: {e}')