import os
import shutil
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import UserMixin, current_user

from EpiML import app, db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    security_code = db.Column(db.String(6))
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    jobs = db.relationship('Job', backref='author', lazy='dynamic')
    models = db.relationship('Model', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def check_security_code(self, security_code):
        return self.security_code == security_code


@login.user_loader
def user_loader(id):
    return User.query.get(int(id))


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    category = db.Column(db.String(64))
    type = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    description = db.Column(db.String(280))
    selected_algorithm = db.Column(db.String(64))  # format like algorithm1|algorithm2|algorithm3
    status = db.Column(db.String(32))
    running_time = db.Column(db.String(32))
    feature_file=db.Column(db.String(32))
    label_file = db.Column(db.String(32))
    celery_id = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    models = db.relationship('Model', backref='job', lazy='dynamic')

    def __repr__(self):
        return '<Job {}>'.format(self.name)


class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    algorithm = db.Column(db.String(64))
    parameters = db.Column(db.String(64))
    performance = db.Column(db.String(64))
    description = db.Column(db.String(280))
    status = db.Column(db.String(32))
    recall_times = db.Column(db.Integer, default=0)
    training_time = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    is_shared = db.Column(db.Boolean, default=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))

    def __repr__(self):
        return '<Model {}>'.format((self.algorithm))
