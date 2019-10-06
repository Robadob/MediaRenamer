from pytvdbapi import api;
import os.path;
import re;
import sys;
import pickle;


def readInvertedDictionary ( inp ):
    rtn = {};
    try:
        for tln in open(inp):
            tln = tln.strip('\n').strip('\r');
            ln = tln.split('=');
            if len(ln)==2:
                rtn[ln[1]]=ln[0];
            else:
                print("Err unable to parse replacement: %s" % (tln));
    except FileNotFoundError:
        print("Unable to load dictionary: %s"%(inp))
        pass;
    return rtn;
#Enumerates files in directory and adds them to showDirectory
def enumerateFilesToDirectory(dirPath):
  for file in os.scandir(dirPath):
      if not(file.is_dir()):
          show = showRegex.match(file.name);
          if show:
              showName = show.group(1);
              seasonNo = str(int(show.group(2)));#Keep as string for convenient dictionary, but trim leading 0
              episodeNo = int(show.group(3));
              if not(showName in showDirectory):
                showDirectory[showName] = {}
              if not(seasonNo in showDirectory[showName]):
                showDirectory[showName][seasonNo] = set();
              if not(episodeNo in showDirectory[showName][seasonNo]):
                showDirectory[showName][seasonNo].add(episodeNo);
              #Support for e0xe0y format
              if show.group(4)!=None:
                showDirectory[showName][seasonNo].add(int(show.group(5)));
                
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
          print("\rAttempt %d/5 failed!" %(retries), end="");
          if retries<5:
            continue
          else:
            print("\rtvdb.search() failed after 5 retries!", end="");
            raise
        print("\r", end="");
        hasResult = True;
    return showResults;
'''
Main Entry Point
'''
tvdb = api.TVDB('B43FF87DE395DF56');
showRegex = re.compile('^(.+) - s([0-9]{2})e([0-9]{2})(e([0-9]{2}))?', re.IGNORECASE);

videoRoot = sys.argv[len(sys.argv)-1];

replacements = readInvertedDictionary('replacements.cfg');

namePairs = {}
if os.path.exists('namePairs.cfg'):
    namePairsF = open('namePairs.cfg', 'rb');
    namePairs = pickle.load(namePairsF);

showDirectory = {};

#Call enumerateFilesToDirectory() for root and all subdirectories  
enumerateFilesToDirectory(videoRoot);
for f in os.scandir(videoRoot):
  if f.is_dir():
    enumerateFilesToDirectory(f.path);

print("%d Shows To Check!" %(len(showDirectory)))
      
# For each followed show
for show, mySeasons in showDirectory.items():
  showName = show;
  # Undo any replacements
  if showName in replacements:
    showName = replacements[showName];
  
  if not(showName in namePairs):
    showResults = tvdbsearch(showName)
    if len(showResults) == 0:
      print("TVDB could not identify show: %s"%(showName));
      continue;
    namePairs[showName]=showResults[0];
  else:
    namePairs[showName].update();
    
  for season in namePairs[showName]:
    if str(season.season_number) in mySeasons:
      myEpisodes = mySeasons[str(season.season_number)];
      for episode in season:
        if not(episode.EpisodeNumber in myEpisodes):
          print("Missing: %s - s%02de%02d"%(show, season.season_number, episode.EpisodeNumber));
    else:
      print("Missing: %s - s%02d"%(show, season.season_number));