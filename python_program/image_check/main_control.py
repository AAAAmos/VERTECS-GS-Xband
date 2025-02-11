import time 
import os 

raw_data_folder = "./raw_data/"
requested_data_folder = "./requested_data/"
image_data_folder = "./optical/"
processed_raw_files = set()
processed_req_files = set()
processed_img_files = set()

def call_check_data(raw_file_path):
    print(f"Call check_data for {raw_file_path}")
    # os.system(
    #     f"python3 ./check_data.py {raw_file_path}"
    # )
    time.sleep(1)
    print(f"Finished {raw_file_path}")

def call_merge_packets(RMP_file_path):
    print(f"Call combine for {RMP_file_path}")
    # os.system(
    #     f"python3 ./combine.py {RMP_file_path}"
    # )
    time.sleep(1)
    print("Finished combine")
    
def call_read_bin(optical_file_path):
    print(f"Call read_bin for {optical_file_path}")
    # os.system(
    #     f"python3 ./read_bin.py {optical_file_path}"
    # )
    time.sleep(1)
    print("Finished read_bin")

while True:
    current_raw_files = {f for f in os.listdir(raw_data_folder) if os.path.isfile(os.path.join(raw_data_folder, f))}
    new_raw_files = current_raw_files - processed_raw_files
    current_req_files = {f for f in os.listdir(requested_data_folder) if os.path.isfile(os.path.join(requested_data_folder, f))}
    new_raw_files = current_req_files - processed_req_files
    current_img_files = {f for f in os.listdir(image_data_folder) if os.path.isfile(os.path.join(image_data_folder, f))}
    new_img_files = current_img_files - processed_img_files

    for file in sorted(new_raw_files):  # Process in order
        file_path = os.path.join(raw_data_folder, file)
        call_check_data(file_path)
        processed_raw_files.add(file)
        
    # call cmd_gen.py
    os.system(
        f"python3 ./cmd_gen.py"
    )
    
    for file in sorted(new_raw_files):  # Process in order
        file_path = os.path.join(requested_data_folder, file)
        call_merge_packets(file_path)
        processed_req_files.add(file)
        
    for file in sorted(new_img_files):  # Process in order
        file_path = os.path.join(image_data_folder, file)
        call_read_bin(file_path)
        processed_img_files.add(file)

    time.sleep(3)  # Check for new files every x seconds
    # print(f'files: {current_files}')

