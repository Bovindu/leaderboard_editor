import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import subprocess
import re
import os
from git import Repo

# Path to the .tsx file
FILE_PATH = r"C:\Users\HR.Info\Documents\Leaderboard\leader_board\src\components\ImageSlideshow.tsx"
GIT_REPO_PATH = r"C:\Users\HR.Info\Documents\WLeaderboard\leader_board"

class SlideEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Slideshow Editor")

        self.slides = []
        self.selected_index = None

        # Layout: Left Listbox | Right Form
        self.left_frame = tk.Frame(root)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(self.left_frame, width=50)
        self.listbox.pack(pady=10)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        self.load_button = tk.Button(self.left_frame, text="Load Slides", command=self.load_slides)
        self.load_button.pack(fill=tk.X)

        #self.move_up_button = tk.Button(self.left_frame, text="Move Up", command=self.move_up)
        #self.move_up_button.pack(fill=tk.X)

        #self.move_down_button = tk.Button(self.left_frame, text="Move Down", command=self.move_down)
        #self.move_down_button.pack(fill=tk.X)

        self.remove_button = tk.Button(self.left_frame, text="Remove", command=self.remove_slide)
        self.remove_button.pack(fill=tk.X)

        # Form fields
        self.form_labels = ["Index", "URL", "Title", "Description"]
        self.form_entries = {}
        for label in self.form_labels:
            tk.Label(self.right_frame, text=label).pack()
            entry = tk.Entry(self.right_frame, width=60)
            entry.pack()
            self.form_entries[label] = entry

        self.add_update_button = tk.Button(self.right_frame, text="Add / Update Slide", command=self.add_or_update)
        self.add_update_button.pack(pady=5)

        self.update_file_button = tk.Button(self.right_frame, text="Update .tsx File", command=self.update_tsx)
        self.update_file_button.pack(pady=5)

        self.push_button = tk.Button(self.right_frame, text="Push to GitHub", command=self.push_to_git)
        self.push_button.pack(pady=5)

    def load_slides(self):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            self.slides = []
            self.listbox.delete(0, tk.END)

            pattern = re.compile(r'\{[\s\n]*id:\s*(\d+),\s*url:\s*"([^"]+)",\s*title:\s*"([^"]+)",\s*description:\s*"([^"]+)"[\s\n]*\}')
            for match in pattern.finditer(content):
                slide = {
                    "Index": len(self.slides),
                    "id": int(match.group(1)),
                    "url": match.group(2),
                    "title": match.group(3),
                    "description": match.group(4)
                }
                self.slides.append(slide)
                self.listbox.insert(tk.END, f'{slide["Index"]}: {slide["title"]}')
        except Exception as e:
            messagebox.showerror("Error", str(e))
    def push_to_git(self):
        try:
            repo = Repo(GIT_REPO_PATH)
            repo.git.add(update=True)
            repo.index.commit("Update leaderboard data")
            origin = repo.remote(name='origin')
            origin.push()
            messagebox.showinfo("Git", "Changes committed and pushed to GitHub.")
        except Exception as e:
            messagebox.showerror("Git Error", str(e))

    def on_select(self, event):
        try:
            index = self.listbox.curselection()[0]
            self.selected_index = index
            slide = self.slides[index]
            self.form_entries["Index"].delete(0, tk.END)
            self.form_entries["Index"].insert(0, str(slide["Index"]))
            self.form_entries["URL"].delete(0, tk.END)
            self.form_entries["URL"].insert(0, slide["url"])
            self.form_entries["Title"].delete(0, tk.END)
            self.form_entries["Title"].insert(0, slide["title"])
            self.form_entries["Description"].delete(0, tk.END)
            self.form_entries["Description"].insert(0, slide["description"])
        except IndexError:
            pass

    def add_or_update(self):
        try:
            idx = int(self.form_entries["Index"].get())
            url = self.form_entries["URL"].get()
            title = self.form_entries["Title"].get()
            desc = self.form_entries["Description"].get()

            if idx < len(self.slides):
                self.slides[idx].update({"url": url, "title": title, "description": desc})
            else:
                self.slides.append({"Index": idx, "id": idx + 1, "url": url, "title": title, "description": desc})
            self.refresh_list()
        except ValueError:
            messagebox.showerror("Invalid Input", "Index must be a number.")

    def move_up(self):
        i = self.selected_index
        if i is not None and i > 0:
            self.slides[i], self.slides[i - 1] = self.slides[i - 1], self.slides[i]
            self.refresh_list()

    def move_down(self):
        i = self.selected_index
        if i is not None and i < len(self.slides) - 1:
            self.slides[i], self.slides[i + 1] = self.slides[i + 1], self.slides[i]
            self.refresh_list()

    def remove_slide(self):
        i = self.selected_index
        if i is not None:
            del self.slides[i]
            self.refresh_list()

    def refresh_list(self):
        self.slides.sort(key=lambda s: s["Index"])
        self.listbox.delete(0, tk.END)
        for i, slide in enumerate(self.slides):
            slide["Index"] = i
            slide["id"] = i + 1
            self.listbox.insert(tk.END, f'{i}: {slide["title"]}')

    def update_tsx(self):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()

            new_array = "const slideshowImages: SlideshowImage[] = [\n"
            for slide in self.slides:
                new_array += f'''  {{
    id: {slide["id"]},
    url: "{slide["url"]}",
    title: "{slide["title"]}",
    description: "{slide["description"]}"
  }},\n'''
            new_array += "];"

            updated_content = re.sub(
                r'const slideshowImages: SlideshowImage\[\] = \[[\s\S]*?\];',
                new_array,
                content
            )

            with open(FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            messagebox.showinfo("Success", ".tsx file updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    


if __name__ == "__main__":
    root = tk.Tk()
    app = SlideEditorApp(root)
    root.mainloop()
