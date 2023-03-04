# default python imports
import json

# tkinter imports
from tkinter import *
from tkinter import filedialog

# utils code imports
from utils.wrangler import File
from utils.data_selector import DataSelector

# get configs
with open("config.json", "r") as f:
    config = json.load(f)

# get config values
sensors = config["sensors"]
OneDriveFolder = config["OneDriveFolder"]
questdb_settings = config["questdb"]

# give file selector dialog
root = Tk()
root.filename = filedialog.askopenfilename(
    initialdir=OneDriveFolder,
    title="Select file",
    filetypes=(("zip file", "*.zip"), ("json file", "*.json")),
)

# get file
file = File(path=root.filename, sensors=sensors)
data = file.get_data().to_pandas().set_index("time")

# get data selector
selector = DataSelector(
    df=data, title_prefix=root.filename.split("/")[-1], show_cols=sensors[:3]
)

# get truncated data
truncated_data = selector.truncate()

# write truncated data to database
# status = file.write_data(questdb_settings, truncated_data, "dev")
# print status of import
# print("Write successful: ", status)
