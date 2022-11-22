from tkinter import Tk, LabelFrame
from tkinter.filedialog import askdirectory, askopenfile
from tkinter.ttk import Label, Button
from pathlib import Path
from sys import exit
from json import load, dump
from platform import system
from functools import reduce
from operator import getitem
# Libraries with hightened security
from subprocess import run # run wolvenkit.console to create JSON files
from os import makedirs # create temp folder for JSON files
from shutil import rmtree  # delete temp folder convert JSON files
from shutil import move # move JSON files into DepotPath structure for ref validation (wkit.cli convert limitation)
from subprocess import Popen # open macos/linux file browser when program ends
from os import startfile # open windows file browser when program ends


def CreateUI():
    # configure the root window
    tkwindow.title('Deep Asset Discovery Tool')
    # Create frame
    WelcomeFrame = LabelFrame(tkwindow, text='Welcome Mod Developers', font= ('Helvetica 12 bold'))
    WelcomeFrame.grid(column=0, row=0, padx=10, pady=(5, 0), sticky='w')
    # Create widgets
    WelcomeLabel = Label(WelcomeFrame, text=Config['WelcomeMessage'], anchor='w')
    WelcomeLabel.grid(column=0, row=0, ipady=5)
    # Create frame
    InstructionsFrame = LabelFrame(tkwindow, text='Instructions', font= ('Helvetica 12 bold'))
    InstructionsFrame.grid(padx=10, pady=(5, 10), sticky='w')
    # Create widgets
    Label(InstructionsFrame, text="Step 1) Select your project's source folder.", font= ('Helvetica 10')).grid(ipady=5, sticky='w')
    Button(InstructionsFrame, text="Select project folder", command=onClickFindProject).grid(padx=(40,0), sticky='w')
    Config['Project']['SelectLabel'] = Label(InstructionsFrame, text=Config['Project']['SelectLabel'])
    Config['Project']['SelectLabel'].grid(padx=(42,0), sticky='w')
    Label(InstructionsFrame, text="Step 2) Select the WolvenKit Console executable.", font= ('Helvetica 10')).grid(ipady=5, sticky='w')
    Button(InstructionsFrame, text="Select WolvenKit.Console", command=onClickFindConsole).grid(padx=(40,0), sticky='w')
    Config['Console']['SelectLabel'] = Label(InstructionsFrame, text=Config['Console']['SelectLabel'])
    Config['Console']['SelectLabel'].grid(padx=(42,0), sticky='w')
    Label(InstructionsFrame, text="-Optional- Select the Cyberpunk game folder to add missing resources to your project.", font= ('Helvetica 10')).grid(ipady=5, sticky='w')
    Button(InstructionsFrame, text="Select REDprelauncher.exe", command=onClickFindGame).grid(padx=(40,0), sticky='w')
    Config['Cyberpunk']['SelectLabel'] = Label(InstructionsFrame, text=Config['Cyberpunk']['SelectLabel'])
    Config['Cyberpunk']['SelectLabel'].grid(padx=(42,0), sticky='w')
    Label(InstructionsFrame, text="Step 3) Run the program.", font= ('Helvetica 10')).grid(ipady=5, sticky='w')
    Config['Project']['RunButton'] = Button(InstructionsFrame, text="Run Program", command=onClickRunCheck, state=Config['Project']['RunButton'])
    Config['Project']['RunButton'].grid(padx=(40,0), sticky='w')


def onClickFindProject():
    path = askdirectory(title="Select the project's source folder")
    if path in [None,Path(),'']:
        Config['Project']['RunButton'].configure(state="disabled")
        Config['Project']['SelectLabel'].configure(text='Not selected', foreground='black')
        Config['Project']['SourceDir'] = Path('None')
    else:
        path = Path(path)
        if not (path / 'raw').is_dir():
            Config['Project']['RunButton'].configure(state="disabled")
            Config['Project']['SelectLabel'].configure(text='raw folder not found at that location', foreground='red')
            Config['Project']['SourceDir'] = Path('None')
        elif not (path / 'archive').is_dir():
            Config['Project']['RunButton'].configure(state="disabled")
            Config['Project']['SelectLabel'].configure(text='archive folder not found at that location', foreground='red')
            Config['Project']['SourceDir'] = Path('None')
        else:
            Config['Project']['SelectLabel'].configure(text=path, foreground='black')
            Config['Project']['SourceDir'] = path
            Config['Project']['ArchiveDir'] = path / 'archive'
            Config['Project']['JSONDir'] = path / 'DAD_JSONFiles'
            if Config['Project']['JSONDir'].is_dir():
                rmtree(Config['Project']['JSONDir'])
            if Config['Console']['Dir'].exists():
                Config['Project']['RunButton'].configure(state="normal")


