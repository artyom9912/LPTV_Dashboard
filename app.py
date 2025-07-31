from dash import Dash, html
from flask import Flask
import flask_login
import dash_bootstrap_components as dbc
import json
from flask_caching import Cache
from sqlalchemy import create_engine

f = open('config.json')
config = json.load(f)
engine = create_engine(f'mysql+pymysql://{config["username"]}:{config["psswd"]}@{config["ip"]}/{config["db"]}')

app = Flask(__name__)
app.secret_key = b'_5f#cky2L"F4Q8z]/'

appDash = Dash(__name__,
                     server=app,
                     url_base_pathname='/dash/',
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True,)

cache = Cache(appDash.server, config={
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': 'cache',
    'CACHE_DEFAULT_TIMEOUT': 600
})

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

