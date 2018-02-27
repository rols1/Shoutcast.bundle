import sys	
import htmllib		# unescape_html
import urllib		# urllib.unquote
import urllib2
import ssl			# HTTPS-Handshake
import re	

import cookielib	# für Radionomy
# keepalive - Quelle: https://github.com/wikier/keepalive, als 3rd party 
#	Python module in ../Contents/Libraries/Shared (Thanks, mikedm139 in forum:
#	https://forums.plex.tv/discussion/comment/296468/#Comment_296468
import keepalive	# für Radionomy 
from keepalive import HTTPHandler
import random		# Radionomy: random-ID's für global openerStore

						
import updater
from urlparse import urlparse 	# StationCheck, getStreamMeta


# +++++ Shoutcast2017 - shoutcast.com-Plugin für den Plex Media Server +++++
# Forum:		https://forums.plex.tv/discussion/296423/rel-shoutcast2017

VERSION =  '0.3.1'		
VDATE = '27.02.2018'

ICON_MAIN_UPDATER 		= 'plugin-update.png'		
ICON_UPDATER_NEW 		= 'plugin-update-new.png'
ICON_OK					= 'icon-ok.png'
ICON_SEARCH 			= 'suche.png'

ART    		= 'art-default.jpg'		# Quelle: https://de.wikipedia.org/w/index.php?curid=4483484
ICON   		= 'icon-default.jpg'	# wie oben, Symbol ohne Schriftzug,  angepasst auf 512x512px

RE_FILE = Regex('File1=(https?://.+)')

SC_DEVID         = 'sh1t7hyn3Kh0jhlV'
SC_ROOT          = 'http://api.shoutcast.com/'
SC_SEARCH        = SC_ROOT + 'legacy/stationsearch?k=' + SC_DEVID + '&search=%s'
SC_BYGENRE       = SC_ROOT + 'legacy/genresearch?k=' + SC_DEVID + '&genre=%s'
SC_NOWPLAYING    = SC_ROOT + 'station/nowplaying?k=' + SC_DEVID + '&ct=%s&f=xml'
SC_TOP500        = SC_ROOT + 'legacy/Top500?%sk=' + SC_DEVID
SC_ALLGENRES     = SC_ROOT + 'legacy/genrelist?k=' + SC_DEVID
SC_PRIMARYGENRES = SC_ROOT + 'genre/primary?k=' + SC_DEVID + '&f=xml'
SC_SUBGENRES     = SC_ROOT + 'genre/secondary?parentid=%s&k=' + SC_DEVID + '&f=xml'
SC_PLAY          = 'http://yp.shoutcast.com/sbin/tunein-station.pls?id=%s&k='+ SC_DEVID # Default .pls

NAME		= 'Shoutcast2017'
PREFIX 		= '/music/shoutcast2017'

REPO_NAME		 	= NAME
GITHUB_REPOSITORY 	= 'rols1/' + REPO_NAME
REPO_URL 			= 'https://github.com/{0}/releases/latest'.format(GITHUB_REPOSITORY)

####################################################################################################
def Start():

	ObjectContainer.title1 = "SHOUTcast"
	ObjectContainer.art = R(ART)
	DirectoryObject.art = R(ART)
	DirectoryObject.thumb = R(ICON)
	HTTP.CacheTime = 3600*5
	
	global openerStore		# Radionomy
	openerStore = {}
	
	ValidatePrefs()
		
####################################################################################################
def ValidatePrefs():	
	# Dict['Favourites'] = []						# Test: Favs löschen
	
	loc = Prefs['RadionomyLang']
	if loc == None:
		loc = "EN/English"
	Dict['loc'] = loc.split('/')[0]
	Log('loc: ' + loc)

####################################################################################################
def CreateDict():
	Log('CreateDict')

	# Create dict objects
	Dict['genres'] = {}
	Dict['sortedGenres'] = []
	if not Dict['Favourites']:
		Dict['Favourites'] = []

####################################################################################################
def UpdateCache():
	Log('UpdateCache')

	genres = {}

	for g in XML.ElementFromURL(SC_PRIMARYGENRES).xpath("//genre"):
		genre = g.get('name')
		subgenres = []

		if g.get('haschildren') == 'true':
			for sg in XML.ElementFromURL(SC_SUBGENRES % g.get('id')).xpath("//genre"):
				subgenres.append(sg.get('name'))

		genres[genre] = subgenres

	Dict['genres'] = genres
	Dict['sortedGenres'] = sorted(genres.keys())

####################################################################################################
@handler(PREFIX, NAME)
@route(PREFIX)
def MainMenu():
	Log('MainMenu')

	# nützliche Debugging-Variablen:
	Log('Plugin-Version: ' + VERSION); Log('Plugin-Datum: ' + VDATE)	
	client_platform = str(Client.Platform)								# Client.Platform: None möglich
	client_product = str(Client.Product)								# Client.Product: None möglich
	Log('Client-Platform: ' + client_platform)							
	Log('Client-Product: ' + client_product)							    
	Log('Plattform: ' + sys.platform)									# Server-Infos
	Log('Platform.OSVersion: ' + Platform.OSVersion)					# dto.
	Log('Platform.CPU: '+ Platform.CPU)									# dto.
	Log('Platform.ServerVersion: ' + Platform.ServerVersion)			# dto.
	
	Log('min-bitrate: ' + str(Prefs['min-bitrate']))
	Log('sort-key: ' + str(Prefs['sort-key']))
	
	oc = ObjectContainer(no_cache=True)				# no_cache für Favorites
		
	if Dict['Favourites']:
		Log('Favourites: ' + str(len(Dict['Favourites'])))
	# Log(Dict['Favourites'])
	if Prefs['UseFavourites']:						# Favoriten einbinden
		if Dict['Favourites']:
			oc.add(DirectoryObject(key=Callback(FavouritesShow), title="Favourites", thumb=R('favs.png')))
						
	oc.add(InputDirectoryObject(key=Callback(GetGenre, title="Search for Stations", queryParamName=SC_SEARCH), 
		title=L("Search for Stations by Keyword..."), prompt=L("Search for Stations"),
		thumb=R(ICON_SEARCH)))
	oc.add(InputDirectoryObject(key=Callback(GetGenre, title="Now Playing", queryParamName=SC_NOWPLAYING), 
		title=L("Search for Now Playing by Keyword..."), prompt=L("Search for Now Playing"),
		thumb=R(ICON_SEARCH)))
		
	oc.add(DirectoryObject(key=Callback(GetGenres), title=L('By Genre')))
	oc.add(DirectoryObject(key=Callback(GetGenre, title=L("Top 500 Stations"), queryParamName=SC_TOP500, query='**ignore**'), 
		title=L("Top 500 Stations")))
	oc.add(PrefsObject(title=L("Preferences...")))

