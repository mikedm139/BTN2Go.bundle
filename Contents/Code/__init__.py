PREFIX 		= '/video/btn2go'
NAME 		= 'BTN2Go'
ICON 		= 'icon-default.png'
ART		= 'art-default.jpg'

SCHEDULE 	= 'http://www.btn2go.com/btn2go/schedule'
GAMES_JSON	= 'http://smbsolr.cdnak.neulion.com/solr/btn_sch/select?q=%s&sort=gameTime+asc&rows=300&wt=json'
VIDEO_URL 	= 'http://www.btn2go.com/btn2go/live.jsp?id=%s'

def Start():
	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = NAME
	DirectoryObject.thumb = R(ICON)
	DirectoryObject.art = R(ART)
	VideoClipObject.thumb= R(ICON)

def ValidatePrefs():
    ## do some checks and return a
    ## message container
    if( Prefs['username'] and Prefs['password'] ):
        Log("Login succeeded")
    else:
        Log("Login failed")
        return ObjectContainer(
            header="Error",
            message="You need to provide a valid username and password. Please buy a subscription."
        )

@handler(PREFIX, NAME)
def MainMenu():
	oc = ObjectContainer()
	oc.add(DirectoryObject(key=Callback(SortMenu, option = "All"), title = "All"))
	oc.add(DirectoryObject(key=Callback(SortMenu, option = "Sport"), title = "Search by Sport"))
	oc.add(DirectoryObject(key=Callback(SortMenu, option = "School"), title = "Search by School"))
	return oc

@route(PREFIX + '/sortmenu')
def SortMenu(option):
	oc = ObjectContainer(title2=option)
	if option == "All":
		return DateMenu(option="All")
	elif option == "Sport":
		selector = "sportSelector"
		
	elif option == "School":
		selector = "schoolSelector"
	data = HTML.ElementFromURL(SCHEDULE)
	
	for entry in data.xpath('//div[@id="'+selector+'"]//a'):
		entry_id = entry.get('id').split('_')[1]
		entry_name = entry.text
		values = {"title":entry_name, "id":entry_id}
		oc.add(DirectoryObject(key=Callback(DateMenu, option=option, values=values), title=entry_name))
	return oc

@route(PREFIX + '/datemenu', values=dict)
def DateMenu(option, values=None):
	if values:
		oc = ObjectContainer(title1=option, title2=values['title'])
	else:
		oc = ObjectContainer(title2=option)
	oc.add(DirectoryObject(key=Callback(Today, option=option, values=values), title="Today"))
	oc.add(DirectoryObject(key=Callback(Previous, option=option, values=values), title="Previous Games"))
	return oc

@route(PREFIX + '/today', values=dict)
def Today(option, values=None):
	if values:
		oc = ObjectContainer(title1 = option, title2 = values['title'], no_cache = True)
		if option == "Sport":
			params = "?day=today&lsid=%s" % values['id']
		elif option == "School":
			params = "?day=today&sid=%s" % values['id']
	else:
		oc = ObjectContainer(title2 = option, no_cache = True)
		params = "?day=today"
	data = HTML.ElementFromURL(SCHEDULE + params)
	for game in data.xpath('//table/tr'):
		game_id 	= game.get('id').split('_')[1]
		sport 		= ''.join(game.xpath('.//div[@class="item sport"]//text()'))
		awayTeam 	= game.xpath('.//div[@class="teamName"]')[0].text
		homeTeam 	= game.xpath('.//div[@class="teamName"]')[1].text
		gameStatus	= game.xpath('.//div[@class="item"]/span')[0].text
		if option == "Sport":
			title = "%s vs. %s" % (awayTeam, homeTeam)
		else:
			title = "%s vs. %s - %s" % (awayTeam, homeTeam, sport)
		summary = gameStatus
		if gameStatus == "Final":
			if Prefs['score_summary']:
				awayScore = game.xpath('.//span[@class="showscore"]')[0].text
				homeScore = game.xpath('.//span[@class="showscore"]')[1].text
				summary = "%s - %s %s" % (awayScore, homeScore, gameStatus)
			oc.add(VideoClipObject(url=VIDEO_URL % game_id, title=title, summary=summary))
		else:
			started = game.xpath('.//div[@class="item watchBtnBox"]/a')[0].text
			if started == "WATCH LIVE":
				oc.add(VideoClipObject(url=VIDEO_URL % game_id, title=title, summary=started))
			elif started == "UPCOMING EVENT":
				oc.add(DirectoryObject(key=Callback(NotStarted, title=title, status=gameStatus), title=title, summary=summary))
			else:
				Log.Debug("Unknown status: %s" % started)
	return oc

