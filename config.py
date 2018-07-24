import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'R\xb7\xff\xfc\x1a\x94\xd3\xfa\xce\x1e\x1az+J!\xdfW\xf7k\x9br\xd9?\xc5'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # for upload file
    UPLOAD_FOLDER = os.path.join(basedir, 'EpiMap', 'upload_data')
    ALLOWED_EXTENSIONS = set(['txt', 'csv'])

    # for sample data
    SAMPLE_DATA_DIR = os.path.join(basedir, 'EpiMap', 'datasets', 'sample_data')

    # for run scripts
    EBEN_TRAIN_SCRIPT = os.path.join(basedir, 'EpiMap', 'scripts', 'EBEN_train.R')
    EBEN_PREDICT_SCRIPT = os.path.join(basedir, 'EpiMap', 'scripts', 'EBEN_predict.R')
    LASSO_TRAIN_SCRIPT = os.path.join(basedir, 'EpiMap', 'scripts', 'lasso_train.R')
    MATRIX_EQTL_TRAIN_SCRIPT = os.path.join(basedir, 'EpiMap', 'scripts', 'Matrix_eQTL_train.R')

    # for mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'junjie.chen.hit@gmail.com'
    MAIL_PASSWORD = 'Keepsmile_520'
