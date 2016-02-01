import json
import urllib2
import os
import django

def get_linux_appid_dic():
    # read all steam appid<->names    
    response = urllib2.urlopen('http://api.steampowered.com/ISteamApps/GetAppList/v2/')
    applist = json.loads(response.read())['applist']['apps']
    
    # convert the steam list in a dictionary
    appid2name = {}
    for a in applist:
        appid2name[a['appid']] = a['name']
    
    
    # get all the linux appids
    response = urllib2.urlopen('https://raw.githubusercontent.com/SteamDatabase/SteamLinux/master/GAMES.json')
    linux_appids = [int(k) for k in json.loads(response.read()).keys()]
    
    
    # build the final dictionary
    linux_appid2name = {}
    
    for appid in set(linux_appids) & set(appid2name):
        linux_appid2name[appid] = appid2name[appid]
    
    
    return linux_appid2name
    
    
    
# get the list of linux appids from steamdb.info
appid2name = get_linux_appid_dic()


# setup django to access the API and database
os.environ["DJANGO_SETTINGS_MODULE"] = "linux_game_benchmarks_database.settings"
django.setup()

# get the current list of steam app ids in our db
from lgbdb.models import Game



current_appid_list = []
for g in Game.objects.values():
    current_appid_list +=[g['steam_appid']]


# for each game found in steamdb.info that is not found in our db, create a new game and insert it into the db
for appid in appid2name:
    if appid not in current_appid_list:
        g = Game(title=appid2name[appid], steam_appid = appid)
        print "Adding: " , appid2name[appid]
        g.save()


# if there is some entry in our db that does not match any appid in steamdb.info, delete it
for appid in current_appid_list:
    if appid not in appid2name:
        g = Game.objects.get(steam_appid=appid)
        print "Removing: " , g.title
        g.delete()


