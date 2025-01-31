# This script is used to check the data quality of the raw data. 
# It reads the raw data and checks for missing packets in the data.
# The output is a text file that contains the header information of the packets and the missing packets.
# In principle, the image shold be compile without any missing packets.

from tqdm import tqdm
import glob
import os
import datetime
import numpy as np
import pandas as pd

# location for the raw data
files = glob.glob('./raw_data/test_x-band/*.bin')
files += glob.glob('./raw_data/test_x-band/*/*.bin')
files.sort()

# loop through all the files
for file_name in tqdm(files):

    # read the raw data, split the data into packets using sync bytes
    with open(file_name, 'rb') as f:
        packetData = f.read().split(b'\x1A\xCF\xFC\x1D')[1:]
    
    # output file that contains the header information of the packets
    fout_name = f'./DQ_check/{'/'.join(file_name.split('/')[2:])}'
    fout_name = fout_name.replace('.bin', '_header.txt')
    fout = open(fout_name, 'w')
        
    mpduPackets = []
    
    # remove information from the X-band transmitter
    for packet in packetData:
        mpduPackets.append(packet[28:])
        
    imgData = bytes()
    headers = [[], [], [], []]
    desyncs = []
    hk = []

    # loop through all the packets
    for k, packet in enumerate(mpduPackets):
        
        # classify the packets by the VCDU header
        if packet[:2] == b'\x55\x40':
            headers[0].append('IM')
            # imgData += packet[28:-160]
        elif packet[:2] == b'\x40\x3F':
            headers[0].append('HK')
            hk.append(packet.hex())
        else:
            headers[0].append('UnClassified')
        
        headers[1].append(int.from_bytes(packet[2:5], 'big'))
        headers[2].append(packet[6])
        headers[3].append(packet[-160:].hex())
        fout.write(
            f'{headers[0][-1]}, {headers[1][-1]}, {headers[2][-1]}, {headers[3][-1]}\n'
        )
    fout.write(f'Number of Packets: {len(packetData)}\n')
    fout.close()

    try:
        fout = open(fout_name, 'a')
        headerDF = pd.DataFrame(np.array(headers).T, columns=['VCDU', 'PSC', 'IB', 'Parity'])
        fout.write(f'Total Image Packets: {headerDF[headerDF['VCDU'] == 'IM'].shape[0]}\n')
        fout.write(f'UnClassified Packets: {headerDF[headerDF['VCDU'] == 'UnClassified'].shape[0]}\n')

        IM, HK = headerDF[headerDF['VCDU'] == 'IM']['PSC'].astype(int), headerDF[headerDF['VCDU'] == 'HK']['PSC'].astype(int)
        IM_range = set(range(0, 16620))
        max_HK = HK[HK < 10000].max()
        HK_range = set(range(int(min(HK)), int(max_HK)+1))
        missing_IM = IM_range - set(IM)
        missing_HK = HK_range - set(HK)

        fout.write(f'Sequence number of Missing Image Packets: {missing_IM}\n')
        fout.write(f'Number of Missing Image Packets: {len(missing_IM)}\n')
        fout.write(f'Sequence number of Missing HK Packets: {missing_HK}\n')
        fout.write(f'Number of Missing HK Packets: {len(missing_HK)}\n')
        fout.write(f'Total missing packets: {len(missing_IM)+len(missing_HK)}\n')
        fout.write(f'Missed image rate (missing image/Image packet %): {(len(missing_IM)/16621)*100}\n')
        fout.close()
    
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