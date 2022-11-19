from tkinter import Tk, StringVar, BooleanVar
from tkinter.filedialog import askdirectory, askopenfile
from tkinter.ttk import Label, Radiobutton, Button, Checkbutton, Style
from pathlib import Path
from sys import exit
from json import load, dump
from os import startfile
from platform import system
from subprocess import Popen, run
from functools import reduce
from operator import getitem


def CreateUI():
    indentContent = 35
    header = StringVar(tkwindow, 'Deep Asset Discovery Tool')
    Label( tkwindow, textvariable=header, font= ('Helvetica 15 bold')).pack(pady=(0,5), anchor='w')
    about = StringVar(tkwindow, 'About:')
    Label( tkwindow, textvariable=about, font= ('Helvetica 12 underline')).pack(pady=(0,5), anchor='w')
    instructions = StringVar(tkwindow, "\
Welcome mod developers, DAD's primary purpose is to assist you\n\
with adding new items to the game. It does this by:\n\
    1) Creating a report on:\n\
        - Broken references in your mod,\n\
        - Naming schemes,\n\
        - Any missing downstream resource files,\n\
    2) Adding any missing resource files to your project.")
    Label( tkwindow, textvariable=instructions, font= ('Helvetica 10')).pack(pady=(0, 20), padx=(indentContent,0), anchor='w')
    Config['RunMode'] = StringVar(tkwindow, Config['RunMode'])
    Config['AddMissingFiles'] = BooleanVar(tkwindow, Config['AddMissingFiles'])
    Config['SelectedProjectFolder'] = BooleanVar(tkwindow, Config['SelectedProjectFolder'])
    options = StringVar(tkwindow, 'Runtime Options:')
    Label( tkwindow, textvariable=options, font= ('Helvetica 12 underline')).pack(pady=(0,5), anchor='w')
    for (runmode, description) in Config['RunModes'].items():
        Radiobutton(tkwindow, text = description, variable = Config['RunMode'], value = runmode
                    ).pack(side='top', anchor='w', pady=0, padx=(indentContent,0))
    Checkbutton(tkwindow, text='Optionally select Wolvenkit.CLI.exe to add missing resources', variable=Config['AddMissingFiles'], 
                onvalue=True, offvalue=False, command=onClickFindCLI
                ).pack(pady=(5,0), padx=(indentContent,0), anchor='w')
    Checkbutton(tkwindow, text="Select the project's source folder", variable=Config['SelectedProjectFolder'], 
                onvalue=True, offvalue=False, command=onClickFindProject
                ).pack(pady=(5,0), padx=(indentContent,0), anchor='w')
    Button(tkwindow, text= "Run Program", command=onClickRunProgram).pack(pady= 5, padx=(indentContent,0), anchor='w')
    tkwindow.mainloop()


def onClickFindCLI():
    if Config['AddMissingFiles'].get() == True:
        Config['WolvenKit.CLI'] = askopenfile(title='Select the WolvenKit.CLI executable file', filetypes =[("WolvenKit Console", "cp77tools.exe WolvenKit.CLI.exe")])
        if Config['WolvenKit.CLI'] == None:
            Config['AddMissingFiles'].set(False)
        else:
            Config['WolvenKit.CLI'] = Path(str(Config['WolvenKit.CLI'].name))
            if Config['WolvenKit.CLI'].suffix != '.exe':
                Config['WolvenKit.CLI'] = Path()
                Config['AddMissingFiles'].set(False)


def onClickFindProject():
    if Config['SelectedProjectFolder'].get() == True:
        Config['ProjectDirectory'] = Path(askdirectory(title="Select the project's source folder"))
        if Config['ProjectDirectory'] == None:
            Config['SelectedProjectFolder'].set(False)
        elif (Config['ProjectDirectory'] / 'raw').exists() and (Config['ProjectDirectory'] / 'archive').exists():
            Config['RawDirectory'] = Config['ProjectDirectory'] / 'raw'
            Config['ArchiveDirectory'] = Config['ProjectDirectory'] / 'archive'
            Config['SelectedProjectFolder'].set(True)
        else:
            Config['SelectedProjectFolder'].set(False)


def onClickRunProgram():
    if Config['SelectedProjectFolder'].get() == True:
        tkwindow.withdraw()
        RunDAD()


def RunDAD():
    if Config['RunMode'].get() == 'Discovery':
        # Collect data
        for DataBuffer['RawFile'] in Config['RawDirectory'].rglob('*.json'):
            if (GetData() == 'Success'):
                # Change absolute path to relative path
                DataBuffer['RawFile'] = str(DataBuffer['RawFile']).replace(str(Config['RawDirectory']),'')
                DiscoverData(key=None, value=DataBuffer['RawData'])
                CollectReferences(resourcefile=DataBuffer['RawFile'], resourcedata=DataBuffer['RawData'])
            else:
                print(f"File {DataBuffer['RawFile'].name} could not be converted to JSON for parsing.")    
        # Validate references
        ValidateReferences()
        DataBuffer['DiscoveryData'] = SortDictionary(DataBuffer['DiscoveryData'])
        DataBuffer['MissingFiles'] = sorted(DataBuffer['MissingFiles'])
        VerifyMissingFiles()
        if Config['AddMissingFiles'].get() == True:
            AddMissingFiles()
        ExportParse()
    # elif Config['RunMode'].get() == 'Change':
    #     for DataBuffer['RawFile'] in Config['RawDirectory'].rglob('*.json'):
    #         if (GetData() == 'Success'):
    #             LinkData() 
    #             print('')
    #         else:
    #             print(f"File {DataBuffer['RawFile'].name} could not be converted to JSON for parsing.")    
    #     ExportData()
    OpenFileExplorer(Config['ProjectDirectory'])
    exit('Done')


