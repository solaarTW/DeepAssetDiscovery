# Search mode selection UI
from tkinter import *
from tkinter.ttk import *
# Folder dialog compatible with Windows, Unix, and macOS
from tkinter.filedialog import askdirectory
# Measure screen width to resolve tkwindow
import tkinter.font as tkfont
# File handling and cancel buttons
import os
import sys
import platform
import subprocess
# Read JSON parse files
import json
# Recursion library
from pathlib import Path
# Use append to manage duplicate keys
from collections import defaultdict
# Optionally sort dictionary
from operator import itemgetter


# Create UI for runtime settings and then pass control off to the code
def CreateTkWindow():
    # Calculate resolution of screen for dynamic resizing
    font = tkfont.Font(family="Consolas", size=10, weight="normal")
    width = 0
    height = 1
    # Identify the quantity of characters to fill the largest width and height
    for key, val in ScriptParameters['SearchModes'].items():
        if len(key+val) > width:
            width = len(key+val)
        else:
            None # housekeeping
        height += 1
    # Uneducated calculations for the dynamic resizing
    width = width * font.measure("m")
    height = round(100/(height*2)) * font.measure("m") * len(ScriptParameters['SearchModes'])
    # Hopes and prayers
    tkwindow.geometry(f"{width}x{height}")
    # Tkinter string variable that will anchor the radiobutton selections
    ScriptParameters['SearchMode'] = StringVar(tkwindow, "Include")
    # ScriptParameters['SortMode'] = StringVar(tkwindow, "Chronological")
    header = StringVar()
    # Create radiobuttons for all the search modes
    label = Label( tkwindow, textvariable=header, font= ('Helvetica 15 underline')).pack(anchor=W)
    header.set("Choose what keys to filter for:")
    for (searchmode, description) in ScriptParameters['SearchModes'].items():
        Radiobutton(tkwindow, text = description, variable = ScriptParameters['SearchMode'],
            value = searchmode).pack(side = TOP, anchor=W, ipady = 5)
    # Checkbutton(tkwindow, text='Sort output alphabetically', variable=ScriptParameters['SortMode'], onvalue='Alphabetic', offvalue='Chronological').pack()
    Button(tkwindow, text= "Set wkit project's raw folder", command=onClick).pack(pady= 10, anchor=W)
    # Infinite loop terminated in the onClick definition
    tkwindow.mainloop()


# tkinter button action to start the recursion and then stop the program when the parsing is done.
# I have no idea why, but this program ends at this definition.
def onClick():
    RunMode(ScriptParameters['SearchMode'].get())
    DumpBuffer()
    open_file(ScriptParameters['ProjectDirectory'])
    tkwindow.destroy()