def onClickFindConsole():
    path = askopenfile(title='Select the WolvenKit.CLI executable file', filetypes =[("WolvenKit Console", "cp77tools.exe WolvenKit.CLI.exe")])
    if path in [None,Path(),'']:
        Config['Project']['RunButton'].configure(state="disabled")
        Config['Console']['SelectLabel'].configure(text='Not selected', foreground='black')
        Config['Console']['Dir'] = Path('None')
    else:
        path = Path(path.name)
        if path.suffix != '.exe':
            Config['Project']['RunButton'].configure(state="disabled")
            Config['Console']['SelectLabel'].configure(text='WolvenKit.CLI executable was not selected', foreground='red')
            Config['Console']['Dir'] = Path('None')
        else:
            Config['Console']['SelectLabel'].configure(text=path, foreground='black')
            Config['Console']['Dir'] = path
            if Config['Project']['SourceDir'].exists():
                Config['Project']['RunButton'].configure(state="normal")


def onClickFindGame():
    path = askopenfile(title='Select the REDprelauncher executable file', filetypes =[("Cyberpunk Prelauncher", "REDprelauncher.exe")])
    if path in [None,Path(),'']:
        Config['Cyberpunk']['SelectLabel'].configure(text='Not selected', foreground='black')
        Config['Cyberpunk']['Dir'] = Path('None')
    else:
        path = Path(path.name)
        if path.name != 'REDprelauncher.exe':
            Config['Cyberpunk']['SelectLabel'].configure(text='REDprelauncher executable was not selected', foreground='red')
            Config['Cyberpunk']['Dir'] = Path('None')
        elif (path.parent / 'archive\pc\content').is_dir():
            # Keep label's text as REDprelauncher.exe to avoid confusion
            Config['Cyberpunk']['SelectLabel'].configure(text=path, foreground='black')
            path = path.parent / 'archive\pc\content'
            Config['Cyberpunk']['Dir'] = path
        else:
            Config['Cyberpunk']['SelectLabel'].configure(text='Not selected', foreground='black')
            Config['Cyberpunk']['Dir'] = Path('None')


def onClickRunCheck():
    tkwindow.withdraw()
    RunDAD()


def RunDAD():
    parseFiles = True
    snapshotArchive = ['Flag',['ArchiveFileList']]
    while parseFiles == True:
        # Check if the person wants to add missing resources
        if Config['Cyberpunk']['Dir'].exists():
            snapshotArchive = CompareSnapshots(snapshotArchive[1])
            DataBuffer['RecentlyAddedFiles'] = snapshotArchive[0]
            if DataBuffer['RecentlyAddedFiles'] == False:
                # Terminate while loop
                Config['Cyberpunk']['Dir'] = Path('None')
        # Only serialize on first loop or if files were recently added
        if not Config['Project']['JSONDir'].is_dir() or DataBuffer['RecentlyAddedFiles'] == True:
            SerializeArchive()
            ## DELETE THIS FUNCTION WHEN CONVERT NATIVELY PUTS JSONS INTO DEPOTPATH STRUCTURE
            MoveSerializedFilesToDepotPath()
        for DataBuffer['JSONFile'] in Config['Project']['JSONDir'].rglob('*.json'):
            if (OpenJSONFile() == 'Success'):
                if Config['Cyberpunk']['Dir'].exists():
                    FindAllReferencedFiles(key=None, value=DataBuffer['JSONData'])
                else:
                    # Convert to relative path for the reports
                    DataBuffer['JSONFile'] = str(DataBuffer['JSONFile']).replace(str(Config['Project']['JSONDir']),'')
                    # Create report files on last loop of parseResources
                    BuildCacheForDiscoveryFile(key=None, value=DataBuffer['JSONData'])
                    BuildCacheForReferenceFile(resourcefile=DataBuffer['JSONFile'], resourcedata=DataBuffer['JSONData'])
                    # Terminate while loop
                    parseFiles = False
        PopAlreadyAddedFiles()
        if Config['Cyberpunk']['Dir'].exists():
            AddMissingFiles()
    ValidateReferenceCache()
    ExportParse()
    if Config['Project']['JSONDir'].is_dir():
        rmtree(Config['Project']['JSONDir'])
    OpenFileExplorer(Config['Project']['SourceDir'])
    exit('Done')


