import os
import json
import shlex
import subprocess
import pandas as pd
from datetime import datetime, timezone

from flask_login import current_user

from EpiML import app, db, celery

from EpiML.db_tables import User, Job, Model


def create_job_folder(upload_folder='', userid=None, jobid=None):
    # create upload_folder
    if not os.path.exists(upload_folder):
        cmd_args = shlex.split('mkdir ' + upload_folder)
        subprocess.Popen(cmd_args).wait()

    # create user dir
    user_dir = os.path.join(upload_folder, '_'.join(['userid', str(userid)]))
    if not os.path.exists(user_dir):
        cmd_args = shlex.split('mkdir ' + user_dir)
        subprocess.Popen(cmd_args).wait()

    # create job dir
    job_dir = os.path.join(user_dir, '_'.join(['jobid', str(jobid)]))
    if not os.path.exists(job_dir):
        cmd_args = shlex.split('mkdir ' + job_dir)
        subprocess.Popen(cmd_args).wait()

    return job_dir


@celery.task()
def call_train_scripts(jobid, category, method, params=None, job_dir='', x_filename='', y_filename=''):
    print('Background start...')
    job = Job.query.filter_by(id=jobid).first_or_404()
    job.status = 'Running'
    db.session.add(job)
    db.session.commit()
    if category == 'General':
        if method == 'EBEN':
            print('run EBEN')
            with open(os.path.join(job_dir, 'EBEN_train.stdout'), 'w') as EBEN_stdout, \
                    open(os.path.join(job_dir, 'EBEN_train.stderr'), 'w') as EBEN_stderr:
                subprocess.run(['Rscript', app.config['EBEN_TRAIN_SCRIPT'], job_dir, x_filename, y_filename,
                                params['fold_number'], params['seed_number']],
                               stdout=EBEN_stdout,
                               stderr=EBEN_stderr)

        if method == 'SSLASSO':
            print('run SSLASSO')
            with open(os.path.join(job_dir, 'SSLASSO_train.stdout'), 'w') as SSLASSO_stdout, \
                    open(os.path.join(job_dir, 'SSLASSO_train.stderr'), 'w') as SSLASSO_stderr:
                subprocess.run(['Rscript', app.config['SSLASSO_SCRIPT'], job_dir, x_filename, y_filename,
                                params['fold_number'], params['seed_number']],
                               stdout=SSLASSO_stdout,
                               stderr=SSLASSO_stderr)
    else:
        if method == 'EBEN':
            with open(os.path.join(job_dir, 'EBEN_train.stdout'), 'w') as EBEN_stdout, \
                    open(os.path.join(job_dir, 'EBEN_train.stderr'), 'w') as EBEN_stderr:
                subprocess.Popen(['Rscript', app.config['EBEN_TRAIN_SCRIPT'], job_dir, x_filename, y_filename,
                                  params['fold_number'], params['seed_number']],
                                 stdout=EBEN_stdout,
                                 stderr=EBEN_stderr)

        if method == 'LASSO':
            with open(os.path.join(job_dir, 'LASSO_train.stdout'), 'w') as LASSO_stdout, \
                    open(os.path.join(job_dir, 'LASSO_train.stderr'), 'w') as LASSO_stderr:
                subprocess.Popen(
                    ['Rscript', app.config['LASSO_TRAIN_SCRIPT'], params['alpha'], job_dir, x_filename, y_filename],
                    stdout=LASSO_stdout,
                    stderr=LASSO_stderr)

        if method == 'Matrix_eQTL':
            with open(os.path.join(job_dir, 'Matrix_eQTL_train.stdout'), 'w') as Matrix_eQTL_stdout, \
                    open(os.path.join(job_dir, 'Matrix_eQTL_train.stderr'), 'w') as Matrix_eQTL_stderr:
                subprocess.Popen(['Rscript', app.config['MATRIX_EQTL_TRAIN_SCRIPT'], job_dir, x_filename, y_filename],
                                 stdout=Matrix_eQTL_stdout,
                                 stderr=Matrix_eQTL_stderr)

    job.status = 'Done'
    job.running_time = str(datetime.now(timezone.utc).replace(tzinfo=None) - job.timestamp)[:-7]
    db.session.add(job)
    db.session.commit()
    print('Background Done!')


def call_predict_scripts(job_dir='', model_dir='', method=None, x_filename=''):
    print(job_dir, model_dir, method)
    if method == 'EBEN':
        print('run EBEN predict')
        with open(os.path.join(job_dir, 'EBEN_predict.stdout'), 'w') as EBEN_stdout, \
                open(os.path.join(job_dir, 'EBEN_predict.stderr'), 'w') as EBEN_stderr:
            subprocess.Popen(['Rscript', app.config['EBEN_PREDICT_SCRIPT'], job_dir, model_dir, x_filename],
                             stdout=EBEN_stdout,
                             stderr=EBEN_stderr)

    if method == 'LASSO':
        with open(os.path.join(job_dir, 'LASSO_predict.stdout'), 'w') as LASSO_stdout, \
                open(os.path.join(job_dir, 'LASSO_predict.stderr'), 'w') as LASSO_stderr:
            subprocess.Popen(
                ['Rscript', app.config['LASSO_PREDICT_SCRIPT'], job_dir, model_dir, x_filename],
                stdout=LASSO_stdout,
                stderr=LASSO_stderr)

    if method == 'Matrix_eQTL':
        with open(os.path.join(job_dir, 'Matrix_eQTL_predict.stdout'), 'w') as Matrix_eQTL_stdout, \
                open(os.path.join(job_dir, 'Matrix_eQTL_predict.stderr'), 'w') as Matrix_eQTL_stderr:
            subprocess.Popen(['Rscript', app.config['MATRIX_EQTL_PREDICT_SCRIPT'], job_dir, model_dir, x_filename],
                             stdout=Matrix_eQTL_stdout,
                             stderr=Matrix_eQTL_stderr)


'''
def check_job_status(jobid, methods):
    # Every method should output a finished sign when it finished.
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                           '_'.join(['userid', str(current_user.id)]),
                           '_'.join(['jobid', str(jobid)]))
    job = Job.query.filter_by(id=jobid).first_or_404()

    # updating job status as running
    if job.status == 0:
        job.status = 1
        db.session.add(job)
        db.session.commit()

    flag = 0  # number of finished methods
    filelist = os.listdir(job_dir)
    for filename in filelist:
        if filename.endswith('.stdout') and os.stat(os.path.join(job_dir, filename)).st_size != 0:
            with open(os.path.join(job_dir, filename), 'r') as fin:
                # find finished flag in last line
                last_line = fin.readlines()[-1]
                if 'Done!' in last_line:
                    flag += 1

    # updating job status as done
    methods = methods.split(';')
    print(methods)
    print(flag)
    if flag == len(methods):
        print('job.status', job.status)
        job.status = 2
        # this result is not exactly running time
        job.running_time = str(datetime.now(timezone.utc).replace(tzinfo=None) - job.timestamp)[:-7]
        db.session.add(job)
        db.session.commit()
'''
