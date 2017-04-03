# this is meant to be run as a cronjob every two weeks to update the user-flairs automatically

# it get's a list of userflairs for the subreddit, and checks for every user who has a ranked flair set 
# if he exists in our database. if yes we look up the playerprofile on playoverwatch.com to get
# the most recent rank. if that rank differs from the one that is already set in the subreddit
# we set it to the new one.


import sqlite3
import praw
import playoverwatch

from flask import Config

def get_flair_for_sr(sr):
    ranks = config['OW_RANKS']
    res = ("", 0)
    for rank in ranks.items():
        if rank[1] <= sr and rank[1] > res[1]:
            res = rank
    return res[0]

def connect_db(config):
    rv = sqlite3.connect(config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def main():
    config = Config(__name__)

    config.from_envvar('COMPOWSR_SETTINGS', silent=True)

    # get the praw stuff
    reddit = praw.Reddit(config['PRAW_SITE_NAME'], user_agent='flair_updater by /u/Witchtower')
    subreddit = reddit.subreddit(config['PRAW_SUBREDDIT_NAME'])

    # get reddit users with rank flair set
    print "getting all users with rank-flair from reddit"

    to_update = [
            (user['user'].name, user['flair_css_class'])
            for user in subreddit.flair() 
            if user['flair_css_class'] in config['OW_RANKS'].keys()
            ]

    print "got %i users with a rank flair" % len(to_update)

    # check who really needs to be updated
    db = connect_db(config)

    to_update_usernames = [i[0] for i in to_update]

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
        new_rank = playoverwatch.CareerProfile('eu', row['bnet_name']).rank
        db.execute("UPDATE acc_links SET \
                            last_rank = ?, \
                            last_update = datetime('now') \
                        WHERE bnet_name = ?", [new_rank, row['bnet_name']])
        subreddit.flair.set(row['reddit_name'], css_class=new_rank)
        print "flair '%s' set for '%s'" % (new_rank, row['reddit_name'])




    print "all done"

if __name__ == "__main__":
    main()











