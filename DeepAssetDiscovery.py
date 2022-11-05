# Search mode selection UI
from tkinter import *
from tkinter.ttk import *
# Folder dialog compatible with Windows, Unix, and macOS
from tkinter.filedialog import askdirectory
# Measure screen width to resolve tkwindow
import tkinter.font as tkfont
# File handling
import os
# Break on the cancel button
import sys
# Read JSON parse files
import json
# Recursion library
from pathlib import Path
# Use append to manage duplicate keys
from collections import defaultdict
# Optionally sort dictionary
from operator import itemgetter


# Evaluate project files and initiate recursion
# Input: ScriptParameters['SearchModes']
# Output: None (except the dummy light I guess)
def RunMode(mode):
    tkwindow.minsize()
    
    # Folder dialog prompt
    ProjectDirectory = askdirectory(title='Select Folder', initialdir='.') # shows dialog box and return the path
    # Assign path to the output file
    ScriptParameters['OutputFile'] = f"{ProjectDirectory}/{ScriptParameters['OutputFile']}"

    # Delete file from previous runtime
    if (os.path.isfile(ScriptParameters['OutputFile'])):
        os.remove(ScriptParameters['OutputFile'])
    
    # Identify JSON files in the folder structure
    RawFiles = list(Path(ProjectDirectory).rglob("*.json"))
    
    # Start recursion
    FoundBuffer['NumberOfFiles'] = len(RawFiles) - 1
    for FoundBuffer['cntIndex'], RawFile in enumerate(RawFiles):
        # Prepare the raw file for parsing
        data = open(RawFile, 'r', encoding="UTF-8", errors="ignore")
        data = convertJSON(data)
        if isinstance(data, dict):
            ScriptParameters['InputFile'] = RawFile.name
            data['EndOfFile'] = 'EndOfFile'
            RecursiveSearch(Primary=data, Secondary=None)
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
def RecursiveSearch(Primary, Secondary=None):
    # Dictory found -- dive into ScriptParameters
    if isinstance(Primary, dict):
        for key, val in Primary.items():
            RecursiveSearch(val, key)
    # List found -- dive into list
    elif isinstance(Primary, list):
        for val in Primary:
            RecursiveSearch(val, Secondary)
    # String found -- validate and then record if valid
    elif isinstance(Primary, str):
        # Ignore hashes
        if (len(Primary) + len(Secondary) < 200):
            # Include search mode
            if ScriptParameters['SearchMode'].get() == 'Include':
                # Filter for keys in the Include list
                if Secondary.lower() in ScriptParameters['Include']:
                    BufferData(Secondary, Primary)
            # Exclude search mode
            elif ScriptParameters['SearchMode'].get() == 'Exclude':
                # Filter out keys in the Exclude list
                if Secondary.lower() not in ScriptParameters['Exclude']:
                    BufferData(Secondary, Primary)
            # Neither search mode
            elif ScriptParameters['SearchMode'].get() == 'Neither':
                # Filter out keys in Include and Exclude lists
                if Secondary.lower() not in [*ScriptParameters['Include'],*ScriptParameters['Exclude']]:
                    BufferData(Secondary, Primary)
            # Discovery search mode
            elif ScriptParameters['SearchMode'].get() == 'Discovery':
                # Filter out keys in the Include list
                if Secondary.lower() not in ScriptParameters['Include']:
                    BufferData(Secondary, Primary)
            # Oohhhhh yeeaaaaahhhhhhhhhhh
            elif ScriptParameters['SearchMode'].get() == 'NoFilter':
                BufferData(Secondary, Primary)
            # Unexpected error
            else:
                print(f"An Unexpected error occurred at {Secondary}:::{Primary}\n")
        else:
            None # housekeeping
    # Integer, float, or null found -- ignore
    elif isinstance(Primary, (int, float)) or Primary==None:
        None # I dunno, future development?
    # Unexpected error -- print for prosterity
    else:
        if len(Primary) + len(Secondary) < 100:
            print(f"An Unexpected error occurred at {ScriptParameters['InputFile']}:::{Secondary}:::{Primary}\n")


def BufferData(Secondary, Primary):   
    key = f"{ScriptParameters['InputFile']}:::{Secondary}"
    # Check for a duplicate key
    if key not in FoundBuffer['Data']:
        FoundBuffer['Data'][key] = Primary
    # Duplicate key found, check if it already has the Primary
    elif isinstance(FoundBuffer['Data'][key], list) and Primary not in FoundBuffer['Data'][key]:
        FoundBuffer['Data'][key].append(Primary)
    # Cast string value to list[] value
    elif isinstance(FoundBuffer['Data'][key], str):
        tmp = FoundBuffer['Data'][key]
        FoundBuffer['Data'][key] = [tmp]
        FoundBuffer['Data'][key].append(Primary)
    #Duplicate in key and value
    else:
        None # housekeeping


