import threading
import time
import datetime
import os
import serial  # Replace `col_utils.connect_to_serial` with `serial.Serial`

def listen_to_serial(ser, timeout, filename, stop_event):
    """Serial port listener."""
    while not stop_event.is_set():
        start_time = time.time()
        response = ser.readline()
        response_str = response.decode('utf-8')
        print(f'Received: {response_str}')
        
        time_now = datetime.datetime.now()
        time_str = f"{time_now.strftime('%Y%m%d-%H:%M:%S')}"
        with open(filename, "a") as file:
            file.write(f'{time_str}: {response_str}')


def send_commands(ser, stop_event):
    """Command sender."""
    while not stop_event.is_set():
        command = input("Enter command (or type 'exit' to quit): ")
        command = "".join(command.split())
        command = command.upper()
        print(command)
        if command.lower() == 'exit':
            stop_event.set()
            break
        if command:
            if all(c in "0123456789ABCDEF" for c in command):
                ser.write(bytearray.fromhex(command))
                print(f"Command sent: {command}")
            else:
                print('error: it is not command string')

def main():
    port = "COM4"  # Update to your actual port
    baudrate = 57600
    ser = serial.Serial(port, baudrate, timeout=1)

    os.makedirs('./log', exist_ok=True)
    time_now = datetime.datetime.now()
    time_str = f"{time_now.strftime('%Y%m%d')}"
    filename = f'./log/{time_str}_log.txt'

    timeout = 10
    stop_event = threading.Event()

    # Start listener thread
    listener_thread = threading.Thread(target=listen_to_serial, args=(ser, timeout, filename, stop_event))
    listener_thread.start()

    # Start command sender thread
    send_commands(ser, stop_event)

    # Wait for threads to finish
    listener_thread.join()
    ser.close()

if __name__ == "__main__":
    main()
