import os
import shutil
import random
import time
from EpiMap import app, db

# third-parties packages
from flask import render_template, request, redirect, url_for, flash, make_response, abort, send_file
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from sqlalchemy import desc
from bokeh.embed import components
from bokeh.resources import INLINE

# customized functions
from EpiMap.run_scripts import call_train_scripts, call_predict_scripts, create_job_folder, check_job_status
from EpiMap.generate_json import load_results, load_json, EBEN_json
from EpiMap.create_figures import create_pca_figure, create_lasso_figure
from EpiMap.db_tables import User, Job, Model
from EpiMap.safety_check import is_safe_url, is_allowed_file, security_code_generator
from EpiMap.email import send_email


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/webserver', methods=['GET', 'POST'])
def webserver():
    if request.method == 'POST':
        jobname = request.form['jobname']
        description = request.form['description']
        email = request.form['email']
        methods = request.form.getlist('methods')

        input_x = request.files['input-x']
        input_y = request.files['input-y']
        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            x_filename = secure_filename(input_x.filename)
            y_filename = secure_filename(input_y.filename)

            if x_filename == y_filename:
                flash("Training data have the same file name.")
                return redirect(request.url)

            if len(methods) == 0:
                flash("You must choose at least one method!")
                return redirect(request.url)

            # return security_code when user exists, otherwise add user into User database
            # then login
            user = User.query.filter_by(email=email).first()
            if user is not None:
                security_code = user.security_code
            else:
                security_code = security_code_generator()
                user = User(username='anonymous', email=email, security_code=security_code)
                # user.set_password(request.form['password'])
                db.session.add(user)
                db.session.commit()
            login_user(user)

            # add job into Job database
            job = Job(jobname=jobname, description=description, selected_algorithm=';'.join(methods), status=0,
                      user_id=current_user.id)
            db.session.add(job)
            db.session.commit()

            # upload training data
            job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)
            input_x.save(os.path.join(job_dir, x_filename))
            input_y.save(os.path.join(job_dir, y_filename))
            # flash("File has been upload!")

            # call scripts and update Model database
            print(methods)
            for method in methods:
                params = {'alpha': '1'}
                call_train_scripts(method, params, job_dir, x_filename, y_filename)
                params_str = ';'.join([key + '=' + value for key, value in params.items()])
                model = Model(algorithm=method, parameters=params_str, is_shared=True, user_id=current_user.id,
                              job_id=job.id)
                db.session.add(model)
            db.session.commit()

            # send result link and security code via email
            result_link = str(url_for('processing', jobid=job.id))
            send_email(recipients=[email],
                       result_link=result_link, security_code=security_code)

            return redirect(url_for('processing', jobid=job.id))
        else:
            flash("Only .txt and .csv file types are valid!")
    return render_template('webserver.html')


