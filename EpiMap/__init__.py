from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

from EpiMap.momentjs import momentjs

app = Flask(__name__)
app.config.from_object(Config)
app.jinja_env.globals['momentjs']=momentjs

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
mail=Mail(app)

# Keep this under the statement of app variable.
# because views module will import app,
from EpiMap import views, db_tables
