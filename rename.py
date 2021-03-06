from pytvdbapi import api;
import os.path;
import re;
import shutil;
import pickle;
import sys;

#Cleans a string of chars which cannot be in a windows file path
def cleanString( inp ):
    inp = str(inp).replace('\\',', ').replace('/',', ').replace(':',', ').replace('*','').replace('?','').replace('"','').replace('<','(').replace('>',')').replace('|','');
    return inp;
#Cleans removes non standards symbols from show names before db search
def cleanShowName( inp ):
    inp = str(inp).replace('-',' ').replace('.',' ');
    return inp;

#Reads a plaintext dictionary from the file specified by arg
def readDictionary ( inp ):
    rtn = {};
    try:
        for tln in open(inp):
            tln = tln.strip('\n').strip('\r');
            ln = tln.split('=');
            if len(ln)==2:
                rtn[ln[0]]=ln[1];
            else:
                print("Err unable to parse replacement: %s" % (tln));
    except FileNotFoundError:
        print("Unable to load dictionary: %s"%(inp))
        pass;
    return rtn;
#def writeDictionary ( outDictionary, filePath ):
#    with open(filePath, 'wb') as outFile:
#        for key in outDictionary:
#            outFile.write("%s=%s\n" % (key, outDictionary[value]));
#Reads a plaintext array from the file specified by arg
def readList ( inp ):
    rtn = [];
    try:
        for tln in open(inp):
            rtn.append(tln.strip('\n').strip('\r'));
    except FileNotFoundError:
        pass;
    return rtn;
def writeList ( outList, filePath ):
    with open(filePath, 'w') as outFile:
        for i in outList:
            outFile.write("%s\n" % i);
            
def tvdbsearch (showName):
    #Basic loop to give 5 attempts to TVDB api before crashing
    showResults = []
    retries = 0;
    hasResult = False;
    while not(hasResult):
        try :
            showResults = tvdb.search(showName, 'en')
        except :
          retries+=1;
          print("\rAttempt %d/5 failed!" %(retries));
          if retries<5:
            continue
          else:
            print("\rtvdb.search() failed after 5 retries!");
            raise
        print("\r");
        hasResult = True;
    return showResults;
#TVDB returns strings in unicode, this causes crashes where certain foreign characters are found
def stripUnicode (inp):
    return (b"".join([x.encode('ascii', 'replace') for x in inp])).decode()
    
#Attempts to turn arg showName into a valid show name recognised by tvdb
#Returns emptystring on failure
def findShow ( showName, isSilent ):
    showResults = tvdbsearch(showName)
    if len(showResults)!=1:
        while len(showResults)!=1:
            #If silent, exit with failure
            if isSilent or showName == "":
                return "";
            #If no results, ask for new term and rerun search
            elif len(showResults) == 0:
                print("'%s' does not resolve to any results, please enter an alternate search.\n Blank search will skip file." %(showName))
                showName = input("Search term: ")
                showResults = tvdbsearch(showName)
            #If multiple results, prompt the user to select the desired
            elif len(showResults) > 1:#Could also check result 1 isn't identical to cleaned show name
                print("'%s' has multiple results, please select desired result." %(showName))
                for i in range(0,len(showResults)):
                    print("%d: %s" % (i, stripUnicode(showResults[i].SeriesName)))
                print("x: Perform new search")
                print("c: Cancel and skip file")
                while len(showResults) > 1:
                    option = input("Enter desired option: ").strip().lower();
                    if option=='x':
                        showResults=[]
                    elif option=='c':
                        showName = ""
                        showResults=[]
                    elif option.isdigit() and int(option) < len(showResults):
                        showResults=[showResults[int(option)]]
    return showResults[0];
    
#Config
runSilent = False;
runRecursive = False;
runInplace = False;
videoRoot = ".";
videoDest = "";
videoTypes = [".mp4", ".avi", ".mkv", ".wmv"];
files = [];
dropShows = [];

def printHelp():
    print("Usage:");
    print("rename.py [args] <sourcePath>");
    print("Args:");
    print("-silent, -s: Suppress output");
    print("-recurse, -r: Recursively find files in source path");
    print("-inplace, -i: Rename files inplace, not compatible with -dest or -d");
    print("-dest <destPath>, -d <destPath>: Specify a destination path (else source will be used)");
    print("-drop <showName>: Specify a showname to be dropped from namePairs");
    exit();  

#Process Args
if len(sys.argv)>1:
    i = 0;
    while i < len(sys.argv)-2:
        i=i+1;
        if sys.argv[i]=="-help" or sys.argv[i]=="-?":
            printHelp();
        elif sys.argv[i]=="-silent" or sys.argv[i]=="-s":
            runSilent = True;
        elif sys.argv[i]=="-recurse" or sys.argv[i]=="-r":
            runRecursive=True;
        elif sys.argv[i]=="-inplace" or sys.argv[i]=="-i":
            runInplace=True;
        elif sys.argv[i]=="-dest" or sys.argv[i]=="-d":
            i=i+1;
            if i < (len(sys.argv)-1):
                videoDest=sys.argv[i];
            else:
                print("-dest, -d args require a trailing arg");
                printHelp();
        elif sys.argv[i]=="-drop":
            i=i+1;
            if i < (len(sys.argv)-1):
                dropShows.append(sys.argv[i]);
            else:
                print("-drop args require a trailing arg");
                printHelp();
        else:
            print("Arg '%s' was not recognised."%(sys.argv[i]));
            printHelp();
else:
    printHelp();

