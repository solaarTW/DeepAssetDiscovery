# Search mode selection UI
from tkinter import *
from tkinter.ttk import *
# Folder dialog compatible with Windows, Unix, and macOS
from tkinter.filedialog import askdirectory
# File handling and cancel buttons
import os
import sys
import platform
import subprocess
# Read JSON parse files
import json
# Recursion library
from pathlib import Path
from tkinter import ttk


# Create UI for runtime settings and then pass control off to the code
def CreateTkWindow():
    # Tkinter string variable that will anchor the radiobutton selections
    ScriptParameters['RunMode'] = StringVar(tkwindow, 'Discovery')
    header = StringVar()
    # Create radiobuttons for all the search modes
    Label( tkwindow, textvariable=header, font= ('Helvetica 15 underline')).pack(anchor=W)
    header.set('Deep Asset Discovery Tool:')
    for (runmode, description) in ScriptParameters['RunModes'].items():
        Radiobutton(tkwindow, text = description, variable = ScriptParameters['RunMode'], value = runmode
                    ).pack(side = TOP, anchor=W, ipady = 0)
    Button(tkwindow, text= "Set wkit project's raw folder", command=onClick
           ).pack(pady= 5, anchor=W)
    # Infinite loop terminated in the onClick definition
    tkwindow.mainloop()


# tkinter button action to start the recursion and then stop the program when the parsing is done.
# I have no idea why, but this program ends at this definition.
def onClick():
    RunMode(ScriptParameters['RunMode'].get())
    DumpBuffer()
    open_file(ScriptParameters['ProjectDirectory'])
    sys.exit() 


# Open file explorer at the dump file
def open_file(path):
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


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
# Input: ScriptParameters['RunModes']
# Output: None (except the dummy light I guess)
def RunMode(mode):
    # Folder dialog prompt
    ScriptParameters['ProjectDirectory'] = askdirectory(title='Select Folder', initialdir='.') # shows dialog box and return the path
    # Close program if cancel is clicked
    sys.exit() if ScriptParameters['ProjectDirectory'] == '' else tkwindow.withdraw()

    # Assign path to the output files
    ScriptParameters['DiscoveryFile'] = f"{ScriptParameters['ProjectDirectory']}/{ScriptParameters['DiscoveryFile']}"
    ScriptParameters['ChangeFile'] = f"{ScriptParameters['ProjectDirectory']}/{ScriptParameters['ChangeFile']}"

    # Delete file from previous runtime
    if mode == 'Change':
        data[1] = open(ScriptParameters['ChangeFile'], 'r', encoding='UTF-8', errors='ignore')
    else:
        if os.path.isfile(ScriptParameters['DiscoveryFile']):
            os.remove(ScriptParameters['DiscoveryFile'])
        else:
            None # housekeeping
        if (os.path.isfile(ScriptParameters['ChangeFile'])):
            os.remove(ScriptParameters['ChangeFile'])
        else:
            None # housekeeping


    # Identify JSON files in the folder structure
    RawFiles = list(Path(ScriptParameters['ProjectDirectory']).rglob('*.json'))
    # Start recursion
    FoundBuffer['NumberOfFiles'] = len(RawFiles) - 1
    for FoundBuffer['cntIndex'], RawFile in enumerate(RawFiles):
        # Prepare the raw file for parsing
        if mode == 'Change':
            data[0] = open(RawFile, 'w', encoding='UTF-8', errors='ignore')
        else:
            data = open(RawFile, 'r', encoding='UTF-8', errors='ignore')
        data = convertJSON(data)
        if isinstance(data, dict):
            FoundBuffer['Data'][RawFile.name] = dict()
            FoundBuffer['RawFile'] = RawFile.name
            RecursiveSearch(val=data, key=None)
        else:
            print(f"Could not convert {RawFile.name}")
    # Dummy light
    print('Done')


