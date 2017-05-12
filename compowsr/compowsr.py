# ##################################################################### #
#   ___    ___     ___ ___   _____     ___   __  __  __    ____  _ __   #
#  /'___\ / __`\ /' __` __`\/\ '__`\  / __`\/\ \/\ \/\ \  /',__\/\`'__\ #
# /\ \__//\ \L\ \/\ \/\ \/\ \ \ \L\ \/\ \L\ \ \ \_/ \_/ \/\__, `\ \ \/  #
# \ \____\ \____/\ \_\ \_\ \_\ \ ,__/\ \____/\ \___x___/'\/\____/\ \_\  #
#  \/____/\/___/  \/_/\/_/\/_/\ \ \/  \/___/  \/__//__/   \/___/  \/_/  #
#                              \ \_\                                    #
#                               \/_/                                    #
#                                                                       #
#       [comp]etetive [o]ver[w]atch [s]kill[r]ating verification        #
# ##################################################################### #

import os
import sqlite3
import json
import urllib
import requests
import requests.auth
import praw
import datetime
from uuid import uuid4
from playoverwatch import CareerProfile
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

# initialize application instance
app = Flask(__name__)

app.config.from_object(__name__)

# default config to load
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'compowsr.db'),
    SECRET_KEY='fnord',

    PRAW_CLIENT_ID='',
    PRAW_CLIENT_SECRET='',
    PRAW_USERNAME='',
    PRAW_PASSWORD='',
    PRAW_SUBREDDIT_NAME='',
    PRAW_USER_AGENT='compowsr by /u/Witchtower_',

    REDDIT_CLIENT_ID='',
    REDDIT_CLIENT_SECRET='',
    REDDIT_REDIRECT_URI='https://localhost:5000/callback_reddit',
    REDDIT_USER_AGENT='compowsr by /u/Witchtower_',

    BNET_CLIENT_ID='',
    BNET_CLIENT_SECRET='',
    BNET_REDIRECT_URI='https://localhost:5000/callback_bnet',

    OW_RANKS={
        'bronze'     : 1,
        'silver'     : 1500,
        'gold'       : 2000,
        'platinum'   : 2500,
        'diamond'    : 3000,
        'master'     : 3500,
        'grandmaster': 4000
    }
))

# overwrite config from environment vars if they've been set 
app.config.from_envvar('COMPOWSR_SETTINGS', silent=True)

# database management
def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
# end of database management

# database initialization via '$ flask initdb' cmd
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')
# end of database initialization

# this is the only route that actually shows something to the user. 
# everything else just does whatever it's supposed to do and then it
# redirects here.
@app.route('/', methods=['GET'])
def show_status():

    if session.get('bnet_token') and not session.get('bnet_user'):
        # get username from bnet
        try:
            user = bnet_get_user(session.get('bnet_token'))
            session['bnet_user'] = user['battletag']
            session['bnet_user_id'] = user['id']
        except:
            session['bnet_user'] = None

    if session.get('reddit_token') and not session.get('reddit_user'):
        # get username from reddit
        try:
            user = reddit_get_user(session.get('reddit_token'))
            session['reddit_user'] = user['name'] 

    if session.get('reddit_token') and not session.get('reddit_user'):
        # get username from reddit
        try:
            user = reddit_get_user(session.get('reddit_token'))
            session['reddit_user'] = user['name'] 
            session['reddit_user_id'] = user['id']
        except:
            print >> sys.stderr, "show_status -> reddit_get_user failed to get user"
            session['reddit_user'] = None

    if session.get('reddit_user') and session.get('reddit_user_id') \
    and session.get('bnet_user') and session.get('bnet_user_id'):
        # get the skill rank from playoverwatch
        try:
            cp = CareerProfile('eu', session.get('bnet_user'))
            session['rank'] = cp.rank
            # session['sr'] = int(playoverwatch_get_skillrating(session.get('bnet_user'), 'eu'))
        except:
            session['rank'] = None

    # template has to check if 'sr' is True and offer a link to url_for('set_flair') in that case
    return render_template('show_status.html', status={
        'session_dump': str(session),
        'bnet_user': session.get('bnet_user'),
        'reddit_user': session.get('reddit_user'),
        'sr': session.get('rank')
    })


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('show_status'))

def is_valid_state(state):
    if state == session.get('reddit_oauth_state'):
        return True
    return False

