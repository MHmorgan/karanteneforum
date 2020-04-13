#!/usr/bin/env python3.8

# Copyright 2020 Magnus Aa. Hirth. All rights reserved.

import karantene_forum_lib.database as database
import os.path
import sys

from datetime import datetime
from karantene_forum_lib import *
from typing import Any

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aoesn.>R7U67Ueu#![('
socketio = SocketIO(app)

def render(page, ctx):
    ctx['PAGE'] = page
    return render_template('base.html', **ctx)


def runner(func, **kwargs) -> Any:
    '''
    Wrapper function for consistent template context, and 
    protecting against not logged in.
    '''
    if (navn := request.cookies.get(NAME_COOKIE)):
        activity, status, messages = database.all()
        _, kvissmaster_perm, status_perm, tilganger_perm, bdfl_perm = database.get_permissions(navn)
        ctx = {
            'APP_NAME' : 'Karanteneforum',
            'ERROR' : None,
            'USER' : navn,
            'PATH' : request.path,
            'ACTIVITY' : activity[1] if activity else 'Ingen aktivitet...',
            'STATUS' : status[2] if status else 'Ingen status...',
            'STATUS_TIME' : status[0] if status else '-',
            'STATUS_USER' : status[1] if status else '-',
            'MESSAGES' : messages,
            'KVISSMASTER_RETTIGHET' : kvissmaster_perm,
            'STATUS_RETTIGHET' : status_perm,
            'TILGANGER_RETTIGHET' : tilganger_perm,
            'BDFL_RETTIGHET' : bdfl_perm,
        }
        ctx.update(kwargs)
        return func(ctx)
    else:
        return redirect(url_for('index'))


# ------------------------------------------------------------------------------
# Error handlers

# 404 Page not found
@app.errorhandler(404)
def page_not_fonud(error):
    def func(ctx):
        ctx['ERROR'] = 'Har aldri hørt om denne hybelen før...'
        return render('feilside.html', ctx)
    return runner(func)

# 403 Forbidden
@app.errorhandler(403)
def page_not_fonud(error):
    def func(ctx):
        ctx['ERROR'] = 'Denne hybelen er stengt...'
        return render('feilside.html', ctx)
    return runner(func)


# ------------------------------------------------------------------------------
# Logout

@app.route('/logout', methods=['POST'])
def logout():

    def func(ctx):
        text = f'{ctx["USER"]} dro hjem...'
        database.add_activity(text, ctx["USER"])
        # socketio.emit('news', text)
        resp = redirect(url_for('index'))
        resp.set_cookie(NAME_COOKIE, expires=0)
        return resp

    return runner(func)


# ------------------------------------------------------------------------------
# Skål!

@socketio.on('cheers')
def cheers_socket(json, methods=['GET', 'POST']):
    if (navn := request.cookies.get(NAME_COOKIE)):

        # Limit rappid cheering
        last_cheer = 'last-cheer-time'
        if last_cheer in session:
            if (datetime.now() - session[last_cheer]).seconds < 60:
                emit('cheers-quarantine', '')
                return
        session[last_cheer] = datetime.now()

        text = f'{navn} skålet!'
        database.add_activity(text, navn)
        socketio.emit('cheers', navn)


# ------------------------------------------------------------------------------
# Aktivitet

@app.route('/aktivitet', methods=['GET'])
def aktivitet():

    def func(ctx):
        ctx['ALL_ACTIVITY'] = database.all_activity()
        return render('aktivitet.html', ctx)

    return runner(func)


# ------------------------------------------------------------------------------
# Permissions

@app.route('/tilganger', methods=['GET'])
def get_permissions():

    def func(ctx):
        if not database.check_permissions(ctx['USER'], tilganger=True):
            abort(403)
        ctx['ALL_PERMISSIONS'] = database.all_permissions()
        return render('tilganger.html', ctx)

    return runner(func)