def CompareSnapshots(snapshotArchive_previous):
    snapshotArchive_current = []
    #for files in Path(Config['Project']['ArchiveDir']).rglob( '*[!.json].*' ):
    for files in Path(Config['Project']['ArchiveDir']).rglob( '*.*' ):
        snapshotArchive_current.append(files)
    snapshotArchive_current = sorted(snapshotArchive_current)
    if snapshotArchive_current != snapshotArchive_previous:
        return [True,snapshotArchive_current]
    else:
        return [False,None]


def SerializeArchive():
    Config['Project']['JSONDir'].mkdir(exist_ok=True)
    prg = str(Config['Console']['Dir'])
    arg1 = 'convert'
    arg2 = Config['Project']['ArchiveDir']
    arg2 = f's "{arg2}"'
    arg3 = Config['Project']['JSONDir']
    arg3 = f'-o "{arg3}"'
    run(f'{prg} {arg1} {arg2} {arg3}', shell=False)
# DELETE THIS FUNCTION ONCE WKIT CONSOLE CONVERTS FILES INTO THEIR DEPOTPATH
# CURRENTLY CONVERT PUTS ALL JSON FILES INTO A SINGLE LOCATION
def MoveSerializedFilesToDepotPath():
    for DataBuffer['JSONFile'] in Path(Config['Project']['JSONDir']).glob('*.json'):
        if OpenJSONFile() == 'Success':
            dest = DataBuffer['JSONData']['Header']['ArchiveFileName']
            dest = Config['Project']['JSONDir'] / dest.split("\\source\\archive\\")[1]
            if not (dest.parent).is_dir():
                makedirs(str(dest.parent))
            dest = dest.parent / (dest.name + '.json')
            move(DataBuffer['JSONFile'], dest)


def OpenJSONFile():
    if DataBuffer['JSONFile'].exists():
        with open(DataBuffer['JSONFile'], 'r', encoding='UTF-8', errors='ignore') as resource:
            DataBuffer['JSONData'] = convertJSON(resource)
        if isinstance(DataBuffer['JSONData'], dict):
            return 'Success'
    else:
        return False


def convertJSON(tup):
    try:
        tup_json = load(tup)
        return tup_json
    except ValueError as error:
        return None


def BuildCacheForDiscoveryFile(value, key):
    if isinstance(value, dict):
        for k, v in value.items():
            BuildCacheForDiscoveryFile(key=k, value=v)
    if isinstance(value, list):
        for v in value:
            BuildCacheForDiscoveryFile(key=key, value=v)
    if isinstance(value, str):
        if len(key) + len(value) < 200:
            if key.lower() in Config['Discover']:
                # Declare keys
                if DataBuffer['JSONFile'] not in DataBuffer['DiscoveredCache']:
                    DataBuffer['DiscoveredCache'][DataBuffer['JSONFile']] = dict()
                if key not in DataBuffer['DiscoveredCache'][DataBuffer['JSONFile']]:
                    DataBuffer['DiscoveredCache'][DataBuffer['JSONFile']][key] = []
                if value not in DataBuffer['DiscoveredCache'][DataBuffer['JSONFile']][key]:
                    DataBuffer['DiscoveredCache'][DataBuffer['JSONFile']][key].append(value)
                # Add all files to MissingFiles and then pop in 
                if key.lower() == 'depotpath' and value not in DataBuffer['MissingFiles']:
                    DataBuffer['MissingFiles'].append(value)