@app.route('/webserver/lasso/train', methods=['GET', 'POST'])
def webserver_lasso_train():
    if request.method == 'POST':
        jobname = request.form['jobname']
        email = request.form['email']
        description = request.form['description']
        input_x = request.files['input-x']
        input_y = request.files['input-y']
        methods = request.form.getlist('methods')
        params = {'lasso_alpha': request.form['lasso_alpha'],
                  'sslasso_s1': request.form['sslasso_s1'],
                  'sslasso_s2': request.form['sslasso_s2'],
                  'grouplasso_alpha': request.form['grouplasso_alpha'],
                  'fold_number': request.form['fold_number'],
                  'seed_number': request.form['seed_number']
                  }

        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            x_filename = secure_filename(input_x.filename)
            y_filename = secure_filename(input_y.filename)
        else:
            flash("Only .txt and .csv file types are valid!")
            return redirect(request.url)

        if x_filename == y_filename:
            flash("Training data have the same file name.")
            return redirect(request.url)

        if len(methods) == 0:
            flash("You must choose at least one method!")
            return redirect(request.url)

        # return security_code when user exists, otherwise add user into User database
        # then login
        user = User.query.filter_by(email=email).first()
        if user is not None:
            security_code = user.security_code
        else:
            security_code = security_code_generator()
            user = User(username='anonymous', email=email, security_code=security_code)
            # user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
        login_user(user)

        # add job into Job database
        job = Job(name=jobname, category='lasso-based method', type='train', description=description,
                  selected_algorithm=';'.join(methods), status=0, user_id=current_user.id)
        db.session.add(job)
        db.session.commit()

        # upload training data
        job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)
        input_x.save(os.path.join(job_dir, x_filename))
        input_y.save(os.path.join(job_dir, y_filename))
        # flash("File has been upload!")

        # call scripts and update Model database
        print(methods)
        for method in methods:
            call_train_scripts(method, params, job_dir, x_filename, y_filename)
            params_str = ';'.join([key + '=' + value for key, value in params.items()])
            model = Model(algorithm=method, parameters=params_str, user_id=current_user.id,
                          job_id=job.id)
            db.session.add(model)
        db.session.commit()

        # send result link and security code via email
        result_link = str(url_for('processing', jobid=job.id))
        send_email(recipients=[email],
                   result_link=result_link, security_code=security_code)

        return redirect(url_for('processing', jobid=job.id))

    return render_template('webserver_lasso_train.html')


@app.route('/webserver/lasso/predict', methods=['GET', 'POST'])
def webserver_lasso_predict():
    if request.method == 'POST':
        jobname = request.form['jobname']
        description = request.form['description']
        email = request.form['email']
        methods = request.form.getlist('methods')

        input_x = request.files['input-x']
        input_y = request.files['input-y']
        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            x_filename = secure_filename(input_x.filename)
            y_filename = secure_filename(input_y.filename)

            if x_filename == y_filename:
                flash("Training data have the same file name.")
                return redirect(request.url)

            if len(methods) == 0:
                flash("You must choose at least one method!")
                return redirect(request.url)

            # return security_code when user exists, otherwise add user into User database
            # then login
            user = User.query.filter_by(email=email).first()
            if user is not None:
                security_code = user.security_code
            else:
                security_code = security_code_generator()
                user = User(username='anonymous', email=email, security_code=security_code)
                # user.set_password(request.form['password'])
                db.session.add(user)
                db.session.commit()
            login_user(user)

            # add job into Job database
            job = Job(jobname=jobname, description=description, selected_algorithm=';'.join(methods), status=0,
                      user_id=current_user.id)
            db.session.add(job)
            db.session.commit()

            # upload training data
            job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)
            input_x.save(os.path.join(job_dir, x_filename))
            input_y.save(os.path.join(job_dir, y_filename))
            # flash("File has been upload!")

            # call scripts and update Model database
            print(methods)
            for method in methods:
                params = {'alpha': '1'}
                call_train_scripts(method, params, job_dir, x_filename, y_filename)
                params_str = ';'.join([key + '=' + value for key, value in params.items()])
                model = Model(algorithm=method, parameters=params_str, is_shared=True, user_id=current_user.id,
                              job_id=job.id)
                db.session.add(model)
            db.session.commit()

            # send result link and security code via email
            result_link = str(url_for('processing', jobid=job.id))
            send_email(recipients=[email],
                       result_link=result_link, security_code=security_code)

            return redirect(url_for('processing', jobid=job.id))
        else:
            flash("Only .txt and .csv file types are valid!")
    return render_template('webserver_lasso_test.html')


