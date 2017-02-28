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
import requests
import requests.auth
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

# initialize application instance
app = Flask(__name__)

# load conf from this file
app.config.from_object(__name__)

# default config to load
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'compowsr.db'),
    SECRET_KEY='fnord',
    USERNAME='fnord',
    PASSWORD='fnord',
    REDDIT_CLIENT_ID='',
    REDDIT_CLIENT_SECRET='',
    REDDIT_REDIRECT_URI='http://127.0.0.1:5000/callback_reddit'
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
    bnet_logged_in = False
    bnet_user = ""
    reddit_logged_in = False
    reddit_user = ""
    if session.get('bnet_token'):
        bnet_logged_in = True
    if session.get('reddit_token'):
        reddit_user = reddit_get_username(session.get('reddit_token'))
        if reddit_user:
            reddit_logged_in = True


    return render_template('show_status.html', status={
        'bnet_logged_in': bnet_logged_in, 
        'bnet_user': bnet_user,
        'reddit_logged_in': reddit_logged_in,
        'reddit_user': reddit_user
        })


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('show_status'))

@app.route('/login_bnet')
def login_bnet():
    True

@app.route('/login_reddit')
def login_reddit():
    from uuid import uuid4
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
    import urllib
    redir_uri = 'https://ssl.reddit.com/api/v1/authorize?' + urllib.urlencode(params)
    return redirect(redir_uri)

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
    return 'yay we got a code: %s\n and a token from the code: %s' % (code, token)

def is_valid_state(state):
    # haha jokes on me, this need to be done but for testing should work with return True
    if state == session.get('reddit_oauth_state'):
        return True
    return False

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

def reddit_get_username(token):
    headers = {
        'Authorization': 'bearer ' + token
    }
    response = requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)
    me_json = json.loads(response.text)
    return me_json['name']
    #return response.content










