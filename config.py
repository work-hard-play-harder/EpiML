import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'R\xb7\xff\xfc\x1a\x94\xd3\xfa\xce\x1e\x1az+J!\xdfW\xf7k\x9br\xd9?\xc5'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # for upload file
    UPLOAD_FOLDER = os.path.join(basedir, 'EpiMLML', 'upload_data')
    ALLOWED_EXTENSIONS = set(['txt', 'csv'])

    # for datasets
    SAMPLE_DATA_DIR = os.path.join(basedir, 'EpiMLL', 'datasets', 'sample_data')
    MIR2DISEASE_DIR = os.path.join(basedir, 'EpiMLL', 'datasets', 'miR2Disease')
    MIR2BASE_DIR = os.path.join(basedir, 'EpiMLL', 'datasets', 'miRBase')

    # for run scripts
    GENERAL_EBEN_TRAIN_SCRIPT = os.path.join(basedir, 'EpiMLL', 'scripts', 'general_EBEN_train.R')

    EBEN_TRAIN_SCRIPT = os.path.join(basedir, 'EpiMLL', 'scripts', 'EBEN_train.R')
    EBEN_PREDICT_SCRIPT = os.path.join(basedir, 'EpiMLL', 'scripts', 'EBEN_predict.R')
    SSLASSO_SCRIPT = os.path.join(basedir, 'EpiMLL', 'scripts', 'ssLASSO.R')
    MATRIX_EQTL_TRAIN_SCRIPT = os.path.join(basedir, 'EpiMLL', 'scripts', 'Matrix_eQTL_train.R')

    # for mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'junjie.chen.hit@gmail.com'
    MAIL_PASSWORD = 'Keepsmile_520'

    # for celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