@app.route('/webserver/epistatic_analysis/train', methods=['GET', 'POST'])
def webserver_epistatic_analysis_train():
    if request.method == 'POST':
        jobname = request.form['jobname']
        email = request.form['email']
        description = request.form['description']
        input_x = request.files['input-x']
        input_y = request.files['input-y']
        methods = request.form.getlist('methods')

        params = {}
        if request.form.get('cv') == 'on':
            params['fold_number'] = request.form['fold_number']
        else:
            params['fold_number'] = 5
        if request.form.get('ss') == 'on':
            params['seed_number'] = request.form['seed_number']
        else:
            params['seed_number'] = random.randint(0, 28213)

        print(jobname, description, email, methods, input_x, input_y, params['fold_number'], params['seed_number'])

        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            x_filename = secure_filename(input_x.filename)
            y_filename = secure_filename(input_y.filename)
        else:
            flash("Only .txt and .csv file types are valid!")
            return redirect(request.url)

        if x_filename == y_filename:
            flash("Training data have the same file name.")
            return redirect(request.url)

        if len(methods) == 0:
            flash("You must choose at least one method!")
            return redirect(request.url)

        # return security_code when user exists, otherwise add user into User database
        # then login
        user = User.query.filter_by(email=email).first()
        if user is not None:
            security_code = user.security_code
        else:
            security_code = security_code_generator()
            user = User(username='anonymous', email=email, security_code=security_code)
            # user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
        login_user(user)

        # add job into Job database
        job = Job(name=jobname, category='General', type='Train', description=description,
                  selected_algorithm=';'.join(methods), status=0,
                  user_id=current_user.id)
        db.session.add(job)
        db.session.commit()

        # upload training data
        job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)
        input_x.save(os.path.join(job_dir, x_filename))
        input_y.save(os.path.join(job_dir, y_filename))
        # flash("File has been upload!")

        # call scripts and update Model database
        print(methods)
        for method in methods:
            call_train_scripts('General', method, params, job_dir, x_filename, y_filename)
            params_str = ';'.join([key + '=' + value for key, value in params.items()])
            model = Model(algorithm=method, parameters=params_str, is_shared=True, user_id=current_user.id,
                          job_id=job.id)
            db.session.add(model)
        db.session.commit()

        # send result link and security code via email
        result_link = str(url_for('processing', jobid=job.id))
        send_email(recipients=[email],
                   result_link=result_link, security_code=security_code)

        return redirect(url_for('processing', jobid=job.id))

    return render_template('webserver_epis_analysis_train.html')


@app.route('/webserver/epistatic_analysis/predict', methods=['GET', 'POST'])
@login_required
def webserver_epistatic_analysis_predict():
    if request.method == 'POST':
        jobname = request.form['jobname']
        description = request.form['description']
        input_x = request.files['input-x']
        models_id = request.form.getlist('id[]')
        print(jobname, description, input_x, models_id)

        if input_x and is_allowed_file(input_x.filename):
            x_filename = secure_filename(input_x.filename)
        else:
            flash("Only .txt and .csv file types are valid!")
            return redirect(request.url)

        if len(models_id) == 0:
            flash("You must choose at least one model!")
            return redirect(request.url)

        models = []
        for id in models_id:
            model = Model.query.filter_by(id=id, user_id=current_user.id).first_or_404()
            models.append(model)
        print(models)

        # add job into Job database

        job = Job(name=jobname, category='General', type='Predict', description=description,
                  selected_algorithm=';'.join([model.algorithm for model in models]), status=0, user_id=current_user.id)
        db.session.add(job)
        db.session.commit()

        # upload training data
        job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)
        input_x.save(os.path.join(job_dir, x_filename))

        # call scripts and update Model database
        for model in models:
            train_job_id = model.job_id
            model_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                                     '_'.join(['userid', str(current_user.id)]),
                                     '_'.join(['jobid', str(train_job_id)]))
            if not os.path.exists(model_dir):
                flash(model.algorithm + " model doesn't exist!", category='error')
                return redirect(request.url)

            call_predict_scripts(job_dir, model_dir, model.algorithm, x_filename)

        # send result link and security code via email
        result_link = str(url_for('processing', jobid=job.id))
        send_email(recipients=[current_user.email],
                   result_link=result_link, security_code=current_user.security_code)

        return redirect(url_for('processing', jobid=job.id))

    # for GET method return
    users_models = Model.query.filter_by(user_id=current_user.id).order_by(desc(Model.timestamp)).all()
    # print(models)
    jobnames = []
    valid_models = []
    for model in users_models:
        job = Job.query.filter_by(id=model.job_id).first_or_404()
        if job.category != 'General':
            continue
        jobname = Job.query.filter_by(id=model.job_id).first_or_404().name
        jobnames.append(jobname)
        valid_models.append(model)

    return render_template('webserver_epis_analysis_predict.html', models=valid_models, jobnames=jobnames)


