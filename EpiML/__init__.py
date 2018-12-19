from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from redis import Redis
from celery import Celery

from EpiML.momentjs import momentjs
from EpiML.prefixMiddleware import PrefixMiddleware


app = Flask(__name__)
app.config.from_object(Config)

# for csrf protection
CSRFProtect(app)

# for url prefix string
#app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=app.config['APPLICATION_ROOT'])

# for time format in html
app.jinja_env.globals['momentjs'] = momentjs

# for background job
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
celery.conf.update(app.config)

# for database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

mail = Mail(app)

# Keep this under the statement of app variable.
# because views module will import app,
from EpiML import views, run_scripts, db_tables
