# this is meant to be run as a cronjob every two weeks to update the user-flairs automatically

# it get's a list of userflairs for the subreddit, and checks for every user who has a ranked flair set 
# if he exists in our database. if yes we look up the playerprofile on playoverwatch.com to get
# the most recent rank. if that rank differs from the one that is already set in the subreddit
# we set it to the new one.


import sqlite3
import praw

from flask import Config
# from compowsr import 


def get_flair_for_sr(sr):
    ranks = config['OW_RANKS']
    res = ("", 0)
    for rank in ranks.items():
        if rank[1] <= sr and rank[1] > res[1]:
            res = rank
    return res[0]

def is_rank_flair(flair):
    ranks = config['OW_RANKS']
    if flair in ranks.keys():
        return True
    return False

def connect_db():
    rv = sqlite3.connect(config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def playoverwatch_get_skillrating(battletag, region):
    import re
    url='https://playoverwatch.com/de-de/career/pc/%s/%s' % (region, battletag.replace('#', '-'))
    resp = requests.get(url)
    xpr = '<div class="u-align-center h6">(\d+)</div>'
    m = re.search(xpr, resp.text)
    return m.group(1)

def update_sr(battletag, region):
    sr = playoverwatch_get_skillrating(battletag, region)
    global db
    db.execute("UPDATE app_links SET \
                        last_rank = ?, \
                        last_update = datetime('now'), \
                    WHERE bnet_name = ?", [sr, battletag])
    
    return sr



config = Config(__name__)

config.from_envvar('COMPOWSR_SETTINGS', silent=True)

# here it begins

# get reddit users with rank flair set
print "getting all users with rank-flair from reddit"
reddit = praw.Reddit(config['PRAW_SITE_NAME'], user_agent='flair_updater by /u/Witchtower')
subreddit = reddit.subreddit(config['PRAW_SUBREDDIT_NAME'])
to_update = [
        (user['user'].name, user['flair_css_class'])
        for user in subreddit.flair() 
        if is_rank_flair(user['flair_css_class'])
        ]
print "got %i users with a rank flair" % len(to_update)

# check who really needs to be updated

db = connect_db()

to_update_usernames = [i[0] for i in to_update]

print "db lookup if any of them haven't been updated in the last 14 days"
statement = "SELECT * FROM acc_links " #\
                        #% ','.join(['?']*len(to_update_usernames))
# AND last_update > datetime('now', '+14 days')" \
print statement
print to_update_usernames
cursor = db.execute(statement)#, to_update_usernames)
to_update2 = cursor.fetchall()
print "%i users haven't been updated in the last 14 days" % len(to_update2)


for row in to_update2:
    # pull sr and update in db
    sr = update_sr(row['bnet_name'], 'eu')
    flair = get_flair_for_sr(sr)
    subreddit.flair.set(user, css_class=flair)
    print "flair '%s' set for '%s'" % (flair, user)




print "all done"













