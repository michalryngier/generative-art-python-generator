import json
import tkinter as tk
import threading
import subprocess
import os
from tkinter import colorchooser
from typing import TYPE_CHECKING

from gui.monitor_window import MonitorWindow

if TYPE_CHECKING:
    from main import Application


class GeneratorView(tk.Frame):
    master: 'Application'
    PARAMETER_TYPES = {
        "iterations": int,
        "savingFreq": int,
        "crossoverChance": float,
        "pointsMinMax": list,
        "thresholdMinMax": list,
        "crossoverPoints": int,
        "mutationChance": float,
        "numberOfInterpolationPoints": int,
        "populationSize": int,
        "alleleLength": int,
        "significantAlleles": int,
        "startingPositionRadius": int,
    }

    def __init__(self, master: 'Application', image_path):
        super().__init__(master)
        self.process = None
        self.entry_fields = {}
        self.image_path = image_path
        self.initial_values = self.load_config()
        self.background_color_entry = None
        self.foreground_color_entry = None
        self.cutoff_value_entry = None
        self.create_widgets()
        self.focus_first_entry()

    def create_widgets(self):
        # Create a frame to hold the buttons
        button_frame = tk.Frame(self)
        button_frame.pack(side="top", anchor="nw", padx=10, pady=10)

        # Create the "Wróć do galerii" button
        gallery_button = tk.Button(button_frame, text="Powrót do galerii", command=self.back_to_gallery)
        gallery_button.pack(side="left", padx=5, pady=5)

        # Create the "Wróć do obrazu" button
        image_button = tk.Button(button_frame, text="Powrót do obrazu", command=self.back_to_image_view)
        image_button.pack(side="left", padx=5, pady=5)

        # Create a frame to hold the form inputs
        frame = tk.Frame(self)
        frame.pack(padx=10, pady=10)

        # Custom labels for each parameter
        custom_labels = {
            "iterations": "Liczba iteracji algorytmu",
            "savingFreq": "Częstotliwość zapisu",
            "crossoverChance": "Prawdopodobieństwo krzyżowania (0 -> 1)",
            "crossoverPoints": "Liczba punktów krzyżowania",
            "mutationChance": "Prawdopodobieństwo mutacji (0 -> 1)",
            "pointsMinMax": "Liczba punktów krzywych min-max (np. 1,2)",
            "thresholdMinMax": "Grubość krzywych min-max (np. 1,2)",
            "numberOfInterpolationPoints": "Liczba rysowanych punktów na krzywej",
            "populationSize": "Liczeność populacji początkowej",
            "alleleLength": "Długość genu (32 lub 64)",
            "significantAlleles": "Istotne allele",
            "startingPositionRadius": "Promień rozrzutu punktów początkowych krzywych",
        }

        row = 0
        for param, custom_label in custom_labels.items():
            label = tk.Label(frame, text=f"{custom_label}:")
            label.grid(row=row, column=0, padx=10, pady=5, sticky="e")

            initial_value = self.initial_values.get(param, "") if self.initial_values else ""
            entry = tk.Entry(frame)
            entry.insert(0, initial_value)  # Set initial value
            entry.grid(row=row, column=1, padx=10, pady=5, sticky="w")

            self.entry_fields[param] = entry  # Add entry field to dictionary
            row += 1

        # Color pickers
        foreground_color_label = tk.Label(frame, text="Kolor bazowy:")
        foreground_color_label.grid(row=row, column=0, padx=10, pady=5, sticky="e")

        self.foreground_color_entry = tk.Entry(frame)
        self.foreground_color_entry.insert(0, "#FFFFFF")  # Default color is white
        self.foreground_color_entry.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        base_color_picker_button = tk.Button(frame, text="Wybierz kolor", command=self.pick_base_color)
        base_color_picker_button.grid(row=row, column=2, padx=5, pady=5)

        row += 1

        background_color_label = tk.Label(frame, text="Kolor tła:")
        background_color_label.grid(row=row, column=0, padx=10, pady=5, sticky="e")

        self.background_color_entry = tk.Entry(frame)
        self.background_color_entry.insert(0, "#000000")  # Default color is black
        self.background_color_entry.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        background_color_picker_button = tk.Button(frame, text="Wybierz kolor", command=self.pick_background_color)
        background_color_picker_button.grid(row=row, column=2, padx=5, pady=5)

        row += 1

        cutoff_value_label = tk.Label(frame, text="Wartość odcięcia:")
        cutoff_value_label.grid(row=row, column=0, padx=10, pady=5, sticky="e")

        self.cutoff_value_entry = tk.Entry(frame)
        self.cutoff_value_entry.insert(0, "0.0")  # Default cutoff value
        self.cutoff_value_entry.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        row += 1

        # Create the "Generate" button
        generate_button = tk.Button(self, text="Generuj", command=self.generate)
        generate_button.pack(padx=10, pady=10)

    def pick_base_color(self):
        color = colorchooser.askcolor()[1]  # Returns a tuple (rgb, hex)
        if color:
            self.foreground_color_entry.delete(0, tk.END)
            self.foreground_color_entry.insert(0, color)

    def pick_background_color(self):
        color = colorchooser.askcolor()[1]  # Returns a tuple (rgb, hex)
        if color:
            self.background_color_entry.delete(0, tk.END)
            self.background_color_entry.insert(0, color)

    def focus_first_entry(self):
        # Focus on the first entry field
        first_entry = next(iter(self.entry_fields.values()))
        first_entry.focus_set()

    def back_to_gallery(self):
        from gui.image_gallery import ImageGallery
        self.master.switch_view(ImageGallery)

    def back_to_image_view(self):
        from gui.image_view import ImageView
        self.master.switch_view(ImageView, image_path=self.image_path)

    def generate(self):
        self.save_config()
        threading.Thread(target=self.run_generator_subprocess).start()
        threading.Thread(target=self.open_monitor).start()

    def run_generator_subprocess(self):
        folder_name = os.path.basename(os.path.dirname(self.image_path))
        subprocess.run(["python", "genetic_algorithm.py", folder_name])

    def open_monitor(self):
        self.master.open_new_window(MonitorWindow, image_path=self.image_path, fg_color=self.foreground_color_entry.get(),
                                    bg_color=self.background_color_entry.get(), cutoff=self.cutoff_value_entry.get())

    def save_config(self):
        # Retrieve values from entry fields and construct the JSON input
        json_input = {}
        for param, entry in self.entry_fields.items():
            # Get the value from the entry field
            param_value = entry.get()
            # Get the data type for the parameter
            param_type = self.PARAMETER_TYPES[param]
            # Convert the value to the appropriate data type
            if param_type == list:
                param_value = [int(val.strip()) for val in param_value.split(",")]
            else:
                param_value = param_type(param_value)
            # Add the parameter and its value to the JSON input
            json_input[param] = param_value

        # Get the path for config.json
        config_path = self.get_config_path()

        # Write the JSON input to config.json with nicely formatted indentation
        with open(config_path, 'w') as json_file:
            json.dump(json_input, json_file, indent=4)

        print("Config file saved successfully.")

    def load_config(self):
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            # Load config from config.json if it exists
            config_path = self.get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r') as json_file:
                    config = json.load(json_file)
                    # Convert values to appropriate data types based on PARAMETER_TYPES
                    for param, param_type in self.PARAMETER_TYPES.items():
                        if param in config:
                            if param_type == list:
                                config[param] = ','.join(str(x) for x in config[param]),
                            else:
                                config[param] = param_type(config[param])
                return config
            else:
                return {}
        else:
            return {
                "iterations": 100,
                "savingFreq": 1,
                "crossoverChance": 0.8,
                "crossoverPoints": 3,
                "mutationChance": 0.0001,
                "pointsMinMax": "5, 10",
                "thresholdMinMax": "1, 2",
                "numberOfInterpolationPoints": 150,
                "populationSize": 10000,
                "alleleLength": 64,
                "significantAlleles": 4,
                "startingPositionRadius": 200
            }

    def get_config_path(self):
        image_dir = os.path.dirname(self.image_path)
        config_path = os.path.join(image_dir, "config.json")

        return config_path

    def on_destroy(self):
        pass
