import os
import tkinter as tk
from PIL import Image, ImageTk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Application  # Forward declaration for typing


class ImageGallery(tk.Frame):
    master: 'Application'

    def __init__(self, master: 'Application', folder_name="__out"):
        super().__init__(master)
        self.scrollbar = None
        self.canvas_frame = None
        self.canvas = None
        self.cards = []
        self.master = master
        self.folder_name = folder_name
        self.images = self.load_images()
        self.create_widgets()

    def load_images(self):
        images = []
        out_dir = os.path.join(os.getcwd(), self.folder_name)  # Get the full path to the __out directory
        for folder_name in os.listdir(out_dir):
            folder_path = os.path.join(out_dir, folder_name)
            if os.path.isdir(folder_path):
                for file_name in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file_name)
                    if os.path.isfile(file_path) and "_em" not in file_name and not file_name.startswith('.') and any(
                            file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                        images.append(file_path)
        return images

    def create_widgets(self):
        # Create the canvas and scrollbar
        self.canvas = tk.Canvas(self)
        self.canvas_frame = tk.Frame(self.canvas)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Create images on canvas
        self.canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")
        self.populate_images()

        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)  # Bind mouse wheel scrolling

    def populate_images(self):
        # Populate images on the canvas
        row, col = 0, 0
        for image_path in self.images:
            folder_name = os.path.basename(os.path.dirname(image_path))
            img = Image.open(image_path)
            img.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(img)

            # Create a frame to hold the image and folder name label
            card_frame = tk.Frame(self.canvas_frame, bd=1, relief="solid")
            card_frame.grid(row=row, column=col, padx=5, pady=5)

            # Create a label for the image
            card = tk.Label(card_frame, image=photo, cursor="hand2", bd=0, highlightthickness=0, borderwidth=0)
            card.image = photo  # To prevent garbage collection
            card.config(image=card.image)
            card.pack(padx=5, pady=5)

            # Bind mouse click event to open new view with image path
            card.bind("<Button-1>", lambda event, path=image_path: self.on_click(path))

            # Create a label for the folder name
            folder_label = tk.Label(card_frame, text=folder_name)
            folder_label.pack()

            col += 1
            if col == 3:  # Change the number of columns according to your preference
                col = 0
                row += 1
            self.cards.append(card_frame)

    def on_click(self, image_path):
        from gui.image_view import ImageView
        self.master.switch_view(ImageView, image_path=image_path)

    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  # Scroll down
            self.canvas.yview_scroll(1, "units")

    def on_destroy(self):
        self.canvas.unbind_all("<MouseWheel>")
