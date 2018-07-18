import os
import json
import shlex
import subprocess
import pandas as pd
from datetime import datetime, timezone

from flask_login import current_user

from EpiMap import app, db
from EpiMap.db_tables import User, Job, Model
from EpiMap.datasets import miRNA2Disease

miR2D_dataset = miRNA2Disease()


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


def call_scripts(method, params=None, job_dir='', x_filename='', y_filename=''):
    print(method)
    if method == 'EBEN':
        with open(os.path.join(job_dir, 'EBEN.stdout'), 'w') as EBEN_stdout, \
                open(os.path.join(job_dir, 'EBEN.stderr'), 'w') as EBEN_stderr:
            subprocess.Popen(['Rscript', app.config['EBEN_SCRIPT'], job_dir, x_filename, y_filename],
                             stdout=EBEN_stdout,
                             stderr=EBEN_stderr)

    if method == 'LASSO':
        with open(os.path.join(job_dir, 'LASSO.stdout'), 'w') as LASSO_stdout, \
                open(os.path.join(job_dir, 'LASSO.stderr'), 'w') as LASSO_stderr:
            subprocess.Popen(
                ['Rscript', app.config['LASSO_SCRIPT'], params['alpha'], job_dir, x_filename, y_filename],
                stdout=LASSO_stdout,
                stderr=LASSO_stderr)

    if method == 'Matrix_eQTL':
        with open(os.path.join(job_dir, 'Matrix_eQTL.R.stdout'), 'w') as Matrix_eQTL_stdout, \
                open(os.path.join(job_dir, 'Matrix_eQTL.R.stderr'), 'w') as Matrix_eQTL_stderr:
            subprocess.Popen(['Rscript', app.config['MATRIX_EQTL_SCRIPT'], job_dir, x_filename, y_filename],
                             stdout=Matrix_eQTL_stdout,
                             stderr=Matrix_eQTL_stderr)


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


def load_results(filename):
    content = []
    with open(filename, 'r') as fin:
        for line in fin:
            line = line.strip().split()
            content.append(line)
    return content


def load_json(filename):
    with open(filename, 'r') as fin:
        data = json.load(fin)
    print(data['nodes'])
    for node in data['nodes']:
        # TODO: use identified key
        # node_id = node['id'].replace('.', '-')

        linked_targets = miR2D_dataset.miRNA_target[miR2D_dataset.miRNA_target['miRNA'].str.lower() == node['id']]
        target_nodes = []
        # add links
        for index, row in linked_targets.iterrows():
            '''
            data['links'].append({'target': row['Validated target'],
                                  'source': row['miRNA'],
                                  'strength': 0.7})
            '''
            data['links'].append({'target': row['Validated target'],
                                  'source': node['id'],
                                  'strength': 0.7})
            target_nodes.append(row['Validated target'])

        # add target nodes
        target_nodes = set(target_nodes)
        for node in target_nodes:
            data['nodes'].append({'id': node,
                                  'group': 1,
                                  'label': node,
                                  'level': 2})

    print(data)
    return data['nodes'], data['links']