@app.route('/webserver/epistasis_miRNA/training', methods=['GET', 'POST'])
def webserver_epistasis_miRNA_train():
    if request.method == 'POST':
        jobcategory = request.form['jobcategory']
        jobname = request.form['jobname']
        email = request.form['email']
        description = request.form['description']
        input_x = request.files['input-x']
        input_y = request.files['input-y']
        methods = request.form.getlist('methods')

        params = {}
        if request.form.get('cv') == 'on':
            params['fold_number'] = request.form['fold_number']
        else:
            params['fold_number'] = 5
        if request.form.get('ss') == 'on':
            params['seed_number'] = request.form['seed_number']
        else:
            params['seed_number'] = random.randint(0, 28213)

        print(jobname, description, email, methods, input_x, input_y, params['fold_number'], params['seed_number'])

        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            x_filename = secure_filename(input_x.filename)
            y_filename = secure_filename(input_y.filename)
        else:
            flash("Only .txt and .csv file types are valid!")
            return redirect(request.url)

        if x_filename == y_filename:
            flash("Training and label data must have the different file names.")
            return redirect(request.url)

        if len(methods) == 0:
            flash("You must choose at least one method!")
            return redirect(request.url)

        # return security_code when user exists, otherwise add user into User database
        # then login
        user = User.query.filter_by(email=email).first()
        if user is not None:
            security_code = user.security_code
        else:
            security_code = security_code_generator()
            user = User(username='anonymous', email=email, security_code=security_code)
            # user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
        login_user(user)

        # add job into Job database
        job = Job(name=jobname, category=jobcategory, type='Train', description=description,
                  selected_algorithm=';'.join(methods), status=0, user_id=current_user.id)
        db.session.add(job)
        db.session.commit()

        # upload training data
        job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)
        input_x.save(os.path.join(job_dir, x_filename))
        input_y.save(os.path.join(job_dir, y_filename))
        # flash("File has been upload!")

        # call scripts and update Model database
        print(methods)
        for method in methods:
            call_train_scripts(jobcategory, method, params, job_dir, x_filename, y_filename)
            params_str = ';'.join([key + '=' + value for key, value in params.items()])
            model = Model(algorithm=method, parameters=params_str, is_shared=True, user_id=current_user.id,
                          job_id=job.id)
            db.session.add(model)
        db.session.commit()

        # send result link and security code via email
        result_link = str(url_for('processing', jobid=job.id))
        send_email(recipients=[email], result_link=result_link, security_code=security_code)

        return redirect(url_for('processing', jobid=job.id))

    return render_template('webserver_epistasis_miRNA_train.html')