def GetData():
    if DataBuffer['RawFile'].exists():
        with open(DataBuffer['RawFile'], 'r', encoding='UTF-8', errors='ignore') as resource:
            DataBuffer['RawData'] = convertJSON(resource)
        if isinstance(DataBuffer['RawData'], dict):
            return 'Success'
    else:
        return False


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
                # Add all files to MissingFiles and then remove later in one batch search of .\archive
                if key.lower() == 'depotpath' and value not in DataBuffer['MissingFiles']:
                    DataBuffer['MissingFiles'].append(value)


# ReferenceData data structure of a resource resource that contains references
# to resources and values expected in those resources.
# LinkData{} = 
# |-- Resource[0]
# |   |-- dict(path, expected key, expected value)
# |   |-- dict(path, expected key, expected value)
# |   |-- dict(path, expected key, expected value)
# |-- Resource[1]
# |   |-- dict(path, expected key, expected value)
# |   |-- dict(path, expected key, expected value)
# |   |-- dict(path, expected key, expected value)
# |-- Resource[n-1]
# |   |-- dict(path, expected key, expected value)
# |   |-- dict(path, expected key, expected value)
# |   |-- dict(path, expected key, expected value)
def CollectReferences(resourcefile, resourcedata):
    # Critical identifier for each asset type
    ResourceTypePath = ['Data','RootChunk','$type']
    resourcetype = GetValueFromPath(ResourceTypePath, resourcedata).lower()
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
                referencepath = ['Data','RootChunk','appearances']
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
                    raRef = resourcefile[:resourcefile.index('.json')] #raRef == self
                    # Creater wrapper for references
                    if raRef not in DataBuffer['ReferenceData']:
                        DataBuffer['ReferenceData'][raRef] = []
                    for chunkmaterial in chunkmaterials:
                        DataBuffer['ReferenceData'][raRef].append(dict(drill=referencepath,key='name',value=chunkmaterial,flag=None))
        # Clear raRef for next reference block
        raRef = None
        if resourcedata['Data']['RootChunk'].get('localMaterialBuffer'):
            # Creater wrapper for references
            raRef = resourcefile[:resourcefile.index('.json')] #raRef == self
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
                                    DataBuffer['ReferenceData'][raRef].append(dict(drill=referencepath,key='index',value=i,mlsetup=value[k_val]['DepotPath'],flag=None))


# Verify references in downstream resources
def ValidateReferences():
    for resources in DataBuffer['ReferenceData']:
        # Change relative path into absolute path so the file can be opened
        DataBuffer['RawFile'] = Path(str(Config['RawDirectory']) + resources + '.json')
        if GetData() == 'Success':
            # Get each references that's expected in the resource
            for references in DataBuffer['ReferenceData'][resources]:
                # Drill into the arrays
                resourceref = GetValueFromPath(references['drill'], DataBuffer['RawData'])#[i]
                for ref in resourceref:
                    # APP and root entity have lists to parse through
                    if references['drill'][-1] == 'appearances':
                        ref = ref['Data']
                    for key, value in ref.items():
                        # Lower needed here instead of two lines below because sometimes it's type(int) and lower causes error
                        if isinstance(value, str):
                            value = value.lower()
                        if not isinstance(value, list):
                            if key.lower() == references['key'] and value == references['value']:
                                if references['drill'][-1] == 'materialEntries' and references['key'] == 'index':
                                    references['flag'] = ref['name']
                                else:
                                    references['flag'] = True
                                break
                    if references['flag'] != None:
                        break
                if references['flag'] == None:
                    references['flag'] = False


def GetValueFromPath(path, mapping):
    try:
        return reduce(getitem, path, mapping)
    except ValueError:
        return None


def VerifyMissingFiles():
    for file in reversed(DataBuffer['MissingFiles']):
        if (Config['ArchiveDirectory'] / file).exists():
            i = DataBuffer['MissingFiles'].index(file)
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


def AddMissingFiles():
    prg = str(Config['WolvenKit.CLI'])
    arg1 = 'unbundle'
    arg2 = Path('C:\\Program Files (x86)\\Steam\\steamapps\\common\\Cyberpunk 2077\\archive\\pc\\content')
    arg2 = f'-p "{arg2}"'
    arg3 = Config['ArchiveDirectory']
    arg3 = f'-o "{arg3}"'
    arg4 = ''
    for file in DataBuffer['MissingFiles']:
        if len(f'{prg} {arg1} {arg2} {arg3} {arg4}') > 240:
            arg4 = f'-w "{arg4}"'
            run(f'{prg} {arg1} {arg2} {arg3} {arg4}')
            arg4 = ''
        else:
            if arg4 == '':
                arg4 = f"{file}"
            else:
                arg4 += f"|{file}"
    if arg4 != '':
        arg4 = f'-w "{arg4}"'
        run(f'{prg} {arg1} {arg2} {arg3} {arg4}')


Config = {
'DiscoveryFile': 'discovery_DAD.json',
'ReferenceFile': 'reference_DAD.json',
'RunMode': 'Discovery',
'RunModes': {
    'Discovery': 'Create discovery files'
    #'Change': 'Import the reference file to update your project'
    },
'AddMissingFiles': False,
'SelectedProjectFolder': False,
'Discover': [
    'appearancename','appearanceresource',
    'componentname',
    'defaultappearance','depotpath',
    'meshappearance',
    'name'
    ],
'ProjectDirectory': Path('.'),
'RawDirectory': '',
'ArchiveDirectory': '',
'WolvenKit.CLI': Path()
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