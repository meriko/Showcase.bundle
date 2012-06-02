import datetime, operator

####################################################################################################

TITLE = "Showcase"
ART = 'art-default.jpg'
ICON = 'icon-default.png'
SHOWCASE_PARAMS = ["sx9rVurvXUY4nOXBoB2_AdD1BionOoPy", "z/Showcase%20Video%20Centre"]
FEED_LIST = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=%s&startIndex=1&endIndex=500&query=hasReleases&query=CustomText|PlayerTag|%s&field=airdate&field=fullTitle&field=author&field=description&field=PID&field=thumbnailURL&field=title&contentCustomField=title&field=ID&field=parent"
FEEDS_LIST = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?field=ID&field=contentID&field=PID&field=URL&field=airdate&PID=%s&contentCustomField=Episode&contentCustomField=Season&query=CategoryIDs|%s&field=thumbnailURL&field=title&field=length&field=description&startIndex=1&endIndex=500&sortField=airdate&sortDescending=true"
DIRECT_FEED = "http://release.theplatform.com/content.select?format=SMIL&pid=%s&UserName=Unknown&Embedded=True"
VIDEO_URL = 'http://www.%s/%s/video/full+episodes/%s/video.html?v=%s&p=1&s=dd#%s/video/full+episodes'
LOADCATS = { 
	'shows':['/Shows/']
	}


###################################################################################################

def Start():
	Plugin.AddPrefixHandler("/video/showcase", MainMenu, TITLE, ICON, ART)

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

	# Setup the default attributes for the ObjectContainer
	ObjectContainer.title1 = TITLE
	ObjectContainer.view_group = 'List'
	ObjectContainer.art = R(ART)
	
	# Setup the default attributes for the other objects
	DirectoryObject.thumb = R(ICON)
	DirectoryObject.art = R(ART)
	EpisodeObject.thumb = R(ICON)
	EpisodeObject.art = R(ART)

	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
def MainMenu():
	return LoadShowList(cats='shows')


####################################################################################################
def LoadShowList(cats):

 	oc = ObjectContainer ( view_group="List")
	Log("started MainMenu")
	network = SHOWCASE_PARAMS

	content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
	showList = {}
	showCount = 0
	Log(content)
	
	items = content['items']

	for item in items:
		#Log("Gerk: fullTitle: %s",item['fullTitle'])
		if WantedCats(item['fullTitle'],cats):
			title = item['fullTitle'].split('/')[2]
			iid = item['ID']
			thumb_url = item['thumbnailURL']
			if not(title in showList):
				showList[title]=""
				oc.add(
					DirectoryObject(
						key = Callback(SeasonsPage, cats=cats, network=network, showtitle=title),
						title = title, 
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)
					)
				)
	# sort here
	oc.objects.sort(key = lambda obj: obj.title)

 	return oc

####################################################################################################

def VideoPlayer(sender, pid, show, title, id):

	network = "showcase.ca"
	show = show.replace(' ', '')

	title = String.Quote(title, usePlus=True)

	video_url = VIDEO_URL % (network, show, title, id, show)
	#Log(video_url)

	return Redirect(WebVideoItem(video_url))

####################################################################################################

def VideosPage(pid, iid, show):
	
	oc = ObjectContainer(
		view_group = 'InfoList'
	)
	pageURL = FEEDS_LIST % (pid, iid)
	feeds = JSON.ObjectFromURL(pageURL)

	showList = {}
	Log("Gerk: allFeeds: %s",feeds['items'])
	
	for item in feeds['items']:
		#Log("Gerk: VideosPage item: %s",item)
		title = item['title']
		try:
			# show exists, skip adding multiples
			if showList[title]:
				continue
		except:
			# show doesn't exist, add it
			showList[title]=""
			pid = item['PID']
			iid = item['contentID']
			summary =  item['description']
			duration = item['length']
			thumb_url = item['thumbnailURL']
			airdate = int(item['airdate'])/1000
			originally_available_at = Datetime.FromTimestamp(airdate).date()
			
			try:
				# try to set the seasons and episode info
				# NB: episode is set with 'index' (not in framework docs)!
				season = item['contentCustomData'][1]['value']
				seasonint = int(float(season))
				episode = item['contentCustomData'][0]['value']
				episodeint = int(float(episode))
	 			Log("Gerk: Seasoninfo %i-%i : %s",seasonint, episodeint, title)
				oc.add(
					EpisodeObject(
						key = Callback(VideoParse, pid=pid, show=show, title=title, iid=iid),
						rating_key = pid, 
						title = title,
						summary=summary,
						duration=duration,
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON),
						originally_available_at = originally_available_at,
		 				season = seasonint,
		 				index = episodeint
					)
				)
	
			except:
				# if we don't get the season/episode info then don't set it
				oc.add(
					EpisodeObject(
						key = Callback(VideoParse, pid=pid, show=show, title=title, iid=iid),
						rating_key = pid, 
						title = title,
						summary=summary,
						duration=duration,
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON),
						originally_available_at = originally_available_at
					)
				)

	return oc

