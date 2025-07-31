import os
import shutil
import stat
import subprocess
import tkinter as tk
from tkinter import messagebox

FOLDER_PATH = r"D:\Leaderboard\page\leader_board"
REPO_URL = "https://github.com/Bovindu/leader_board.git"

# Handle permission error
def handle_remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def delete_and_clone():
    try:
        if os.path.exists(FOLDER_PATH):
            shutil.rmtree(FOLDER_PATH, onerror=handle_remove_readonly)
            print("Deleted existing folder.")

        subprocess.check_call(["git", "clone", REPO_URL, FOLDER_PATH])
        messagebox.showinfo("Success", "Repository cloned successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")

# GUI
root = tk.Tk()
root.title("Reset Repository")

btn = tk.Button(root, text="Reset Leaderboard Repo", command=delete_and_clone, width=40)
btn.pack(padx=20, pady=20)

root.mainloop()