# battle.net OAuth begin #
@app.route('/login_bnet')
def login_bnet():
    from uuid import uuid4
    state = str(uuid4())
    session['bnet_oauth_state'] = state
    params = {
        'client_id': app.config['BNET_CLIENT_ID'],
        'state': state,
        'redirect_uri': app.config['BNET_REDIRECT_URI'],
        'response_type': 'code',
        'auth_flow': 'auth_code'
    }
    redir_url = 'https://eu.battle.net/oauth/authorize?' + urllib.urlencode(params)
    return redirect(redir_url)

@app.route('/callback_bnet')
def callback_bnet():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state','')
    if not session.get('bnet_oauth_state') == state:
        abort(403)
    code = request.args.get('code')
    token = bnet_access_token_from_code(code)
    if token:
        session['bnet_token'] = token
    return redirect(url_for('show_status'))

def bnet_access_token_from_code(code):
    client_auth = requests.auth.HTTPBasicAuth(app.config['BNET_CLIENT_ID'], app.config['BNET_CLIENT_SECRET'])
    post_data = {
        'grant_type': 'authorization_code',
        'scope': '',
        'code': code,
        'redirect_uri': app.config['BNET_REDIRECT_URI']
    }
    response = requests.post('https://eu.battle.net/oauth/token', auth=client_auth, data=post_data)
    token_json = response.json()
    if token_json.has_key('access_token'):
        return token_json['access_token']
    return None

def bnet_get_user(token):
    response = requests.get('https://eu.api.battle.net/account/user?access_token=' + token)
    me_json = json.loads(response.text)
    return me_json
# battle.net OAuth end #

# reddit.com OAuth begin #
@app.route('/login_reddit')
def login_reddit():
    # we need to save the state somewhere for future use
    state = str(uuid4())
    session['reddit_oauth_state'] = state
    params = {
        'client_id': app.config['REDDIT_CLIENT_ID'],
        'response_type': 'code',
        'state': state,
        'redirect_uri': app.config['REDDIT_REDIRECT_URI'],
        'duration': 'temporary',
        'scope': 'identity'
    }
    redir_url = 'https://ssl.reddit.com/api/v1/authorize?' + urllib.urlencode(params)
    return redirect(redir_url)

@app.route('/callback_reddit')
def callback_reddit():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not is_valid_state(state):
        # something fishy, don't do fishy
        abort(403)
    code = request.args.get('code')
    token = reddit_access_token_from_code(code)
    if token: 
        session['reddit_token'] = token
    return redirect(url_for('show_status'))

def reddit_access_token_from_code(code):
    client_auth = requests.auth.HTTPBasicAuth(app.config['REDDIT_CLIENT_ID'], app.config['REDDIT_CLIENT_SECRET'])
    post_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': app.config['REDDIT_REDIRECT_URI']
    }
    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': app.config['REDDIT_USER_AGENT']
    })
    response = requests.post(
        'https://ssl.reddit.com/api/v1/access_token',
        headers=headers,
        auth=client_auth,
        data=post_data
    )
    token_json = response.json()
    if token_json.has_key('error'):
	msg = "Unknown error."
        if token_json.has_key('message'):
            msg = token_json['message']
        flash("Something went wrong with reddit: %s %s" % (token_json.get('error',''), msg ))
    if token_json.has_key('access_token'):
        return token_json['access_token']
    return None

def reddit_get_user(token):
    headers = requests.utils.default_headers()
    headers.update({'Authorization': 'bearer ' + token})
    headers.update({'User-Agent': app.config['REDDIT_USER_AGENT']})
    response = requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)
    me_json = json.loads(response.text)
    return me_json
# reddit.com OAuth end #

# playoverwatch.com SkillRating-Scraper begin #
def playoverwatch_get_skillrating(battletag, region):
    import re
    url='https://playoverwatch.com/de-de/career/pc/%s/%s' % (region, battletag.replace('#', '-'))
    resp = requests.get(url)
    xpr = '<div class="u-align-center h6">(\d+)</div>'
    m = re.search(xpr, resp.text)
    return m.group(1)
# playoverwatch.com SkillRating-Scraper end #

# praw set rank flair
""" to help you understand the logic of what happens here:
        bnet    reddit  new_sr      action
============================================
CaseX   =       =       <=          nothing
                                    set reddit flair

Case1   =       =       >           update skill_rank in db
                                    set reddit flair

Case3   =       !=      ?           remove reddit flair (from old account)
                                    update reddit_id and skill_rank in db
                                    set reddit flair (for new reddit account)

Case2   !=      =       ?           update bnet_id and skill_rank in db
                                    set reddit flair

Case0   !=      !=      ?           insert bnet_id, reddit_id, skill_rank in db
                                    set reddit_flair
set reddit flair in every case, put below
"""