# def VideosPage(sender, pid, id, network=None, show=None):
# 
# 	dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList", art=sender.art)
# 	pageUrl = FEEDS_LIST % (pid, id)
# 	feeds = JSON.ObjectFromURL(pageUrl)
# 	#Log(feeds)
# 
# 	for item in feeds['items']:
# 		title = item['title']
# 		pid = item['PID']
# 		summary =  item['description'].replace('In Full:', '')
# 		duration = item['length']
# 		thumb = item['thumbnailURL']
# 		id = item['contentID']
# 		airdate = int(item['airdate'])/1000
# 		subtitle = 'Originally Aired: ' + datetime.datetime.fromtimestamp(airdate).strftime('%a %b %d, %Y')
# 		dir.Append(Function(VideoItem(VideoPlayer, title=title, subtitle=subtitle, summary=summary, thumb=thumb, duration=duration), pid=pid, show=show, title=title, id=id))
# 
# 	return dir

####################################################################################################

def SeasonsPage(cats, network, showtitle):

	oc = ObjectContainer()
	
	pageURL = FEED_LIST % (network[0], network[1])
#	Log("SeasonsPage URL: %s",pageURL)
	content = JSON.ObjectFromURL(pageURL)
	season_list = []
	
	for item in content['items']:
		if WantedCats(item['parent'], cats) and showtitle in item['fullTitle']:
			#Log(item)
			title = item['fullTitle'].split('/')[3]
			if title not in season_list:
				if title=="":
					# bad data from provider, this is a corner case and happens often
					# enough that it's worth adding these in as uncategorized if they
					# made it to the Seasons list (it means they have child elements to view)
					title="Uncategorized Items"
				season_list.append(title)
				iid = item['ID']
				#pid = item['PID']
				thumb_url = item['thumbnailURL']
				oc.add(
					DirectoryObject(
						key = Callback(VideosPage, pid=network[0], iid=iid, show=showtitle),
						title = title,
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)
					)
				)
	oc.objects.sort(key = lambda obj: obj.title)
	return oc

# def SeasonsPage(sender, network):
# 	dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", art=sender.art)
# 
# 	content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
# 
# 	for item in content['items']:
# 		if sender.itemTitle in item['fullTitle']:
# 			title = item['fullTitle']
# 			#Log(title)
# 			title = title.split('/')[-1]
# 			#if title == 'New This Week':
# 			#	title = item['title']
# 			id = item['ID']
# 			#thumb = item['thumbnailURL']
# 			dir.Append(Function(DirectoryItem(VideosPage, title, thumb=sender.thumb), pid=network[0], id=id, network=network, show=title))
# 
# 	dir.Sort('title')
# 
# 	return dir

####################################################################################################
def WantedCats(thisShow,cats):
	
	for show in LOADCATS[cats]:
		if show in thisShow:
			return 1				
	return 0

####################################################################################################
def VideoParse(pid, show, title, iid):

	videosmil = HTTP.Request(DIRECT_FEED % pid).content
	player = videosmil.split("ref src")
	player = player[2].split('"')
	Log("Gerk: player: %s",player[1])
	# check for rtmpe, if it is for now use the webvideo
	if player[1][0:8] == "rtmpe://":
		Log("Gerk: is rtmpe based")
		network = "showcase.ca"
		show = show.replace(' ', '')
		title = String.Quote(title, usePlus=True)
		video_url = VIDEO_URL % (network, show, title, iid, show)
		Log("Gerl: video_url: %s",video_url)
		return Redirect(WebVideoItem(video_url))	

	Log("Gerk: is NOT rtmpe based, %s", player[1][0:8])
	if ".mp4" in player[1]:
		player = player[1].replace(".mp4", "")
		try:
			clip = player.split(";")
			clip = "mp4:" + clip[4]
		except:
			clip = player.split("/video/")
			player = player.split("/video/")[0]
			clip = "mp4:/video/" + clip[-1]
	else:
		player = player[1].replace(".flv", "")
		try:
			clip = player.split(";")
			clip = clip[4]
		except:
			clip = player.split("/video/")
			player = player.split("/video/")[0]
			clip = "/video/" + clip[-1]

	return Redirect(RTMPVideoItem(player, clip))