@app.route('/webserver/epistasis_miRNA/predict', methods=['GET', 'POST'])
@login_required
def webserver_epistasis_miRNA_predict():
    if request.method == 'POST':
        jobname = request.form['jobname']
        # email = request.form['email']
        description = request.form['description']
        input_x = request.files['input-x']
        models_id = request.form.getlist('id[]')
        print(jobname, description, input_x, models_id)

        if input_x and is_allowed_file(input_x.filename):
            x_filename = secure_filename(input_x.filename)
        else:
            flash("Only .txt and .csv file types are valid!")
            return redirect(request.url)

        if len(models_id) == 0:
            flash("You must choose at least one model!")
            return redirect(request.url)

        models = []
        for id in models_id:
            model = Model.query.filter_by(id=id, user_id=current_user.id).first_or_404()
            models.append(model)
        print(models)

        # add job into Job database
        job = Job(name=jobname, category='epistatic analysis of miRNAs', type='Predict', description=description,
                  selected_algorithm=';'.join([model.algorithm for model in models]), status=0, user_id=current_user.id)
        db.session.add(job)
        db.session.commit()

        # upload training data
        job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)
        input_x.save(os.path.join(job_dir, x_filename))

        # call scripts and update Model database
        for model in models:
            train_job_id = model.job_id
            model_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                                     '_'.join(['userid', str(current_user.id)]),
                                     '_'.join(['jobid', str(train_job_id)]))
            if not os.path.exists(model_dir):
                flash(model.algorithm + " model doesn't exist!", category='error')
                return redirect(request.url)

            call_predict_scripts(job_dir, model_dir, model.algorithm, x_filename)

        # send result link and security code via email
        result_link = str(url_for('processing', jobid=job.id))

        send_email(recipients=[current_user.email],
                   result_link=result_link, security_code=current_user.security_code)

        return redirect(url_for('processing', jobid=job.id, type='predict'))

    # for GET method return
    users_models = Model.query.filter_by(user_id=current_user.id).order_by(desc(Model.timestamp)).all()
    # print(models)
    jobnames = []
    valid_models = []
    for model in users_models:
        job = Job.query.filter_by(id=model.job_id).first_or_404()
        if job.category != 'epistatic analysis of miRNAs':
            continue
        jobname = Job.query.filter_by(id=model.job_id).first_or_404().name
        jobnames.append(jobname)
        valid_models.append(model)

    return render_template('webserver_epistasis_miRNA_predict.html', models=valid_models, jobnames=jobnames)


@app.route('/webserver/testing', methods=['GET', 'POST'])
@login_required
def webserver_testing():
    if request.method == 'POST':
        jobname = request.form['jobname']
        description = request.form['description']
        email = request.form['email']
        methods = request.form.getlist('methods')

        input_x = request.files['input-x']
        input_y = request.files['input-y']
        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            x_filename = secure_filename(input_x.filename)
            y_filename = secure_filename(input_y.filename)

            if x_filename == y_filename:
                flash("Training data have the same file name.")
                return redirect(request.url)

            if len(methods) == 0:
                flash("You must choose at least one method!")
                return redirect(request.url)

            # return security_code when user exists, otherwise add user into User database
            # then login
            user = User.query.filter_by(email=email).first()
            if user is not None:
                security_code = user.security_code
            else:
                security_code = security_code_generator()
                user = User(username='anonymous', email=email, security_code=security_code)
                # user.set_password(request.form['password'])
                db.session.add(user)
                db.session.commit()
            login_user(user)

            # add job into Job database
            job = Job(jobname=jobname, description=description, selected_algorithm=';'.join(methods), status=0,
                      user_id=current_user.id)
            db.session.add(job)
            db.session.commit()

            # upload training data
            job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)
            input_x.save(os.path.join(job_dir, x_filename))
            input_y.save(os.path.join(job_dir, y_filename))
            # flash("File has been upload!")

            # call scripts and update Model database
            print(methods)
            for method in methods:
                params = {'alpha': '1'}
                call_train_scripts(method, params, job_dir, x_filename, y_filename)
                params_str = ';'.join([key + '=' + value for key, value in params.items()])
                model = Model(algorithm=method, parameters=params_str, is_shared=True, user_id=current_user.id,
                              job_id=job.id)
                db.session.add(model)
            db.session.commit()

            # send result link and security code via email
            result_link = str(url_for('processing', jobid=job.id))
            send_email(recipients=[email],
                       result_link=result_link, security_code=security_code)

            return redirect(url_for('processing', jobid=job.id))
        else:
            flash("Only .txt and .csv file types are valid!")

    models = Model.query.filter_by(user_id=current_user.id).order_by(desc(Model.timestamp)).all()
    # print(models)
    jobnames = []
    usernames = []
    for model in models:
        jobname = Job.query.filter_by(id=model.job_id).first_or_404().jobname
        jobnames.append(jobname)
        username = User.query.filter_by(id=model.user_id).first_or_404().username
        usernames.append(username)

    return render_template('webserver_testing.html', models=models, jobnames=jobnames, usernames=usernames)


