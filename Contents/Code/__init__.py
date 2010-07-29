import urllib
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

SC_ROOT     = 'http://www.shoutcast.com'
SC_GENRE    = SC_ROOT + '/sbin/newxml.phtml'
SC_GENREJSP = 'http://www.shoutcast.com/cusGenre.jsp'
SC_PREFIX   = '/music/shoutcast'

CACHE_INTERVAL = 3600*5

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(SC_PREFIX, MainMenu, 'SHOUTcast', 'icon-default.png', 'art-default.png')
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.title1 = 'SHOUTcast'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.png')
  DirectoryItem.thumb = R("icon-default.png")
  HTTP.SetCacheTime(CACHE_INTERVAL)

####################################################################################################
def CreatePrefs():
  Prefs.Add(id='min-bitrate', type='enum', default='(None)', label='Minimum Bitrate', values='(None)|64 kbps|96 kbps|128 kbps|192 kbps|256 kbps|320 kbps')
  Prefs.Add(id='sort-key',    type='enum', default='Station Name', label='Sort Order', values='Station Name|Bitrate|Listeners')

####################################################################################################
def CreateDict():
  # Create dict objects
  Dict.Set("genres", {})
  Dict.Set("sortedGenres", [])

####################################################################################################
def UpdateCache():
  page = XML.ElementFromURL(SC_GENREJSP, isHTML=True)
  genres = {}
  for g in page.xpath("//a[@class='rdropPriFont']"):
    genre = g.text
    subgenres = []
    for sg in g.xpath("following::div")[0].xpath("a"):
      subgenres.append(sg.text)
    genres[genre] = subgenres

  Dict.Set("genres", genres)
  Dict.Set("sortedGenres", sorted(genres.keys()))
  
####################################################################################################
def MainMenu():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(GetGenres, L('By Genre'))))
  #dir.Append(Function(DirectoryItem(GetSubGenres, L('All Genres'))))
  dir.Append(Function(SearchDirectoryItem(GetGenre, title=L("Search for Stations..."), prompt=L("Search for Stations"), thumb=R('search.png')), queryParamName='?search=%s'))
  dir.Append(PrefsItem(L("Preferences...")))
  return dir
  
####################################################################################################
def GetGenres(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  sortedGenres = Dict.Get("sortedGenres")
  for genre in sortedGenres:
    dir.Append(Function(DirectoryItem(GetSubGenres, title=genre)))
  return dir
  
####################################################################################################
def GetSubGenres(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  dir.Append(Function(DirectoryItem(GetGenre, title="All " + sender.itemTitle + " Stations"), query=sender.itemTitle))
  genres = Dict.Get("genres")
  for subGenre in genres[sender.itemTitle]:
    dir.Append(Function(DirectoryItem(GetGenre, title=subGenre)))
  return dir
  
####################################################################################################
def GetGenre(sender, queryParamName='?genre=%s', query=''):
  dir = MediaContainer(viewGroup='Details', title1='By Genre', title2=sender.itemTitle)
  if query == '':
    query = sender.itemTitle
  else:
    if len(query) < 3: #search doesn't work for short strings
      return MessageContainer(header='Search error.', message='Searches must have a minimum of three characters.')
    dir.title1 = 'Search'
    dir.title2 = '"' + query + '"'
    
  Log(urllib.quote(sender.itemTitle))
  fullUrl = SC_GENRE + queryParamName % String.Quote(query, True)
  Log("Full URL:"+fullUrl)
  xml = XML.ElementFromURL(fullUrl, cacheTime=1)
  root = xml.xpath('//tunein')[0].get('base')
  
  min_bitrate = Prefs.Get('min-bitrate')
  if min_bitrate[0] == '(':
    min_bitrate = 0
  else:
    min_bitrate = int(min_bitrate.split()[0])
  
  for station in xml.xpath('//station'):
    listeners = 0
    bitrate = int(station.get('br'))
    
    key = SC_ROOT + root + '?id=' + station.get('id')
    subtitle = station.get('ct')
    if station.get('lc'):
      if len(subtitle) > 0:
        subtitle += "\n"
      listeners = int(station.get('lc'))
      if listeners > 0:
        subtitle += station.get('lc')+' Listeners'
    
    # Filter.
    if bitrate >= min_bitrate:
      dir.Append(TrackItem(key, station.get('name'), subtitle=subtitle, bitrate=bitrate, listeners=listeners, thumb=R('icon-default.png')))

  # Sort.
  if Prefs.Get('sort-key') == 'Bitrate':
    dir.Sort('bitrate')
    dir.Reverse()
  elif Prefs.Get('sort-key') == 'Listeners':
    dir.Sort('listeners')
    dir.Reverse()
      
  return dir
  
####################################################################################################