def DumpBuffer():
    # Check sort mode for alpha, be default it remains chronological
    if ScriptParameters['SortMode'].get() == 'Alphabetic':
        # Case insensitive sort of dictionary
        FoundBuffer['Data'] = dict(sorted(FoundBuffer['Data'].items(), key=lambda i: i[0].lower()))
        # Case insensitive sort of lists
        for key, val in FoundBuffer['Data'].items():
            if isinstance(val, list):
                var = sorted(val, key=str.casefold)
    # Dump buffer to file
    with open(ScriptParameters['OutputFile'], 'a', encoding="UTF-8", errors="ignore") as output: 
        for key, val in FoundBuffer['Data'].items(): 
            output.write('%s:%s\n' % (key, val))
    output.close()
    FoundBuffer['Data'] = dict() # Reset buffer


# Convert file to JSON format
# Input: file from ProjectDirectory[]
# Output: JSON format or None
def convertJSON(tup):                                                                                                                                    
    try:                                                                           
        tup_json = json.load(tup)                                                 
        return tup_json                                                            
    except ValueError as error:  # includes JSONDecodeError                           
        return None 


# tkinter button action to start the recursion and then stop the program when the parsing is done.
# I have no idea why, but this program ends at this definition.
def onClick():
    RunMode(ScriptParameters['SearchMode'].get())
    DumpBuffer()
    tkwindow.destroy()


def CreateTkWindow():
    # Calculate resolution of screen for dynamic resizing
    font = tkfont.Font(family="Consolas", size=10, weight="normal")
    width = 0
    height = 5
    # Identify the quantity of characters to fill the largest width and height
    for key, val in ScriptParameters['SearchModes'].items():
        if len(key+val) > width:
            width = len(key+val)
        height += 1
    # Uneducated calculations for the dynamic resizing
    width = width * font.measure("m")
    height = height * font.measure("m") * len(ScriptParameters['SearchModes'])
    # Hopes and prayers
    tkwindow.geometry(f"{width}x{height}")


    # Tkinter string variable that will anchor the radiobutton selections
    ScriptParameters['SearchMode'] = StringVar(tkwindow, "Include")
    ScriptParameters['SortMode'] = StringVar(tkwindow, "Chronological")
    header = StringVar()
    # Create radiobuttons for all the search modes
    label = Label( tkwindow, textvariable=header, font= ('Helvetica 15 underline')).pack(anchor=W)
    header.set("Choose what keys to filter for:")
    for (searchmode, description) in ScriptParameters['SearchModes'].items():
        Radiobutton(tkwindow, text = description, variable = ScriptParameters['SearchMode'],
            value = searchmode).pack(side = TOP, anchor=W, ipady = 5)
    Checkbutton(tkwindow, text='Sort output alphabetically', variable=ScriptParameters['SortMode'], onvalue='Alphabetic', offvalue='Chronological').pack()
    Button(tkwindow, text= "Set wkit project's raw folder", command=onClick).pack(pady= 20)


    # Infinite loop terminated in the onClick definition
    tkwindow.mainloop()


# Declare buffer queue of found keys during the recursive definition
FoundBuffer = {
    'cntIndex': 0,
    'NumberOfFiles': 0,
    'Data': dict()
}
x = 0

# Array of keywords to filter the recursion on
# SearchMode == Include ::: Find keys that are in this list
# SearchMode == Exclude ::: Ignore keys that are in this list
# SearchMode == Neither ::: Ignore keys that are in both lists
# SearchMode == Discovery ::: Ignore keys in the Include list
# SearchMode == NoFilter ::: You know how I like it. Just load me up and crash this computer
# SortMode == Chronological ::: Leave values as they were found in the files
# SortMode == Alphabetic ::: Sort FoundBuffer['Data'] and then each individual list aphabetically
ScriptParameters = {
    'InputFile': '',
    'OutputFile': 'out_DAD.txt',
    'SearchMode': 'Include',
    'SearchModes': {
        "Include": "Only find keys that are in the Include list",
        "Discovery": "Find all keys except ones in the Include list",
        "Exclude": "Find all keys except ones in the Exclude list",
        "Neither": "Find all keys except ones in the Include and Exclude list",
        "NoFilter": "Do not filter, Find all unique key-value pairs"
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