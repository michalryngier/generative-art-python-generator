import time
import tkinter as tk
import subprocess
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Application


class MonitorWindow(tk.Toplevel):
    def __init__(self, master: 'Application', image_path):
        super().__init__(master)
        self.title("Monitor")
        self.image_path = image_path
        self.last_created_dir = None
        self.file_set = set()
        self.monitor_directory()

    def monitor_directory(self):
        image_dir = os.path.dirname(self.image_path)
        last_dir = self.get_last_created_directory(image_dir)
        while True:
            self.last_created_dir = last_dir
            self.process_new_files(last_dir)
            time.sleep(0.1)

    def get_last_created_directory(self, path):
        while True:
            directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
            if directories:
                latest_dir = max(directories, key=lambda d: int(d.split('_')[-1]))
                latest_dir_path = os.path.join(path, latest_dir)
                timestamp = os.path.getctime(latest_dir_path)
                current_time = time.time()
                if current_time - timestamp < 5:  # Check if the directory is created within the last 5 seconds
                    return latest_dir_path
                print('Waiting for recent directory...')
            time.sleep(1)

    def process_new_files(self, directory):
        new_files = set(os.listdir(directory)) - self.file_set
        for file_name in new_files:
            if file_name != "config.json":
                file_path = os.path.join(directory, file_name)
                if os.path.isfile(file_path):
                    subprocess.run(["python", "single_output_image_generator.py", directory, file_path], check=True)
        self.file_set.update(new_files)

    def on_destroy(self):
        pass