@app.route('/predict')
@login_required
def predict():
    return render_template('predict.html')


@app.route('/processing/<jobid>')
@login_required
def processing(jobid):
    job = Job.query.filter_by(id=jobid).first_or_404()
    print('job.status', job.status)
    if job.status == 2:
        if job.type == 'Train':
            return redirect(url_for('result_train', jobid=job.id))
        if job.type == 'Predict':
            return redirect(url_for('result_predict', jobid=job.id))
    else:
        methods = job.selected_algorithm
        check_job_status(jobid, methods)
        return render_template('processing.html', jobid=job.id)


@app.route('/result/train/<jobid>')
@login_required
def result_train(jobid):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                           '_'.join(['userid', str(current_user.id)]),
                           '_'.join(['jobid', str(jobid)]))
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)

    job = Job.query.filter_by(id=jobid).first_or_404()

    EBEN_main_result = load_results(os.path.join(job_dir, 'EBEN.main_result.txt')).values.tolist()
    EBEN_epis_result = load_results(os.path.join(job_dir, 'EBEN.epis_result.txt')).values.tolist()

    if not os.path.isfile(os.path.join(job_dir, 'nodes_links.json')):
        E_json = EBEN_json(job_dir)
        nodes = E_json.generate_nodes_json()
        links = E_json.generate_links_json()
        legends = E_json.generate_legend_json()
        E_json.write_json()
    else:
        nodes, links, legends = load_json(os.path.join(job_dir, 'nodes_links.json'))

    return render_template('result_train.html', jobid=jobid, job_dir=job_dir, methods=job.selected_algorithm,
                           EBEN_main_result=EBEN_main_result, EBEN_epis_result=EBEN_epis_result,
                           nodes=nodes, links=links, legends=legends)

    '''
    # for visulization
    fit_file = os.path.join(job_dir, 'lasso.fit')
    lasso_figure = create_lasso_figure(fit_file)
    lasso_script, lasso_div = components(lasso_figure)
    EBEN_figure = create_lasso_figure(fit_file)
    EBEN_script, EBEN_div = components(EBEN_figure)
    Matrix_eQTL_figure = create_lasso_figure(fit_file)
    Matrix_eQTL_script, Matrix_eQTL_div = components(Matrix_eQTL_figure)
    

    return render_template('result_train.html', jobid=jobid, job_dir=job_dir, methods=job.selected_algorithm,
                           lasso_script=lasso_script,
                           lasso_div=lasso_div,
                           EBEN_script=EBEN_script,
                           EBEN_div=EBEN_div,
                           Matrix_eQTL_script=Matrix_eQTL_script,
                           Matrix_eQTL_div=Matrix_eQTL_div,
                           js_resources=INLINE.render_js(),
                           css_resources=INLINE.render_css())
    '''


@app.route('/result/predict/<jobid>')
@login_required
def result_predict(jobid):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                           '_'.join(['userid', str(current_user.id)]),
                           '_'.join(['jobid', str(jobid)]))
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)

    EBEN_predict_results = load_results(os.path.join(job_dir, 'EBEN_predict.txt')).values.tolist()

    return render_template('result_predict.html', jobid=jobid, job_dir=job_dir,
                           EBEN_predict_results=EBEN_predict_results)


@app.route('/user/jobs', methods=['GET', 'POST'])
@login_required
def jobs():
    if request.method == 'POST':
        choosed_jobs = request.form.getlist('id[]')
        print(choosed_jobs)
        for id in choosed_jobs:
            # must delete related models first, otherwise foreigner key will be delete then can't link to related model
            models = Model.query.filter_by(job_id=id).all()
            if models:
                for model in models:
                    db.session.delete(model)

            job = Job.query.filter_by(id=int(id)).first_or_404()
            print(job)
            db.session.delete(job)

            # delete job_dir
            job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                                   '_'.join(['userid', str(current_user.id)]),
                                   '_'.join(['jobid', str(id)]))
            shutil.rmtree(job_dir)
        db.session.commit()

    user = User.query.filter_by(id=current_user.id).first_or_404()
    jobs = user.jobs.order_by(desc('timestamp')).all()

    return render_template('jobs.html', jobs=jobs)


