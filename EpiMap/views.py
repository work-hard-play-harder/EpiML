import os
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
from EpiMap.run_scripts import call_scripts, create_job_folder, check_job_status
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
                call_scripts(method, params, job_dir, x_filename, y_filename)
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


@app.route('/processing/<jobid>')
@login_required
def processing(jobid):
    job = Job.query.filter_by(id=jobid).first_or_404()
    print('job.status', job.status)
    if job.status == 2:
        return redirect(url_for('result', jobid=job.id))
    else:
        methods = job.selected_algorithm
        check_job_status(jobid, methods)
        return render_template('processing.html', jobid=job.id)


@app.route('/result/<jobid>')
@login_required
def result(jobid):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                           '_'.join(['userid', str(current_user.id)]),
                           '_'.join(['jobid', str(jobid)]))
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)

    job = Job.query.filter_by(id=jobid).first_or_404()

    fit_file=os.path.join(job_dir,'lasso.fit')
    lasso_figure = create_lasso_figure(fit_file)
    lasso_script, lasso_div = components(lasso_figure)
    EBEN_figure = create_lasso_figure(fit_file)
    EBEN_script, EBEN_div = components(EBEN_figure)
    Matrix_eQTL_figure = create_lasso_figure(fit_file)
    Matrix_eQTL_script, Matrix_eQTL_div = components(Matrix_eQTL_figure)

    return render_template('result.html', jobid=jobid, job_dir=job_dir, methods=job.selected_algorithm,
                           lasso_script=lasso_script,
                           lasso_div=lasso_div,
                           EBEN_script=EBEN_script,
                           EBEN_div=EBEN_div,
                           Matrix_eQTL_script=Matrix_eQTL_script,
                           Matrix_eQTL_div=Matrix_eQTL_div,
                           js_resources=INLINE.render_js(),
                           css_resources=INLINE.render_css())


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


@app.route('/user/jobs', methods=['GET', 'POST'])
@login_required
def jobs():
    user = User.query.filter_by(id=current_user.id).first_or_404()
    jobs = user.jobs.order_by(desc('timestamp')).all()

    return render_template('jobs.html', jobs=jobs)


@app.route('/models', methods=['GET', 'POST'])
@login_required
def models():
    models=Model.query.filter_by(user_id=current_user.id).order_by(desc(Model.timestamp)).all()
    print(models)
    jobnames = []
    usernames = []
    for model in models:
        jobname = Job.query.filter_by(id=model.job_id).first_or_404().jobname
        jobnames.append(jobname)
        username = User.query.filter_by(id=model.user_id).first_or_404().username
        usernames.append(username)

    return render_template('models.html', models=models, jobnames=jobnames, usernames=usernames)


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
