NAME = 'Dailymotion'
ART = 'art-default.jpg'
ICON = 'icon-default.png'

BASEURL="http://www.dailymotion.com"

# used to see if we are in a listing page or not
INLISTING=Regex("\/([0-9]+)$")

DM_QUERY = "/%ssearch/%s/1"

# Family Filter Setting ( true = filter is active, false = no filtering)
# web site defaults to the filter being active, and so does this plugin
# in the future if parental control is enabled this can be adjusted, leaving
# this code in for reference
FF=True

##############################################################################
def Start():
	Plugin.AddPrefixHandler("/video/dailymotion", MainMenu, NAME, ICON, ART)

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
	HTTP.CacheTime = CACHE_1HOUR

	# We need to read our country/language code for later usage
	# Let's default to us first off
	Dict['CCODE'] = "us"
	try:
		page_request = HTTP.Request("http://www.dailymotion.com", follow_redirects = False)
		page = page_request.content
	except Ex.RedirectError, e:
		if e.headers.has_key('Location'):
			redirect_url = e.headers['Location']
			# eg. /ca-en or /us
			Dict['CCODE']=redirect_url.split('/')[1]
	
	Dict.Save()

##############################################################################
def MainMenu():
	oc = ObjectContainer()

	# main video channel listings
	oc.add(DirectoryObject(key=Callback(GetChannels), title="Video Channels"))

	# Home page Featured videos
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE']), title="Featured Videos"))

	# What's Hot? / Popular items
	whatsHotURL=HTML.ElementFromURL(BASEURL + "/" + Dict['CCODE']).xpath('//div[@class="dmpi_list_buzz"]//div[contains(@class,"dmco_box right_title")]/a/@href')[0].split('#')[0]
	oc.add(DirectoryObject(key=Callback(GetVideoList,url=whatsHotURL), title="Popular Videos"))

	# latest videos
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE'] + "/1"), title="Latest Videos"))

	# search videos
	oc.add(DirectoryObject(key=Callback(SearchOptions), title="Search Videos"))	

	# most views
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE'] + "/visited/1"), title="Most Viewed Videos - All Time"))
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE'] + "/visited-today/1"), title="Most Viewed Videos - Today"))
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE'] + "/visited-week/1"), title="Most Viewed Videos - This Week"))
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE'] + "/visited-month/1"), title="Most Viewed Videos - This Month"))
	
	# best rated (note: rated-today doesn't work)
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE'] + "/rated/1"), title="Best Rated Videos - All Time"))
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE'] + "/rated-week/1"), title="Best Rated Videos - This Week"))
	oc.add(DirectoryObject(key=Callback(GetVideoList,url="/" + Dict['CCODE'] + "/rated-month/1"), title="Best Rated Videos - This Month"))

	return oc


##############################################################################
def GetChannels():
	
	oc = ObjectContainer()

	# get all of the categories from the bottom of the page
	data = HTML.ElementFromURL(BASEURL + "/" + Dict['CCODE'] + "/channels/1").xpath('//div[@class="dmco_html"]/a[@class="foreground"]')
	for channel in data:
		url = channel.xpath('./@href')[0]
		title = channel.xpath('./text()')[0]
		if title in ["3D Videos", "Sexy"]:
			# 3D Videos = a dedicated custom content page that's not worth parsing!
			# Sexy = mostly soft, but xxx content
			continue

		oc.add(DirectoryObject(key=Callback(ShowChoices, url=url), title=title))

	# sort here
	oc.objects.sort(key = lambda obj: obj.title)
			
	return oc


##############################################################################
def ShowChoices(url):
	oc = ObjectContainer()

	# corner case:  a few categories start with /featured in provided links ... which results in no content! 
	# removing /featured makes it works as expected.  No other urls have /featured anywhere in them (for now), 
	# so just remove it
	url=url.replace('/featured','')
	
	if not url[-2:] == "/1":
		# if we don't end in /1 we have a features page and not a listing, let's give the user featured videos option
		oc.add (
			DirectoryObject(key=Callback(GetVideoList, url=url), title="Featured Videos")
		)
		# we want to add /1 for further usage of the url variable here to land us on the first video page 
		# for further options
		url=url+"/1"

	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, url=url), 
			title="Latest Videos"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, url=url.replace("/channel/","/rated/channel/")), 
			title="Highest Rated Videos"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, url=url.replace("/channel/","/visited/channel/")), 
			title="Most Viewed Videos - All Time"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, url=url.replace("/channel/","/visited-today/channel/")), 
			title="Most Viewed Videos - Today"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, url=url.replace("/channel/","/visited-week/channel/")), 
			title="Most Viewed Videos - This Week"
		)	
	)
	oc.add(
		DirectoryObject(
			key=Callback(GetVideoList, url=url.replace("/channel/","/visited-month/channel/")), 
			title="Most Viewed Videos - This Month"
		)	
	)

	return oc
	
