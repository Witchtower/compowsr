# this is meant to be run as a cronjob every two weeks to update the user-flairs automatically
# it get's a list of userflairs for the subreddit, and checks for every user who has a ranked flair set 
# if he exists in our database. if yes we look up the playerprofile on playoverwatch.com to get
# the most recent rank. if that rank differs from the one that is already set in the subreddit
# we set it to the new one.


import sqlite3
import praw

from flask import Config
# from compowsr import 

def is_rank_flair(flair):
    ranks = config['OW_RANKS']
    if flair in ranks.keys():
        return True
    return False

config = Config(__name__)
config.from_envvar('COMPOWSR_SETTINGS', silent=True)

reddit = praw.Reddit(config['PRAW_SITE_NAME'], user_agent='flair_updater by /u/Witchtower')
subreddit = reddit.subreddit(config['PRAW_SUBREDDIT_NAME'])
to_update = [
        (user['user'].name, user['flair_css_class'])
        for user in subreddit.flair() 
        if is_rank_flair(user['flair_css_class'])
        ]

print to_update



















