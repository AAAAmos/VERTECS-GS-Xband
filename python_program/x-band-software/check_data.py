'''
This script reads the raw data, checks completeness of the data, and the data quality.
------Parameters------
1. file_name: the name of the raw data file to be checked (full path). 
    If no input, the last file in the raw_data folder will be checked.
2. mode: "detail" or no input for normal mode
------Output------
1. If mode is "detail", the script will output a txt file that contains the header information of the packets.
2. If mode is "normal", the script will write the report to the last report file (.csv) in the report folder.:
    - If there is no missing image packets, the script will save the image data to the optical folder.
    - If there are missing image packets, the script will store the incomplete image data to the tmp folder.
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

def encode_data(filename, VCDU, PSC_DF, data_DF, mode, sync_bytes=b'\x1A\xCF\xFC\x1D'):
    '''
    Used for storing data. Only DQ=0 data will be stored.
    ------Parameters------
    filename: str
        The name of the file to write to.
    VCDU: bytes
        The VCDU header for identifying the data.
    PSC_DF: DataFrame
        The DataFrame containing the PSC values.
    data_DF: DataFrame
        The DataFrame containing the data values.
    mode: str
        The mode to open the file in. 'wb' and 'ab'.
    sync_bytes: bytes
        The sync bytes to use to separate records.
    '''
    try:
        PSC_list = PSC_DF.values.tolist()
        data_list = data_DF.values.tolist()
        with open(filename, mode) as f: 
            for i in range(0, len(data_DF)):
                f.write(sync_bytes)
                f.write(VCDU)
                # Pack the sequence count into bytes
                PSC_bytes = PSC_list[i].to_bytes(3, byteorder='big')
                f.write(PSC_bytes)
                f.write(data_list[i])
            if mode == 'wb':
                print(f"Data write to {filename}")
            else:
                print(f"Data append to {filename}")
    except Exception as e:
         print(f"Error writing to file: {e}")

def DF_raw_data(file_name):
    
    '''
    Read the raw data file and return a DataFrame containing the header information.
    Input:
        file_name: str
            The name of the raw data file.
    Output:
        dataDF: DataFrame
            The DataFrame containing the header information.
    '''
    
    with open(file_name, 'rb') as f:
        mpduPackets = f.read().split(b'\x1A\xCF\xFC\x1D')[1:]

    headers = [[], [], [], [], []]
    for k, packet in enumerate(mpduPackets):
        # classify the packets by the VCDU header
        if packet[28:30] == b'\x55\x40':
            headers[0].append('IM')
            headers[4].append(packet[56:-160])
            # headers[4].append(0)
        elif packet[28:30] == b'\x40\x3F':
            headers[0].append('HK')
            headers[4].append(packet[56:-160])
            # headers[4].append(0)
        else:
            continue
        
        headers[1].append(int.from_bytes(packet[30:33], 'big'))
        headers[2].append(packet[34])
        headers[3].append(packet[1])
        
    dataDF = pd.DataFrame({
        'VCDU': headers[0],
        'PSC': pd.Series(headers[1], dtype=int),
        'IB': headers[2],
        'DQ': pd.Series(headers[3], dtype=int),
        'data': pd.Series(headers[4], dtype='object')  # Preserve binary data
    })
    
    return dataDF

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
    file_name = sys.argv[1]
    
# reports = glob.glob('./report/*.csv')
# reports.sort()

VCDU_image = b'\x55\x40'
VCDU_HK = b'\x40\x3F'

# read the raw data, split the data into packets using sync bytes
with open(file_name, 'rb') as f:
    mpduPackets = f.read().split(b'\x1A\xCF\xFC\x1D')[1:]

# create a output file if needed
if (len(sys.argv)>2) and (sys.argv[2] == "detail"):
    # output file that contains the header information of the packets
    # fout_name = f'./DQ_check/{'/'.join(file_name.split('/')[2:])}'
    fout_name = f'./{file_name.split('/')[-1]}'
    fout_name = fout_name.replace('.bin', '_header.txt')
    print(f'Detail output: {fout_name}')
    fout = open(fout_name, 'w')
else:
    print(f'Raw data file: {file_name}')
    # determine normal mode report file
    if os.path.isfile('./report/un_gen.csv'):
        fout_name = './report/un_gen.csv'
    else:
        fout_name = './report/un_gen.csv'
        with open(fout_name, 'w') as f:
            f.write('Filename,Type,Start_Packet_number,End_Packet_number,Incompleteness(100*missing/16621)\n')
    print(f'Report file: {fout_name}')
    
    # if len(reports) == 0:
    #     dt_now = datetime.datetime.now()
    #     # https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
    #     time_now = dt_now.strftime('%Y%m%d%H%M%S')
    #     print('No report file found, create a new one.')
    #     fout_name = f'{report_path}report_0000_{time_now}.csv'
    #     with open(fout_name, 'w') as f:
    #         f.write('Filename,Type,Start_Packet_number,End_Packet_number,Incompleteness(100*missing/16621)\n')
    # else:
    #     fout_name = reports[-1]
    #     if os.path.getsize(fout_name) > 1e7: # size limit of a report file is ~ 10MB
    #         print('The last report file is too large, create a new one.')
    #         dt_now = datetime.datetime.now()
    #         time_now = dt_now.strftime('%Y%m%d%H%M%S')
    #         fout_name = f'{report_path}report_{str(len(reports)).zfill(4)}_{time_now}.csv'
    #         with open(fout_name, 'w') as f:
    #             f.write('Filename,Type,Start_Packet_number,End_Packet_number,Incompleteness(100*missing/16621)\n')
    #     else:
    #         print(f'Write to the last report file: {fout_name}')
            
headers = [[], [], [], []]
hk = []

# loop through all the packets, extract the header information
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
    headerDF = pd.DataFrame({
        'VCDU': headers[0],
        'PSC': pd.Series(headers[1], dtype=int),
        'IB': headers[2],
        'DQ': headers[3]
    })
else:
    headerDF = DF_raw_data(file_name)

# check the completeness of the data
try: 
    im_mask, hk_mask = headerDF['VCDU'] == 'IM', headerDF['VCDU'] == 'HK'
    IM, HK = headerDF[im_mask]['PSC'].astype(int), headerDF[hk_mask]['PSC'].astype(int)
    bad_IM, bad_HK = headerDF[(im_mask)&(headerDF['DQ'] != 0)]['PSC'].astype(int), headerDF[(hk_mask)&(headerDF['DQ'] != 0)]['PSC'].astype(int)
    IM_range = set(range(0, 16620))
    max_HK = HK[HK <= 8136].max() # observed, not confrimed by the document
    HK_range = set(range(int(min(HK)), int(max_HK)+1)) # if the number of HK is fixed, please change the range 
    IM = set(IM) - set(bad_IM)
    HK = set(HK) - set(bad_HK)
    missing_IM = IM_range - set(IM)
    missing_HK = HK_range - set(HK)
    missing_IM = sorted(list(missing_IM))
    missing_HK = sorted(list(missing_HK))
    missing_rate_IM = (len(missing_IM)/16621)*100
    missing_segment_IM = find_consecutive_ranges(list(missing_IM))
    missing_segment_HK = find_consecutive_ranges(list(missing_HK))
    
    # output the report
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
        IM_mask = lambda x: (x['VCDU'] == 'IM') & (x['DQ'] == 0)
        HK_mask = lambda x: (x['VCDU'] == 'HK') & (x['DQ'] == 0) # can be replaced by the packet type that store the fits header information in the future update.    
        if (missing_rate_IM == 0) and (len(missing_HK) == 0):
            # no missing packets, save the image data
            nfiles = len(glob.glob(output_IM_folder_path+'*.bin'))
            nfiles = str(nfiles).zfill(4)
            outfile = f'./optical/opt_frame_{nfiles}_{file_name.split("/")[-1]}'  # output file name
            # write the image data to the optical folder
            encode_data(outfile, VCDU_image, headerDF[IM_mask(headerDF)]['PSC'], headerDF[IM_mask(headerDF)]['data'], 'wb')
            # append the HK data to the optical folder
            encode_data(outfile, VCDU_HK, headerDF[HK_mask(headerDF)]['PSC'], headerDF[HK_mask(headerDF)]['data'], 'ab')
            # output the report
            with open(fout_name, 'a') as f:
                f.write(f'{file_name.split('/')[-1]},OK,0,0,0\n')
        else:
            outfile = f'./tmp/tmp_{file_name.split("/")[-1]}'
            # store the incomplete image data
            encode_data(outfile, VCDU_image, headerDF[IM_mask(headerDF)]['PSC'], headerDF[IM_mask(headerDF)]['data'], 'wb')
            # append the incomplete HK data
            encode_data(outfile, VCDU_HK, headerDF[HK_mask(headerDF)]['PSC'], headerDF[HK_mask(headerDF)]['data'], 'ab')
            # output the report for the missing packets
            with open(fout_name, 'a') as f:
                for segment in missing_segment_IM:
                    f.write(f'{file_name.split('/')[-1]},IM,{segment[0]},{segment[1]},{missing_rate_IM}\n')
                for segment in missing_segment_HK:
                    f.write(f'{file_name.split('/')[-1]},HK,{segment[0]},{segment[1]},255\n')

except Exception as e:
    # report for unreadable files
    with open(fout_name, 'a') as f:
        f.write(f'{file_name.split('/')[-1]},Error,255,255,255\n')
    # print(f'Error in {file_name}: {e}')