##############################################################################
def GetVideoList(url):
	oc = ObjectContainer()
	page = HTML.ElementFromURL(BASEURL + BuildURL(url))

	if INLISTING.search(url):
		# this is a standard listing page
		data = page.xpath('id("dual_list")//div[contains(@class,"dmpi_video_item")]')
		for video in data:	
			try:
				title = video.xpath('./h3/a[contains(@class,"video_title")]/text()')[0]
				url = video.xpath('./h3/a[contains(@class,"video_title")]/@href')[0]
				if not url[:7] == "/video/":
					# currently unparsable data such as a custom content player page, let's skip in this case
					continue

				# try for biggest/best thumbnail possible (_source) but fallback to _large and/or _medium,
				# they are not all that consistent but they should all have medium (that's what the site uses in layout)
				thumb_urls = []
				try:
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0].replace('_medium','_source'))
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0].replace('_medium','_large'))
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0])
				except:
					thumbs = []
					
				try:
					summary = video.xpath('.//div[@class="dmpi_video_description foreground"]/text()')[0]
				except:
					summary = ""
				
				duration = GetDurationFromString(video.xpath('.//div[contains(@class, "duration")]/text()')[0])
				
				# calculate rating
				# max 80px wide, 80px=5/5, 0px=0/5
				# set as style="width:80px" 
				# Plex is rating out of 10, therefore /8
				rWidth = int(video.xpath('.//div[@class="rating"]/@style')[0].replace('width:','').replace('px',''))
				rating = round(rWidth/8)
				
				oc.add(
					VideoClipObject(
						url = BASEURL + url,
						title = title, 
						summary = summary, 
						duration = duration,
						rating=rating,  
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_urls, fallback=ICON)
					)
				)
			except:
				# sometimes they leave empty div containers, skip these
				continue
	elif url == "/" + Dict['CCODE']:
		# this is the home page, we want all the featured items, there are two areas to capture here
		# and it's slightly different than standard features pages :(
		
		# first is the top area
		# they provide the top info in JSON format for their Carousel Player
		# and our HTML GET doesn't execute the Carousel so we can't get it via xpath, 
		# so let's use the JSON data they provide

		pageData = HTML.StringFromElement(page)
		topData = JSON.ObjectFromString(pageData.split('DM_Widget_PageItem_Video_Carousel.slideList = ')[1].strip().split('DM_Widget_PageItem_Video_Carousel.initialize')[0][:-1])

		for item in topData:
			try:
				title = item['videoTitle']
				url = item['videoUrl']
				if not url.startswith('http'):
				    url = BASE_URL + url
				summary = item['videoDescription']
				duration = GetDurationFromString(item['videoDuration'])
				thumb_urls = []
				thumb_urls.append(item['videoPreviewUri480'])
				thumb_urls.append(item['videoPreviewUri120'])
				oc.add(
					VideoClipObject(
						url = url,
						title = title, 
						summary = summary, 
						duration = duration, 
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_urls, fallback=ICON)
					)
				)
			except:
				continue
		
		# The rest we can get via xpath
		data = page.xpath('//div[contains(@class,"dmpi_list")]/div[contains(@class,"dmpi_slotitem_video")]')
		for video in data:
			try:
				title = video.xpath('./h3[2]/a[contains(@class,"video_title")]/text()')[0]
				url = video.xpath('./h3[2]/a[contains(@class,"video_title")]/@href')[0]
				if not url[:7] == "/video/":
					# currently unparsable data such as a custom content player page, let's skip in this case
					continue

				# try for biggest/best thumbnail possible (_source) but fallback to _large and/or _medium,
				# they are not all that consistent but they should all have medium (that's what the site uses in layout)
				thumb_urls = []
				try:
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0].replace('_medium','_source'))
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0].replace('_medium','_large'))
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0])
				except:
					thumbs = []
					
				try:
					summary = video.xpath('.//div[@class="dmco_html foreground"]/text()')[0]
				except:
					summary = ""
				duration = GetDurationFromString(video.xpath('.//div[contains(@class, "duration")]/text()')[0])
				# no rating on these pages
				
				oc.add(
					VideoClipObject(
						url = BASEURL + url,
						title = title, 
						summary = summary, 
						duration = duration, 
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_urls, fallback=ICON)
					)
				)
			except:
				# sometimes they leave empty div containers, skip these
				continue

	else:
		# this is a feature page, slightly different paths than a standard list page
		
		# first is the top area
		# they provide the top info in JSON format for their Carosel Player
		# and our HTML GET doesn't execute the Carosel so we can't get it via xpath, 
		# so let's use the JSON data the provide

		pageData = HTML.StringFromElement(page)
		topData = JSON.ObjectFromString(pageData.split('DM_Widget_PageItem_Video_Carousel.slideList = ')[1].strip().split('DM_Widget_PageItem_Video_Carousel.initialize')[0][:-1])
		
		for item in topData:
			try:
				title = item['videoTitle']
				url = item['videoUrl']
				summary = item['videoDescription']
				duration = GetDurationFromString(item['videoDuration'])
				thumb_urls = []
				thumb_urls.append(item['videoPreviewUri480'])
				thumb_urls.append(item['videoPreviewUri120'])
				oc.add(
					VideoClipObject(
						url = url,
						title = title, 
						summary = summary, 
						duration = duration, 
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_urls, fallback=ICON)
					)
				)
			except:
				continue

		# grab the rest of the featured items
		data = page.xpath('id("dual_list")//div[contains(@class,"dmpi_slotitem_video")]')
		for video in data:
			try:
				title = video.xpath('./h3[2]/a[contains(@class,"video_title")]/text()')[0]
				url = video.xpath('./h3[2]/a[contains(@class,"video_title")]/@href')[0]
				if not url[:7] == "/video/":
					# currently unparsable data such as a custom content player page, let's skip in this case
					continue

				# try for biggest/best thumbnail possible (_source) but fallback to _large and/or _medium,
				# they are not all that consistent but they should all have medium (that's what the site uses in layout)
				thumb_urls = []
				try:
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0].replace('_medium','_source'))
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0].replace('_medium','_large'))
					thumb_urls.append(video.xpath('.//img[@class="dmco_image"]/@data-src')[0])
				except:
					thumbs = []
					
				try:
					summary = video.xpath('.//div[@class="dmco_html foreground"]/text()')[0]
				except:
					summary = ""
				
				duration = GetDurationFromString(video.xpath('.//div[contains(@class, "duration")]/text()')[0])
				# no rating on these pages
				
				oc.add(
					VideoClipObject(
						url = BASEURL + url,
						title = title, 
						summary = summary, 
						duration = duration, 
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_urls, fallback=ICON)
					)
				)
			except:
				# sometimes they leave empty div containers, skip these
				continue
	
	# do we have a next link?  If so add this to our container
	next=""
	try:
		next = page.xpath('//div[@class="next"]/a/@href')[0]
		if next:
			oc.add(DirectoryObject(key=Callback(GetVideoList, url=next), title="Next Page of Results"))
	except:
		next=""
	
	return oc