@app.route('/tilganger', methods=['POST'])
def set_permissions():

    def func(ctx):
        if not database.check_permissions(ctx['USER'], tilganger=True):
            abort(403)
        json = request.get_json()
        user = json['user'].lower()
        kvissmaster = json['kvissmaster']
        status = json['status']
        tilganger = json['tilganger']
        database.set_permissions(
            user=user,
            kvissmaster=kvissmaster,
            status=status,
            tilganger=tilganger,
        )
        return ('', 204)

    return runner(func)


# ------------------------------------------------------------------------------
# Sub-pages

@app.route('/<path:page>', methods=['GET'])
def sub_pages(page: str):

    def func(ctx):
        file = f'{page}.html'
        # Check existence of requested page
        if not os.path.exists(f'templates/{file}'):
            abort(404)
        return render(file, ctx)

    return runner(func)


# ------------------------------------------------------------------------------
# Chatting

@app.route('/message', methods=['POST'])
def post_message():

    def func(ctx):
        json = request.get_json()
        database.new_message(json['msg'], ctx['USER'])
        latest = database.latest_messages()[0]
        socketio.emit('new_message', (latest[0], latest[1], latest[2]))
        return ('', 204)

    return runner(func)


# ------------------------------------------------------------------------------
# Status

@app.route('/status', methods=['GET'])
def get_status():

    def func(ctx):
        # Check existence of requested page
        if not database.check_permissions(user=ctx['USER'], status=True):
            abort(403)
        return render('status.html', ctx)

    return runner(func)

@app.route('/status', methods=['POST', 'UPDATE', 'DELETE'])
def handle_status():

    def func(ctx):
        if not database.check_permissions(ctx['USER'], status=True):
            abort(403)
        json = request.get_json()

        if request.method == 'POST':
            database.new_status(json['txt'], ctx['USER'])
        elif request.method == 'UPDATE':
            database.edit_latest_status(json['txt'])
        elif request.method == 'DELETE':
            database.delete_latest_status()

        status = database.latest_status()
        if status:
            status = status[0]
            socketio.emit('new_message', status[2])
        return ('', 204)

    return runner(func)


# ------------------------------------------------------------------------------
# Kviss

@app.route('/kviss', methods=['GET'])
def get_kviss():
    def func(ctx):
        ctx['ALL_LIVE_QUIZ'] = database.all_live_quiz()
        return render('kviss.html', ctx)
    return runner(func)

@app.route('/livekviss/<int:id>', methods=['GET'])
def get_livekviss(id: int):
    def func(ctx):
        return ('', 204)
    return runner(func)


################################################################################
#                                                                              #
#  Main page
#                                                                              #
################################################################################

@app.route('/', methods=['GET','POST'])
def index():

    # --------------------------------------------------------------------------
    # Login submit

    if request.method == 'POST':
        krikegard: str = request.form['kirkegard'].strip()
        navn: str = request.form['strindtnavn'].strip().lower()

        # Validate login
        if not kirkegard_validator.match(krikegard):
            return render_template('base.html', PAGE='login.html', ERROR=valid_kirkegard)
        if not name_validator.match(navn):
            return render_template('base.html', PAGE='login.html', ERROR=valid_name)

        # Register activity
        text = f'{navn} ankom hybelen!'
        database.add_activity(text, navn)
        # socketio.emit('news', text)

        # Set cookie with name
        resp = redirect(url_for('index'))
        resp.set_cookie(NAME_COOKIE, navn)
        return resp


    # --------------------------------------------------------------------------
    # Login page

    if not request.cookies.get(NAME_COOKIE):
        return render_template('base.html', PAGE='login.html')

    # --------------------------------------------------------------------------
    # Main page

    def func(ctx):
        session[NAME_COOKIE] = ctx['USER']
        return render('main.html', ctx)

    return runner(func)


################################################################################
#                                                                              #
#  Main
#                                                                              #
################################################################################

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == 'DEBUG':
        socketio.run(app, debug=True)
    elif len(sys.argv) == 1:
        socketio.run(app, host='0.0.0.0', port=4202)
    else:
        raise Exception(f'Invalid use.\nUsage: {sys.argv[0]} [DEBUG]')