#-----------------------------	
	# Addons
	if  Prefs['UseRadionomyAddon']:	
		oc.add(DirectoryObject(key=Callback(MainMenuRadionomy, title='Radionomy'), 
			title="Radionomy", thumb=R('radionomy.png')))		
#-----------------------------	

	oc = SearchUpdate(title=NAME, start='true', oc=oc)	# Updater-Modul einbinden
	
	ValidatePrefs()				
	return oc
	
####################################################################################################
@route(PREFIX + '/MainMenuRadionomy')
def MainMenuRadionomy(title):
	Log('MainMenuRadionomy')
	
	oc = ObjectContainer(no_cache=True, title2=title)
	# Home to Menü Shoutcast2017			
	oc.add(DirectoryObject(key=Callback(MainMenu),title='Home', summary='Home',thumb=R('home.png')))
	path = 'https://www.radionomy.com/%s/style' % Dict['loc'] 
	page = HTTP.Request(path, cacheTime=86400).content						# cacheTime 1 Tag
		
	GenreBlock = stringextract('id="browseMainGenre', '</ul>', page)		# Menü Genres
	genres = blockextract('<li class=', GenreBlock)
	for genre in genres:
		url 	= stringextract('href="', '"', genre)
		url		= 'https://www.radionomy.com' + url
		# title	= stringextract('internal">', '</a>', genre)
		# title	= unescape_html(title)										# entfernt Sprachsonderzeichen
		title 	= url.split('/')[-1]
		title 	= urllib.unquote(title).decode('utf8')

		# Log(title); Log(url)
		if "featured" in genre:												# ohne Subgenres (2 am Anfang)
			oc.add(DirectoryObject(key=Callback(RD_Genre, url=url, title=title, browse='no'),
				title=title, thumb=R('icon-folder.png')))			
		else:																# mit Subgenres 
			oc.add(DirectoryObject(key=Callback(RD_SubGenres, url=url, title=title),
				title=title, thumb=R('icon-folder.png')))

	oc.add(InputDirectoryObject(key=Callback(RD_Search, title="Search Radionomy",), 
		title=L("Search for Stations by Keyword..."), prompt=L("Search for Stations"), thumb=R(ICON_SEARCH)))
		
	ValidatePrefs()
	return oc
####################################################################################################
@route(PREFIX + '/genres')
def GetGenres():
	Log('GetGenres')

	if Dict['sortedGenres'] == None:
		UpdateCache()

	oc = ObjectContainer(title2=L('By Genre'))
	oc.add(DirectoryObject(key=Callback(MainMenu),title='Home', summary='Home',thumb=R('home.png')))
	sortedGenres = Dict['sortedGenres']

	for genre in sortedGenres:
		oc.add(DirectoryObject(
			key = Callback(GetSubGenres, genre=genre),
			title = genre
		))

	return oc

####################################################################################################
@route(PREFIX + '/subgenres')
def GetSubGenres(genre):
	Log('GetSubGenres')

	oc = ObjectContainer(title2=genre)
	oc.add(DirectoryObject(key=Callback(MainMenu),title='Home', summary='Home',thumb=R('home.png')))
	oc.add(DirectoryObject(
		key = Callback(GetGenre, title=genre, query=genre),
		title = "All %s Stations" % genre
	))

	genres = Dict['genres']

	for subgenre in genres[genre]:
		if XML.ElementFromURL(SC_BYGENRE % String.Quote(subgenre, usePlus=True)).xpath('//station') != []: #skip empty subgenres
			oc.add(DirectoryObject(
				key = Callback(GetGenre, title=subgenre),
				title = subgenre
			))

	return oc

