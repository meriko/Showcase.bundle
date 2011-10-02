
import re, string, datetime, operator

####################################################################################################

VIDEO_PREFIX = "/video/showcase"

NAME = L('Title')

ART             = 'art-default.jpg'
ICON            = 'icon-default.png'

SHOWCASE_PARAMS     = ["sx9rVurvXUY4nOXBoB2_AdD1BionOoPy", "z/Showcase%20Video%20Centre"]

FEED_LIST    = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=%s&startIndex=1&endIndex=500&query=hasReleases&query=CustomText|PlayerTag|%s&field=airdate&field=fullTitle&field=author&field=description&field=PID&field=thumbnailURL&field=title&contentCustomField=title&field=ID&field=parent"
FEEDS_LIST      = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?field=ID&field=contentID&field=PID&field=URL&field=categoryIDs&query=BitrateEqualOrGreaterThan|400000&query=BitrateLessThan|601000&field=length&field=airdate&field=requestCount&PID=%s&contentCustomField=Show&contentCustomField=Episode&contentCustomField=Network&contentCustomField=Season&contentCustomField=Zone&contentCustomField=Subject&query=CategoryIDs|%s&field=thumbnailURL&field=title&field=length&field=description&field=assets&startIndex=1&endIndex=20&sortField=airdate&sortDescending=true"
DIRECT_FEED = "http://release.theplatform.com/content.select?format=SMIL&pid=%s&UserName=Unknown&Embedded=True"

VIDEO_URL = 'http://www.%s/%s/video/full+episodes/%s/video.html?v=%s&p=1&s=dd#%s/video/full+episodes'

###################################################################################################

def Start():
    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, L('VideoTitle'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)


####################################################################################################
def MainMenu():
    dir = MediaContainer(viewGroup="List")
    
    network = SHOWCASE_PARAMS
    
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
    showList = {}
    showCount = 0
    #parent = ""
    items = content['items']
    items.sort(key=operator.itemgetter('fullTitle'))
    for item in items:
        if "SHOWVC/Shows/" in item['fullTitle']:
            title = item['fullTitle']
            #Log(title)
            title = title.split('/')[2]
            id = item['ID']
            #thumb = item['thumbnailURL']
            try:
                if showList[title]:
                    discard = dir.Pop(showList[title]['index'])
                    #Log('Removed: %s' %discard.title)
                    dir.Append(Function(DirectoryItem(SeasonsPage, title), network=network))
                else:
                    pass
            except:
                #Log('showList does not contain %s' % title)
                showList[title] = {'id':id, 'index':showCount}
                showCount +=1
                dir.Append(Function(DirectoryItem(VideosPage, title), pid=network[0], id=id, show=title))
   
    dir.Sort('title')            
   
    return dir
    
####################################################################################################

def VideoPlayer(sender, pid, show, title, id):

    network = "showcase.ca"
    show = show.replace(' ', '')
    
    title = String.Quote(title, usePlus=True)
    
    video_url = VIDEO_URL % (network, show, title, id, show)
    #Log(video_url)
    
    return Redirect(WebVideoItem(video_url))
    
####################################################################################################

def VideosPage(sender, pid, id, network=None, show=None):

    dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList", art=sender.art)
    pageUrl = FEEDS_LIST % (pid, id)
    feeds = JSON.ObjectFromURL(pageUrl)
    #Log(feeds)

    for item in feeds['items']:
        title = item['title']
        pid = item['PID']
        summary =  item['description'].replace('In Full:', '')
        duration = item['length']
        thumb = item['thumbnailURL']
        id = item['contentID']
        airdate = int(item['airdate'])/1000
        subtitle = 'Originally Aired: ' + datetime.datetime.fromtimestamp(airdate).strftime('%a %b %d, %Y')
        dir.Append(Function(VideoItem(VideoPlayer, title=title, subtitle=subtitle, summary=summary, thumb=thumb, duration=duration), pid=pid, show=show, title=title, id=id))
    
    return dir
    
####################################################################################################

def SeasonsPage(sender, network):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", art=sender.art)

    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))

    for item in content['items']:
        if sender.itemTitle in item['fullTitle']:
            title = item['fullTitle']
            #Log(title)
            title = title.split('/')[-1]
            #if title == 'New This Week':
            #    title = item['title']
            id = item['ID']
            #thumb = item['thumbnailURL']
            dir.Append(Function(DirectoryItem(VideosPage, title, thumb=sender.thumb), pid=network[0], id=id, network=network, show=title))
    
    dir.Sort('title')
    
    return dir
####################################################################################################

