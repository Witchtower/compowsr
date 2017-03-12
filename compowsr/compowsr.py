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
        'Bronze'     : 1,
        'Silver'     : 1500,
        'Gold'       : 2000,
        'Platinum'   : 2500,
        'Diamond'    : 3000,
        'Master'     : 3500,
        'Grandmaster': 4000
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

# ###### #
# ROUTES #
# ###### #

@app.route('/', methods=['GET'])
def show_status():

    if session.get('bnet_token') and not session.get('bnet_user'):
        try:
            user = bnet_get_user(session.get('bnet_token'))
            session['bnet_user'] = user['battletag']
            session['bnet_user_id'] = user['id']
        except:
            session['bnet_user'] = None

    if session.get('reddit_token') and not session.get('reddit_user'):
        try:
            user = reddit_get_user(session.get('reddit_token'))
            session['reddit_user'] = user['name'] 
            session['reddit_user_id'] = user['id']
        except:
            session['reddit_user'] = None

    if session.get('reddit_user') and session.get('reddit_user_id') \
    and session.get('bnet_user') and session.get('bnet_user_id'):
        # if we have both handles 
        # get the skill rank from playoverwatch
        try:
            session['sr'] = int(playoverwatch_get_skillrating(session.get('bnet_user'), 'eu'))
        except:
            session['sr'] = None

    # flair is send after user flair selection and form submit
    # to '/set_flair'
    return render_template('show_status.html', status={
        'session_dump': str(session),
        'bnet_user': session.get('bnet_user'),
        'reddit_user': session.get('reddit_user'),
        'sr': session.get('sr'),
        'ranks': [ (rank, min_sr) \
                    for rank, min_sr \
                    in app.config['OW_RANKS'].items() \
                    if session.get('sr') >= min_sr \
                 ]
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
    open('log.txt', 'a').write(response.text)
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
    response = requests.post('https://ssl.reddit.com/api/v1/access_token', auth=client_auth, data=post_data)
    token_json = response.json()
    if token_json.has_key('access_token'):
        return token_json['access_token']
    return None

def reddit_get_user(token):
    headers = {
        'Authorization': 'bearer ' + token
    }
    response = requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)
    open('log.txt', 'a').write(response.text)
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

@app.route('/set_flair', methods=['POST'])
def set_flair():
    selected_rank = request.form.get('rank')
    skill_rank = session.get('sr')
    ranks = app.config['OW_RANKS']

    if skill_rank >= ranks[selected_rank]:
        # check db for existing usage of bnet account
        db = get_db()
        query = """
        SELECT 
            emc.exact_match AS exact_match,
            dre.different_reddit_acc AS different_reddit_acc
        FROM 
            (
                SELECT
                    COUNT(bnet_id) AS exact_match
                FROM
                    acc_links
                WHERE
                    bnet_id = ?
                    AND reddit_id = ?
            
            ) AS emc,
            (
                SELECT
                    COUNT(bnet_id) as different_reddit_acc
                FROM
                    acc_links
                WHERE
                    bnet_id = ?
                    AND NOT reddit_id = ?
            ) AS dre
        """
        cur = db.execute(query, [
            session.get('bnet_user_id'),
            session.get('reddit_user_id'),
            session.get('bnet_user_id'),
            session.get('reddit_user_id')
            ])
        row = cur.fetchone()

        #if no duplicates write db entry
        if row['exact_match'] < 1 and row['different_reddit_acc'] < 1:
            query = "INSERT INTO acc_links (bnet_id, reddit_id, last_update, last_rank) VALUES (?, ?, ?, ?)"
            db.execute(query, [
                    session.get('bnet_user_id'), 
                    session.get('reddit_user_id'), 
                    datetime.datetime.now(), 
                    session.get('sr')   ])
            db.commit()
                
            # and call reddit-api to set modflair
            ok = praw_set_reddit_user_flair(session.get('reddit_user'), selected_rank.lower())
            flash("We've successfully set your user flair on /r/competitiveoverwatch to '%s'." % selected_rank)
            return redirect(url_for('show_status'))
        elif row['exact_match'] > 0 and row['different_reddit_acc'] < 1:
            statement = """
            UPDATE acc_links 
            SET last_update = ?, last_rank = ? 
            WHERE bnet_id = ?  AND reddit_id = ?"""
            db.execute(statement, [
                datetime.datetime.now(), 
                session.get('sr'), 
                session.get('bnet_user_id'), 
                session.get('reddit_user_id')   ])
            db.commit()
            ok = praw_set_user_flair(session.get('reddit_user'), selected_rank.lower())
            flash("We've successfully updated your user flair on /r/competitiveoverwatch to '%s'." % selected_rank)
            return redirect(url_for('show_status'))

        # if we're here there is already another reddit account linked with the bnet acc
        flash("You can only set the flair for <b>one</b> reddit account with a single battle.net account. Sadly, the feature to remove the flair from the old acc is not yet implemented.")
        return redirect(url_for('show_status'))

    flash("Either I made a mistake while programming (shame on me) or you're trying to trick the program... shame on you.")
    return redirect(url_for('show_status'))

def praw_set_user_flair(user, flair):
    ok = True
    try:
        # the user_agent is overridden by the praw.ini
        reddit = praw.Reddit(app.config['PRAW_SITE_NAME'], user_agent='test by /u/Witchtower_')
        subreddit = reddit.subreddit(app.config['PRAW_SUBREDDIT_NAME']) 
        subreddit.flair.set(user, css_class=flair)
    except:
        ok = False
    return ok


