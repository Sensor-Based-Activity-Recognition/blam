# default python imports
import json

# tkinter imports
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog

# utils code imports
from utils.wrangler import File
from utils.selector import Selector
from utils.dbconnector import Database

# get configs
with open("config.json", "r") as f:
    config = json.load(f)

# get config values
sensors = config["sensors"]
OneDriveFolder = config["OneDriveFolder"]
questdb_settings = config["questdb"]
dev = config["dev"]

# get database name
db_name = "dev" if dev else "prod"

# set up tkinter and hide root window
root = Tk()
root.withdraw()

# give file selector dialog
root.filename = filedialog.askopenfilename(
    initialdir=OneDriveFolder,
    title="Select file",
    filetypes=(("zip file", "*.zip"), ("json file", "*.json")),
)
# if no file is selected, exit program
if not root.filename:
    # show error message with tk
    messagebox.showerror("Error", "No file selected")
    # exit program
    exit(1)

# check if file has already been processed
short_filename = root.filename.split("/")[-1].split(".")[0]
if n_datavals := Database().get_scalar(
    f"SELECT count(*) AS value FROM {db_name} WHERE filename %3D '{short_filename}'"
):
    msg_box = messagebox.askyesno(
        "File already processed",
        f"File already processed with {n_datavals} values in Database. Continue?",
    )
    if not msg_box:
        exit(0)

# get file
file = File(path=root.filename, sensors=sensors)
data = file.get_data().to_pandas().set_index("time")

# get data selector
try:
    truncated_data = (
        Selector(
            df=data, title_prefix=root.filename.split("/")[-1], show_cols=sensors[:3]
        )
        .truncate()
        .reset_index(drop=False)
    )
except Exception as e:
    # show error message with tk
    messagebox.showerror("Error", e)
    # exit program
    exit(1)

# prompt if write to database
if messagebox.askyesno("Write to database", "Write to database?"):
    # write to database
    if status := file.write_data(questdb_settings, truncated_data, db_name):
        messagebox.showinfo("Success", "Write successful")
    else:
        messagebox.showerror("Error", "Write unsuccessful")

exit()