# Recursively drill down into JSON for specific key-value pairs
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
        if len(key) + len(val) < 200:
            # Filter for keys in the Dsicover list
            if key.lower() in ScriptParameters['Discovery']:
                BufferData(key, val)
            else:
                None # housekeeper
        else:
            None # housekeeping
    # Integer, float, or null found -- ignore
    elif isinstance(val, (int, float)) or val==None:
        None # I dunno, future development?
    # Unexpected error -- print for prosterity
    else:
        if len(val) + len(key) < 200:
            print(f"An Unexpected error occurred at {FoundBuffer['RawFile']}:::{key}:::{val}\n")
        else:
            None # housekeeping


def BufferData(key, val):   
    # Shorthand the variable for easier reading below
    file = FoundBuffer['RawFile']
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
    ArchiveFiles = str(list(Path(ArchiveLocation).rglob('*.*')))
    for ArchiveFile in ArchiveFiles:
        # Substring file's path to get /base...
        ArchiveFile = ArchiveFile[ArchiveFile.find('base'):-5]
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


# Return collapsed buffer for the file change_DAD.json
def CollapseBuffer(item: dict):
    for key, val in item.items():
        if isinstance(val, dict):
            CollapseBuffer(val)
        elif isinstance(val, list):
            for v in val:
                if key not in FoundBuffer['CollapsedData']:
                    FoundBuffer['CollapsedData'][key] = dict()
                if (key, {v: ""}) not in FoundBuffer['CollapsedData'].items():
                    FoundBuffer['CollapsedData'][key][v] = ""
                else:
                    None # housekeeping
        else:
            if key not in FoundBuffer['CollapsedData']:
                FoundBuffer['CollapsedData'[key]] = dict()
            if (key, {v: ""}) not in FoundBuffer['CollapsedData'].items():
                FoundBuffer['CollapsedData'][key][v] = ""
            else:
                None # housekeeping


# Dump discovery buffer to file in JSON format
def DumpBuffer():
    # Identify and sort files missing from the project
    RemoveArchiveFiles()
    # Sort buffer and convert to dict for json.dump
    FoundBuffer['Data'] = dict(sort_dict(FoundBuffer['Data']))
    # Sort the missing files
    FoundBuffer['MissingFiles'] = sorted(FoundBuffer['MissingFiles'])
    # Dump buffer to change file
    CollapseBuffer(FoundBuffer['Data'])
    # Sort buffer and convert to dict for json.dump
    FoundBuffer['CollapsedData'] = dict(sort_dict(FoundBuffer['CollapsedData']))
    with open(ScriptParameters['ChangeFile'], 'w', encoding='UTF-8') as output_c:
        json.dump(FoundBuffer['CollapsedData'], output_c, ensure_ascii=False, indent=4)
    FoundBuffer.pop('CollapsedData', None)
    # Move the missing files into the export section of the buffer
    FoundBuffer['Data']['Missing_Files'] = FoundBuffer['MissingFiles']
    # Dump buffer to discovery file
    with open(ScriptParameters['DiscoveryFile'], 'w', encoding='UTF-8') as output_d:
        json.dump(FoundBuffer['Data'], output_d, ensure_ascii=False, indent=4)
    output_d.close()
    output_c.close()


# Declare buffer queue of found keys during the recursive definition
FoundBuffer = {
    'cntIndex': 0,
    'NumberOfFiles': 0,
    'RawFile': '',
    'Data': dict(),
    'MissingFiles':[],
    'CollapsedData': dict()
}


# Outer wrapper of configuration
ScriptParameters = {
    'ProjectDirectory': '',
    'ChangeFile': 'change_DAD.json',
    'DiscoveryFile': 'discovery_DAD.json',
    'RunMode': 'Discovery',
    'RunModes': {
        'Discovery': 'Discover linked values in JSON files.',
        'Change': 'Import change_DAD.json to update your assets.'
        },
    'Discovery': [
        'appearancename','appearanceresource',
        'componentname',
        'defaultAppearance','depotpath',
        'meshappearance',
        'name'
    ]
}


# main()
# Create the UI window
tkwindow = Tk()
CreateTkWindow()