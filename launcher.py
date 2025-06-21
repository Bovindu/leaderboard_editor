import tkinter as tk
import subprocess
import sys
import os

# Helper to get python interpreter
PY = sys.executable

def run_script(script_name):
    path = os.path.join(os.path.dirname(__file__), script_name)
    subprocess.Popen([PY, path], cwd=os.path.dirname(__file__))

root = tk.Tk()
root.title("Launcher")

btn1 = tk.Button(root, text="Leader Board Editor", width=30,
                 command=lambda: run_script("contestant_manage.py"))
btn1.pack(pady=10)

btn2 = tk.Button(root, text="Slide Show Editor", width=30,
                 command=lambda: run_script("image_form.py"))
btn2.pack(pady=10)

root.mainloop()