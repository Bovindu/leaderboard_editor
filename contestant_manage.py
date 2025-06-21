import os
import re
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from git import Repo, GitCommandError
import json
import sys
from datetime import datetime

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config_form.json')

def get_base_path():
    """Get the base path for the application, handling PyInstaller bundled files."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Running in development mode
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path

def read_config():
    try:
        base_path = get_base_path()
        config_path = os.path.join(base_path, 'config_form.json')
        
        with open(config_path, 'r') as file:
            config = json.load(file)
            
            # Validate required fields
            if not all(key in config for key in ['LEADERBOARD_FILE', 'CONSTANTS_FILE', 'GIT_REPO_PATH', 'DATE_CONFIG']):
                raise ValueError("Missing required fields in config.json")
                
            return config
    except FileNotFoundError:
        messagebox.showerror("Error", "config_form.json file not found")
        raise
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Invalid JSON in config file")
        raise
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read config: {str(e)}")
        raise

# Read configuration
try:
    config = read_config()
    LEADERBOARD_FILE = config['LEADERBOARD_FILE']
    CONSTANTS_FILE = config['CONSTANTS_FILE']
    GIT_REPO_PATH = config['GIT_REPO_PATH']
    DATE_CONFIG = config['DATE_CONFIG']
    
except Exception as e:
    messagebox.showerror("Error", str(e))
    exit()

def update_date():
    try:
        
        # Get today's date in YYYY/MM/DD format
        today_date = datetime.now().strftime("%Y/%m/%d")

        new_content = f"""export const DATE_CONFIG = {{
            
            LATEST_UPDATE: '{today_date}'
            }} as const; 
            """

        with open(DATE_CONFIG, 'w') as file:
            file.write(new_content)

    except Exception as e:
        messagebox.showerror("Error", str(e))


# Helper: read and parse the TypeScript data file
def read_leaderboard():
    imports = []
    data_text = ""
    contestants = []
    with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Collect import lines and separate array content
    in_array = False
    brace_level = 0
    obj_buffer = ""
    for line in lines:
        stripped = line.strip()
        # Keep import lines
        if stripped.startswith("import "):
            imports.append(line.rstrip())
            continue
        # Find start of array
        if stripped.startswith("export const leaderboardData"):
            in_array = True
            continue
        if not in_array:
            continue
        # Process lines inside array
        # End of array
        if '];' in stripped:
            in_array = False
            # If buffer has content, close it
            if obj_buffer.strip():
                contestants.append(parse_contestant(obj_buffer))
            break
        # Accumulate object text by tracking braces
        for ch in line:
            if ch == '{':
                brace_level += 1
                if brace_level == 1:
                    obj_buffer = "{"
                elif brace_level > 1:
                    obj_buffer += "{"
            elif ch == '}':
                brace_level -= 1
                obj_buffer += "}"
                if brace_level == 0:
                    # Finished one object
                    contestants.append(parse_contestant(obj_buffer))
                    obj_buffer = ""
            else:
                if brace_level >= 1:
                    obj_buffer += ch

    return imports, contestants

# Parse a single "{...}" object text into a dict
def parse_contestant(obj_str):
    c = {}
    # Extract fields with regex
    rank_match = re.search(r"rank\s*:\s*(\d+)", obj_str)
    name_match = re.search(r"name\s*:\s*\"([^\"]+)\"", obj_str)
    hours_match = re.search(r"hours\s*:\s*(\d+)", obj_str)
    money_match = re.search(r"money\s*:\s*(\d+)", obj_str)
    pic_match = re.search(r"profilePic\s*:\s*([^,\}]+)", obj_str)

    if rank_match:
        c['rank'] = int(rank_match.group(1))
    if name_match:
        c['name'] = name_match.group(1)
    if hours_match:
        c['hours'] = int(hours_match.group(1))
    if money_match:
        c['money'] = int(money_match.group(1))
    if pic_match:
        pic_val = pic_match.group(1).strip()
        # Remove quotes if they exist
        if pic_val.startswith('"') or pic_val.startswith("'"):
            pic_val = pic_val.strip('"\'')
            c['profilePic'] = pic_val
            c['picType'] = 'url'
        else:
            c['profilePic'] = pic_val
            c['picType'] = 'import'
    return c

# Write the updated contestants back to the TS file
def write_leaderboard(imports, contestants):
    # Sort by hours desc and update ranks
    contestants.sort(key=lambda x: x['hours'], reverse=True)
    for i, c in enumerate(contestants, start=1):
        c['rank'] = i

    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        # Write import lines
        for imp_line in imports:
            f.write(imp_line + '\n')
        f.write("\nexport const leaderboardData = [\n")
        # Write each contestant
        for c in contestants:
            name = c['name']
            hours = c['hours']
            money = c['money']
            rank = c['rank']
            if c.get('picType') == 'url':
                pic_str = f"\"{c['profilePic']}\""
            else:
                pic_str = c['profilePic']
            line = f"  {{ rank: {rank}, name: \"{name}\", hours: {hours}, money: {money}, profilePic: {pic_str} }},\n"
            f.write(line)
        f.write("];\n")

# Sort contestants and refresh the Listbox display
def sort_and_refresh():
    contestants.sort(key=lambda x: x['hours'], reverse=True)
    for i, c in enumerate(contestants, start=1):
        c['rank'] = i
    listbox.delete(0, tk.END)
    for c in contestants:
        listbox.insert(tk.END, f"{c['rank']} - {c['name']}")

# Button callbacks
def add_contestant():
    name = entry_name.get().strip()
    hours_str = entry_hours.get().strip()
    money_str = entry_money.get().strip()
    pic = entry_pic.get().strip()
    if not name or not hours_str:
        messagebox.showerror("Input Error", "Name and Hours are required")
        return
    try:
        hours = int(hours_str)
        money = int(money_str) if money_str else 0
    except ValueError:
        messagebox.showerror("Input Error", "Hours and Money must be integers")
        return
    # Determine pic type
    if pic.startswith("http://") or pic.startswith("https://"):
        pic_type = 'url'
    elif pic:  # assume import identifier if not blank
        pic_type = 'import'
    else:
        pic_type = 'url'
    new_contestant = {'name': name, 'hours': hours, 'money': money, 'profilePic': pic, 'picType': pic_type}
    contestants.append(new_contestant)
    sort_and_refresh()
    clear_form()

def update_contestant():
    sel = listbox.curselection()
    if not sel:
        return
    index = sel[0]
    name = entry_name.get().strip()
    hours_str = entry_hours.get().strip()
    money_str = entry_money.get().strip()
    pic = entry_pic.get().strip()
    if not name or not hours_str:
        messagebox.showerror("Input Error", "Name and Hours are required")
        return
    try:
        hours = int(hours_str)
        money = int(money_str)
    except ValueError:
        messagebox.showerror("Input Error", "Hours must be an integer")
        return
    if pic.startswith("http://") or pic.startswith("https://"):
        pic_type = 'url'
    elif pic:
        pic_type = 'import'
    else:
        pic_type = 'url'
    # Update the selected contestant's data
    contestants[index]['name'] = name
    contestants[index]['hours'] = hours
    contestants[index]['money'] = money
    contestants[index]['profilePic'] = pic
    contestants[index]['picType'] = pic_type
    sort_and_refresh()
    clear_form()

def delete_contestant():
    sel = listbox.curselection()
    if not sel:
        return
    index = sel[0]
    del contestants[index]
    sort_and_refresh()
    clear_form()

def on_select(evt):
    sel = listbox.curselection()
    if not sel:
        return
    index = sel[0]
    c = contestants[index]
    entry_name.delete(0, tk.END)
    entry_name.insert(0, c['name'])
    entry_hours.delete(0, tk.END)
    entry_hours.insert(0, str(c['hours']))
    entry_money.delete(0, tk.END)
    entry_money.insert(0, str(c.get('money', 0)))
    entry_pic.delete(0, tk.END)
    entry_pic.insert(0, c['profilePic'])

def clear_form():
    entry_name.delete(0, tk.END)
    entry_hours.delete(0, tk.END)
    entry_money.delete(0, tk.END)
    entry_pic.delete(0, tk.END)
    listbox.selection_clear(0, tk.END)

def update_constants():
    update_date()
    try:
        pool_price = entry_pool_price.get()
        price_per_hour = entry_price_per_hour.get()
        total_hour = entry_total_hour.get()

        if not pool_price.isdigit() or not price_per_hour.isdigit():
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")
            return
        
        # Get today's date in YYYY/MM/DD format
        today_date = datetime.now().strftime("%Y/%m/%d")

        new_content = f"""export const PRICE_CONFIG = {{
            POOL_PRICE: {pool_price},
            PRICE_PER_HOUR: {price_per_hour},
            TOTAL_HOURS: {total_hour},
            }} as const; 
            """

        with open(CONSTANTS_FILE, 'w') as file:
            file.write(new_content)

        messagebox.showinfo("Success", "Constants updated successfully.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def submit_changes():
    update_date()
    write_leaderboard(import_lines, contestants)
    messagebox.showinfo("Saved", "leaderboard-data.ts has been updated.")

def open_constants():
    subprocess.Popen(['C:\\Windows\\notepad.exe', CONSTANTS_FILE])

def commit_and_push():
    try:
        repo = Repo(GIT_REPO_PATH)
        origin = repo.remote(name='origin')

        # Stash local changes if any
        if repo.is_dirty(untracked_files=True):
            repo.git.stash('save', 'Auto-stash before pull')

        # Pull with rebase
        origin.pull(rebase=True)

        # Apply stashed changes back (if any)
        stashes = repo.git.stash('list')
        if stashes:
            repo.git.stash('pop')

        # Stage, commit, and push
        repo.git.add(update=True)
        repo.index.commit("Update leaderboard data")
        origin.push()

        messagebox.showinfo("Git", "Changes pulled, committed, and pushed to GitHub.")
    except GitCommandError as git_err:
        messagebox.showerror("Git Error", f"Git command failed:\n{git_err}")
    except Exception as e:
        messagebox.showerror("Git Error", str(e))

# Initialize data
import_lines, contestants = read_leaderboard()
contestants.sort(key=lambda x: x['hours'], reverse=True)

# Build GUI
root = tk.Tk()
root.title("Leaderboard Editor")
root.geometry("600x400")

# Listbox of contestants
frame_list = tk.Frame(root)
frame_list.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
listbox = tk.Listbox(frame_list, width=30)
listbox.pack(fill=tk.BOTH, expand=True)
listbox.bind('<<ListboxSelect>>', on_select)

# Form entries and buttons
frame_form = tk.Frame(root)
frame_form.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

tk.Label(frame_form, text="Contestant Update").grid(row=0, column=0, columnspan=2, pady=5)
tk.Label(frame_form, text="Session Update").grid(row=7, column=0, columnspan=2, pady=(15, 5))

tk.Label(frame_form, text="Name:").grid(row=1, column=0, sticky=tk.W)
entry_name = tk.Entry(frame_form)
entry_name.grid(row=1, column=1, pady=2, sticky="ew")

tk.Label(frame_form, text="Hours:").grid(row=2, column=0, sticky=tk.W)
entry_hours = tk.Entry(frame_form)
entry_hours.grid(row=2, column=1, pady=2, sticky="ew")

tk.Label(frame_form, text="Money:").grid(row=3, column=0, sticky=tk.W)
entry_money = tk.Entry(frame_form)
entry_money.grid(row=3, column=1, pady=2, sticky="ew")

tk.Label(frame_form, text="ProfilePic:").grid(row=4, column=0, sticky=tk.W)
entry_pic = tk.Entry(frame_form)
entry_pic.grid(row=4, column=1, pady=2, sticky="ew")

tk.Label(frame_form, text="Pool Prize:").grid(row=8, column=0, sticky=tk.W)
entry_pool_price = tk.Entry(frame_form)
entry_pool_price.grid(row=8, column=1, pady=2, sticky="ew")

tk.Label(frame_form, text="Prize Per Hour:").grid(row=9, column=0, sticky=tk.W)
entry_price_per_hour = tk.Entry(frame_form)
entry_price_per_hour.grid(row=9, column=1, pady=2, sticky="ew")

tk.Label(frame_form, text="Total Hour:").grid(row=10, column=0, sticky=tk.W)
entry_total_hour = tk.Entry(frame_form)
entry_total_hour.grid(row=10, column=1, pady=2, sticky="ew")

# Buttons
btn_add = tk.Button(frame_form, text="Add", command=add_contestant)
btn_add.grid(row=5, column=0, pady=5, sticky="ew")
btn_update = tk.Button(frame_form, text="Update", command=update_contestant)
btn_update.grid(row=5, column=1, pady=5, sticky="ew")
btn_delete = tk.Button(frame_form, text="Delete", command=delete_contestant)
btn_delete.grid(row=6, column=0, pady=5, sticky="ew")
btn_submit = tk.Button(frame_form, text="Submit", command=submit_changes)
btn_submit.grid(row=6, column=1, pady=5, sticky="ew")
btn_open = tk.Button(frame_form, text="Submit", command=update_constants)
btn_open.grid(row=11, column=0, columnspan=2, pady=5, sticky="ew")
btn_git = tk.Button(frame_form, text="Commit & Push", command=commit_and_push, fg='#FF0000')
btn_git.grid(row=12, column=0, columnspan=2, pady=(20, 0), sticky="ew")

# Make form columns expand
frame_form.columnconfigure(1, weight=1)

# Populate initial listbox
for c in contestants:
    listbox.insert(tk.END, f"{c['rank']} - {c['name']}")

root.mainloop()