# Open file explorer at the dump file
def open_file(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


# Convert file to JSON format
# Input: file from ProjectDirectory[]
# Output: JSON format or None
def convertJSON(tup):                                                                                                                                    
    try:                                                                           
        tup_json = json.load(tup)                                                 
        return tup_json                                                            
    except ValueError as error:  # includes JSONDecodeError                           
        return None 


# Evaluate project files and initiate recursion
# Input: ScriptParameters['SearchModes']
# Output: None (except the dummy light I guess)
def RunMode(mode):
    tkwindow.minsize()

    # Folder dialog prompt
    ScriptParameters['ProjectDirectory'] = askdirectory(title='Select Folder', initialdir='.') # shows dialog box and return the path
    # Assign path to the output file
    ScriptParameters['OutputFile'] = f"{ScriptParameters['ProjectDirectory']}/{ScriptParameters['OutputFile']}"

    # Delete file from previous runtime
    if (os.path.isfile(ScriptParameters['OutputFile'])):
        os.remove(ScriptParameters['OutputFile'])
    else:
        None # housekeeping
    
    # Identify JSON files in the folder structure
    RawFiles = list(Path(ScriptParameters['ProjectDirectory']).rglob("*.json"))
    # Start recursion
    FoundBuffer['NumberOfFiles'] = len(RawFiles) - 1
    for FoundBuffer['cntIndex'], RawFile in enumerate(RawFiles):
        # Prepare the raw file for parsing
        data = open(RawFile, 'r', encoding="UTF-8", errors="ignore")
        data = convertJSON(data)
        if isinstance(data, dict):
            FoundBuffer['Data'][RawFile.name] = dict()
            ScriptParameters['InputFile'] = RawFile.name
            data['EndOfFile'] = 'EndOfFile'
            RecursiveSearch(val=data, key=None)
        else:
            print(f"Could not convert {RawFile.name}")
    # Dummy light
    print("Done")


# Recursively drill down into JSON for specific key-value pairs
# Input 1: Primary constaint to evaluate,
# Input 2: Optional secondary holds meta info on primary constraint
# Input 3: Initiates buffer to hold values from primary constraint
# Output: None
# Step 1: Identify type(primary)
# Step 2: Recurse if possible or otherwise evaluate for FoundBuffer[]
# Step 3: Log primary value or dump FoundBuffer[] to file
def RecursiveSearch(val, key=None):
    # Dictory found -- dive into ScriptParameters
    if isinstance(val, dict):
        for k, v in val.items():
            RecursiveSearch(v, k)
    # List found -- dive into list
    elif isinstance(val, list):
        for v in val:
            RecursiveSearch(v, key)
    # String found -- validate and then record if valid
    elif isinstance(val, str):
        # Ignore hashes
        if (len(key) + len(val) < 200):
            # Include search mode
            if ScriptParameters['SearchMode'].get() == 'Include':
                # Filter for keys in the Include list
                if key.lower() in ScriptParameters['Include']:
                    BufferData(key, val)
                else:
                    None # housekeeping
            # Exclude search mode
            elif ScriptParameters['SearchMode'].get() == 'Exclude':
                # Filter out keys in the Exclude list
                if key.lower() not in ScriptParameters['Exclude']:
                    BufferData(key, val)
                else:
                    None # housekeeping
            # Neither search mode
            elif ScriptParameters['SearchMode'].get() == 'Neither':
                # Filter out keys in Include and Exclude lists
                if key.lower() not in [*ScriptParameters['Include'],*ScriptParameters['Exclude']]:
                    BufferData(key, val)
                else:
                    None # housekeeping
            # Discovery search mode
            elif ScriptParameters['SearchMode'].get() == 'Discovery':
                # Filter out keys in the Include list
                if val.lower() not in ScriptParameters['Include']:
                    BufferData(key, val)
                else:
                    None # housekeeping
            # Oohhhhh yeeaaaaahhhhhhhhhhh
            elif ScriptParameters['SearchMode'].get() == 'NoFilter':
                BufferData(key, val)
            # Unexpected error
            else:
                print(f"An Unexpected error occurred file {ScriptParameters['InputFile']} at {key}:::{val}\n")
        else:
            None # housekeeping
    # Integer, float, or null found -- ignore
    elif isinstance(val, (int, float)) or val==None:
        None # I dunno, future development?
    # Unexpected error -- print for prosterity
    else:
        if len(val) + len(key) < 100:
            print(f"An Unexpected error occurred at {ScriptParameters['InputFile']}:::{Secondary}:::{Primary}\n")
        else:
            None # housekeeping


def BufferData(key, val):   
    # Shorthand the variable for easier reading below
    file = ScriptParameters['InputFile']
    # Compile a list of linked files
    if key == 'DepotPath' and val not in FoundBuffer['MissingFiles']:
        FoundBuffer['MissingFiles'].append(val)
    else:
        None # housekeeping
    # If the key is not already buffered then add it
    if key not in FoundBuffer['Data'][file]:
        FoundBuffer['Data'][file][key] = val
    # If the value is not buffered yet and that index is a list then append the new value
    elif val not in FoundBuffer['Data'][file][key] and isinstance(FoundBuffer['Data'][file][key], list):
        FoundBuffer['Data'][file][key].append(val)
    # if the index is a string then change it to a list before appending it
    elif isinstance(FoundBuffer['Data'][file][key], str):
        tmp = FoundBuffer['Data'][file][key]
        FoundBuffer['Data'][file][key] = [tmp]
        FoundBuffer['Data'][file][key].append(val)
    # The value is already buffered and can be ignored
    else:
        None # housekeeping


# Remove files from the missing list that are in the project's archive folder
def RemoveArchiveFiles():
    # Replace ./raw with ./archive
    ArchiveLocation = (f"{str(ScriptParameters['ProjectDirectory'])[:-3]}archive")
    # Get all the archive files
    ArchiveFiles = str(list(Path(ArchiveLocation).rglob("*.*")))
    for ArchiveFile in ArchiveFiles:
        # Substring file's path to get /base...
        ArchiveFile = ArchiveFile[ArchiveFile.find("base"):-5]
        if ArchiveFile in FoundBuffer['MissingFiles']:
            # Remove alreaady added file from the missing list
            FoundBuffer['MissingFiles'].remove(ArchiveFile)


# Recursive sort definition for dictionary values
def sort_dict(item: dict):
    # If the current recursion is a list then sort it alphabetically
    for k, v in sorted(item.items()):
        item[k] = sorted(v) if isinstance(v, list) else v
    # Recursively drill into JSON while it remains a dictionary.
    return {k: sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(item.items())}


# Dump discovery buffer to file in JSON format
def DumpBuffer():
    # Identify and sort files missing from the project
    RemoveArchiveFiles()
    # Sort buffer and convert to dict for json.dump
    FoundBuffer['Data'] = dict(sort_dict(FoundBuffer['Data']))
    # Sort the missing files
    FoundBuffer['MissingFiles'] = sorted(FoundBuffer['MissingFiles'])
    # Move the missing files into the export section of the buffer
    FoundBuffer['Data']['Missing_Files'] = FoundBuffer['MissingFiles']
    # Dump buffer to file
    with open(ScriptParameters['OutputFile'], 'w', encoding='UTF-8') as output:
        json.dump(FoundBuffer['Data'], output, ensure_ascii=False, indent=4)
    output.close()
    FoundBuffer['Data'] = dict() # Reset buffer


# Declare buffer queue of found keys during the recursive definition
FoundBuffer = {
    'cntIndex': 0,
    'NumberOfFiles': 0,
    'Data': dict(),
    'MissingFiles':[]
}


# Array of keywords to filter the recursion on
# SearchMode == Include ::: Find keys that are in this list
# SearchMode == Exclude ::: Ignore keys that are in this list
# SearchMode == Neither ::: Ignore keys that are in both lists
# SearchMode == Discovery ::: Ignore keys in the Include list
# SearchMode == NoFilter ::: You know how I like it. Just load me up and crash this computer
# SortMode == Chronological ::: Leave values as they were found in the files
# SortMode == Alphabetic ::: Sort FoundBuffer['Data'] and then each individual list aphabetically
ScriptParameters = {
    'ProjectDirectory': '',
    'InputFile': '',
    'OutputFile': 'out_DAD.json',
    'SearchMode': 'Include',
    'SearchModes': {
        "Include": "Only find linking properties",
        "Discovery": "Discovery mode that ignores known linking properties"
        # "Exclude": "Find all keys except ones in the Exclude list",
        # "Neither": "Find all keys except ones in the Include and Exclude list",
        # "NoFilter": "Do not filter, Find all unique key-value pairs"
        },
    'SortMode': 'Chronological',
    'Include': [
        'appearancename','appearanceresource',
        'componentname',
        'defaultAppearance','depotpath',
        'meshappearance',
        'name'
    ],
    'Exclude': [
        '$type',
        'activationstate',
        'bodypart','bonename','bonenames','buffer','bufferid','bufferrefid','bytes',
        'callbackaction','clnumber','cltimestamp','colorscale','compression','constrainttype','cookingplatform',
        'datatype','density','devicestate','documenttype','EndOfFile','entryphasename','enumeratedtype','exporteddatetime',
        'fieldname','flatfeetgroupname','forceopendocumenttype',
        'gradientmode',
        'handleid','hingeaxis',
        'isoscriptcode',
        'languagecode','languageid','liftedfeetgroupname','linktype','lootstate',
        'mergemode','metallevelsin','metallevelsout','movexaxis','moveyaxis',
        'normalstrength',
        'onchildfailure','onchildsuccess',
        'parentweightmode','pe','periodname','perspective','projectiontype',
        'rootresolution','roughlevelsin','roughlevelsout',
        'streamtype','submitkey','swingy','swingz',
        'textdirection','timestampargument','twist','type',
        'vectorcoodrinatetype',
        'wkitjsonversion','wolvenkitversion',
        'x','y','z'
    ]
}


# main()
# Create the UI window
tkwindow = Tk()
CreateTkWindow()