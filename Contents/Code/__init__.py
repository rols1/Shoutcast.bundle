import urllib

PREFIX           = '/music/shoutcast'
SC_DEVID         = 'sh1t7hyn3Kh0jhlV'
SC_ROOT          = 'http://api.shoutcast.com/'
SC_SEARCH        = SC_ROOT + 'legacy/stationsearch?k=' + SC_DEVID + '&search=%s'
SC_BYGENRE       = SC_ROOT + 'legacy/genresearch?k=' + SC_DEVID + '&genre=%s'
SC_NOWPLAYING    = SC_ROOT + 'station/nowplaying?k=' + SC_DEVID + '&ct=%s&f=xml'
SC_TOP500        = SC_ROOT + 'legacy/Top500?%sk=' + SC_DEVID
SC_ALLGENRES     = SC_ROOT + 'legacy/genrelist?k=' + SC_DEVID
SC_PRIMARYGENRES = SC_ROOT + 'genre/primary?k=' + SC_DEVID + '&f=xml'
SC_SUBGENRES     = SC_ROOT + 'genre/secondary?parentid=%s&k=' + SC_DEVID + '&f=xml'
SC_PLAY          = 'http://yp.shoutcast.com/sbin/tunein-station.pls?id=%s&k='+ SC_DEVID

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(PREFIX, MainMenu, 'SHOUTcast', 'icon-default.png', 'art-default.png')
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.title1 = 'SHOUTcast'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.png')
  DirectoryItem.thumb = R("icon-default.png")
  HTTP.CacheTime = 3600*5

####################################################################################################
def CreateDict():
  # Create dict objects
  Dict["genres"] = {}
  Dict["sortedGenres"] = []

####################################################################################################
def UpdateCache():
  genres = {}
  for g in XML.ElementFromURL(SC_PRIMARYGENRES).xpath("//genre"):
    genre = g.get('name')
    subgenres = []
    if g.get('haschildren') == 'true':
      for sg in XML.ElementFromURL(SC_SUBGENRES % g.get('id')).xpath("//genre"):
        subgenres.append(sg.get('name')) #  + ' [' +   + 'stations]')
    genres[genre] = subgenres
  Dict["genres"] = genres
  Dict["sortedGenres"] = sorted(genres.keys())
  
####################################################################################################
def MainMenu():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(GetGenres, L('By Genre'))))
  #dir.Append(Function(DirectoryItem(GetSubGenres, L('All Genres'))))
  dir.Append(Function(InputDirectoryItem(GetGenre, title=L("Search for Stations by Keyword..."), prompt=L("Search for Stations"), thumb=R('icon-search.png')), queryParamName=SC_SEARCH))
  dir.Append(Function(InputDirectoryItem(GetGenre, title=L("Search for Now Playing by Keyword..."), prompt=L("Search for Now Playing"), thumb=R('icon-search.png')), queryParamName=SC_NOWPLAYING))
  dir.Append(Function(DirectoryItem(GetGenre, title=L("Top 500 Stations")), queryParamName=SC_TOP500, query='**ignore**'))
  dir.Append(PrefsItem(L("Preferences..."), thumb=R('icon-prefs.png')))
  return dir
  
####################################################################################################
def GetGenres(sender):
  if Dict["sortedGenres"] == None:
    UpdateCache()
  dir = MediaContainer(title2=sender.itemTitle)
  sortedGenres = Dict["sortedGenres"]
  for genre in sortedGenres:
    dir.Append(Function(DirectoryItem(GetSubGenres, title=genre)))
  return dir
  
####################################################################################################
def GetSubGenres(sender):
  dir = MediaContainer(title2=sender.itemTitle)
  dir.Append(Function(DirectoryItem(GetGenre, title="All " + sender.itemTitle + " Stations"), query=sender.itemTitle))
  genres = Dict["genres"]
  for subGenre in genres[sender.itemTitle]:
    if XML.ElementFromURL(SC_BYGENRE % String.Quote(subGenre, True), cacheTime=3600).xpath('//station') != []: #skip empty subgenres
      dir.Append(Function(DirectoryItem(GetGenre, title=subGenre)))
  return dir
  
####################################################################################################
def GetGenre(sender, queryParamName=SC_BYGENRE, query=''):
  dir = MediaContainer(viewGroup='Details', title1='By Genre', title2=sender.itemTitle)
  if query == '':
    query = sender.itemTitle
  elif query == '**ignore**':
    query = ''
  else:
    if len(query) < 3 and queryParamName == SC_SEARCH: #search doesn't work for short strings
      return MessageContainer(header='Search error.', message='Searches must have a minimum of three characters.')
    dir.title1 = 'Search'
    dir.title2 = '"' + query + '"'
    
  #Log(urllib.quote(sender.itemTitle))
  fullUrl = queryParamName % String.Quote(query, True)
  #Log("Full URL:"+fullUrl)
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
    
    key = SC_PLAY % station.get('id')
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