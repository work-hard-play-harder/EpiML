import os, glob
import shutil
import random
import time
from EpiML import app, db, celery
from celery.result import AsyncResult

# third-parties packages
from flask import render_template, request, redirect, url_for, flash, make_response, abort, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import desc

# customized functions
from EpiML.run_scripts import call_scripts, create_job_folder
from EpiML.generate_json import load_results, scientific_notation, GenerateJson
from EpiML.db_tables import Job, Model
from EpiML.safety_check import is_safe_url, is_allowed_file, security_code_generator
from EpiML.email import send_submit_job_email
from EpiML.generate_r_notebook import generate_EBEN_notebook, generate_ssLASSO_notebook, generate_LASSO_notebook


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/webserver', methods=['GET', 'POST'])
def webserver():
    if request.method == 'POST':
        jobname = request.form['jobname']
        email = request.form['email']
        jobcategory = request.form['jobcategory']
        if jobcategory == 'Gene':
            select_species = request.form.get('species')
            jobcategory = '{0}({1})'.format(jobcategory, select_species)
        datatype = request.form['datatype']
        description = request.form['description']
        input_x = request.files['input-x']
        input_y = request.files['input-y']
        method = request.form['method']

        params = {}
        if request.form.get('cv') == 'on':
            params['fold_number'] = request.form['fold_number']
        else:
            params['fold_number'] = str(5)
        if request.form.get('ss') == 'on':
            params['seed_number'] = request.form['seed_number']
        else:
            params['seed_number'] = str(random.randint(0, 28213))
        params['datatype'] = datatype

        print(jobname, email, jobcategory, params['datatype'], description, input_x, input_y, method,
              params['fold_number'], params['seed_number'])

        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            x_filename = secure_filename(input_x.filename)
            y_filename = secure_filename(input_y.filename)
        else:
            flash("Only .txt and .csv file types are valid!")
            return redirect(request.url)

        if x_filename == y_filename:
            flash("Training data have the same file name.")
            return redirect(request.url)

        # generate security_code
        security_code = security_code_generator()

        # add job into Job database
        job = Job(name=jobname, user_email=email, category=jobcategory, type='Train', description=description,
                  selected_algorithm=method, status='Queuing', feature_file=x_filename, label_file=y_filename,
                  security_code=security_code)
        db.session.add(job)
        db.session.commit()

        # upload training data
        job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], jobid=job.id, security_code=security_code)
        input_x.save(os.path.join(job_dir, x_filename))
        input_y.save(os.path.join(job_dir, y_filename))
        # flash("File has been upload!")

        # call scripts and update Model database
        celery_task = call_scripts.apply_async([job.id, method, params, x_filename, y_filename],
                                               countdown=5)
        job.celery_id = celery_task.id
        db.session.add(job)

        params_str = ';'.join([key + '=' + str(value) for key, value in params.items()])
        model = Model(algorithm=method, parameters=params_str, is_shared=True, job_id=job.id)
        db.session.add(model)
        db.session.commit()

        # send result link and security code via email
        if email != '':
            send_submit_job_email([email], jobname=jobname, jobid=job.id, security_code=security_code)

        return redirect(url_for('processing', jobid=job.id, security_code=security_code))

    return render_template('webserver.html')


@app.route('/processing/<jobid>_<security_code>')
def processing(jobid, security_code):
    job = Job.query.filter_by(id=jobid).first_or_404()
    print('job.status', job.status)
    print(security_code)
    if job.status == 'Done':
        jobcategory = job.category.split('(')[0]  # delete species
        if jobcategory == 'Gene':
            return redirect(url_for('result', jobid=job.id, security_code=security_code))
        if jobcategory == 'microRNA':
            return redirect(url_for('result', jobid=job.id, security_code=security_code))
        if jobcategory == 'Other':
            return redirect(url_for('result', jobid=job.id, security_code=security_code))
    elif job.status == 'Error':
        return redirect(url_for('error', jobid=job.id, security_code=security_code))
    else:
        return render_template('processing.html', host_domain=request.headers['Host'], jobid=job.id,
                               jobstatus=job.status,
                               security_code=security_code)