# ReferenceData data structure of a resource resource that contains references
# to resources and values expected in those resources.
# ReferenceCache{} = 
# |-- Resource[0]
# |   |-- dict(drill path, expected key, expected value)
# |   |-- dict(drill path, expected key, expected value)
# |   |-- dict(drill path, expected key, expected value)
# |-- Resource[1]
# |   |-- dict(drill path, expected key, expected value)
# |   |-- dict(drill path, expected key, expected value)
# |   |-- dict(drill path, expected key, expected value)
# |-- Resource[n-1]
# |   |-- dict(drill path, expected key, expected value)
# |   |-- dict(drill path, expected key, expected value)
# |   |-- dict(drill path, expected key, expected value)
def BuildCacheForReferenceFile(resourcefile, resourcedata):
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
                    if raRef not in DataBuffer['ReferenceCache']:
                        DataBuffer['ReferenceCache'][raRef] = []
                    DataBuffer['ReferenceCache'][raRef].append(dict(drill=referencepath,key='name',value=appearancename,flag=None))
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
                    if raRef not in DataBuffer['ReferenceCache']:
                        DataBuffer['ReferenceCache'][raRef] = []
                    DataBuffer['ReferenceCache'][raRef].append(dict(drill=referencepath,key='name',value=meshappearance,flag=None))
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
                    if raRef not in DataBuffer['ReferenceCache']:
                        DataBuffer['ReferenceCache'][raRef] = []
                    DataBuffer['ReferenceCache'][raRef].append(dict(drill=referencepath,key='name',value=meshappearance,flag=None))
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
                    if raRef not in DataBuffer['ReferenceCache']:
                        DataBuffer['ReferenceCache'][raRef] = []
                    for chunkmaterial in chunkmaterials:
                        DataBuffer['ReferenceCache'][raRef].append(dict(drill=referencepath,key='name',value=chunkmaterial,flag=None))
        # Clear raRef for next reference block
        raRef = None
        if resourcedata['Data']['RootChunk'].get('localMaterialBuffer'):
            # Creater wrapper for references
            raRef = resourcefile[:resourcefile.index('.json')] #raRef == self
            if raRef not in DataBuffer['ReferenceCache']:
                DataBuffer['ReferenceCache'][raRef] = []
            referencepath = ['Data','RootChunk','materialEntries']
            #Collect references
            for i, materialentry in enumerate(resourcedata['Data']['RootChunk']['localMaterialBuffer']['materials']):
                for k_mat in materialentry.keys():
                    if k_mat.lower() == 'values':
                        for value in materialentry[k_mat]:
                            for k_val in value.keys():
                                if k_val.lower() == 'multilayersetup':
                                    # Cache references
                                    DataBuffer['ReferenceCache'][raRef].append(dict(drill=referencepath,key='index',value=i,mlsetup=value[k_val]['DepotPath'],flag=None))


# Verify references in downstream resources
def ValidateReferenceCache():
    for resources in DataBuffer['ReferenceCache']:
        # Change relative path into absolute path so the file can be opened
        DataBuffer['JSONFile'] = Path(str(Config['Project']['JSONDir']) + resources + '.json')
        if OpenJSONFile() == 'Success':
            # Get each references that's expected in the resource
            for references in DataBuffer['ReferenceCache'][resources]:
                # Drill into the arrays
                resourceref = GetValueFromPath(references['drill'], DataBuffer['JSONData'])#[i]
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


def SortDictionary(item: dict):
    # Lists
    for k, v in sorted(item.items()):
        item[k] = sorted(v) if isinstance(v, list) else v
    # Dictionaries
    return {k: SortDictionary(v) if isinstance(v, dict) else v for k, v in sorted(item.items())}


