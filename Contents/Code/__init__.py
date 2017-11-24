import sys			
import updater
#					# weitere Module in getStreamMeta

# +++++ Shoutcast2017 - shoutcast.com-Plugin für den Plex Media Server +++++

VERSION =  '0.1.6'		
VDATE = '24.11.2017'

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

####################################################################################################
def CreateDict():
	Log('CreateDict')

	# Create dict objects
	Dict['genres'] = {}
	Dict['sortedGenres'] = []

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

	oc = ObjectContainer()
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
	oc = SearchUpdate(title=NAME, start='true', oc=oc)	# Updater-Modul einbinden
						
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
@route(PREFIX + '/StationCheck')
def StationCheck(url, title, summary, fmt, logo):
	Log('StationCheck')
	Log(title);Log(summary);Log(fmt);Log(logo);
	title_org = title; summ_org = summary
	
	oc = ObjectContainer(title1='Station-Check', title2=title)
	Log(Client.Platform)						# PHT verweigert TrackObject bei vorh. DirectoryObject 
	client = str(Client.Platform)				# None möglich
	if client.find ('Plex Home Theater') == -1: # 
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
	if '=http' not in content:
		msg='Playlist is empty: ' + title 
		return ObjectContainer(header=L('Error'), message=msg)			
		
	urls =content.splitlines()

	pls_cont = []
	for line in urls:
		if '=http' in line:	
			url = line.split('=')[1]
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
		if st == 0:							# verwerfen
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
					song = unescape(song)
				except:
					song=''
				if song.find('adw_ad=') == -1:		# ID3-Tags (Indiz: adw_ad=) verwerfen
					if bitrate and song:							
						summ = 'Song: %s | Bitrate: %sKB' % (song, bitrate) # neues summary
					if bitrate and song == '':	
						summ = '%s | Bitrate: %sKB' % (summ_org, bitrate)	# altes summary (i.d.R Song) ergänzen
					
			if  ret.get('hasPortNumber') == 'true': # auch SHOUTcast ohne Metadaten möglich, Bsp. Holland FM Gran Canaria,
				if stream_url.endswith('/'):				#	http://stream01.streamhier.nl:9010
					stream_url = '%s;' % stream_url
				else:
					stream_url = '%s/;' % stream_url
			else:	
				if stream_url.endswith('.fm/'):			# Bsp. http://mp3.dinamo.fm/ (SHOUTcast-Stream)
					stream_url = '%s;' % stream_url
			
		summ  = '%s | %s' % (summ, stream_url)
		summ = summ.decode('utf-8')
		title = title_org + ' | Stream %s | %s'  % (str(cnt), fmt)

		oc.add(CreateTrackObject(url=stream_url,title=title,summary=summ,fmt=fmt,thumb=logo,))
		
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
	import httplib
	# import httplib2 as http	# hier nicht genutzt
	# import pprint				# hier nicht genutzt
	import re					
	import urllib2			
	import ssl				# HTTPS-Handshake
	from urlparse import urlparse 
				
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
