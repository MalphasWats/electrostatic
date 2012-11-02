from flask import Blueprint

blueprint = Blueprint('electrostatic', __name__, template_folder='templates', static_folder='static')
from instruments import app

blueprint.config = app.config['ELECTROSTATIC']


import electrostatic.core

LABEL = 'Electrostatic'
ICON = 'pencil'