from tkinter.ttk import Label, Radiobutton, Button
from tkinter import Tk, StringVar
from tkinter.filedialog import askdirectory
from pathlib import Path
from pathlib import PurePath
from sys import exit
from json import load, dump
from os import startfile
from platform import system
from subprocess import Popen
from functools import reduce
from operator import getitem


def CreateUI():
    header = StringVar(tkwindow, 'Deep Asset Discovery Tool')
    Label( tkwindow, textvariable=header, font= ('Helvetica 15 underline')).pack(anchor='w')
    Config['RunMode'] = StringVar(tkwindow, Config['RunMode'])
    for (runmode, description) in Config['RunModes'].items():
        Radiobutton(tkwindow, text = description, variable = Config['RunMode'], value = runmode
                    ).pack(side='top', anchor='w', ipady = 0)
    Button(tkwindow, text= "Select project's source directory", command=onClick
           ).pack(pady= 5, anchor='w')
    tkwindow.mainloop()


def onClick():
    GetDirectories()
    # if Config['RunMode'].get() == 'Discovery':
    for DataBuffer['RawFile'] in Config['RawDirectory'].rglob('*.json'):
        if (GetData() == 'Success'):
            DataBuffer['RawFile'] = str(DataBuffer['RawFile']).replace(str(Config['RawDirectory']),'')
            DiscoverData(key=None, value=DataBuffer['RawData'])
            ReferenceCheck(resourcefile=DataBuffer['RawFile'], resourcedata=DataBuffer['RawData'])
        else:
            print(f"File {DataBuffer['RawFile'].name} could not be converted to JSON for parsing.")    
    DataBuffer['DiscoveryData'] = SortDictionary(DataBuffer['DiscoveryData'])
    DataBuffer['MissingFiles'] = sorted(DataBuffer['MissingFiles'])
    VerifyMissingFiles()
    ExportParse()
    # elif Config['RunMode'].get() == 'Change':
    #     for DataBuffer['RawFile'] in Config['RawDirectory'].rglob('*.json'):
    #         if (GetData() == 'Success'):
    #             #LinkData() 
    #             print('')
    #         else:
    #             print(f"File {DataBuffer['RawFile'].name} could not be converted to JSON for parsing.")    
    #    # ExportData()
    OpenFileExplorer(Config['ProjectDirectory'])
    exit('Done')


def GetDirectories():
    while Config['ProjectDirectory'] == Path('.'):
        Config['ProjectDirectory'] = Path(askdirectory(title='Select Folder', initialdir='.'))
    else:
        Config['RawDirectory'] = Config['ProjectDirectory'] / 'raw'
        Config['ArchiveDirectory'] = Config['ProjectDirectory'] / 'archive'
        if not Config['RawDirectory'].exists():
            exit('Raw directory not found at that location.')
        elif not Config['ArchiveDirectory'].exists():
            exit('Archive directory not found at that location.')
        else:
            tkwindow.withdraw()


def GetData():
    # DataBuffer['RawData'] = open(DataBuffer['RawFile'], 'r', encoding='UTF-8', errors='ignore')
    with open(DataBuffer['RawFile'], 'r', encoding='UTF-8', errors='ignore') as resource:
        DataBuffer['RawData'] = convertJSON(resource)
    if isinstance(DataBuffer['RawData'], dict):
        return 'Success' 


def convertJSON(tup):                                                                                                                                    
    try:                                                                           
        tup_json = load(tup)                                                 
        return tup_json                                                            
    except ValueError as error:  # includes JSONDecodeError                           
        return None 


def DiscoverData(value, key):
    if isinstance(value, dict):
        for k, v in value.items():
            DiscoverData(key=k, value=v)
    if isinstance(value, list):
        for v in value:
            DiscoverData(key=key, value=v)
    if isinstance(value, str):
        if len(key) + len(value) < 200:
            if key.lower() in Config['Discover']:
                # Declare keys
                if DataBuffer['RawFile'] not in DataBuffer['DiscoveryData']:
                    DataBuffer['DiscoveryData'][DataBuffer['RawFile']] = dict()
                if key not in DataBuffer['DiscoveryData'][DataBuffer['RawFile']]:
                    DataBuffer['DiscoveryData'][DataBuffer['RawFile']][key] = []
                if value not in DataBuffer['DiscoveryData'][DataBuffer['RawFile']][key]:
                    DataBuffer['DiscoveryData'][DataBuffer['RawFile']][key].append(value)
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
        dump(DataBuffer['DiscoveryData'], output, ensure_ascii=False, indent=4)
    file = Config['ReferenceFile'] = f"{Config['ProjectDirectory']}/{Config['ReferenceFile']}"
    with open(file, 'w', encoding='UTF-8', errors='ignore') as output:
        dump(DataBuffer['ReferenceData'], output, ensure_ascii=False, indent=4)
    output.close()


# Open file explorer at the dump file
def OpenFileExplorer(path):
    if system() == 'Windows':
        startfile(path)
    elif system() == 'Darwin':
        Popen(['open', path])
    else:
        Popen(['xdg-open', path])


def CheckResourceType(path, mapping):
    try:
        return reduce(getitem, path, mapping)
    except ValueError:
        return None


