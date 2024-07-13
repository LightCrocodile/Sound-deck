import os
import serial
import pygame
import tkinter as tk
from tkinter import filedialog
from threading import Thread
import shutil
import time
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize pygame mixer
pygame.mixer.init()

# Global variables
ser = None
sound_directory = "sounds"  # Folder to store sound files
sound_paths = [""] * 4  # Holds paths to sound files for buttons 1 to 4
playing_status = [False] * 4  # Indicates if a sound is currently playing for each button
upload_buttons = []  # List to hold upload buttons

# Ensure sound directory exists
if not os.path.exists(sound_directory):
    os.makedirs(sound_directory)

# Function to open serial port
def open_serial_port(com_port):
    global ser
    try:
        ser = serial.Serial(com_port, 9600, timeout=1)
        print(f"Serial port opened: {com_port}")
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    except Exception as e:
        print(f"Error: {e}")

# Function to play or pause sound file for a button
def play_or_pause_sound(button_num):
    global playing_status
    if playing_status[button_num - 1]:
        pygame.mixer.music.pause()
        playing_status[button_num - 1] = False
    else:
        if sound_paths[button_num - 1] != "":
            pygame.mixer.music.load(sound_paths[button_num - 1])
            pygame.mixer.music.play()
            playing_status[button_num - 1] = True
        else:
            print(f"No sound assigned to Button {button_num}")

# Function to stop playing sound file for a button
def stop_sound(button_num):
    pygame.mixer.music.stop()
    playing_status[button_num - 1] = False

# Function to upload sound file for a specific button
def upload_sound_file(button_num):
    file_path = filedialog.askopenfilename(filetypes=[("Sound Files", "*.mp3;*.wav")])
    if file_path:
        # Create a new file name in the sounds directory
        file_name = os.path.basename(file_path)
        new_file_path = os.path.join(sound_directory, file_name)
        
        # Copy the selected sound file to the sounds directory
        try:
            shutil.copy(file_path, new_file_path)
        except Exception as e:
            print(f"Error copying file: {e}")
            return
        
        sound_paths[button_num - 1] = new_file_path
        update_button_label(button_num, file_name)
        save_sound_paths()

# Function to update button label after assigning a sound file
def update_button_label(button_num, file_name):
    upload_buttons[button_num - 1].config(text=f"{file_name}")

# Function to save sound paths to a JSON file
def save_sound_paths():
    with open("sound_paths.json", "w") as f:
        json.dump(sound_paths, f)

# Function to load sound paths from a JSON file
def load_sound_paths():
    global sound_paths
    if os.path.exists("sound_paths.json"):
        with open("sound_paths.json", "r") as f:
            sound_paths = json.load(f)
            for i, file_name in enumerate(sound_paths):
                if file_name:
                    update_button_label(i + 1, os.path.basename(file_name))

# GUI setup using tkinter
def setup_gui():
    global upload_buttons  # Declare as global to modify the global variable
    root = tk.Tk()
    root.title("Sound Deck")

    # Set window icon
    root.iconbitmap("path_to_your_icon.ico")

    button_frames = []

    # Function to create buttons dynamically
    def create_button(button_num):
        global upload_buttons  # Reference to outer variable
        button_frame = tk.Frame(root, padx=10, pady=10)
        button_frame.grid(row=(button_num-1)//2, column=(button_num-1)%2, padx=10, pady=10)

        upload_button = tk.Button(button_frame, text=f"Button {button_num}", command=lambda num=button_num: upload_sound_file(num))
        upload_button.pack(pady=5)
        upload_buttons.append(upload_button)  # Add upload button to the list

        play_pause_button = tk.Button(button_frame, text="Play/Pause", command=lambda num=button_num: play_or_pause_sound(num))
        play_pause_button.pack(pady=5)

        stop_button = tk.Button(button_frame, text="Stop", command=lambda num=button_num: stop_sound(num))
        stop_button.pack(pady=5)

    # Create buttons dynamically for each button number (1 to 4)
    for btn_num in range(1, 5):
        create_button(btn_num)

    # Start serial communication on a separate thread
    Thread(target=serial_communication).start()

    root.mainloop()

# Function to handle serial communication and button presses
def serial_communication():
    while True:
        if ser and ser.is_open:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().strip().decode('utf-8')
                    print(f"Received: {line}")

                    # Handle button press events
                    if line in ['1', '2', '3', '4']:
                        button_num = int(line)
                        play_or_pause_sound(button_num)
                        time.sleep(0.3)  # Debounce delay

            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    # Replace 'COM14' with your Arduino's COM port
    open_serial_port('COM14')

    # Load saved sound paths
    load_sound_paths()

    # Start GUI setup
    setup_gui()

    # Close serial port on exit
    if ser and ser.is_open:
        ser.close()
        print("Serial port closed.")
