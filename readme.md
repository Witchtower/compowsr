# compowsr
**comp**etetive **o**ver**w**atch **s**kill**r**ank verification

*abondoned*

### What it does:
It is a website that asks the user to log in with both:
 - a battle.net account
 - and a reddit account

It then looks up the skillrating of the battle.net account
~~and offers the user a selection of rank user flairs(bronze-grandmaster) for the subreddit
that depends on the skillrating.~~

~~The user chooses a flair which is then set for him.~~

And sets the highest possible flair for the user.

You will also be able to add a cronjob to update the flair for all users in the subreddit that have one of the rank-flairs set. Be careful with how often you do this, this puts a quite substantial load on playoverwatch.com if you have enough people.

### Current Status
In development. I advise to not yet use this, since it might not do exactly what it says in this readme.

### Installation for testing
You need:
 - python2.7
 - clone this repository
 - a certificate for https [self-signed works](http://www.akadia.com/services/ssh_test_certificate.html)
 - a [dev.battle.net](https://dev.battle.net/docs/read/registrations) account and app for oauth
 - a reddit account that is moderator in the subreddit
 - a reddit 'personal use script' app for api access to this moderator account
 - a reddit 'web app' app for oauth (go to preferences\>apps)
 - put all the client id's and secrets into a config:
```python
# just random stuff to encrypt the cookie with... the more the better
SECRET_KEY='fnarlaskfhöalhföäalsdhfaölsdkhflölkjjjjj'

# reddit web app
REDDIT_CLIENT_ID=''
REDDIT_CLIENT_SECRET=''
REDDIT_REDIRECT_URI='https://localhost:5000/callback_reddit'
# REDDIT_USER_AGENT='compowsr by /u/Witchtower_'


# bnet web app
BNET_CLIENT_ID=''
BNET_CLIENT_SECRET=''
BNET_REDIRECT_URI='https://localhost:5000/callback_bnet',

# set the client_id, client_secret, username, password and user_agent
# in the praw.ini (see http://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html#)
PRAW_SITE_NAME='flair_automation'
PRAW_SUBREDDIT_NAME='flair_automation'
```
 - do the praw.ini thing mentioned in the example config for the moderator account and the 'personal use script'
 - install compowsr:
```
# reference:
# C:\Users\Vann\projects\compowsr\compowser\compowser.py
C:\Users\Vann\projects\compowsr> pip install --editable .
```
 - edit the `C:\Users\Vann\projects\compowsr\start.py` to point to your certificate and key
 - set (or export) the following environment variables 
```bash
set FLASK_APP=compowsr
set FLASK_DEBUG=true
set COMPOWSR_SETTINGS=<full path to your config file>
```
 - make sure the praw.ini thing is correct (you might have to set another envvar for this)
 - initialize the database with `flask initdb`
 - start the application with `flask run`

