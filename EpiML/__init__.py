from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from flask_mail import Mail
from redis import Redis
from celery import Celery

from EpiML.momentjs import momentjs

app = Flask(__name__)
app.config.from_object(Config)
app.jinja_env.globals['momentjs'] = momentjs

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
celery.conf.update(app.config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

mail = Mail(app)

# Keep this under the statement of app variable.
# because views module will import app,

from EpiML import views, run_scripts, db_tables