# ReferenceData data structure of a resource resource that contains references
# to resources and values expected in those resources.
# LinkData{} = 
# |-- Resource[] (DepotPath)
# |   |-- dictpath[]
# |   |-- key
# |   |-- expected value
# |-- Resource[] (DepotPath)
# |   |-- dictpath[]
# |   |-- key
# |   |-- expected value
# |-- Resource[] (DepotPath)
# |   |-- dictpath[]
# |   |-- key
# |   |-- expected value
#
def ReferenceCheck(resourcefile, resourcedata):
    # Critical identifier for each asset type
    ResourceTypePath = ['Data','RootChunk','$type']
    resourcetype = CheckResourceType(ResourceTypePath, resourcedata).lower()
    # ENT resource found
    if resourcetype == 'ententitytemplate':
        if resourcedata['Data']['RootChunk'].get('appearances'):
            # Collect references
            referencepath = ['Data','RootChunk','appearances']
            for appearance in resourcedata['Data']['RootChunk']['appearances']:
                for k, v in appearance.items():
                    if k.lower() == 'appearanceresource':
                        if appearance[k].get('DepotPath') is not None:
                            raRef = f"\\{appearance[k]['DepotPath']}"
                    elif k.lower() == 'appearancename':
                        appearancename = v
                # Cache references
                if raRef is not None:
                    # Create wrapper for references
                    if raRef not in DataBuffer['ReferenceData']:
                        DataBuffer['ReferenceData'][raRef] = []
                    DataBuffer['ReferenceData'][raRef].append(dict(drill=referencepath,key='name',value=appearancename,flag=None))
            # Clear raRef for next reference block
            raRef = None
        elif resourcedata['Data']['RootChunk'].get('components'):
            # Collect references
            referencepath = ['Data','RootChunk','appearances']
            for component in resourcedata['Data']['RootChunk']['components']:
                raRef=None
                for k, v in component.items():
                    if k.lower() == 'mesh':
                        if component[k].get('DepotPath') is not None:
                            raRef = f"\\{component[k]['DepotPath']}"
                    elif k.lower() == 'meshappearance':
                        meshappearance = v
                # Cache references
                if raRef is not None:
                    # Create wrapper for references
                    if raRef not in DataBuffer['ReferenceData']:
                        DataBuffer['ReferenceData'][raRef] = []
                    DataBuffer['ReferenceData'][raRef].append(dict(drill=referencepath,key='name',value=meshappearance,flag=None))
    # APP resource found
    elif resourcetype == 'appearanceappearanceresource':
        if resourcedata['Data']['RootChunk'].get('appearances'):
            # Collect references
            # skipping referencepath_app, only needed for overrides, will build into next version
            for appearance in resourcedata['Data']['RootChunk']['appearances']:
                referencepath = ['Data','RootChunk','appearance']
                # Collect references
                for component in appearance['Data']['components']:
                    for k_comp, v_comp in component.items():
                        if k_comp.lower() == 'meshappearance':
                            meshappearance = v_comp
                        elif k_comp.lower() == 'mesh':
                            if component[k_comp].get('DepotPath') is not None:
                                raRef = f"\\{component[k_comp]['DepotPath']}"
                # Cache references
                if raRef is not None:
                    # Create wrapper for references
                    if raRef not in DataBuffer['ReferenceData']:
                        DataBuffer['ReferenceData'][raRef] = []
                    DataBuffer['ReferenceData'][raRef].append(dict(drill=referencepath,key='name',value=meshappearance,flag=None))
    # MESH resource found
    elif resourcetype == 'cmesh':
        if resourcedata['Data']['RootChunk'].get('appearances'):
            referencepath = ['Data','RootChunk','materialEntries']
            chunkmaterials = []
            # Collect references
            for appearance in resourcedata['Data']['RootChunk']['appearances']:
                for k_app, v_app in appearance['Data'].items():
                    if k_app.lower() == 'chunkmaterials':
                        chunkmaterials += v_app
                # Cache references
                if len(chunkmaterials) > 0:
                    raRef = resourcefile #raRef == self
                    # Creater wrapper for references
                    if raRef not in DataBuffer['ReferenceData']:
                        DataBuffer['ReferenceData'][raRef] = []
                    for chunkmaterial in chunkmaterials:
                        DataBuffer['ReferenceData'][raRef].append(dict(drill=referencepath,key='name',value=chunkmaterial,flag=None))
        # Clear raRef for next reference block
        raRef = None
        if resourcedata['Data']['RootChunk'].get('localMaterialBuffer'):
            # Creater wrapper for references
            raRef = resourcefile #raRef == self
            if raRef not in DataBuffer['ReferenceData']:
                DataBuffer['ReferenceData'][raRef] = []
            referencepath = ['Data','RootChunk','materialEntries']
            #Collect references
            for i, materialentry in enumerate(resourcedata['Data']['RootChunk']['localMaterialBuffer']['materials']):
                for k_mat in materialentry.keys():
                    if k_mat.lower() == 'values':
                        for value in materialentry[k_mat]:
                            for k_val in value.keys():
                                if k_val.lower() == 'multilayersetup':
                                    # Cache references
                                    DataBuffer['ReferenceData'][raRef].append(dict(drill=referencepath,key='index',value=i,comment=value[k_val]['DepotPath'],flag=None))


Config = {
    'DiscoveryFile': 'discovery_DAD.json',
    'ReferenceFile': 'reference_DAD.json',
    'RunMode': 'Discovery',
    'RunModes': {
        'Discovery': 'Export any discovered links in your project',
        'Change': 'Import the reference file to update your project'
        },
    'Discover': [
        'appearancename','appearanceresource',
        'componentname',
        'defaultAppearance','depotpath',
        'meshappearance',
        'name'
        ],
    'ProjectDirectory': Path('.'),
    'RawDirectory': '',
    'ArchiveDirectory': '',
    }


DataBuffer = {
    'DiscoveryData': dict(), #Export discovery cache
    'ReferenceData': dict(), #Export reference cache
    'RawFile': '',
    'RawData': dict(),
    'ArchiveFile': '',
    'ArchiveData': dict(),
    'MissingFiles': []
    }


tkwindow = Tk()
CreateUI()