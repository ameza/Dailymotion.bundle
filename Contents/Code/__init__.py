NAME='Dailymotion'
ICON='icon-default.png'
ART='art-default.jpg'

##############################################################################
def Start():

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

	# Setup the default attributes for the ObjectContainer
	ObjectContainer.title1 = NAME
	ObjectContainer.view_group = 'List'
	ObjectContainer.art = R(ART)
	
	# Setup the default attributes for the other objects
	DirectoryObject.thumb = R(ICON)
	DirectoryObject.art = R(ART)
	VideoClipObject.thumb = R(ICON)
	VideoClipObject.art = R(ART)
	EpisodeObject.thumb = R(ICON)
	EpisodeObject.art = R(ART)

	# Setup some basic things the plugin needs to know about
	# we probably don't want to use cache otherwise some things will give bad results (like popular today and the like)
	# HTTP.CacheTime = CACHE_1HOUR


##############################################################################
@handler('/video/dailymotion', NAME, art=ART, thumb=ICON)
def MainMenu():
	oc = ObjectContainer()

	# main video channel listings
	oc.add(DirectoryObject(key=Callback(GetChannels), title="Video Channels"))

	oc.add(DirectoryObject(key=Callback(GetVideoList, path="videos", filters="featured", sort="recent", title2="Featured Videos"), title="Featured Videos"))
	oc.add(DirectoryObject(key=Callback(GetVideoList, path="videos", filters="buzz", sort="recent", title2="Popular Videos"), title="Popular Videos"))
	oc.add(DirectoryObject(key=Callback(GetVideoList, path="videos", sort="recent", title2="Latest Videos"), title="Latest Videos"))

	# search videos
	oc.add(DirectoryObject(key=Callback(SearchOptions), title="Search Videos"))	

	# most views
	oc.add(DirectoryObject(key=Callback(GetVideoList, sort="visited", title2="Most Viewed Videos - All Time"), title="Most Viewed Videos - All Time"))
	oc.add(DirectoryObject(key=Callback(GetVideoList, sort="visited-today", title2="Most Viewed Videos - Today"), title="Most Viewed Videos - Today"))
	oc.add(DirectoryObject(key=Callback(GetVideoList, sort="visited-week", title2="Most Viewed Videos - This Week"), title="Most Viewed Videos - This Week"))
	oc.add(DirectoryObject(key=Callback(GetVideoList, sort="visited-month", title2="Most Viewed Videos - This Month"), title="Most Viewed Videos - This Month"))
	
	# best rated (note: rated-today doesn't work)
	oc.add(DirectoryObject(key=Callback(GetVideoList, sort="rated", title2="Best Rated Videos - All Time"), title="Best Rated Videos - All Time"))
	oc.add(DirectoryObject(key=Callback(GetVideoList, sort="rated-today", title2="Best Rated Videos - Today"), title="Best Rated Videos - Today"))
	oc.add(DirectoryObject(key=Callback(GetVideoList, sort="rated-week", title2="Best Rated Videos - This Week"), title="Best Rated Videos - This Week"))
	oc.add(DirectoryObject(key=Callback(GetVideoList, sort="rated-month", title2="Best Rated Videos - This Month"), title="Best Rated Videos - This Month"))

	return oc


##############################################################################
@route("/video/dailymotion/getvideolist")
def GetVideoList(path="videos", filters="", sort="recent", limit=25, page=1, title2="Videos", search=""):
	oc = ObjectContainer(title2=title2)
	fields="title,description,thumbnail_large_url,rating,url,duration,created_time,views_total"
	fullURL = "https://api.dailymotion.com/%s?sort=%s&filters=%s&limit=%i&page=%i&fields=%s" % (path, sort, filters, limit, page, fields)
	if search!="":
		fullURL = "%s&search=%s" % (fullURL, search) # only add search if applicable, API doesn't like a NULL search request
	data = JSON.ObjectFromURL(fullURL)
	for video in data['list']:
		title = video['title']
		url = video['url']
		duration = video['duration']*1000 # worst case duration is 0 so we get 0

		try:
			views = video["views_total"]
		except:
			views = 0	

		try:
			summary = String.StripTags(video['description'].replace("<br />","\n")) + "\n\nViews: %i" % views
		except:
			summary = ""

		try:
			thumb_url = video['thumbnail_large_url']
		except:
			thumb_url = ""
		
		try:
			rating = float(video['rating']*2)
		except:
			rating = float(0)
			
		try:
			originally_available_at = Datetime.FromTimestamp(video['created_time'])
		except:
			originally_available_at = Datetime.Now()
			
		oc.add(
			VideoClipObject(
				title=title, 
				summary=summary,
				url=url,
				duration=duration,
				rating=rating,
				originally_available_at=originally_available_at, 
				thumb=Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)
			)
		)
	
	# pagination
	if data['has_more']:
		oc.add(NextPageObject(key=Callback(GetVideoList, sort=sort, filters=filters, limit=limit, page=page+1, title2=title2), title="Next Page of Results"))
		
	
	return oc