####################################################################################################
@route(PREFIX + '/GetGenre')
def GetGenre(title, queryParamName=SC_BYGENRE, query=''):
	Log('GetGenre')

	if title == '' and query != '' and query != '**ignore**':
		title = query

	oc = ObjectContainer(title1='By Genre', title2=title)
	oc.add(DirectoryObject(key=Callback(MainMenu),title='Home', summary='Home',thumb=R('home.png')))

	if query == '':
		query = title
	elif query == '**ignore**':
		query = ''
	else:
		if len(query) < 3 and queryParamName == SC_SEARCH: #search doesn't work for short strings
			return ObjectContainer(header='Search error.', message='Searches must have a minimum of three characters.')

		oc.title1 = 'Search'
		oc.title2 = '"' + query + '"'

	fullUrl = queryParamName % String.Quote(query, usePlus=True)
	xml = XML.ElementFromURL(fullUrl, cacheTime=1)
	root = xml.xpath('//tunein')[0].get('base')

	min_bitrate = Prefs['min-bitrate']
	if min_bitrate[0] == '(':
		min_bitrate = 0
	else:
		min_bitrate = int(min_bitrate.split()[0])
	Log(min_bitrate)

	stations = xml.xpath('//station')

	# Sort.
	if Prefs['sort-key'] == 'Bitrate':
		stations.sort(key = lambda station: station.get('br'), reverse=True)
	elif Prefs['sort-key'] == 'Listeners':
		stations.sort(key = lambda station: station.get('lc'), reverse=True)
	else:
		stations.sort(key = lambda station: station.get('name'), reverse=False)

	Log(len(stations))
	if len(stations) == 0:
		error_txt = 'Sorry, nothing found'
		return ObjectContainer(header=L('Info'), message=error_txt)			

	rcnt=0						# zählt Stationen
	for station in stations:
		rcnt = rcnt + 1				# Test-Szenarien mit kleiner Zahl
		#if rcnt > 10:				 
		#	return oc	
		#s = XML.StringFromElement(station)
		#Log(s)
		
		listeners = 0
		bitrate = int(station.get('br'))

		url = SC_PLAY % station.get('id')		# Playlist-Url
		title = station.get('name').split(' - a SHOUTcast.com member station')[0]
		summary = station.get('ct')
		summary = "" if summary is None else summary
		logo =  station.get('logo')				# fehlt häufig
		if logo == None:
			logo = R(ICON)

		if station.get('mt') == "audio/mpeg":
			fmt = 'mp3'
		elif station.get('mt') == "audio/aacp":
			fmt = 'aac'
		else:
			continue

		if station.get('lc'):
			if len(summary) > 0:
				summary += "\n"

			listeners = int(station.get('lc'))

			if listeners > 0:
				summary += station.get('lc') + ' Listeners'
				
		if bitrate >= min_bitrate:			# Fundstellen: 1 bei 256 Kbps,  
			# wegen des Problems "Zusammenbruch der track_objects-Liste" (s. PlayAudio)	
			#	schalten wir ein DirectoryObject dazwischen:					
			# oc.add(CreateTrackObject(url = url,title = title,summary = summary,fmt = fmt))
			oc.add(DirectoryObject(
				key = Callback(StationCheck, url=url,title=title,summary=summary,fmt=fmt,logo=logo),
				title=title, summary=summary))
		 
	return oc
 			
####################################################################################################
# add_loc: Länder postfix z.B. EN für Radionomy
@route(PREFIX + '/StationCheck')
def StationCheck(url, title, summary, fmt, logo, home=''):
	Log('StationCheck')
	Log(title);Log(summary);Log(fmt);Log(logo);
	title_org=title; summ_org=summary; station_url=url
	
	oc = ObjectContainer(title1='Station-Check', title2=title)
	Log(Client.Platform)						# PHT verweigert TrackObject bei vorh. DirectoryObject 
	client = str(Client.Platform)				# None möglich
	if client.find ('Plex Home Theater') == -1: # 
		if home == 'Radionomy':
			oc.add(DirectoryObject(key=Callback(MainMenuRadionomy,title='Radionomy'),title='Home', 
				summary='Home',thumb=R('home_radionomy.png')))	
		else:
			oc.add(DirectoryObject(key=Callback(MainMenu),title='Home', summary='Home',thumb=R('home.png')))
	
	try:
		content = HTTP.Request(url, cacheTime=0).content	# Playlist im .pls-Format (SC_PLAY)
	except:
		Log('HTTP.Request fehlgeschlagen')
		content=''
	Log('content:' + content)
	
	if content == '':
		msg='Playlist could not be loaded: ' + title 
		return ObjectContainer(header=L('Error'), message=msg)			
	if 'http' not in content:
		msg='Playlist is empty: ' + title 
		return ObjectContainer(header=L('Error'), message=msg)			
		
	urls =content.splitlines()

	pls_cont = []
	for line in urls:
		if '=http' in line:	
			url = line.split('=')[1]
		if line.startswith('http'):					# z.B. Radionomy
			url = line 
		pls_cont.append(url)
			
	pls = repl_dop(pls_cont)
	Log(pls[:100])
	
	cnt=0
	for stream_url in pls:
		summ=''
		cnt = cnt + 1		
		ret = getStreamMeta(stream_url)				# getStreamMeta
		st = ret.get('status')	
		Log('ret.get.status: ' + str(st))
		if st == 0:									# kein Stream, verwerfen
			stream_url=R('not_available_en.mp3')	# mp3: Dieser Sender ist leider nicht verfügbar
			title=title + ' | ' + 'not available'
		else:
			if ret.get('metadata'):					# Status 1: Stream ist up, Metadaten aktualisieren (nicht .mp3)
				metadata = ret.get('metadata')
				Log('metadata:'); Log(metadata)						
				bitrate = metadata.get('bitrate')	# bitrate aktualisieren, falls in Metadaten vorh.
				Log(bitrate)
				try:
					song = metadata.get('song')		# mögl.: UnicodeDecodeError: 'utf8' codec can't decode..., Bsp.
					song = song.decode('utf-8')		# 	'song': 'R\r3\x90\x86\x11\xd7[\x14\xa6\xe1k...
					song = unescape_html(song)
				except:
					song=''
				
				if song.find('adw_ad=') == -1:		# ID3-Tags (Indiz: adw_ad=) verwerfen
					if bitrate and song:							
						summ = 'Song: %s | Bitrate: %sKB' % (song, bitrate) # neues summary
					if bitrate and song == '':	
						summ = '%s | Bitrate: %sKB' % (str(summ_org), bitrate)	# altes summary (i.d.R Song) ergänzen
					if bitrate == None and song == '':
						summ = 'song title and bitrate unknown'	
				
			if  ret.get('hasPortNumber') == 'true': # auch SHOUTcast ohne Metadaten möglich, Bsp. Holland FM Gran Canaria,
				if stream_url.endswith('/'):				#	http://stream01.streamhier.nl:9010
					stream_url = '%s;' % stream_url
				else:
					stream_url = '%s/;' % stream_url
			else:	
				if stream_url.endswith('.fm/'):			# Bsp. http://mp3.dinamo.fm/ (SHOUTcast-Stream)
					stream_url = '%s;' % stream_url
				else:								# ohne Portnummer, ohne Pfad: letzter Test auf Shoutcast-Status 
					p = urlparse(url)
					if p.path == '':
						cont = HTTP.Request(url).content# Bsp. Radio Soma -> http://live.radiosoma.com
						if 	'<b>Stream is up at' in cont:
							Log('Shoutcast ohne Portnummer: <b>Stream is up at')
							url = '%s/;' % url	
			
		if summ.startswith('None'):	
			summ = summ.replace('None', 'song title not found')
		if summ == '':	
			summ = 'song title and bitrate unknown'	
		Log('summ: %s' % summ)
		summ  = '%s | %s' % (summ, stream_url)
		summ = summ.decode('utf-8')
		if st == 0:					# ret.get('status')
			title = title
			summ = 'Error message: %s' % ret.get('error')
		else:
			title = title_org + ' | Stream %s | %s'  % (str(cnt), fmt)

		oc.add(CreateTrackObject(url=stream_url,title=title,summary=summ,fmt=fmt,thumb=logo,))
		
	if Prefs['UseFavourites']:		# Favoriten-Menü
		FavExist = False
		try:
			for Fav in Dict['Favourites']:
				if station_url in Fav:
					FavExist = True
					break
		except:
				pass
					
		if FavExist == False:		
			title = 'add Favourite'			
			oc.add(DirectoryObject(key=Callback(Favourit, 
				ID='add',url=station_url,title=title_org,summary=summ_org,fmt=fmt,logo=logo), 
				title=title,summary=title_org,thumb=R('fav_add.png')))
		if FavExist == True:		
			title = 'remove %s' % title_org
			summ = 'remove Favourite'
			oc.add(DirectoryObject(key=Callback(Favourit, 
				ID='remove', url=station_url), 						# url reicht hier für Abgleich
				title=title_org,summary=summ,thumb=R('fav_remove.png')))
		
	return oc

