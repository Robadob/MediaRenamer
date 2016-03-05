from pytvdbapi import api
import os.path
import subprocess
import re
import shutil

#Cleans a string of chars which cannot be in a windows file path
def cleanString( inp ):
    inp = inp.replace('\\',', ').replace('/',', ').replace(':',', ').replace('*','').replace('?','').replace('"','').replace('<','(').replace('>',')').replace('|','')
    return inp

sevenZEx = r"7z.exe"
sevenZDir = os.path.join(r"C:\Program Files\7-Zip",sevenZEx)
splitRoot = r"D:\Test2"
extractedRoot = r"D:\Extracted"
#videoTypes = ['.part01.rar','dve.rar','fov.rar','vf.rar','tla.rar']
videoTypes = ['.rar']
files = []
#Regexes
unwantedRegex = re.compile('[0-9]?[02-9]\.rar$', re.IGNORECASE)

#Build list 'files' of all video files to be handled
for root, directories, filenames in os.walk(splitRoot):
    for filename in filenames: 
        for type in videoTypes:
            if filename.lower().endswith(type):
                if not(unwantedRegex.search(filename)):
                    files.append(os.path.join(root,filename))
                    continue
       
print("%d video files to extract." % (len(files)))

#os.chdir(r"C:\Program Files\7-Zip")
FNULL = open(os.devnull, 'w')
i=1;
for file in files:
    filename = os.path.basename(file)
    print (str(i)+"/"+str(len(files))+" - "+filename);
    i+=1;
    subprocess.call([sevenZEx, 'e', '-o'+extractedRoot, file, '-y'], executable=sevenZDir, stdout=FNULL);


# tvdb = api.TVDB('A0857036BEACEE1A')
# namePairs = {}

# for file in files:
    # filename = os.path.basename(file)
    # print(filename)
    # type = typeRegex.search(filename).group(0)
    # show = showRegex.match(filename)
    # if not(show):
        # print("Cannot detect show details in file: %s" % (filename))
    # else:
        # showName = show.group(1).replace('.',' ').strip().lower()
        # showSeasonNo = int(show.group(3))
        # showEpisodeNo = int(show.group(5))
        # #print("%s - s%se%s - null" % (showName, showSeasonNo, showEpisodeNo))
        # if not(showName in namePairs):
            # showResults = tvdb.search(showName, 'en')
            # if len(showResults)!=1:
                # oldShowName = showName
                # while len(showResults)!=1:
                    # #If no results, ask for new term and rerun search
                    # if len(showResults) == 0:
                        # print("'%s' does not resolve to any results, please enter an alternate search." %(showName))
                        # showName = input("Search term: ")
                        # showResults = tvdb.search(showName, 'en')
                    # #If multiple results, prompt the user to select the desired
                    # elif len(showResults) > 1:#Could also check result 1 isn't identical to cleaned show name
                        # print("'%s' has multiple results, please select desired result." %(showName))
                        # for i in range(0,len(showResults)):
                            # print("%d: %s" % (i, showResults[i].SeriesName))
                        # print("x: Perform new search")
                        # while len(showResults) > 1:
                            # option = input("Enter desired option: ").strip().lower();
                            # if option=='x':
                                # showResults=[]
                            # elif option.isdigit() and int(option) < len(showResults):
                                # showResults=[showResults[int(option)]]
                # #Add show to the dictionary of namePairs and continue asthought it was there to begin with
                # showName=oldShowName
            # namePairs[showName]=showResults[0]
        # #Show is now the desired show, so we can pull episode info
        # show = namePairs[showName]
        # showName = show.SeriesName
        # showSeason = show[showSeasonNo]
        # showEpisode = showSeason[showEpisodeNo]
        # #Create new file name ~/Show Name/Show Name - sXXeYY - Episode Name.type
        # newFilePath = videoRoot
        # #Ensure the root ends with a slash
        # if not(videoRoot.endswith(os.path.sep)):
            # newFilePath += os.path.sep
        # #Append the show name as a directory
        # newFilePath += cleanString(showName)
        # newFilePath += os.path.sep
        # #Attempt to create that directory
        # if not os.path.exists(newFilePath):
            # os.mkdir(newFilePath)
        # #Append the show name as part of the file name
        # newFilePath += cleanString(showName)
        # newFilePath += ' - '
        # #Append the season number
        # newFilePath += 's'
        # newFilePath += format(showEpisode.SeasonNumber, '02')
        # #Append the episode number
        # newFilePath += 'e'
        # newFilePath += format(showEpisode.EpisodeNumber, '02')
        # newFilePath += ' - '
        # #Append episode name
        # newFilePath += cleanString(showEpisode.EpisodeName)
        # #Append file type
        # newFilePath += type
        # print(file)
        # print(newFilePath)
        # #Move file
        # shutil.move(file, newFilePath)
        
    # #End loop - Next file
       
# #Cleanup any empty directories, nfos