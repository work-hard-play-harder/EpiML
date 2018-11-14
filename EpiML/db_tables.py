import os
import shutil
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


from EpiML import app, db


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
    feature_file = db.Column(db.String(32))
    label_file = db.Column(db.String(32))
    celery_id = db.Column(db.String(64))
    security_code=db.Column(db.String(48))

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

    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))

    def __repr__(self):
        return '<Model {}>'.format((self.algorithm))
