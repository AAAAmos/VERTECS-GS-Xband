import ctypes
import os
import gpiozero
import argparse
import time
import datetime
import serial
import glob
# Load the shared library
libx_band = ctypes.CDLL(os.path.abspath('libx_band.so'))

# Define the argument and return types for the functions
libx_band.init_ftdi.restype = ctypes.POINTER(ctypes.c_void_p)
libx_band.send.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
libx_band.send.restype = ctypes.c_int
libx_band.close_ftdi.argtypes = [ctypes.POINTER(ctypes.c_void_p)]

sync_bytes = b'\x1A\xCF\xFC\x1D'

def packData(data, data_type: int, data_id, dest_callsign, src_callsign, max_data_size=1087, spacecraft_id=0x55, vcid=0, version=1):
    vcdu_header = ((version << 14) + (spacecraft_id << 6) + vcid).to_bytes(2, 'big')
    npackets = -(len(data) // -max_data_size)
    mdpu_header = b'\x00\x00'
    trans_info = dest_callsign.encode('ascii') + b'\x00' + src_callsign.encode('ascii') + b'\x00'
    mdpu_header += trans_info
    mdpu_header += data_type.to_bytes(1, 'big')
    mdpu_header += npackets.to_bytes(3, 'big')
    mdpu_header += data_id.to_bytes(2, 'big') # check max number of images for mission or aat least roll over
    pad_size = len(data) + (max_data_size - len(data) % max_data_size)
    data = data.ljust(pad_size, b'\0')

    dataPackets = []
    j = 0
    for i in range(0, len(data), max_data_size):
        dataPackets.append(sync_bytes + vcdu_header + j.to_bytes(3, 'big') + b'\x00' + mdpu_header + data[i:i+max_data_size])
        j+=1
    
    return b''.join(dataPackets)

# Set up argument parsing
# parser = argparse.ArgumentParser(description='Process and send a .bin file.')
# parser.add_argument('file_name', type=str, help='Name of the .bin file to be processed')

# args = parser.parse_args()

# Get the file name from the input argument
# file_name = args.file_name

# Get today's date and format it as YYYYMMDD
#date = str(datetime.date.today())
#renamed_date = date.replace('-', '')

# Define the base folder containing the .bin files
base_folder = '/home/vertecs/vertecs-ccb-testing/ccb/KafiTest/ccb_pi4/image'
latest_files=glob.glob(base_folder+"/*")
latest_files.sort()
folder_path=latest_files[0]
# Create the full path by joining the base folder, renamed_date, and the file name
# print(latest_file)
# exit()
# folder_path = os.path.join(base_folder, file_name)

# Convert the folder path to an absolute path to ensure it's clean
file_path = latest_files[0]

# Check if the file exists
# if not os.path.isfile(file_path):
#     print(f"Error: File '{file_path}' does not exist.")
#     exit(1)

xband_packets = []

pack_start = time.time()

# Process the specified file
with open(file_path, 'rb') as file:
    frame = packData(file.read(), 1, 0, 'JG6YBW', 'JG6YNH')
    xband_packets.append((ctypes.c_ubyte * len(frame)).from_buffer_copy(frame))

pack_end = time.time()

print('File packed and sent!')
print('Time: ', pack_end - pack_start)

# Initialize the FTDI device
ftdi_context = libx_band.init_ftdi()
if not ftdi_context:
    raise RuntimeError("Failed to initialize FTDI device")

trans_start = time.time()
xdio = gpiozero.DigitalOutputDevice(23)
xdio.on()
time.sleep(3)

xbandConfig = serial.Serial("/dev/ttyAMA3", 19200)
print('Serial Port Open!')
xbandConfig.write(b'BC8\r')
xbandConfig.write(b'C0F\r')
time.sleep(3)
print('Begin transfer!')
try:
    for frame in xband_packets:
        # Convert data to a ctypes array
        data_len = len(frame)
        # Send the binary file data
        start_time = time.time()
        ret = libx_band.send(ftdi_context, frame, data_len)
        end_time = time.time()

        # Calculate the transfer time and speed
        transfer_time = end_time - start_time
        transfer_speed = (data_len*8) / transfer_time / (1000 * 1000)  # in MB/s

        print(f"Transfer Time: {transfer_time:.2f} seconds")
        print(f"Transfer Speed: {transfer_speed:.2f} Mbps")
finally:
    # Close the FTDI device
    time.sleep(5)
    libx_band.close_ftdi(ftdi_context)
    xbandConfig.close()
    xdio.off()
    trans_end = time.time()
    print('Done!')
    print('Time: ', trans_end-trans_start)

