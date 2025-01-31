from tqdm import tqdm
import glob
import os
import datetime

# file_name = './F20240822162559.bin'
folder_path = "./optical/"
os.makedirs(folder_path,exist_ok=True)
files = glob.glob('./raw_data/*.bin')
files.sort()
file_name = files[-1]

print(file_name)
with open(file_name, 'rb') as f:
    packetData = f.read().split(b'\x1A\xCF\xFC\x1D')[1:]

mpduPackets = []
print('Number of Packets: ', len(packetData))
for packet in packetData:
    mpduPackets.append(packet[28:])

imgData = bytes()
i = 0
j=0
l=0
desyncs = []
hk = []
index = 0
for k, packet in enumerate(tqdm(mpduPackets)):
    if packet[:2] == b'\x55\x40':
        i += 1
        index = int.from_bytes(packet[26:28],'big')
        imgData += packet[28:-160]
    elif packet[:2] == b'\x40\x3F':
    # elif packet[:2] == b'\x51\xFF':
        hk.append(packet.hex())
        pass
    else:
        desyncs.append((k,index,packet[:2].hex()))
        j+=1

avg = 0
imgData = imgData.rstrip(b'\0')

print('Total Image Packets: ', i)
print('Total images: ',len(imgData))
print('Missed Packets: ', j)
print('Missed packet rate (packet/1000): ', (j/i)*1000)


nfiles = len(glob.glob(os.path.join(folder_path, '*.bin')))
dt_now = datetime.datetime.now()
time_now = dt_now.strftime('%d_%H%M%S')
with open(f'./optical/opt_frame_{nfiles}_{time_now}.bin', 'wb') as f:
    f.write(imgData)

# print(desyncs)
# print(hk[20])