####################################################################################################
@route(PREFIX + '/CreateTrackObject')
def CreateTrackObject(url, title, summary, fmt, thumb, include_container=False, **kwargs):
	Log('CreateTrackObject')
	Log(url);Log(title);Log(summary);Log(fmt);Log(thumb);

	if fmt == 'mp3':
		container = Container.MP3
		audio_codec = AudioCodec.MP3
	elif fmt == 'aac':
		container = Container.MP4
		audio_codec = AudioCodec.AAC

	track_object = TrackObject(
		key = Callback(CreateTrackObject, url=url,title=title,summary=summary,fmt=fmt,thumb=thumb,include_container=True),
		rating_key = url,
		title = title,
		summary = summary,
		thumb=thumb,
		items = [
			MediaObject(
				parts = [
					PartObject(key=Callback(PlayAudio, url=url, ext=fmt))
				],
				container = container,
				audio_codec = audio_codec,
				audio_channels = 2
			)
		]
	)

	if include_container:
		return ObjectContainer(objects=[track_object])
	else:
		return track_object

####################################################################################################
# Problem Zusammenbruch der track_objects-Liste: bei vielen track_objects (> 50) und der 
#	- zeitintensiven - Funktion getStreamMeta hier in PlayAudio bricht die Liste der track_objects 
#	zusammen. Nach 2-3 Aktivierungen aus der Liste wird imer wieder das 1. Objekt der Liste aktiviert, 
#	egal welches Objekt man anwählt.
#	Lösung: Verlegung der getStreamMetaFunktion in ein vorgeschaltetes DirectoryObject, hier in 
#		StationCheck.
#
@route(PREFIX + '/PlayAudio')
def PlayAudio(url):
	Log('PlayAudio')
	Log(url)				
	return Redirect(url)
	
####################################################################################################
#					Favoriten-Funktionen (anders als TuneIn2017 nur lokal und ohne Ordner)
####################################################################################################

@route(PREFIX + '/Favourit')
def Favourit(ID,url,title='',summary='',fmt='',logo=''):		# ID: add / remove
	Log('Favourit: ' + ID); Log(logo)
	
	if Dict['Favourites'] == None:
		Dict['Favourites'] = []
		
	if ID == 'add':
		if logo == '':
			logo = ICON
		Fav = '%s|%s|%s|%s|%s'	% (url,title,summary,fmt,logo)
		Dict['Favourites'].append(Fav)
		Log(Fav)
		msg = 'Favourite added'		
	else:
		Favs = Dict['Favourites']
		for fav in Favs:
			if url in fav:					# url reicht für Abgleich
				Dict['Favourites'].remove(fav)
		msg = 'Favourite removed'
		
	Dict.Save()	
	return ObjectContainer(header=L('Info'), message=msg)
				
#-----------------------------	
	
