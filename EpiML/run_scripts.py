import os
import json
import shlex
import subprocess
import pandas as pd
from datetime import datetime, timezone
from flask import url_for

from EpiML import app, db, celery
from EpiML.db_tables import Job
from EpiML.email import send_job_done_email,send_job_error_email


def create_job_folder(upload_folder='', jobid=None, security_code=None):
    # create upload_folder
    if not os.path.exists(upload_folder):
        cmd_args = shlex.split('mkdir ' + upload_folder)
        subprocess.Popen(cmd_args).wait()

    # create job dir
    job_dir = os.path.join(upload_folder, str(jobid) + '_' + security_code)
    if not os.path.exists(job_dir):
        cmd_args = shlex.split('mkdir ' + job_dir)
        subprocess.Popen(cmd_args).wait()

    return job_dir


@celery.task()
def call_scripts(jobid, method, params=None, x_filename='', y_filename='', processing_url=''):
    print('Background start {}...'.format(method))
    job = Job.query.filter_by(id=jobid).first_or_404()
    job.status = 'Running'
    db.session.add(job)
    db.session.commit()

    job_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(job.id) + '_' + job.security_code)
    print(job_dir)
    if method == 'EBEN':
        print('run EBEN')
        try:
            with open(os.path.join(job_dir, 'EBEN.stdout'), 'w') as EBEN_stdout, \
                    open(os.path.join(job_dir, 'EBEN.stderr'), 'w') as EBEN_stderr:
                subprocess.run(['Rscript', app.config['EBEN_SCRIPT'], job_dir, x_filename, y_filename,
                                params['datatype'], params['fold_number'], params['seed_number']],
                               stdout=EBEN_stdout, stderr=EBEN_stderr)
                job.status = 'Done'
        except Exception as ex:
            print(ex)
            job.status = 'Error'

    if method == 'LASSO':
        print('run LASSO')
        try:
            with open(os.path.join(job_dir, 'LASSO.stdout'), 'w') as LASSO_stdout, \
                    open(os.path.join(job_dir, 'LASSO.stderr'), 'w') as LASSO_stderr:
                subprocess.run(['Rscript', app.config['LASSO_SCRIPT'], job_dir, x_filename, y_filename,
                                params['datatype'], params['fold_number'], params['seed_number']],
                               stdout=LASSO_stdout, stderr=LASSO_stderr)
                job.status = 'Done'
        except Exception as ex:
            print(ex)
            job.status = 'Error'

    if method == 'ssLASSO':
        print('run ssLASSO')
        try:
            with open(os.path.join(job_dir, 'ssLASSO.stdout'), 'w') as SSLASSO_stdout, \
                    open(os.path.join(job_dir, 'ssLASSO.stderr'), 'w') as SSLASSO_stderr:
                subprocess.run(['Rscript', app.config['SSLASSO_SCRIPT'], job_dir, x_filename, y_filename,
                                params['datatype'], params['fold_number'], params['seed_number']],
                               stdout=SSLASSO_stdout, stderr=SSLASSO_stderr)
                job.status = 'Done'
        except Exception as ex:
            print(ex)
            job.status = 'Error'

    # check results
    if not os.path.exists(os.path.join(job_dir, 'main_result.txt')):
        job.status = 'Error'
    if not os.path.exists(os.path.join(job_dir, 'epis_result.txt')):
        job.status = 'Error'

    job.running_time = str(datetime.now(timezone.utc).replace(tzinfo=None) - job.timestamp)[:-7]
    db.session.add(job)
    db.session.commit()

    # send result link
    if job.status == 'Done':
        send_job_done_email.apply_async(args=[job.user_email, job.name, processing_url],
                                        countdown=5)
    elif job.status == 'Error':
        send_job_error_email.apply_async(args=[job.user_email, job.name, processing_url],
                                        countdown=5)

    print('Background Done!')