def ExportParse():
    DataBuffer['DiscoveredCache'] = SortDictionary(DataBuffer['DiscoveredCache'])
    DataBuffer['MissingFiles'] = sorted(DataBuffer['MissingFiles'])
    DataBuffer['DiscoveredCache']['MissingFiles'] = DataBuffer['MissingFiles']
    file = Config['DiscoveryFile'] = f"{Config['Project']['SourceDir']}/{Config['DiscoveryFile']}"
    with open(file, 'w', encoding='UTF-8', errors='ignore') as output:
        dump(DataBuffer['DiscoveredCache'], output, ensure_ascii=False, indent=4)
    file = Config['ReferenceFile'] = f"{Config['Project']['SourceDir']}/{Config['ReferenceFile']}"
    with open(file, 'w', encoding='UTF-8', errors='ignore') as output:
        dump(DataBuffer['ReferenceCache'], output, ensure_ascii=False, indent=4)
    output.close()


# Open file explorer at the dump file
def OpenFileExplorer(path):
    if system() == 'Windows':
        startfile(path)
    elif system() == 'Darwin':
        Popen(['open', path])
    else:
        Popen(['xdg-open', path])


def PopAlreadyAddedFiles():
    for file in reversed(DataBuffer['MissingFiles']):
        if (Config['Project']['ArchiveDir'] / file).exists():
            i = DataBuffer['MissingFiles'].index(file)
            DataBuffer['MissingFiles'].pop(i)


def FindAllReferencedFiles(value, key):
    if isinstance(value, dict):
        for k, v in value.items():
            FindAllReferencedFiles(key=k, value=v)
    if isinstance(value, list):
        for v in value:
            FindAllReferencedFiles(key=key, value=v)
    if isinstance(value, str):
        if key.lower() == 'depotpath' and value not in DataBuffer['MissingFiles']:
            DataBuffer['MissingFiles'].append(value)


def AddMissingFiles():
    prg = str(Config['Console']['Dir'])
    arg1 = 'unbundle'
    arg2 = Config['Cyberpunk']['Dir']
    arg2 = f'-p "{arg2}"'
    arg3 = Config['Project']['ArchiveDir']
    arg3 = f'-o "{arg3}"'
    arg4 = ''
    for file in DataBuffer['MissingFiles']:
        # Execute built up -w filter
        if arg4 != '' and len(f'{prg} {arg1} {arg2} {arg3} {arg4}') > 8150:
            # -r "" regex needs \\ escape characters
            arg4 = arg4.replace("\\","\\\\")
            arg4 = f'-r "{arg4}"'
            run(f'{prg} {arg1} {arg2} {arg3} {arg4}', shell=False)
            arg4 = ''
        # Normal loop to build up -w filter
        else:
            if arg4 == '':
                arg4 = f"{file}"
            else:
                arg4 += f"|{file}"
    # Final convert if -w filter buffer isn't empty
    if arg4 != '':
        # -r "" regex needs \\ escape characters
        arg4 = arg4.replace("\\","\\\\")
        arg4 = f'-r "{arg4}"'
        run(f'{prg} {arg1} {arg2} {arg3} {arg4}', shell=False)


Config = {
'DiscoveryFile': 'discovery_DAD.json',
'ReferenceFile': 'reference_DAD.json',
'Discover': [
    'appearancename','appearanceresource',
    'componentname',
    'defaultappearance','depotpath',
    'meshappearance',
    'name'
    ],
'Project': {
    'SourceDir': Path('None'),
    'ArchiveDir': Path('None'),
    'JSONDir': Path('None'),
    'SelectLabel': 'Not selected',
    'RunButton': 'disabled'
},
'Console': {
    'Dir': Path('None'),
    'SelectLabel': 'Not selected',
},
'Cyberpunk': {
    'Dir': Path('None'),
    'SelectLabel': 'Not selected',
},
'WelcomeMessage': "\
This program is intended to work along with WolvenKit, and its primary purpose is to\n\
assist you with adding new items to the game.\n\
\n\
It does this by parsing your mod for:\n\
    - Broken references,\n\
    - Naming schemes,\n\
    - Missing downstream resources.\n\
\n\
Optionally, it will also add those missing resource files to your project."
}

DataBuffer = {
    'DiscoveredCache': dict(), #Export discovery cache
    'ReferenceCache': dict(), #Export reference cache
    'JSONFile': '',
    'JSONData': dict(),
    'ArchiveFile': '',
    'ArchiveData': dict(),
    'RecentlyAddedFiles': False,
    'MissingFiles': []
    }

tkwindow = Tk()
CreateUI()
tkwindow.mainloop()