@route(PREFIX + '/FavouritesShow')
def FavouritesShow():
	Log('FavouritsShow')
	oc = ObjectContainer(title1='Station-Check', title2='Favourites')
	oc.add(DirectoryObject(key=Callback(MainMenu),title='Home', summary='Home',thumb=R('home.png')))
	
	Favs = Dict['Favourites']
	# Log(Favs)
	for fav in Favs:
		Log(fav)
		thumb = 'icon-default.jpg'
		url,title,summary,fmt,logo = fav.split('|')
		if 'listen.radionomy.com' in url:
			thumb = 'radionomy.png'
		oc.add(DirectoryObject(
			key = Callback(StationCheck, url=url,title=title,summary=summary,fmt=fmt,logo=logo),
			title=title, thumb=R(thumb)))	# summary (song,  Listener) hier nicht verwenden
			
	# remove-Button nicht erforderlich - kommt bei Anwahl der Station
	return oc
	
####################################################################################################
#									Streamtest-Funktionen (TuneIn2017)
####################################################################################################
# getStreamMeta ist Teil von streamscrobbler-python (https://github.com/dirble/streamscrobbler-python),
#	angepasst für dieses Plugin (Wandlung Objekte -> Funktionen, Prüfung Portnummer, Rückgabe Error-Wert).
#	Originalfunktiom: getAllData(self, address).
#	
#	getStreamMeta wertet die Header der Stream-Typen und -Services Shoutcast, Icecast / Radionomy, 
#		Streammachine, tunein aus und ermittelt die Metadaten.
#		Zusätzlich wird die Url auf eine angehängte Portnummer geprüft.
# 	Rückgabe 	Bsp. 1. {'status': 1, 'hasPortNumber': 'false', 'metadata': False, 'error': error}
#				Bsp. 2.	{'status': 1, 'hasPortNumber': 'true', 'error': error, 
#						'metadata': {'contenttype': 'audio/mpeg', 'bitrate': '64', 
#						'song': 'Nasty Habits 41 - Senza Filtro 2017'}}
#		
def getStreamMeta(address):
	Log('getStreamMeta: ' + address)
	# import httplib2 as http	# hier nicht genutzt
	# import pprint				# hier nicht genutzt
				
	shoutcast = False
	status = 0

	# Test auf angehängte Portnummer = zusätzl. Indikator für Stream, Anhängen von ; in StationList
	#	aber nur, wenn Link direkt mit Portnummer oder Portnummer + / endet, Bsp. http://rs1.radiostreamer.com:8020/
	hasPortNumber='false'
	p = urlparse(address)
	if p.port and p.path == '':	
		hasPortNumber='true'		
	if p.port and p.path:
		if address.endswith('/'):		# als path nur / erlaubt
			hasPortNumber='true'
	Log('hasPortNumber: ' + hasPortNumber)	
	
	request = urllib2.Request(address)
	user_agent = 'iTunes/9.1.1'
	request.add_header('User-Agent', user_agent)
	request.add_header('icy-metadata', 1)
	gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1) 	# 08.10.2017 SSLContext für https://hr-youfm-live.sslcast.addradio.de
	gcontext.check_hostname = False
	
	UrlopenTimeout = 3
	try:
		response = urllib2.urlopen(request, context=gcontext, timeout=UrlopenTimeout)	
		headers = getHeaders(response)
		# Log(headers)
		   
		if "server" in headers:
			shoutcast = headers['server']
		elif "X-Powered-By" in headers:
			shoutcast = headers['X-Powered-By']
		elif "icy-notice1" in headers:
			shoutcast = headers['icy-notice2']
		else:
			shoutcast = bool(1)

		if isinstance(shoutcast, bool):
			if shoutcast is True:
				status = 1
			else:
				status = 0
			metadata = False;
		elif "SHOUTcast" in shoutcast:
			status = 1
			metadata = shoutcastCheck(response, headers, False)
		elif "Icecast" or "137" in shoutcast:
			status = 1
			metadata = shoutcastCheck(response, headers, True)
		elif "StreamMachine" in shoutcast:
			status = 1
			metadata = shoutcastCheck(response, headers, True)
		elif shoutcast is not None:
			status = 1
			metadata = shoutcastCheck(response, headers, True)
		else:
			metadata = False
			
		try:										# Test suspended station, Bsp. Rolling Stones Radio
			content = response.read(100)			#	http://server-uk4.radioseninternetuy.com:9528/; 
			Log(content)
			if 'station is suspended' in content:
				Log('station is suspended')
				return {"status": 0, "metadata": None, "hasPortNumber": True, "error": content}
		except:
			pass
					
		response.close()
		error=''
		return {"status": status, "metadata": metadata, "hasPortNumber": hasPortNumber, "error": error}

	except urllib2.HTTPError, e:	
		error='Error, HTTPError = ' + str(e.code)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "error": error}

	except urllib2.URLError, e:						# Bsp. RANA FM 88.5 http://216.221.73.213:8000
		error='Error, URLError: ' + str(e.reason)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "error": error}

	except Exception, err:
		error='Error: ' + str(err)
		Log(error)
		return {"status": status, "metadata": None, "hasPortNumber": hasPortNumber, "error": error}
#----------------------------------------------------------------  
#	Hilfsfunktionen für getStreamMeta
#----------------------------------------------------------------  
def parse_headers(response):
	headers = {}
	int = 0
	while True:
		line = response.readline()
		if line == '\r\n':
			break  # end of headers
		if ':' in line:
			key, value = line.split(':', 1)
			headers[key] = value.rstrip()
		if int == 12:
			break;
		int = int + 1
	return headers
#---------------------------------------------------
def getHeaders(response):
	if is_empty(response.headers.dict) is False:
		headers = response.headers.dict
	elif hasattr(response.info(),"item") and is_empty(response.info().item()) is False:
		headers = response.info().item()
	else:
		headers = parse_headers(response)
	return headers