@route(PREFIX + '/previous', values=dict)
def Previous(option, values=None):
	if values:
		oc = ObjectContainer(title1 = option, title2 = values['title'])
	else:
		oc = ObjectContainer(title2 = option)
	today = Datetime.Now().date()
	yesterday = (today - Datetime.Delta(days=1))
	oc.add(DirectoryObject(key=Callback(Calendar, date_begin=str(yesterday), date_end=str(today), option=option, values=values), title = "Yesterday"))
	oc.add(DirectoryObject(key=Callback(Calendar, date_begin=str(today - Datetime.Delta(days=7)), date_end=str(today), option=option, values=values), title = "Last Week"))
	oc.add(DirectoryObject(key=Callback(Calendar, date_begin=str(today - Datetime.Delta(days=30)), date_end=str(today), option=option, values=values), title = "Last Month"))
	oc.add(DirectoryObject(key=Callback(Seasons, option=option, values=values), title = "Previous Seasons"))
	return oc

@route(PREFIX + '/seasons', values=dict)
def Seasons(option, values=None):
	oc = ObjectContainer(title1=option, title2="Seasons")
	for season in ['2013', '2012', '2011']:
		oc.add(DirectoryObject(key=Callback(Months, season=season, option=option, values=values), title=season))
	return oc

@route(PREFIX + '/months', values=dict)
def Months(season, option, values=None):
	oc = ObjectContainer(title1=option, title2="%s Season" % season)
	MONTHS = [
		{"title":"August", 	"date_begin":"%d-08-01" % (int(season)), 	"date_end":"%d-09-01" % (int(season))},
		{"title":"September", 	"date_begin":"%d-09-01" % (int(season)), 	"date_end":"%d-10-01" % (int(season))},
		{"title":"October", 	"date_begin":"%d-10-01" % (int(season)), 	"date_end":"%d-11-01" % (int(season))},
		{"title":"November", 	"date_begin":"%d-11-01" % (int(season)), 	"date_end":"%d-12-01" % (int(season))},
		{"title":"December", 	"date_begin":"%d-12-01" % (int(season)), 	"date_end":"%d-01-01" % (int(season)+1)},
		{"title":"January", 	"date_begin":"%d-01-01" % (int(season)+1), 	"date_end":"%d-02-01" % (int(season)+1)},
		{"title":"February", 	"date_begin":"%d-02-01" % (int(season)+1), 	"date_end":"%d-03-01" % (int(season)+1)},
		{"title":"March", 	"date_begin":"%d-03-01" % (int(season)+1), 	"date_end":"%d-04-01" % (int(season)+1)},
		{"title":"April", 	"date_begin":"%d-04-01" % (int(season)+1), 	"date_end":"%d-05/01" % (int(season)+1)},
		{"title":"May", 	"date_begin":"%d-05-01" % (int(season)+1), 	"date_end":"%d-06-01" % (int(season)+1)},
		{"title":"June", 	"date_begin":"%d-06-01" % (int(season)+1), 	"date_end":"%d-07-01" % (int(season)+1)},
		]
	for month in MONTHS:
		oc.add(DirectoryObject(key=Callback(Calendar, date_begin=month['date_begin'], date_end=month['date_end'], option=option, values=values), title = month['title']))
	return oc

@route(PREFIX + '/calendar', values=dict)
def Calendar(date_begin, date_end, option, values=None):
	if values:
		oc = ObjectContainer(title1 = option, title2 = values['title'])
	else:
		oc = ObjectContainer(title2 = option)
	time_format = String.Quote("gameTime:[%sT00:00:00Z TO %sT00:00:00Z]" % (date_begin, date_end))
	games = JSON.ObjectFromURL(GAMES_JSON % time_format)
	STATUS = ["Upcoming", "Live", "Final"]
	for game in games['response']['docs']:
		game_id		= game['id']
		awayTeam 	= game['awayTeamName']
		awayScore 	= game['awayTeamScore']
		sport		= game['sportId']
		homeTeam 	= game['homeTeamName']
		homeScore 	= game['awayTeamScore']
		gameTime	= Datetime.ParseDate(game['gameTime'])
		gameStatus	= int(game['status'])
		endTime = Datetime.ParseDate(game['gameEndTime'])
		delta = endTime - gameTime
		duration = int(delta.total_seconds() * 1000)
		if Prefs['score_summary']:
			summary = "%s - %s %s" % (awayScore, homeScore, STATUS[gameStatus])
		else:
			summary = "%s" % STATUS[gameStatus]
		oc.add(VideoClipObject(
			url			= VIDEO_URL % game_id,
			title 			= "%s vs. %s %s" % (awayTeam, homeTeam, sport),
			summary			= summary,
			originally_available_at	= gameTime.date(),
			duration 		= duration,
			thumb			= R('icon-default.png')
		))
	if len(oc) < 1:
		return ObjectContainer(header="No Games", message="No Games found in requested period")
	else:
		return oc
	
@route(PREFIX + '/notstarted')
def NotStarted(title, status):
	return ObjectContainer(header="Not started yet.", message="%s does not start until %s" % (title, status))
