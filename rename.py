from pytvdbapi import api;
import os.path;
import re;
import shutil;
import pickle;

#Cleans a string of chars which cannot be in a windows file path
def cleanString( inp ):
    inp = inp.replace('\\',', ').replace('/',', ').replace(':',', ').replace('*','').replace('?','').replace('"','').replace('<','(').replace('>',')').replace('|','');
    return inp;

def readDictionary ( inp ):
    rtn = {};
    for tln in open(inp):
        tln = tln.strip('\n').strip('\r');
        ln = tln.split('=');
        if len(ln)==2:
            rtn[ln[0]]=ln[1];
        else:
            print("Err unable to parse replacement: %s" % (tln));
    return rtn;
    
videoRoot = 'D:\Test'
videoTypes = ['.mp4', '.avi', '.mkv', '.wmv']
files = []

#Regexes
showRegex = re.compile('^(.+?([. ][0-9]{4})?)[ .]-?[ .]?(s(eason[. ]?)?)?([0-9]{1,2}?)[ x.]?(e(pisode[. ]?)?)?([0-9]{2})', re.IGNORECASE);
typeRegex = re.compile('\.([a-zA-Z0-9]+)$', re.IGNORECASE);

#Build list 'files' of all video files to be handled
for root, directories, filenames in os.walk(videoRoot):
    for filename in filenames: 
        for type in videoTypes:
            if filename.lower().endswith(type):
                files.append(os.path.join(root,filename));
                continue;
       
print("%d video files found for processing." % (len(files)));

tvdb = api.TVDB('A0857036BEACEE1A');

namePairs = {}
if os.path.exists('namePairs.cfg'):
    namePairsF = open('namePairs.cfg', 'rb');
    namePairs = pickle.load(namePairsF);

replacements = readDictionary('replacements.cfg');
    
for file in files:
    filename = os.path.basename(file)
    #print(filename)
    type = typeRegex.search(filename).group(0)
    show = showRegex.match(filename)
    if not(show):
        print("Cannot detect show details in file: %s" % (filename))
    else:
        showName = show.group(1).replace('.',' ').strip().lower()
        showSeasonNo = int(show.group(5))
        showEpisodeNo = int(show.group(8))
        #print("%s - s%se%s - null" % (showName, showSeasonNo, showEpisodeNo))
        if not(showName in namePairs):
            showResults = tvdb.search(showName, 'en')
            if len(showResults)!=1:
                oldShowName = showName
                while len(showResults)!=1:
                    #If no results, ask for new term and rerun search
                    if len(showResults) == 0:
                        print("'%s' does not resolve to any results, please enter an alternate search." %(showName))
                        showName = input("Search term: ")
                        showResults = tvdb.search(showName, 'en')
                    #If multiple results, prompt the user to select the desired
                    elif len(showResults) > 1:#Could also check result 1 isn't identical to cleaned show name
                        print("'%s' has multiple results, please select desired result." %(showName))
                        for i in range(0,len(showResults)):
                            print("%d: %s" % (i, showResults[i].SeriesName))
                        print("x: Perform new search")
                        while len(showResults) > 1:
                            option = input("Enter desired option: ").strip().lower();
                            if option=='x':
                                showResults=[]
                            elif option.isdigit() and int(option) < len(showResults):
                                showResults=[showResults[int(option)]]
                #Add show to the dictionary of namePairs and continue as though it was there to begin with
                showName=oldShowName
            namePairs[showName]=showResults[0]
        #Show is now the desired show, so we can pull episode info
        show = namePairs[showName]
        showName = show.SeriesName
        #Replace show name if desired
        if showName in replacements:
            showName = replacements[showName];
        showSeason = show[showSeasonNo]
        showEpisode = showSeason[showEpisodeNo]
        #Create new file name ~/Show Name/Show Name - sXXeYY - Episode Name.type
        newFilePath = videoRoot
        #Ensure the root ends with a slash
        if not(videoRoot.endswith(os.path.sep)):
            newFilePath += os.path.sep
        #Append the show name as a directory
        newFilePath += cleanString(showName)
        newFilePath += os.path.sep
        #Attempt to create that directory
        if not os.path.exists(newFilePath):
            os.mkdir(newFilePath)
        #Append the show name as part of the file name
        newFilePath += cleanString(showName)
        newFilePath += ' - '
        #Append the season number
        newFilePath += 's'
        newFilePath += format(showEpisode.SeasonNumber, '02')
        #Append the episode number
        newFilePath += 'e'
        newFilePath += format(showEpisode.EpisodeNumber, '02')
        newFilePath += ' - '
        #Append episode name
        newFilePath += cleanString(showEpisode.EpisodeName)
        #Append file type
        newFilePath += type
        if file != newFilePath:
            print(file)
            print(newFilePath)
        #Move file
            shutil.move(file, newFilePath)
        
    #End loop - Next file
       
#Cleanup any empty directories, nfos

#Save namePairs
namePairsF = open('namePairs.cfg', 'wb');
pickle.dump(namePairs, namePairsF);