#---------------------------------------------------
def is_empty(any_structure):
	if any_structure:
		return False
	else:
		return True       
#----------------------------------------------------------------  
def stripTags(text):
	finished = 0
	while not finished:
		finished = 1
		start = text.find("<")
		if start >= 0:
			stop = text[start:].find(">")
			if stop >= 0:
				text = text[:start] + text[start + stop + 1:]
				finished = 0
	return text
#----------------------------------------------------------------  
def shoutcastCheck(response, headers, itsOld):
	if itsOld is not True:
		if 'icy-br' in headers:
			bitrate = headers['icy-br']
			bitrate = bitrate.rstrip()
		else:
			bitrate = None

		if 'icy-metaint' in headers:
			icy_metaint_header = headers['icy-metaint']
		else:
			icy_metaint_header = None

		if "Content-Type" in headers:
			contenttype = headers['Content-Type']
		elif 'content-type' in headers:
			contenttype = headers['content-type']
			
	else:
		if 'icy-br' in headers:
			bitrate = headers['icy-br'].split(",")[0]
		else:
			bitrate = None
		if 'icy-metaint' in headers:
			icy_metaint_header = headers['icy-metaint']
		else:
			icy_metaint_header = None

	if headers.get('Content-Type') is not None:
		contenttype = headers.get('Content-Type')
	elif headers.get('content-type') is not None:
		contenttype = headers.get('content-type')

	if icy_metaint_header is not None:
		metaint = int(icy_metaint_header)
		Log("icy metaint: " + str(metaint))
		read_buffer = metaint + 255
		content = response.read(read_buffer)
		# Log('icy buff: '); Log(content)			# 'utf8'-Error möglich

		start = "StreamTitle='"
		end = "';"
		
		try: 
			title = re.search('%s(.*)%s' % (start, end), content[metaint:]).group(1)
			title = re.sub("StreamUrl='.*?';", "", title).replace("';", "").replace("StreamUrl='", "")
			title = re.sub("&artist=.*", "", title)
			title = re.sub("http://.*", "", title)
			title.rstrip()
		except Exception, err:
			Log("songtitle error: " + str(err))
			title = content[metaint:].split("'")[1]

		return {'song': title, 'bitrate': bitrate, 'contenttype': contenttype.rstrip()}
	else:
		Log("No metaint")
		return False
#---------------------------------------------------	
####################################################################################################
#									Radionomy addon
####################################################################################################
@route(PREFIX + '/RD_Search')
def RD_Search(title, query):		
	Log('RD_Search')
	Log(query);
	oc = ObjectContainer(title2=title)
	oc.add(DirectoryObject(key=Callback(MainMenuRadionomy,title='Radionomy'),title='Home', 
		summary='Home',thumb=R('home_radionomy.png')))
	
	path='https://www.radionomy.com/%s/search/index?query=%s'	% (Dict['loc'], query)
	Log(path)
	page = HTTP.Request(path).content
	records = blockextract('class="browseRadioWrap"', page)
	Log(len(records))
	
	if len(records) == 1:
		return ObjectContainer(header=L('Error'), message='nothing found for >%s<' % query)
	
	for rec in records:
		url = stringextract('<a href="', '"', rec)		# Bsp. /en/radio/thebeatles/index
		url = url.replace('/index', '.m3u')
		url = 'http://listen.radionomy.com/' + url.split('/')[-1]
		img = stringextract('class="radioCover" src="', '"', rec)
		title = stringextract('class="radioName">', '</p>', rec)
		title	= unescape_html(title)
		title	= title.decode('utf-8')
		Log(url); Log(img); Log(title);
		oc.add(DirectoryObject(key=Callback(StationCheck, url=url,title=title,summary=title,
			fmt='mp3',logo=img,home='Radionomy'),title=title, summary=title, thumb=img))
				
	return oc

#---------------------------------------------------	
@route(PREFIX + '/RD_SubGenres')				# Subgenres für ein genre
def RD_SubGenres(url, title):
	Log('RD_SubGenres')
	oc = ObjectContainer(title2=title)
	oc.add(DirectoryObject(key=Callback(MainMenuRadionomy,title='Radionomy'),title='Home', 
		summary='Home',thumb=R('home_radionomy.png')))
	
	page = HTTP.Request(url).content
	GenreBlock = stringextract('id="browseSubGenre', '</ul>', page)		# Menü SubGenres
	genres = blockextract('<li class=', GenreBlock)

	if len(genres) == 0:
		msg='Nothing found for >%s<: ' % title 
		return ObjectContainer(header=L('Error'), message=msg)			
	
	i=0									# Index-Zähler für 'Mehr' (0,1 = ohne weitere Sätze)
	for genre in genres:
		url 	= stringextract('href="', '"', genre)
		url		= 'https://www.radionomy.com' + url
		title	= stringextract('internal">', '</a>', genre)
		title	= unescape_html(title)
		title	= title.decode('utf-8')
		# Log(url); Log(img); Log(title);
		oc.add(DirectoryObject(key=Callback(RD_Genre, url=url, title=title, browse='yes'),
			title=title, thumb=R('icon-folder.png')))			
		i=i+1
	return oc
