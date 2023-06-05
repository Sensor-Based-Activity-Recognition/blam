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

# Load configuration file
with open("config.json", "r") as f:
    config = json.load(f)

# Extract individual settings from the loaded configuration file
sensors = config["sensors"]
OneDriveFolder = config["OneDriveFolder"]
questdb_settings = config["questdb"]
dev = config["dev"]

# Choose the database name based on the 'dev' flag in the configuration file
db_name = "dev" if dev else "prod"

# Initialize a Tkinter GUI application
root = Tk()
root.withdraw()  # Hide the main window

# Show a file selection dialog
root.filename = filedialog.askopenfilename(
    initialdir=OneDriveFolder,
    title="Select file",
    filetypes=(("all", "*.*"), ("zip file", "*.zip"), ("json file", "*.json")),
)
# If no file was selected, show an error message and exit the program
if not root.filename:
    messagebox.showerror("Error", "No file selected")  # Show an error message
    exit(1)  # Exit the program

# Check if the selected file has already been processed
person = root.filename.split("/")[-2]
activity = root.filename.split("/")[-3]
short_filename = root.filename.split("/")[-1].split(".")[0]

# Check for existing data in the database related to the selected file
if n_datavals := Database().get_scalar(
    f"SELECT count(*) AS value FROM {db_name} WHERE filename %3D '{short_filename}' and person %3D '{person}' and activity %3D '{activity}'"
):
    # Ask the user whether to continue if the file was already processed
    msg_box = messagebox.askyesno(
        "File already processed",
        f"File already processed with {n_datavals} values in Database. Continue?",
    )
    if not msg_box:
        exit(0)

# Read the selected file
file = File(path=root.filename, sensors=sensors)
data = file.get_data().to_pandas().set_index("time")

# Select a subset of the data with a user-defined interface
try:
    truncated_data = (
        Selector(
            df=data, title_prefix=root.filename.split("/")[-1], show_cols=sensors[:3]
        )
        .truncate()
        .reset_index(drop=False)
    )
except Exception as e:
    # Show an error message if an exception occurred and exit the program
    messagebox.showerror("Error", e)
    exit(1)

# Ask the user whether to write the selected data to the database
if messagebox.askyesno("Write to database", "Write to database?"):
    # Write the selected data to the database
    if status := file.write_data(questdb_settings, truncated_data, db_name):
        messagebox.showinfo("Success", "Write successful")  # Show a success message
    else:
        messagebox.showerror("Error", "Write unsuccessful")  # Show an error message

exit()  # Exit the program