@app.route('/result/<jobid>_<security_code>')
def result(jobid, security_code):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(jobid) + '_' + security_code)

    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)

    job = Job.query.filter_by(id=jobid).first_or_404()

    EBEN_main_result = scientific_notation(load_results(os.path.join(job_dir, 'main_result.txt')), 1)
    EBEN_epis_result = scientific_notation(load_results(os.path.join(job_dir, 'epis_result.txt')), 2)

    # generate json files for different job categories
    json_handler = GenerateJson(job_dir, job.category)
    cn_graph_json = json_handler.generate_cn_graph_json()
    am_graph_json = json_handler.generate_am_graph_json()
    fd_graph_json = ''
    jobcategory = job.category.split('(')[0]  # delete species
    if jobcategory == 'Gene':
        fd_graph_json = json_handler.generate_gene_fd_graph_json()
    elif jobcategory == 'microRNA':
        fd_graph_json = json_handler.generate_microRNA_fd_graph_json()
    else:
        fd_graph_json = json_handler.generate_other_fd_graph_json()

    # Generate r notebook if not exist
    jupyter_notebook_size = 0
    if job.selected_algorithm == 'EBEN':
        generate_EBEN_notebook(job_dir, job.feature_file, job.label_file)
        jupyter_notebook_size = '{0:.2f}'.format(
            os.path.getsize(os.path.join(job_dir, 'EBEN_r_notebook.ipynb')) / 1024)
    if job.selected_algorithm == 'LASSO':
        generate_LASSO_notebook(job_dir, job.feature_file, job.label_file)
        jupyter_notebook_size = '{0:.2f}'.format(
            os.path.getsize(os.path.join(job_dir, 'LASSO_r_notebook.ipynb')) / 1024)
    if job.selected_algorithm == 'ssLASSO':
        generate_ssLASSO_notebook(job_dir, job.feature_file, job.label_file)
        jupyter_notebook_size = '{0:.2f}'.format(
            os.path.getsize(os.path.join(job_dir, 'ssLASSO_r_notebook.ipynb')) / 1024)

    return render_template('result.html', job=job,
                           feature_file_size='{0:.2f}'.format(
                               os.path.getsize(os.path.join(job_dir, job.feature_file)) / 1024),
                           lable_file_size='{0:.2f}'.format(
                               os.path.getsize(os.path.join(job_dir, job.label_file)) / 1024),
                           main_result_size='{0:.2f}'.format(
                               os.path.getsize(os.path.join(job_dir, 'main_result.txt')) / 1024),
                           epis_result_size='{0:.2f}'.format(
                               os.path.getsize(os.path.join(job_dir, 'epis_result.txt')) / 1024),
                           jupyter_notebook_size=jupyter_notebook_size,
                           # for result tables
                           EBEN_main_result=EBEN_main_result, EBEN_epis_result=EBEN_epis_result,
                           # for visualization
                           cn_graph_json=cn_graph_json,
                           am_graph_json=am_graph_json,
                           fd_graph_json=fd_graph_json)


@app.route('/error/<jobid>_<security_code>')
def error(jobid, security_code):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(jobid) + '_' + security_code)
    error_files = glob.glob(os.path.join(job_dir, '*.stderr'))

    error_content = []
    for stderr_file in error_files:
        with open(os.path.join(job_dir, stderr_file), 'r') as ef:
            for line in ef:
                print(line)
                error_content.append(line)
    print(error_content)
    return render_template('error.html', error_content=error_content)


@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if request.method == 'POST':
        choosed_jobs = request.form.getlist('id[]')
        print(choosed_jobs)
        for id in choosed_jobs:
            job = Job.query.filter_by(id=int(id)).first_or_404()
            print(job)
            # terminate background running task
            if job.status != 'Done':
                print('terminate background running task')
                celery.control.revoke(job.celery_id, terminate=True)

            # must delete related models first, otherwise foreigner key will be delete then can't link to related model
            models = Model.query.filter_by(job_id=id).all()
            if models:
                for model in models:
                    db.session.delete(model)

            db.session.delete(job)

            # delete job_dir
            job_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(job.id) + '_' + job.security_code)
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir)
        db.session.commit()

    jobs = Job.query.order_by(desc('timestamp')).all()

    return render_template('jobs.html', jobs=jobs)


@app.route('/models', methods=['GET', 'POST'])
def models():
    if request.method == 'POST':
        choosed_models = request.form.getlist('id[]')
        print(choosed_models)
        for id in choosed_models:
            model = Model.query.filter_by(id=int(id)).first_or_404()
            db.session.delete(model)
        db.session.commit()

    models = Model.query.order_by(desc(Model.timestamp)).all()

    jobnames = []
    for model in models:
        jobname = Job.query.filter_by(id=model.job_id).first_or_404().name
        jobnames.append(jobname)

    return render_template('models.html', models=models, jobnames=jobnames)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/help')
def help():
    return render_template('help.html')


@app.errorhandler(404)
def page_not_found(error):
    resp = make_response(render_template('page_not_found.html'), 404)
    resp.headers['X-Something'] = 'A value'
    return resp


@app.route('/show_pic/<jobid>_<security_code>/<filename>')
def show_pic(jobid, security_code, filename):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(jobid) + '_' + security_code)
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)

    try:
        return send_file(os.path.join(job_dir, filename), attachment_filename=filename)
    except Exception as e:
        return str(e)


@app.route('/download_result/<jobid>_<security_code>/<filename>')
def download_result(jobid, security_code, filename):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(jobid) + '_' + security_code)
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)
    try:
        return send_file(os.path.join(job_dir, filename), attachment_filename=filename)
    except Exception as e:
        return str(e)


@app.route('/download_sample_data/<filename>')
def download_sample_data(filename):
    try:
        return send_file(os.path.join(app.config['SAMPLE_DATA_DIR'], filename), attachment_filename=filename)
    except Exception as e:
        return str(e)


@app.route('/download_r_notebook/<jobid>_<security_code>/<method>_r_notebook.ipynb')
def download_r_notebook(jobid, security_code, method):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(jobid) + '_' + security_code)
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)

    if method == 'EBEN':
        filename = 'EBEN_r_notebook.ipynb'
        try:
            return send_file(os.path.join(job_dir, filename), add_etags=False,
                             attachment_filename=filename)
        except Exception as e:
            return str(e)
    if method == 'LASSO':
        filename = 'LASSO_r_notebook.ipynb'
        try:
            return send_file(os.path.join(job_dir, filename), attachment_filename=filename)
        except Exception as e:
            return str(e)
    if method == 'ssLASSO':
        filename = 'ssLASSO_r_notebook.ipynb'
        try:
            return send_file(os.path.join(job_dir, filename), attachment_filename=filename)
        except Exception as e:
            return str(e)
