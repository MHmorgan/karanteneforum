
import re

from flask import Flask, render_template, url_for, request, make_response, session, redirect, escape, abort
from flask_socketio import SocketIO, send, emit

# ------------------------------------------------------------------------------
# Input validation

# ^\s*(#b?\d+b?|[Uu]\d+|b\d+) \w+
name_validator = re.compile(r'(#b?|[Uub])\d+ \w+')
valid_name = 'Gyldige strindtnavn: #XXX navn / bXXX navn / UXX navn'

kirkegard_validator = re.compile(r'(?i)havstein')
valid_kirkegard = 'Feil kirkegård...'


# ------------------------------------------------------------------------------
# Constants

NAME_COOKIE = 'strindtnavn'