##############################################################################
def BuildURL(url):
	
	# sometimes we get passed url's without our CCODE, which ends up causing issues, 
	# so if it's missing, prepend it
	# NB: for some international users this can cause issues, need to reproduce to figure out
	# proper work around.  Likely we need to check it first split is a known language prefix -- Gerk, June 28, 2012
	if url.split("/")[1] != Dict['CCODE']:
		url = "/" + Dict['CCODE'] + url

	# check our family filter setting and if required build an appropriate URL to turn if off
	# best to do it this way as their cookies can be unreliable for this purpose, site redirects to 
	# appropriate url after it's disabled
	if FF == False:
		url= "/family_filter?urlback="+String.URLEncode(url)+"&enable=false"

	return url

##############################################################################
def GetDurationFromString(duration):
	seconds = 0
	try:
		duration = duration.split(':')
		duration.reverse()
		
		for i in range(0, len(duration)):
			seconds += int(duration[i]) * (60**i)
	except:
		pass
	
	return seconds * 1000

####################################################################################################
# We add a default query string purely so that it is easier to be tested by the automated channel tester
def Search(query = "pug", stype="relevance"):
  url = DM_QUERY % (stype,String.Quote(query, usePlus = True))
  return GetVideoList(url)

####################################################################################################
def SearchOptions():
	# search videos
	oc = ObjectContainer()
	oc.add(InputDirectoryObject(key = Callback(Search, stype="relevance/"), title = 'By Relevance', prompt = 'Search Videos'))	
	oc.add(InputDirectoryObject(key = Callback(Search, stype=""), title = 'Latest', prompt = 'Search Videos'))	
	oc.add(InputDirectoryObject(key = Callback(Search, stype="rated/"), title = 'Best Rated', prompt = 'Search Videos'))
	oc.add(InputDirectoryObject(key = Callback(Search, stype="visited/"), title = 'Most Viewed - All Time', prompt = 'Search Videos'))
	oc.add(InputDirectoryObject(key = Callback(Search, stype="visited-today/"), title = 'Most Viewed - Today', prompt = 'Search Videos'))
	oc.add(InputDirectoryObject(key = Callback(Search, stype="visited-week/"), title = 'Most Viewed - This Week', prompt = 'Search Videos'))
	oc.add(InputDirectoryObject(key = Callback(Search, stype="visited-month/"), title = 'Most Viewed - This Month', prompt = 'Search Videos'))
	return oc
