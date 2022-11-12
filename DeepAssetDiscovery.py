from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askdirectory
import os
import pathlib
import sys
import platform
import subprocess
import json
from pathlib import Path
from tkinter import ttk


def CreateUI():
    header = StringVar(tkwindow, 'Deep Asset Discovery Tool')
    Label( tkwindow, textvariable=header, font= ('Helvetica 15 underline')).pack(anchor=W)
    Config['RunMode'] = StringVar(tkwindow, Config['RunMode'])
    for (runmode, description) in Config['RunModes'].items():
        Radiobutton(tkwindow, text = description, variable = Config['RunMode'], value = runmode
                    ).pack(side = TOP, anchor=W, ipady = 0)
    Button(tkwindow, text= "Select project's source directory", command=onClick
           ).pack(pady= 5, anchor=W)
    tkwindow.mainloop()


def onClick():
    GetFiles()
    if Config['RunMode'].get() == 'Discovery':
        for DataBuffer['RawFile'] in Config['RawDirectory'].rglob('*.json'):
            if (GetData() == 'Success'):
                DataBuffer['RawFile'] = str(DataBuffer['RawFile']).replace(str(Config['RawDirectory']),'')
                ParseData(key=None, value=DataBuffer['RawData'])
            else:
                print(f"File {DataBuffer['RawFile'].name} could not be converted to JSON for parsing.")    
        DataBuffer['DiscoveryData'] = SortDictionary(DataBuffer['DiscoveryData'])
        DataBuffer['MissingFiles'] = sorted(DataBuffer['MissingFiles'])
        # DataBuffer['LinkData'] = SortDictionary(DataBuffer['LinkData'])
        VerifyMissingFiles()
        ExportParse()
    elif Config['RunMode'].get() == 'Change':
        for DataBuffer['RawFile'] in Config['RawDirectory'].rglob('*.json'):
            if (GetData() == 'Success'):
                LinkData()
            else:
                print(f"File {DataBuffer['RawFile'].name} could not be converted to JSON for parsing.")    
        ExportData()
    OpenFileExplorer(Config['ProjectDirectory'])
    sys.exit('Done')


def GetFiles():
    Config['ProjectDirectory'] = pathlib.Path(askdirectory(title='Select Folder', initialdir='.'))
    if Config['ProjectDirectory'] == '':
        sys.exit('Closing program because the cancel button was clicked.')
    else:
        Config['RawDirectory'] = Config['ProjectDirectory'] / 'raw'
        Config['ArchiveDirectory'] = Config['ProjectDirectory'] / 'archive'
        if not Config['RawDirectory'].exists():
            sys.exit('Raw directory not found at that location.')
        elif not Config['ArchiveDirectory'].exists():
            sys.exit('Archive directory not found at that location.')
        else:
            tkwindow.withdraw()


def GetData():
    DataBuffer['RawData'] = open(DataBuffer['RawFile'], 'r', encoding='UTF-8', errors='ignore')
    DataBuffer['RawData'] = convertJSON(DataBuffer['RawData'])
    if isinstance(DataBuffer['RawData'], dict):
        return 'Success' 


def convertJSON(tup):                                                                                                                                    
    try:                                                                           
        tup_json = json.load(tup)                                                 
        return tup_json                                                            
    except ValueError as error:  # includes JSONDecodeError                           
        return None 


def ParseData(value, key):
    if isinstance(value, dict):
        for k, v in value.items():
            ParseData(key=k, value=v)
    if isinstance(value, list):
        for v in value:
            ParseData(key=key, value=v)
    if isinstance(value, str):
        if len(key) + len(value) < 200:
            if key.lower() in Config['Discover']:
                # Declare keys
                if DataBuffer['RawFile'] not in DataBuffer['DiscoveryData']:
                    DataBuffer['DiscoveryData'][DataBuffer['RawFile']] = dict()
                if key not in DataBuffer['DiscoveryData'][DataBuffer['RawFile']]:
                    DataBuffer['DiscoveryData'][DataBuffer['RawFile']][key] = []
                # if key not in DataBuffer['LinkData']:
                #     DataBuffer['LinkData'][key] = dict()
                # Add discovered value
                if value not in DataBuffer['DiscoveryData'][DataBuffer['RawFile']][key]:
                    DataBuffer['DiscoveryData'][DataBuffer['RawFile']][key].append(value)
                # if value not in DataBuffer['LinkData'][key]:
                #     DataBuffer['LinkData'][key][value] = ''
                # Add missing file
                if key.lower() == 'depotpath' and value not in DataBuffer['MissingFiles']:
                    DataBuffer['MissingFiles'].append(value)


def VerifyMissingFiles():
    for i, file in enumerate(DataBuffer['MissingFiles']):
        if (Config['ArchiveDirectory'] / file).exists():
            DataBuffer['MissingFiles'].pop(i)
    DataBuffer['DiscoveryData']['MissingFiles'] = DataBuffer['MissingFiles']


def SortDictionary(item: dict):
    # Lists
    for k, v in sorted(item.items()):
        item[k] = sorted(v) if isinstance(v, list) else v
    # Dictionaries
    return {k: SortDictionary(v) if isinstance(v, dict) else v for k, v in sorted(item.items())}


def ExportParse():
    file = Config['DiscoveryFile'] = f"{Config['ProjectDirectory']}/{Config['DiscoveryFile']}"
    with open(file, 'w', encoding='UTF-8', errors='ignore') as output:
        json.dump(DataBuffer['DiscoveryData'], output, ensure_ascii=False, indent=4)
    # file = Config['LinkFile'] = f"{Config['ProjectDirectory']}/{Config['LinkFile']}"
    # with open(file, 'w', encoding='UTF-8', errors='ignore') as output:
    #     json.dump(DataBuffer['LinkData'], output, ensure_ascii=False, indent=4)
    output.close()



# Open file explorer at the dump file
def OpenFileExplorer(path):
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


Config = {
    'DiscoveryFile': 'discovery_DAD.json',
    'LinkFile': 'change_DAD.json',
    'RunMode': 'Discovery',
    'RunModes': {
        'Discovery': 'Export any discovered links in your project',
        'Change': 'Import the change file to update your project'
        },
    'Discover': [
        'appearancename','appearanceresource',
        'componentname',
        'defaultAppearance','depotpath',
        'meshappearance',
        'name'
    ],
    'ProjectDirectory': '',
    'RawDirectory': '',
    'ArchiveDirectory': '',
}


DataBuffer = {
    'DiscoveryData': dict(),
    'LinkData': dict(),
    'RawFile': '',
    'RawData': dict(),
    'ArchiveFile': '',
    'ArchiveData': dict(),
    'MissingFiles': []
}


tkwindow = Tk()
CreateUI()