@app.route('/user/models', methods=['GET', 'POST'])
@login_required
def models():
    if request.method == 'POST':
        choosed_models = request.form.getlist('id[]')
        print(choosed_models)
        for id in choosed_models:
            model = Model.query.filter_by(id=int(id)).first_or_404()
            db.session.delete(model)
        db.session.commit()

    models = Model.query.filter_by(user_id=current_user.id).order_by(desc(Model.timestamp)).all()
    # print(models)
    jobnames = []
    for model in models:
        jobname = Job.query.filter_by(id=model.job_id).first_or_404().name
        jobnames.append(jobname)

    return render_template('models.html', models=models, jobnames=jobnames)


@app.route('/repository')
def repository():
    models = Model.query.filter_by(is_shared=True).order_by(desc(Model.timestamp)).all()
    print(models)
    jobnames = []
    usernames = []
    for model in models:
        jobname = Job.query.filter_by(id=model.job_id).first_or_404().jobname
        jobnames.append(jobname)
        username = User.query.filter_by(id=model.user_id).first_or_404().username
        usernames.append(username)

    return render_template('repository.html', models=models, jobnames=jobnames, usernames=usernames)


@app.route('/pca', methods=['GET', 'POST'])
def pca():
    x = [1, 2, 3, 4, 5]
    y = [6, 7, 8, 9, 0]
    boken_figure = create_pca_figure(x, y)

    script, div = components(boken_figure)

    return render_template('pca.html',
                           plot_script=script,
                           plot_div=div,
                           js_resources=INLINE.render_js(),
                           css_resources=INLINE.render_css())

    # return render_template('pca.html', userID=userID, mpld3=mpld3.fig_to_html(fig))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user is not None:
            flash(message='This Email has been registered. Please log in or use another email address.',
                  category='error')
            return redirect(url_for('signup'))
        user = User(username=request.form['username'], email=request.form['email'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        # flash(message='Successful! You will be redirected to Home page.', category='message')
        # time.sleep(5)
        return redirect(url_for('index'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # achieve next page link
    next = request.args.get('next')
    if not is_safe_url(next):
        return abort(400)

    # verify security code
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user is None or not user.check_security_code(request.form['security_code']):
            flash(message='Login Failed! Invalid Username or Password.', category='error')
            return redirect(next or url_for('index'))
        else:
            # login_user(user, remember=request.form['remember_me'])
            login_user(user)
            return redirect(next or url_for('index'))

    return render_template('login.html', title='Login')


@app.route('/user/profile')
@login_required
def profile():
    user = User.query.filter_by(id=current_user.id).first_or_404()
    return render_template('profile.html', user=user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


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


@app.route('/show_pic/<jobid>/<filename>')
@login_required
def show_pic(jobid, filename):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                           '_'.join(['userid', str(current_user.id)]),
                           '_'.join(['jobid', str(jobid)]))
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)

    try:
        return send_file(os.path.join(job_dir, filename), attachment_filename=filename)
    except Exception as e:
        return str(e)


@app.route('/download/result/<jobid>/<filename>')
@login_required
def download_result(jobid, filename):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                           '_'.join(['userid', str(current_user.id)]),
                           '_'.join(['jobid', str(jobid)]))
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)
    try:
        return send_file(os.path.join(job_dir, filename), attachment_filename=filename)
    except Exception as e:
        return str(e)


@app.route('/download/sample_data/<filename>')
def download_sample_data(filename):
    try:
        return send_file(os.path.join(app.config['SAMPLE_DATA_DIR'], filename), attachment_filename=filename)
    except Exception as e:
        return str(e)
