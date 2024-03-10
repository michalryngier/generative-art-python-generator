import tkinter as tk

from gui.image_gallery import ImageGallery


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Application")
        self.geometry("1024x720")
        self.current_view = None
        self.switch_view(ImageGallery)

    def switch_view(self, new_view_class, **kwargs):
        if self.current_view:
            self.current_view.on_destroy()
            self.current_view.destroy()
        self.current_view = new_view_class(self, **kwargs)
        self.current_view.pack(fill="both", expand=True)

    def open_new_window(self, window, **kwargs):
        new_window = window(self, **kwargs)
        new_window.geometry("1024x720")


if __name__ == "__main__":
    app = Application()
    app.mainloop()
