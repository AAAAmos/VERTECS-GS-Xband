import os
import datetime
from tqdm import tqdm


SYNC_MARKER = b'\x1A\xCF\xFC\x1D'
OPT_EXTRA_HEADER = 28      # Optical receiver adds 28 bytes at the beginning
OPT_EXTRA_TRAILER = 160    # ...and 160 bytes at the end of each packet
TX_HEADER_SIZE = 28        # Transmitter header after sync marker (2+3+1+22 = 28 bytes)
MAX_DATA_SIZE = 1087       # Payload size per packet

invalid_vcdu_count = 0

def process_packet(raw_packet):
    """

    Raw optical packet structure:
      [Optical Extra Header (28 bytes)] +
      [Transmitter Packet: (VCDU header (2) + sequence (3) + reserved (1) + MDPU header (22) + payload (MAX_DATA_SIZE))] +
      [Optical Extra Trailer (160 bytes)]
      
    The new MDPU header (22 bytes) is structured as follows:
      • Bytes  0-1: Reserved (unique ID as 2 bytes, from the first 2 bytes of the provided hex identifier)
      • Bytes  2-8: Destination callsign (7 bytes, e.g. "JG6YBW\x00")
      • Bytes  9-15: Unique identifier (4-byte hex derived from the provided hex identifier, padded with 3 null bytes)
      • Byte     16: Data type (1 byte)
      • Bytes 17-20: Actual file length (4 bytes, big-endian)
      • Byte     21: Packet type indicator (1 byte)
    
    """
    global invalid_vcdu_count
    trimmed = raw_packet[OPT_EXTRA_HEADER:]
    transmitter_packet = trimmed[:-OPT_EXTRA_TRAILER]
    if len(transmitter_packet) < TX_HEADER_SIZE: # xxx ? MAX_DATA_SIZE
        return None

    vcdu = transmitter_packet[0:2]
    if vcdu != b'\x55\x40':
        invalid_vcdu_count += 1
        return None

    seq = int.from_bytes(transmitter_packet[2:5], 'big')
    mdpu_header = transmitter_packet[6:28]
    payload = transmitter_packet[28:28+MAX_DATA_SIZE]
    ptype = mdpu_header[21]
    actual_file_length = int.from_bytes(mdpu_header[17:21], 'big')
   
    file_uid = mdpu_header[9:13].hex()
    return seq, ptype, actual_file_length, payload, file_uid, mdpu_header

def decode_packets(received_file):
    
    with open(received_file, 'rb') as f:
        raw_data = f.read()
    packet_chunks = raw_data.split(SYNC_MARKER)[1:]
    if not packet_chunks:
        raise ValueError("No packets found in received file.")
    
    groups = {}  # key: file_uid, value: dictionary with keys: 'packets', 'file_length', 'dest_callsign'
    for chunk in tqdm(packet_chunks, desc="Processing packets"):
        result = process_packet(chunk)
        if result is None:
            continue
        seq, ptype, actual_file_length, payload, file_uid, mdpu_header = result
        if file_uid not in groups:
            
            dest = mdpu_header[2:9].split(b'\x00')[0].decode('ascii', errors='replace')
            groups[file_uid] = {'packets': [], 'file_length': actual_file_length, 'dest_callsign': dest}
        groups[file_uid]['packets'].append((seq, ptype, payload))
    return groups

def reassemble_group(group):
   
    packets = group['packets']
    packets.sort(key=lambda x: x[0])
    seqs = [p[0] for p in packets]
    first_seq = min(seqs)
    last_seq = max(seqs)
    missing_seq = sorted(set(range(first_seq, last_seq + 1)) - set(seqs))
    file_length = group['file_length']
    
    # Determine file type based on the first packet's type.
    first_ptype = packets[0][1]
    if first_ptype == 0x03:
        file_type = 'TXT'
    elif first_ptype == 0x04:
        file_type = 'LOG'
    elif first_ptype == 0x01:
        file_type = 'CSV'
    elif first_ptype == 0x05:
        file_type = 'JPG'
    elif file_length > 0:
        file_type = 'BIN'
    else:
        file_type = 'CSV'
    
    reassembled = bytearray()
    
    if file_type == 'BIN':
        for (seq, ptype, payload) in packets:
            effective_seq = seq - first_seq
            global_offset = effective_seq * MAX_DATA_SIZE
            if ptype == 0x00:
                reassembled.extend(payload)
            elif ptype == 0x02:
                x = file_length - global_offset
                if x < 0:
                    x = 0
                reassembled.extend(payload[:x])
            else:
                pass
        reassembled = reassembled[:file_length]
    elif file_type == 'JPG':
        
        for (_, _, payload) in packets:
            reassembled.extend(payload)
        reassembled = reassembled[:file_length]
    else:
        for (_, _, payload) in packets:
            reassembled.extend(payload)
    
    return bytes(reassembled), first_seq, last_seq, missing_seq, file_type

def save_group_file(data, file_uid, file_type, first_seq, last_seq, missing_seq, output_dir='./decoded'):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if file_type == 'BIN':
        ext = "bin"
    elif file_type == 'CSV':
        ext = "csv"
    elif file_type == 'TXT':
        ext = "txt"
    elif file_type == 'LOG':
        ext = "log"
    elif file_type == 'JPG':
        ext = "jpg"
    else:
        ext = "dat"
    filename = os.path.join(output_dir, f"decoded_{timestamp}_{file_uid}_{file_type}.{ext}")
    with open(filename, 'wb') as f:
        f.write(data)
    print(f"Saved {file_type} file for UID {file_uid} as: {filename}")
    print(f"First packet sequence: {first_seq:06X}, Last packet sequence: {last_seq:06X}")
    if missing_seq:
        print(f"Missing sequences: {[f'{s:06X}' for s in missing_seq]}")
    else:
        print("No missing packets.")
    return filename

def main():
    received_file = r"received_Combined/F20250323115716.bin"
    print(f"Decoding file: {received_file}")
    
    groups = decode_packets(received_file)
    if not groups:
        print("No valid packets found.")
        return
    
    print(f"Total invalid VCDU headers encountered: {invalid_vcdu_count}")
    
    for file_uid, group in groups.items():
        reassembled_data, first_seq, last_seq, missing_seq, file_type = reassemble_group(group)
        total_packets = len(group['packets'])
        file_size = group['file_length']
        print(f"\nUID: {file_uid} | Type: {file_type}")
        print(f"File Size (from MDPU header): {file_size} bytes")
        print(f"Total number of packets: {total_packets}")
        print(f"First packet sequence number (hex): {first_seq:06X}")
        print(f"Last packet sequence number (hex): {last_seq:06X}")
        if missing_seq:
            print("Missing packet sequence numbers (hex):", [f"{s:06X}" for s in missing_seq])
        else:
            print("No missing packets.")
        save_group_file(reassembled_data, file_uid, file_type, first_seq, last_seq, missing_seq)
    
if __name__ == "__main__":
    main()