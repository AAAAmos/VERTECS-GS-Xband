'''
This script is used to check the data quality of the raw data. 
It reads the latest raw data files and checks for missing/bad quality packets in the data.
There are two modes to run the script: "detail" and "normal".
    1.  The "detail" mode will generate a text file that contains the all the header information of the packets.
    2.  The "normal(default)" mode will output the image data (opt_frame_n_Fname.bin) if there is no missing image packets,
        and append report for the input raw data file to a report.txt file, including:
            rate/numbers/segments of missing packets.
            commnads to request the missing packets.
        The report.txt file will collect at most 8310 missing packets, then will create a new report file.
        Each report file represent a raw data file going to be downlinked from the satellite.
        If the missing rate > 50%, we will request the whole raw data file.
    Just run the script without any arguments will be the "normal" mode.
    Run the script with "detail" as the argument will be the "detail" mode.
** not sure about the fits file's header. 
'''

from tqdm import tqdm
import glob
import sys
import os
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

def make_command(file_name,type,id_start,id_end):
    #F20YYMMDDhhmmss
    YY = int(file_name[3:5] )
    MM = int(file_name[5:7] )
    DD = int(file_name[7:9] )
    hh = int(file_name[9:11] )
    mm = int(file_name[11:13])
    ss = int(file_name[13:15])
    out_date = YY.to_bytes(1,'big')+MM.to_bytes(1,'big')\
        +DD.to_bytes(1,'big')+(ss+60*(mm+60*hh)).to_bytes(3,'big')

    if type == 'HK':
        label=0
        out_name = label.to_bytes(1,'big')
    elif type == 'IMG':
        label=1
        out_name = label.to_bytes(1,'big')
    else:
        print("Unknown label: check HouseKeeping(HK) or Image(IMG)")
        exit()

    out_ids = id_start.to_bytes(2,'big') + id_end.to_bytes(2,'big')

    return out_date + out_name + out_ids

def decode_command(com):
    #F20YYMMDDhhmmss
    YY = str(com[0]).zfill(2)
    MM = str(com[1]).zfill(2)
    DD = str(com[2]).zfill(2)
    t = int.from_bytes(com[3:6],'big')
    ss = t%60
    mm = int((t-ss)/60)%60
    hh = int((t-ss-60*mm)/3600)

    file_name = 'F20'+\
        YY + MM + DD + \
        str(hh).zfill(2) + str(mm).zfill(2) + str(ss).zfill(2) +\
            '.dat'
    
    if com[6] == 0:
        label = 'HK'
    elif com[6] == 1:
        label = 'IMG'
    else:
        label = 'UNKNOWN'

    id_start=int.from_bytes(com[7:9],'big')
    id_end=int.from_bytes(com[9:11],'big')

    return [file_name,label,id_start,id_end]

def packet_number(file_name):
    with open(file_name, 'r') as f:
        missingpackets = f.read().split('*:')[1:]
    for i, packet in enumerate(missingpackets):
        missingpackets[i] = int(packet.split('\n')[0])
    return sum(missingpackets)

# location for the raw data
output_IM_folder_path = "./optical/"
report_folder_path = "./request_missing/"
os.makedirs(output_IM_folder_path,exist_ok=True)
os.makedirs(report_folder_path,exist_ok=True)
files = glob.glob('./raw_data/*.bin')
files.sort()
file_name = files[-1]
reports = glob.glob('./request_missing/*.txt')
reports.sort()

# read the raw data, split the data into packets using sync bytes
with open(file_name, 'rb') as f:
    mpduPackets = f.read().split(b'\x1A\xCF\xFC\x1D')[1:]

if sys.argv == "detail":
    # output file that contains the header information of the packets
    # fout_name = f'./DQ_check/{'/'.join(file_name.split('/')[2:])}'
    fout_name = f'./{file_name.split('/')[-1]}'
    fout_name = fout_name.replace('.bin', '_header.txt')
    fout = open(fout_name, 'w')
else:
    dt_now = datetime.datetime.now()
    time_now = dt_now.strftime('%d_%H%M%S')
    if len(reports) == 0:
        print('No report file found, create a new one.')
        fout_name = f'{report_folder_path}report_{time_now}.txt'
    else:
        fout_name = reports[-1]
        if packet_number(fout_name) > 8310:
            print('The last report file is full, create a new one.')
            fout_name = f'{report_folder_path}report_{time_now}.txt'
        else:
            print('Append to the last report file.')
    
imgData = bytes()
headers = [[], [], [], []]
hk = []

# loop through all the packets
if sys.argv == "detail":
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
        headers[3].append(packet[1].hex())
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
            imgData += packet[56:-160]
        elif packet[28:30] == b'\x40\x3F':
            headers[0].append('HK')
            hk.append(packet.hex())
        else:
            headers[0].append('UnClassified')
        
        headers[1].append(int.from_bytes(packet[30:33], 'big'))
        headers[2].append(packet[34])
        headers[3].append(packet[1].hex())

try:
    headerDF = pd.DataFrame(np.array(headers).T, columns=['VCDU', 'PSC', 'IB', 'Parity'])
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
    
    if sys.argv == "detail":
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
        nfiles = len(glob.glob(os.path.join(output_IM_folder_path, '*.bin')))
        # only save the image data if there is no missing image packets
        if missing_rate_IM == 0:
            # no missing packets, save the image data
            imgData = imgData.rstrip(b'\0')
            with open(f'./optical/opt_frame_{nfiles}_{file_name.split('/')[-1]}', 'wb') as f:
                f.write(imgData)
            with open(fout_name, 'a') as f:
                f.write('--- \n')
                f.write(f'{file_name.split('/')[-1]} no missing packets. \n')
        else:
            # output the command to request the missing packets
            with open(fout_name, 'a') as f:
                f.write('--- \n')
                f.write(f'{file_name.split('/')[-1]} have missing packets. \n')
                f.write(f'Number of Missing Image Packets*: {len(missing_IM)} \n')
                # f.write(f'Number of Missing HK Packets*: {len(missing_HK)} \n')
                f.write(f'Missing Image packets rate: {missing_rate_IM} \n')
                f.write(f'True segment of request image packets: {missing_segment_IM} \n')
                # f.write(f'True segment of request HK packets: {missing_segment_HK} \n')

except Exception as e:
    print(f'Error in {file_name}: {e}')
    
# output file that contains only image data 

# folder_path = "./optical/"
# os.makedirs(folder_path,exist_ok=True)
# nfiles = len(glob.glob(os.path.join(folder_path, '*.bin')))
# dt_now = datetime.datetime.now()
# time_now = dt_now.strftime('%d_%H%M%S')
# with open(f'./optical/opt_frame_{nfiles}_{time_now}.bin', 'wb') as f:
#     f.write(imgData)