##############################################################################
@route("/video/dailymotion/getchannels")
def GetChannels():
	
	oc = ObjectContainer()
	
	# will leave sort=alpha in here in case it works in the future, but right now it seems like a bug in their api, it still returns popular and not alpha no matter what you choose
	data = JSON.ObjectFromURL("https://api.dailymotion.com/channels?sort=alpha")
	for channel in data['list']:
		oc.add(DirectoryObject(key=Callback(ShowChannelChoices, channel=channel['id']), title=channel['name'], summary=channel['description']))

	# sort here until they resolve that bug
	oc.objects.sort(key = lambda obj: obj.title)
			
	return oc

@route("/video/dailymotion/showchannelchoices")
##############################################################################
def ShowChannelChoices(channel):
	oc = ObjectContainer()

	oc.add (
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", filters="featured", sort="recent", title2="Featured Videos"), 
			title="Featured Videos"
		)
	)

	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="recent", title2="Latest Videos"), 
			title="Latest Videos"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="rated", title2="Highest Rated Videos - All Time"), 
			title="Highest Rated Videos - All Time"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="rated-today", title2="Highest Rated Videos - Today"), 
			title="Highest Rated Videos - Today"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="rated-week", title2="Highest Rated Videos - This Week"), 
			title="Highest Rated Videos - This Week"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="rated-month", title2="Highest Rated Videos - This Moneh"), 
			title="Highest Rated Videos - This Month"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="visited", title2="Most Viewed Videos - All Time"), 
			title="Most Viewed Videos - All Time"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="visited-today", title2="Most Viewed Videos - Today"), 
			title="Most Viewed Videos - Today"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="visited-week", title2="Most Viewed Videos - This Week"), 
			title="Most Viewed Videos - This Week"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, path="channel/"+channel+"/videos", sort="visited-month", title2="Most Viewed Videos - This Month"), 
			title="Most Viewed Videos - This Month"
		)	
	)

	return oc



####################################################################################################
# We add a default query string purely so that it is easier to be tested by the automated channel tester
def Search(query = "pug", stype="relevance"):
	return GetVideoList(sort=stype, search=String.Quote(query, usePlus = True))
	
####################################################################################################
@route("/video/dailymotion/searchoptions")
def SearchOptions():
	# search videos
	oc = ObjectContainer()
	oc.add(InputDirectoryObject(key = Callback(Search, stype="relevance"), title = 'By Relevance', prompt = 'Search Videos'))	
	oc.add(InputDirectoryObject(key = Callback(Search, stype="recent"), title = 'Latest', prompt = 'Search Videos'))	
	oc.add(InputDirectoryObject(key = Callback(Search, stype="rated"), title = 'Best Rated', prompt = 'Search Videos'))
	oc.add(InputDirectoryObject(key = Callback(Search, stype="visited"), title = 'Most Viewed - All Time', prompt = 'Search Videos'))
	oc.add(InputDirectoryObject(key = Callback(Search, stype="visited-today"), title = 'Most Viewed - Today', prompt = 'Search Videos'))
	oc.add(InputDirectoryObject(key = Callback(Search, stype="visited-week"), title = 'Most Viewed - This Week', prompt = 'Search Videos'))
	oc.add(InputDirectoryObject(key = Callback(Search, stype="visited-month"), title = 'Most Viewed - This Month', prompt = 'Search Videos'))
	return oc
