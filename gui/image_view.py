import subprocess
import tkinter
import tkinter as tk
from PIL import Image, ImageTk
from typing import TYPE_CHECKING
import os

from gui.generator_view import GeneratorView

if TYPE_CHECKING:
    from main import Application


class ImageView(tk.Frame):
    master: 'Application'

    def __init__(self, master: 'Application', image_path):
        super().__init__(master)
        self.em_label = None
        self.em_photo = None
        self.error_label = None
        self.path_label = None
        self.canny_sigma_entry: tkinter.Entry | None = None
        self.blur_sigma_entry: tkinter.Entry | None = None
        self.label = None
        self.image_path = image_path
        self.photo = None
        self.create_widgets()
        self.set_image(image_path)

    def set_image(self, image_path):
        self.image_path = image_path  # Set the image_path attribute
        if self.image_path:
            img = Image.open(self.image_path)
            img.thumbnail((300, 300))  # Resize the image if necessary
            self.photo = ImageTk.PhotoImage(img)  # Keep a reference to the PhotoImage object

            # Update the image displayed in the label
            self.label.config(image=self.photo)
            self.label.image = self.photo  # Ensure the PhotoImage object is not garbage collected

            em_image_path = self.get_em_image_path(image_path)
            em_img = Image.open(em_image_path)
            em_img.thumbnail((300, 300))  # Resize the image if necessary
            self.em_photo = ImageTk.PhotoImage(em_img)
            self.em_label.config(image=self.em_photo)
            self.em_label.image = self.em_photo

    def create_widgets(self):
        # Create the "Back" button
        back_button = tk.Button(self, text="Powrót do galerii", command=self.back_to_gallery)
        back_button.pack(side="top", anchor="nw", padx=10, pady=10)

        # Create a frame to hold the images
        images_frame = tk.Frame(self)
        images_frame.pack(padx=10, pady=10)

        # Create a label for displaying the original image
        self.label = tk.Label(images_frame)
        self.label.pack(side="left", padx=5)

        # Create a label for displaying the _em image
        em_image_path = self.get_em_image_path(self.image_path)
        if not os.path.exists(em_image_path):
            file_name = os.path.join(os.path.basename(os.path.dirname(self.image_path)),
                                     os.path.basename(self.image_path))
            subprocess.run(["python", "reference_generator.py", file_name, '3.0', '1.0'])

        if os.path.exists(em_image_path):
            em_img = Image.open(em_image_path)
            em_img.thumbnail((150, 150))  # Resize the image if necessary
            self.em_photo = ImageTk.PhotoImage(em_img)
            self.em_label = tk.Label(images_frame, image=self.em_photo)
            self.em_label.pack(side="left", padx=5)

        # Create a label for displaying the image path
        self.path_label = tk.Label(self)
        self.path_label.pack(padx=10, pady=5)

        # Create entry fields and labels for cannySigma and blurSigma
        canny_label = tk.Label(self, text="Canny Sigma:")
        canny_label.pack(padx=10, pady=5)
        self.canny_sigma_entry = tk.Entry(self)
        self.canny_sigma_entry.pack(padx=10, pady=5)

        blur_label = tk.Label(self, text="Blur Sigma:")
        blur_label.pack(padx=10, pady=5)
        self.blur_sigma_entry = tk.Entry(self)
        self.blur_sigma_entry.pack(padx=10, pady=5)

        # Create the "Generuj referencję" button
        generate_button = tk.Button(self, text="Generuj referencję", command=self.generate_reference)
        generate_button.pack(padx=10, pady=10)

        # Create the "Przejdź do generacji" button
        generate_ref_button = tk.Button(self, text="Przejdź do generacji", command=self.go_to_generate)
        generate_ref_button.pack(padx=10, pady=10)

        # Set focus to the first entry field
        self.canny_sigma_entry.focus_set()

        # Validation functions
        validate_float = self.register(self.validate_float)

        # Apply validation to entry fields
        self.canny_sigma_entry.config(validate="key", validatecommand=(validate_float, "%P"))
        self.blur_sigma_entry.config(validate="key", validatecommand=(validate_float, "%P"))

        # Display the image if available
        self.set_image(self.image_path)

        # Update the image path label
        self.path_label.config(text="Image Path: " + (self.image_path or ""))

    def validate_float(self, new_value):
        if (new_value == ''):
            return True
        try:
            float(new_value)
            return True
        except ValueError:
            self.master.bell()  # Emit a system beep to alert the user
            self.clear_error_message()
            return False

    def clear_error_message(self):
        if self.error_label is not None:
            self.error_label.destroy()  # Destroy the error label if it exists
        self.error_label = tk.Label(self, text="Tylko wartości numeryczne", fg="red")
        self.error_label.pack(pady=5)
        self.error_label.after(2000, self.error_label.destroy)  # Clear the error message after 2 seconds

    def back_to_gallery(self):
        from gui.image_gallery import ImageGallery
        self.master.switch_view(ImageGallery)

    def get_em_image_path(self, image_path):
        directory, filename = os.path.split(image_path)
        base_filename, extension = os.path.splitext(filename)
        em_filename = f"{base_filename}_em.jpg"
        em_image_path = os.path.join(directory, em_filename)

        return em_image_path

    def generate_reference(self):
        canny_sigma = self.canny_sigma_entry.get()
        blur_sigma = self.blur_sigma_entry.get()
        file_name = os.path.join(os.path.basename(os.path.dirname(self.image_path)), os.path.basename(self.image_path))
        subprocess.run(["python", "reference_generator.py", file_name, canny_sigma, blur_sigma])
        self.update_em_image()

    def update_em_image(self):
        em_img = Image.open(self.get_em_image_path(self.image_path))
        em_img.thumbnail((300, 300))
        self.em_photo = ImageTk.PhotoImage(em_img)
        self.em_label.config(image=self.em_photo)
        self.em_label.image = self.em_photo

    def on_destroy(self):
        pass

    def go_to_generate(self):
        self.master.switch_view(GeneratorView, image_path = self.image_path)
