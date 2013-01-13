from flask import Blueprint, render_template

blueprint = Blueprint('electrostatic', __name__, template_folder='templates', static_folder='static')
from instruments import app

blueprint.config = app.config['ELECTROSTATIC']


import electrostatic.core

LABEL = 'Electrostatic'
ICON = 'pencil'

def get_admin_panel():
    return render_template('electrostatic_admin_panel.html')