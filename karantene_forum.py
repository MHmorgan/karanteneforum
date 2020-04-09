#!/usr/bin/env python3.8

# Copyright 2020 Magnus Aa. Hirth. All rights reserved.

import karantene_forum_lib.database as database
import os.path

from karantene_forum_lib import *
# from flask import Flask, render_template, url_for, request, make_response, session, redirect, escape

app = Flask(__name__)


# ------------------------------------------------------------------------------
# 404 Handler

@app.errorhandler(404)
def page_not_fonud(error):
    navn = request.cookies.get(NAME_COOKIE)
    if navn:
        
        return render_template('base.html', **context(
            PAGE='page_not_found.html',
            USER=navn,
            LATEST=database.latest_activity(),
        ))

    else:
        return render_template('base.html', **context(PAGE='page_not_found.html'))


# ------------------------------------------------------------------------------
# Logout

@app.route('/logout', methods=['POST'])
def logout():
    navn = request.cookies.get(NAME_COOKIE)
    if navn:
        database.add_activity(f'{navn} dro hjem...', navn)
        resp = redirect(url_for('index'))
        resp.set_cookie(NAME_COOKIE, expires=0)
        return resp
    else:
        return redirect(url_for('index'))


# ------------------------------------------------------------------------------
# Latest activity

@app.route('/latest', methods=['GET'])
def latest():
    navn = request.cookies.get(NAME_COOKIE)
    if navn:
        s = database.latest_activity()
        return make_response(s)
    else:
        return redirect(url_for('index'))


# ------------------------------------------------------------------------------
# Skål!

@app.route('/cheers', methods=['GET','POST'])
def cheers():
    navn = request.cookies.get(NAME_COOKIE)
    if navn:
        database.add_activity(f'{navn} skålet!', navn)
        return ('', 204)
    else:
        return redirect(url_for('index'))


# ------------------------------------------------------------------------------
# Aktivitet

@app.route('/aktivitet', methods=['GET'])
def aktivitet():
    navn = request.cookies.get(NAME_COOKIE)
    if navn:
        aktivitet = database.all_activity()
        
        return render_template('base.html', **context(
            PAGE='aktivitet.html',
            USER=navn,
            LATEST=database.latest_activity(),
            AKTIVITET=reversed(aktivitet),
        ))

    else:
        return redirect(url_for('index'))


# ------------------------------------------------------------------------------
# Sub-pages

@app.route('/<path:page>', methods=['GET'])
def agenda(page: str):
    navn = request.cookies.get(NAME_COOKIE)
    if navn:
        file = f'{page}.html'

        # Check existence of requested page
        if not os.path.exists(f'templates/{file}'):
            abort(404)
        
        return render_template('base.html', **context(
            PAGE=file,
            USER=navn,
            LATEST=database.latest_activity(),
        ))

    else:
        return redirect(url_for('index'))


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
        krikegard = request.form['kirkegard'].strip()
        navn = request.form['strindtnavn'].strip()

        # Validate login
        if not kirkegard_validator.match(krikegard):
            return render_template('base.html', **context(PAGE='login.html', ERROR=valid_kirkegard))
        if not name_validator.match(navn):
            return render_template('base.html', **context(PAGE='login.html', ERROR=valid_name))

        # Register activity
        database.add_activity(f'{navn} ankom hybelen!', navn)

        # Set cookie with name
        resp = redirect(url_for('index'))
        resp.set_cookie(NAME_COOKIE, navn)
        return resp

    # --------------------------------------------------------------------------
    # Main page

    navn = request.cookies.get(NAME_COOKIE)
    if navn:
        resp = render_template('base.html', **context(
            PAGE='main.html',
            USER=navn,
            LATEST=database.latest_activity(),
        ))
        return resp


    # --------------------------------------------------------------------------
    # Login page

    return render_template('base.html', **context(PAGE='login.html'))


################################################################################
#                                                                              #
#  Hello World
#                                                                              #
################################################################################

@app.route('/hello')
def hello_world():
    strindtnavn = request.cookies.get(NAME_COOKIE)
    return render_template('base.html', **context(PAGE='hello.html', USER=strindtnavn))
