import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'R\xb7\xff\xfc\x1a\x94\xd3\xfa\xce\x1e\x1az+J!\xdfW\xf7k\x9br\xd9?\xc5'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # developed ROOT URL
    # for local running, add a line in /etc/hosts
    # 127.0.0.1     shilab-apps-d/EpiML/
    #SERVER_NAME = os.environ.get('SERVER_NAME') or 'shilab-dev.uncc.edu:5000'
    #APPLICATION_ROOT = os.environ.get('EpiML_APP_ROOT') or '/EpiML'

    # for upload file
    UPLOAD_FOLDER = os.path.join(basedir, 'EpiML', 'upload_data')
    ALLOWED_EXTENSIONS = set(['txt', 'csv'])

    # for datasets
    SAMPLE_DATA_DIR = os.path.join(basedir, 'EpiML', 'datasets', 'sample_data')
    MIR2DISEASE_DIR = os.path.join(basedir, 'EpiML', 'datasets', 'miR2Disease')
    MIR2BASE_DIR = os.path.join(basedir, 'EpiML', 'datasets', 'miRBase')

    # scripts dir
    SCRIPTS_DIR = os.path.join(basedir, 'EpiML', 'scripts')
    # for run scripts
    EBEN_SCRIPT = os.path.join(SCRIPTS_DIR, 'EBEN.R')
    LASSO_SCRIPT = os.path.join(SCRIPTS_DIR, 'LASSO.R')
    SSLASSO_SCRIPT = os.path.join(SCRIPTS_DIR, 'ssLASSO.R')

    # for mail
    # MAIL_SERVER = 'localhost'
    # MAIL_PORT = 25
    # MAIL_USE_TLS = False
    # MAIL_USE_SSL = False
    # MAIL_USERNAME = 'sender@example.com'
    # MAIL_PASSWORD = None

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'junjie.chen.hit@gmail.com'
    MAIL_PASSWORD = 'Keepsmile_520'

    # for celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
