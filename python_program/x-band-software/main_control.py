import time 
import os 
import subprocess

raw_data_folder = "./raw_data/"
requested_data_folder = "./requested_data/"
image_data_folder = "./optical/"

while True:
    
    processed_raw_files = set()
    processed_req_files = set()
    processed_img_files = set()
    
    # Get new files, not including folders
    current_raw_files = {f for f in os.listdir(raw_data_folder) if os.path.isfile(os.path.join(raw_data_folder, f))}
    new_raw_files = current_raw_files - processed_raw_files
    current_req_files = {f for f in os.listdir(requested_data_folder) if os.path.isfile(os.path.join(requested_data_folder, f))}
    new_req_files = current_req_files - processed_req_files
    current_img_files = {f for f in os.listdir(image_data_folder) if os.path.isfile(os.path.join(image_data_folder, f))}
    new_img_files = current_img_files - processed_img_files

    for file in sorted(new_raw_files):  # Process in order
        file_path = os.path.join(raw_data_folder, file)
        try:
            subprocess.run(["python3", "./check_data.py", file_path], check=True)
            print(f"Finish checking {file}")
            processed_raw_files.add(file)
        except Exception as e:
            print(f"Error for checking {file_path}: {e}")
            continue
    
    for file in sorted(new_req_files):  # Process in order
        file_path = os.path.join(requested_data_folder, file)
        try:
            subprocess.run(["python3", "./combine.py", file_path], check=True)
            print(f"Finished combining {file}")
            processed_req_files.add(file)
        except Exception as e:
            print(f"Error for merging {file_path}: {e}")
            continue
        
    # call cmd_gen.py
    # os.system(
    #     f"python3 ./cmd_gen.py"
    # )
        
    for file in sorted(new_img_files):  # Process in order
        file_path = os.path.join(image_data_folder, file)
        try:
            subprocess.run(["python3", "./read_bin.py", file_path], check=True)
            print(f"Finished reading {file}")
            processed_img_files.add(file)
        except subprocess.CalledProcessError as e:
            print(f"Error for reading {file_path}: {e}")
            continue

    # print(f"Processed raw files: {processed_raw_files}")
    # print(f"Processed requested files: {processed_req_files}")
    # print(f"Processed image files: {processed_img_files}")
    time.sleep(3)  # Check for new files every x seconds
    
    for file in processed_raw_files:
        os.system(f'rm {raw_data_folder}{file}')
    for file in processed_req_files:
        os.system(f'rm {requested_data_folder}{file}')
    for file in processed_img_files:
        os.system(f'rm {image_data_folder}{file}')
    # print(f'files: {current_files}')

