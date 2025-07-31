import tkinter as tk
import subprocess
import os

# Paths to your .exe files
contestant_exe = os.path.abspath("dist/contestant_manage.exe")
image_form_exe = os.path.abspath("dist/image_form.exe")
repository_restore_exe = os.path.abspath("dist/repository_restore.exe")

def open_contestant_manager():
    subprocess.Popen(contestant_exe)

def open_image_form():
    subprocess.Popen(image_form_exe)

def repository_restore_form():
    subprocess.Popen(repository_restore_exe)

# Create the main window
root = tk.Tk()
root.title("Admin Control Panel")
root.geometry("300x200")

# Buttons
btn1 = tk.Button(root, text="Contestant Management", command=open_contestant_manager, width=25, height=2)
btn1.pack(pady=10)

btn2 = tk.Button(root, text="Event & News Update", command=open_image_form, width=25, height=2)
btn2.pack(pady=10)

btn3 = tk.Button(root, text="Restore Repository", command=repository_restore_form, width=25, height=2)
btn3.pack(pady=10)

# Run the GUI
root.mainloop()