videoRoot = sys.argv[len(sys.argv)-1];
    
    
#Block bad args
if runInplace and videoDest!="":
    print("-inplace,-i and -dest,-d args are incompatible");
    printHelp();
  
if videoDest=="":
    videoDest=videoRoot;

#Regexes
showRegex = re.compile('^(.+?([. ][0-9]{4})?)[ .]-?[ .]?(s(eason[. ]?)?)?([0-9]{1,2})[ x.]?(e(pisode[. ]?)?)?([0-9]{2})[^p]', re.IGNORECASE);
typeRegex = re.compile('\.([a-zA-Z0-9]+)$', re.IGNORECASE);

#Build list 'files' of all video files to be handled
for root, directories, filenames in os.walk(videoRoot):
    for filename in filenames: 
        for type in videoTypes:
            if filename.lower().endswith(type):
                files.append(os.path.join(root,filename));
                continue;
    #If not recursive, skip others
    if not runRecursive:
        break;

if not(runSilent):       
    print("%d video files found for processing." % (len(files)));

tvdb = api.TVDB('A0857036BEACEE1A');
# tvdb = api.TVDB('9E8E50DD-AF0C-45D5-BDC4-2A4BFEBEA36D');

namePairs = {}
if os.path.exists('namePairs.cfg'):
    namePairsF = open('namePairs.cfg', 'rb');
    namePairs = pickle.load(namePairsF);

# Drop requested shows
for show in dropShows:
    showName = cleanShowName(show);
    if showName in namePairs:
        print("Confirm that show '%s' should be dropped."%(show));
        option = input("Confirm [Y/N]: ").strip().lower();
        if option=='y':
            del namePairs[showName];
    elif showName.lower() in namePairs:
        print("Confirm that show '%s' should be dropped."%(show));
        option = input("Confirm [Y/N]: ").strip().lower();
        if option=='y':
            del namePairs[showName.lower()];
    else:
        print("Show '%s' was not found to be dropped."%(show));

replacements = readDictionary('replacements.cfg');
skip = readList('skip.cfg');
    
for file in files:
    filename = os.path.basename(file);    
    #print(filename)
    #Skip file if in skiplist
    if any(filename in s for s in skip):
        continue;
    type = typeRegex.search(filename).group(0);
    show = showRegex.match(filename);
    if not(show):
        if not(runSilent): 
            print("Cannot detect show details in file: %s" % (filename));
        #Show skipped, add to skiplist
        skip.append(filename);
    else:
        showName = cleanShowName(show.group(1)).strip().lower();
        showSeasonNo = int(show.group(5));
        showEpisodeNo = int(show.group(8));
        #print("%s - s%se%s - null" % (showName, showSeasonNo, showEpisodeNo))
        if not(showName in namePairs):
            showNameConfirmed = findShow(showName,runSilent);
            if showNameConfirmed=="":
                #Show skipped, add to skiplist
                skip.append(filename);
                continue;
            namePairs[showName]=showNameConfirmed;
        else:
            #Update show stored in namePairs (could optionally only run this if episode missing)
            try:
              namePairs[showName].update();
            except:
              print("Failed to update show: %s with DB." %(showName));
        #Show is now the desired show, so we can pull episode info
        show = namePairs[showName];
        showName = stripUnicode(show.SeriesName);
        #If show name is a list (seems to occur when showname contains '|')
        #Concat the elements
        if isinstance(showName, (list,)):
          showName = ', '.join(showName);
        #Replace show name if desired
        if showName in replacements:
            showName = replacements[showName];
        try:
            showSeason = show[showSeasonNo];
        except:
            print("'%s' season %d was not found, skipping file." %(showName,showSeasonNo));
            continue;
        try:
            showEpisode = showSeason[showEpisodeNo];
        except:
            print("'%s' s%02de%02d has invalid episode no, skipping file." %(showName,showSeasonNo, showEpisodeNo));
            continue;
        #Create new file name ~/Show Name/Show Name - sXXeYY - Episode Name.type
        #runInplace?videoRoot:videoDest;
        newFilePath = videoRoot if runInplace else videoDest;
        #Ensure the root ends with a slash
        if not(newFilePath.endswith(os.path.sep)):
            newFilePath += os.path.sep;
        if not runInplace:
            #Append the show name as a directory
            newFilePath += cleanString(showName);
            newFilePath += os.path.sep;
            #Attempt to create that directory
            if not os.path.exists(newFilePath):
                os.mkdir(newFilePath);
        #Append the show name as part of the file name
        newFilePath += cleanString(showName);
        newFilePath += ' - ';
        #Append the season number
        newFilePath += 's';
        newFilePath += format(showEpisode.SeasonNumber, '02');
        #Append the episode number
        newFilePath += 'e'
        newFilePath += format(showEpisode.EpisodeNumber, '02');
        newFilePath += ' - ';
        #Append episode name
        newFilePath += cleanString(stripUnicode(showEpisode.EpisodeName));
        #Append file type
        newFilePath += type;
        if file != newFilePath and not(runSilent):
            print(file.encode("utf-8"));
            print(newFilePath.encode("utf-8"));
        #Move file
            try:
                shutil.move(file, newFilePath);
            except PermissionError:
                print("Cannot update file %s, access denied." % (file.encode("utf-8")));
        
    #End loop - Next file
       
#Cleanup any empty directories, nfos

#Save skiplist
writeList(skip,'skip.cfg'); 
#Save namePairs
namePairsF = open('namePairs.cfg', 'wb');
pickle.dump(namePairs, namePairsF);