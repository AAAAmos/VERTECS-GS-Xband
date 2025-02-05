import glob
from tqdm import tqdm

files = glob.glob('./raw_data/test_x-band/*.bin')
files += glob.glob('./raw_data/test_x-band/*/*.bin')
files.sort()
# files = files[:2]

for file_name in tqdm(files[:3]):

    with open(file_name, 'rb') as f:
        packetData = f.read().split(b'\x1A\xCF\xFC\x1D')[1:]
        
    fout_name = f'./DQ_check/{'/'.join(file_name.split('/')[2:])}'
    fout_name = fout_name.replace('.bin', '_all_header.txt')
    fout = open(fout_name, 'w')
        
    mpduPackets = []
    
    for packet in packetData:
        mpduPackets.append(packet)
        
    imgData = bytes()
    headers = [[], [], [], []]
    desyncs = []
    hk = []

    for k, packet in enumerate(mpduPackets):
        
        if packet[28:30] == b'\x55\x40':
            headers[0].append(packet[28:30].hex())
            # imgData += packet[28:-160]
        elif packet[28:30] == b'\x40\x3F':
            headers[0].append(packet[28:30].hex())
            # hk.append(packet.hex())
        else:
            headers[0].append(packet[28:30].hex())
        
        headers[1].append(int.from_bytes(packet[30:33], 'big'))
        fout.write(
            f'{packet[:28].hex()}, {headers[0][-1]}, {headers[1][-1]}\n'
        )
    # fout.write(f'Number of Packets: {len(packetData)}\n')
    fout.close()
    # imgData = imgData.rstrip(b'\0')