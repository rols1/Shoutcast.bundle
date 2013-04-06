RE_FILE = Regex('File1=(http.+?)\n')

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
  ObjectContainer.title1 = "SHOUTcast"
  ObjectContainer.art = R('art-default.png')
  DirectoryObject.thumb = R("icon-default.png")
  TrackObject.thumb = R('icon-default.png')
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
        subgenres.append(sg.get('name'))
    genres[genre] = subgenres
  Dict["genres"] = genres
  Dict["sortedGenres"] = sorted(genres.keys())
  
####################################################################################################
@handler("/music/shoutcast", "SHOUTcast", 'icon-default.png', 'art-default.png')
def MainMenu():
  oc = ObjectContainer()
  oc.add(DirectoryObject(key=Callback(GetGenres), title=L('By Genre')))
  oc.add(InputDirectoryObject(key=Callback(GetGenre, title="", queryParamName=SC_SEARCH), title=L("Search for Stations by Keyword..."), prompt=L("Search for Stations"), thumb=R('icon-search.png')))
  oc.add(InputDirectoryObject(key=Callback(GetGenre, title="Now Playing", queryParamName=SC_NOWPLAYING), title=L("Search for Now Playing by Keyword..."), prompt=L("Search for Now Playing"), thumb=R('icon-search.png')))
  oc.add(DirectoryObject(key=Callback(GetGenre, title=L("Top 500 Stations"), queryParamName=SC_TOP500, query='**ignore**'), title=L("Top 500 Stations")))
  oc.add(PrefsObject(title=L("Preferences..."), thumb=R('icon-prefs.png')))
  return oc
  
####################################################################################################
@route("/music/shoutcast/genres")
def GetGenres():
  if Dict["sortedGenres"] == None:
    UpdateCache()
  
  oc = ObjectContainer(title2=L('By Genre'))
  
  sortedGenres = Dict["sortedGenres"]
  for genre in sortedGenres:
    oc.add(DirectoryObject(key=Callback(GetSubGenres, genre=genre), title=genre))
  return oc
  
####################################################################################################
@route("/music/shoutcast/subgenres")
def GetSubGenres(genre):
  oc = ObjectContainer(title2=genre)
  oc.add(DirectoryObject(key=Callback(GetGenre, title=genre, query=genre), title="All %s Stations" % genre))
  genres = Dict["genres"]
  for subGenre in genres[genre]:
    if XML.ElementFromURL(SC_BYGENRE % String.Quote(subGenre, True), cacheTime=3600).xpath('//station') != []: #skip empty subgenres
      oc.add(DirectoryObject(key=Callback(GetGenre, title=subGenre), title=subGenre))
  
  return oc
  
####################################################################################################
@route("/music/shoutcast/genre")
def GetGenre(title, queryParamName=SC_BYGENRE, query=''):
  if title == '' and query != '' and query != '**ignore**':
    title = query
  
  oc = ObjectContainer(title1='By Genre', title2=title)
  
  if query == '':
    query = title
  elif query == '**ignore**':
    query = ''
  else:
    if len(query) < 3 and queryParamName == SC_SEARCH: #search doesn't work for short strings
      return ObjectContainer(header='Search error.', message='Searches must have a minimum of three characters.')
    oc.title1 = 'Search'
    oc.title2 = '"' + query + '"'
    
  fullUrl = queryParamName % String.Quote(query, True)
  xml = XML.ElementFromURL(fullUrl, cacheTime=1)
  root = xml.xpath('//tunein')[0].get('base')
  
  min_bitrate = Prefs['min-bitrate']
  if min_bitrate[0] == '(':
    min_bitrate = 0
  else:
    min_bitrate = int(min_bitrate.split()[0])
  
  stations = xml.xpath('//station')
  # Sort.
  if Prefs['sort-key'] == 'Bitrate':
    stations.sort(key = lambda station: station.get('br'), reverse=True)
  elif Prefs['sort-key'] == 'Listeners':
    stations.sort(key = lambda station: station.get('lc'), reverse=True)
  else:
    stations.sort(key = lambda station: station.get('name'), reverse=False)
    
  for station in stations:
    listeners = 0
    bitrate = int(station.get('br'))
    
    url = SC_PLAY % station.get('id')
    title = station.get('name').split(' - a SHOUTcast.com member station')[0]
    summary = station.get('ct')
    if station.get('mt') == "audio/mpeg":
      fmt = 'mp3'
      codec = AudioCodec.MP3
    elif station.get('mt') == "audio/aacp":
      fmt = 'aac'
      codec = AudioCodec.AAC
    else:
      fmt = 'unknown'
    
    if station.get('lc'):
      if len(summary) > 0:
        summary += "\n"
      listeners = int(station.get('lc'))
      if listeners > 0:
        summary += station.get('lc')+' Listeners'
    
    # Filter.
    if bitrate >= min_bitrate:
      oc.add(
        TrackObject(
          key=Callback(Lookup, url=url, title=title, summary=summary, bitrate=bitrate, fmt=fmt, codec=codec),
          rating_key=url,
          title=title,
          summary=summary,
          items=[
            MediaObject(
              parts = [PartObject(key=Callback(PlayAudio, url=url, extension=fmt))],
              audio_codec = codec,
              container = fmt,
              audio_channels = 2,
              bitrate = bitrate
            )
          ]
        )
      )

  return oc
  
####################################################################################################
@route("/music/shoutcast/lookup")
def Lookup(url, title, summary, bitrate, fmt, codec):
  return TrackObject(
    key=Callback(Lookup, url=url, title=title, summary=summary, bitrate=bitrate, fmt=fmt, codec=codec, extension=fmt),
    rating_key=url,
    title=title,
    summary=summary,
    items=[
      MediaObject(
        parts = [PartObject(key=Callback(PlayAudio, url=url, extension=fmt))],
        audio_codec = codec,
        container = fmt,
        audio_channels = 2,
        bitrate = bitrate
        )
      ]
    )

####################################################################################################
@route("/music/shoutcast/playaudio.{extenstion}")
def PlayAudio(url, extension):
  content = HTTP.Request(url).content
  file_url = RE_FILE.search(content).group(1)
  return Redirect(file_url)
  