#---------------------------------------------------	
@route(PREFIX + '/RD_Genre')					# Stationen eines Subgenres
# www.radionomy.com gibt http-error 302 und einen Redirect auf sich selbst zurück, 
#	 falls keine cookies gesetzt werden.
# Zugriff klappt mit urllib2 nur mit  cookie handler (HTTPCookieProcessor)
# Browsing:
# 	Browsing nicht via URL verfügbar, sondern via HTTP-POST-request.
#	Das Offenhalten der Verbindung wird mit dem keepalive-Modul realisiert
#	(s. Pluginkopf).
#	Für Multi Sessions speichern wir das OpenerDirector-Objekt in der
#	globalen Variablen openerStore[openerID]. Dict ist nicht geeignet:
#	TypeError: can't pickle lock objects (pickle.py, copy_reg.py).
#
# 1. Request: ohne Post + data lädt Startseite des SubGenre
# 2. Request: mit Post und data (scrollOffset=0) lädt erstes Nachlade-Segment

def RD_Genre(url, title, browse, offset=None, openerID=None):
	Log('RD_Genre'); Log(url); Log(browse); Log(str(offset)); Log(openerID)
	client_platform = str(Client.Platform)	# Client.Platform: None möglich
	Log('Client-Platform: ' + client_platform)							
	url_org = url					# sichern für More
	oc = ObjectContainer(title2=title.decode('utf-8'))
	oc.add(DirectoryObject(key=Callback(MainMenuRadionomy,title='Radionomy'),title='Home', 
		summary='Home',thumb=R('home_radionomy.png')))
	
	if 	offset == None:						# 1. Seite laden (ohne POST + data)
		plot = str(offset)
		cookies = cookielib.LWPCookieJar()		

		ctx = ssl.create_default_context()	# funktioniert in PMS nicht ohne SSL + context
		ctx.check_hostname = False
		ctx.verify_mode = ssl.CERT_NONE
		keepalive_handler = HTTPHandler()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies), urllib2.HTTPSHandler(context=ctx, debuglevel=1))
		Log(opener)
		opener.addheaders.append(('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'))
		opener.addheaders.append(('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'))
		opener.addheaders.append(('X-Requested-With', 'XMLHttpRequest'))		# erforderlich (ohne: Ausgabe der gesamten Seite)
		try:
			res = opener.open(url)
			page = res.read()			
		except Exception as exception:
			page = ''
			Log(str(exception))
			
		if browse == 'yes':					# für Folgeseiten: opener speichern
			openerID = 'openerID|' + serial_random()
			openerStore[openerID] = opener	# Session global speichern
			Log('openerID neu:' + openerID)
	else:									# Folgeseite laden
											# wir starten mit 0 für das 1. Nachlade-Segment
		data = {"scrollOffset": offset}		# Post-data zum Scrolling Offset	
		data = urllib.urlencode(data)
		Log(data)
		try:
			Log('openerID offset  %s: %s' % (offset, openerID))
			opener = openerStore[openerID]	# Session holen
			Log(opener)
			res = opener.open(url, data)
			page = res.read()
			# Log(page[:200])
		except Exception as exception:
			page = ''
			Log(str(exception))
							
	Log(len(page))	
	records = blockextract('class="browseRadioWrap', page)		# Stationen eines (Sub-)Genre (wie RD_Search)
	if len(records) == 0:
		msg='Nothing (more) found for >%s<: ' % title 
		return ObjectContainer(header=L('Error'), message=msg)			
		
	for rec in records:
		url = stringextract('<a href="', '"', rec)				# Bsp. /en/radio/thebeatles/index
		# Log(url)
		url = url.replace('/index', '.m3u')
		url = 'http://listen.radionomy.com/' + url.split('/')[-1] # /en/radio/ abschneiden
		# Bsp.-url http://listen.radionomy.com/101smoothjazz.m3u
		img = stringextract('class="radioCover" src="', '"', rec)
		title = stringextract('class="radioName">', '</p>', rec)
		title	= unescape_html(title)
		title	= title.decode('utf-8')

		#Log(url); Log(img); Log(title);
		oc.add(DirectoryObject(key=Callback(StationCheck, url=url,title=title,summary=title,
			fmt='mp3',logo=img,home='Radionomy'),title=title, summary=title, thumb=img))
	
	if browse == 'no':					# ohne weitere Sätze
		return oc
		
	# todo: More-Button - Post-Request ("scrollOffset=x")
	if 	offset == None:	
		offset = 0					# 0 lädt erstes Nachlade-Segment
	else:
		offset = int(offset) + 1
		
	oc.add(DirectoryObject(key=Callback(RD_Genre, url=url_org, title=title, browse='yes',
		offset=offset,openerID=openerID), title='More', thumb=R('more.png')))			
		
	return oc

####################################################################################################
#									Hilfsfunktionen
####################################################################################################
@route(PREFIX + '/SearchUpdate')
def SearchUpdate(title, start, oc=None):		
	Log('SearchUpdate')
	
	if start=='true':									# Aufruf beim Pluginstart
		if Prefs['InfoUpdate'] == True:					# Hinweis auf neues Update beim Start des Plugins 
			oc,available = presentUpdate(oc,start)
			if available == 'no_connect':
				msgH = L('Error'); 
				msg = L('Github is not available') +  ' - ' +  L('Please deselect the Plugin-Notification')
				Log(msg)		
				# return ObjectContainer(header=msgH, message=msg) # skip - das blockt das Startmenü
							
			if 	available == 'true':					# Update präsentieren
				return oc
														# Menü Plugin-Update zeigen														
		title = 'Plugin-Update | Version: ' + VERSION + ' - ' + VDATE 	 
		summary=L('Start searching for new Updates')
		tagline=L('source of supply') + ': ' + REPO_URL			
		oc.add(DirectoryObject(key=Callback(SearchUpdate, title='Plugin-Update', start='false'), 
			title=title, summary=summary, tagline=tagline, thumb=R(ICON_MAIN_UPDATER)))
		return oc
		
	else:					# start=='false', Aufruf aus Menü Plugin-Update
		oc = ObjectContainer(title2=title)	
		oc,available = presentUpdate(oc,start)
		if available == 'no_connect':
			msgH = L('Fehler'); 
			msg = L('Github is not available') 		
			return ObjectContainer(header=msgH, message=msg)
		else:
			return oc	
		