@app.route('/set_flair')
def set_flair():
    # prettier names for stuff
    bnet_user_name = session.get('bnet_user')
    bnet_user_id = session.get('bnet_user_id')
    reddit_user_name = session.get('reddit_user')
    reddit_user_id = session.get('reddit_user_id')
    sr = session.get('rank')

    # initialize praw_user_flair
    reddit = praw.Reddit(app.config['PRAW_SITE_NAME'], user_agent='test by /u/Witchtower_')
    praw_user_flair = reddit.subreddit(app.config['PRAW_SUBREDDIT_NAME']).flair

    # make sure we have everything we need
    if not ( bnet_user_name and bnet_user_id ):
        flash('Aw, Rubbish! You have to log in with reddit.')
        return redirect(url_for('show_status'))

    if not ( reddit_user_name and reddit_user_id ):
        flash('Aw, Rubbish! You have to log in with battle.net.')
        return redirect(url_for('show_status'))

    if not ( sr and type(sr) == int ):
        flash('It seems we cannot find your rank on your profilepage. \
                Maybe playoverwatch.com is down? Or they changed something with the website... \
                please pm me (/u/Witchtower_) on reddit so I can fix this.')
        return redirect(url_for('show_status'))

    # here we start doing stuff 
    db = get_db()

    # check if accounts exist in db
    db_cursor = db.execute("SELECT * FROM acc_links WHERE bnet_id = ? OR reddit_id = ?", \
                                                         [bnet_user_id,  reddit_user_id])
    db_row = db_cursor.fetchone() 
    # None if no entry, can't be multiple because of unique index over acc_links(bnet_id, reddit_id)

    if not db_row: # no entry for either account, just insert + set flair
# start /Case0/
        try:
            with db:
                db.execute("INSERT INTO acc_links ( \
                                bnet_id, bnet_name, \
                                reddit_id, reddit_name, \
                                last_rank, last_update) \
                            VALUES (?, ?, ?, ?, ?, ?)", \
                            (   bnet_user_id, bnet_user_name, \
                                reddit_user_id, reddit_user_name, \
                                sr, datetime.datetime.now() )\
                          )
        except:
            flash('Aw, Rubbish! Couldn\'t write to database. (/Case0/)')
            return redirect(url_for('show_status'))

# end /Case0/

    elif db_row['bnet_id'] == bnet_user_id \
           and db_row['reddit_id'] == reddit_user_id \
           and db_row['last_rank'] < sr:
# start /Case1/
        try:
            with db:
                db.execute("UPDATE acc_links SET \
                                last_rank = ?, last_update = ? \
                            WHERE bnet_id = ? AND reddit_id = ?",\
                            (sr, datetime.datetime.now(), \
                                 bnet_user_id, reddit_user_id) \
                          )
        except:
            flash('Aw, Rubbish! Couldn\'t write to database. (/Case1/)')
            return redirect(url_for('show_status'))
            
# end /Case1/
        
    elif db_row['bnet_id'] != bnet_user_id and db_row['reddit_id'] == reddit_user_id:
# start /Case2/
        try:
            with db:
                db.execute("UPDATE acc_links SET \
                                bnet_id = ?, bnet_name = ?, \
                                last_rank = ?, last_update = ? \
                            WHERE reddit_id = ?", \
                            (bnet_user_id, bnet_user_name, \
                                sr, datetime.datetime.now(), \
                             reddit_user_id)
                          )
        except:
            flash('Aw, Rubbish! Couldn\'t write to database. (/Case2/)')
            return redirect(url_for('show_status'))

# end /Case2/

    elif db_row['reddit_id'] != reddit_user_id and db_row['bnet_id'] == bnet_user_id:
# start /Case3/
        # unset flair for old reddit account
        if praw_user_flair.get(redditor=db_row['reddit_name']) in config['OW_RANKS'].keys():
            praw_user_flair.set(db_row['reddit_name'], css_class="")
        # update reddit account and skill rating in database
    return redirect(url_for('show_status'))

def get_flair_for_sr(sr, ranks):
    res = ("", 0)
    for rank in ranks.items():
        if rank[1] <= sr and rank[1] > res[1]:
            res = rank
    return res[0]
        
