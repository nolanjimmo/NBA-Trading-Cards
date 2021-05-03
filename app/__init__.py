import os

from flask import Flask
from flask_login import LoginManager

basedir = os.path.abspath(os.path.dirname(__file__))

db_filename = os.path.join(basedir, "trading_card_data.db")
schema_filename = os.path.join(basedir, "trading_card_schema.sql")

app = Flask(__name__)
app.secret_key = "final_project"
login = LoginManager(app)
login.login_view = 'login'

from app import query_engine, routes