#-----------------------------
def presentUpdate(oc,start):
	Log('presentUpdate')
	ret = updater.update_available(VERSION)			# bei Github-Ausfall 3 x None
	Log(ret)
	int_lv = ret[0]			# Version Github
	int_lc = ret[1]			# Version aktuell
	latest_version = ret[2]	# Version Github, Format 1.4.1

	if ret[0] == None or ret[0] == False:
		return oc, 'no_connect'
		
	zip_url = ret[5]	# erst hier referenzieren, bei Github-Ausfall None
	url = zip_url
	summ = ret[3]			# History, replace ### + \r\n in get_latest_version, summ -> summary, 
	tag = summ.decode(encoding="utf-8", errors="ignore")  # History -> tag
	Log(latest_version); Log(int_lv); Log(int_lc); Log(tag); Log(zip_url); 
	
	if int_lv > int_lc:								# 2 Update-Button: "installieren" + "abbrechen"
		available = 'true'
		title = L('new Update available') +  ' - ' + L('install now')
		summary = 'Plugin Version: ' + VERSION + ', Github Version: ' + latest_version

		oc.add(DirectoryObject(key=Callback(updater.update, url=url , ver=latest_version), 
			title=title, summary=summary, tagline=tag, thumb=R(ICON_UPDATER_NEW)))
			
		if start == 'false':						# Option Abbrechen nicht beim Start zeigen
			oc.add(DirectoryObject(key = Callback(MainMenu), title = L('Cancel Update'),
				summary = L('continue with present Plugin'), thumb = R(ICON_UPDATER_NEW)))
	else:											# Plugin aktuell -> Main
		available = 'false'
		if start == 'false':						# beim Start unterdrücken
			oc.add(DirectoryObject(key = Callback(MainMenu), 	
				title = 'Plugin up to date | Home',
				summary = 'Plugin Version ' + VERSION + ' ' + L('is the latest version'),
				tagline = tag, thumb = R(ICON_OK)))			

	return oc,available
#----------------------------------------------------------------  
def repl_dop(liste):	# Doppler entfernen
	mylist=liste
	myset=set(mylist)
	mylist=list(myset)
	mylist.sort()
	return mylist
#----------------------------------------------------------------  
def unescape_html(line):	# HTML-Escapezeichen  ersetzen (Sprachsonderzeichen leider nur '')
	if line == None or line == '':
		return line
	
	s = htmllib.HTMLParser(None)
	s.save_bgn()
	s.feed(line)
	return s.save_end()
		
#	line_ret = (line.replace('&#39;', '\'').replace('&#233;', 'é').replace('&#232;', 'è')
#		.replace('&#250;', 'Ú'))
#----------------------------------------------------------------  
def blockextract(blockmark, mString):  	# extrahiert Blöcke begrenzt durch blockmark aus mString
	#	blockmark bleibt Bestandteil der Rückgabe - im Unterschied zu split()
	#	Rückgabe in Liste. Letzter Block reicht bis Ende mString (undefinierte Länge!),
	#		Variante mit definierter Länge siehe Plex-Plugin-TagesschauXL (extra Parameter blockendmark)
	#	Verwendung, wenn xpath nicht funktioniert (Bsp. Tabelle EPG-Daten www.dw.com/de/media-center/live-tv/s-100817)
	rlist = []				
	if 	blockmark == '' or 	mString == '':
		Log('blockextract: blockmark or mString leer')
		return rlist
	
	pos = mString.find(blockmark)
	if 	mString.find(blockmark) == -1:
		Log('blockextract: blockmark nicht in mString')
		# Log(pos); Log(blockmark);Log(len(mString));Log(len(blockmark));
		return rlist
	pos2 = 1
	while pos2 > 0:
		pos1 = mString.find(blockmark)						
		ind = len(blockmark)
		pos2 = mString.find(blockmark, pos1 + ind)		
	
		block = mString[pos1:pos2]	# extrahieren einschl.  1. blockmark
		rlist.append(block)
		# reststring bilden:
		mString = mString[pos2:]	# Rest von mString, Block entfernt	
	return rlist  
#----------------------------------------------------------------  
def stringextract(mFirstChar, mSecondChar, mString):  	# extrahiert Zeichenkette zwischen 1. + 2. Zeichenkette
	pos1 = mString.find(mFirstChar)						# return '' bei Fehlschlag
	ind = len(mFirstChar)
	#pos2 = mString.find(mSecondChar, pos1 + ind+1)		
	pos2 = mString.find(mSecondChar, pos1 + ind)		# ind+1 beginnt bei Leerstring um 1 Pos. zu weit
	rString = ''

	if pos1 >= 0 and pos2 >= 0:
		rString = mString[pos1+ind:pos2]	# extrahieren 
		
	#Log(mString); Log(mFirstChar); Log(mSecondChar); 	# bei Bedarf
	#Log(pos1); Log(ind); Log(pos2);  Log(rString); 
	return rString
#----------------------------------------------------------------  	
def serial_random(): # serial-ID's für tunein erzeugen (keine Formatvorgabe bekannt)
	basis = ['b8cfa75d', '4589', '4fc19', '3a64', '2c2d24dfa1c2'] # 5 Würfelblöcke
	serial = []
	for block in basis:
		new_block = ''.join(random.choice(block) for i in range(len(block)))
		serial.append(new_block)
	serial = '-'.join(serial)
	return serial
#---------------------------------------------------------------- 
