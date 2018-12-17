import random
import string
import time
import uuid
from urllib.parse import urlparse, urljoin
from flask import request,session,abort

from EpiML import app


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def security_code_generator(size=32, chars=string.ascii_letters + string.digits):
    return ''.join(random.choices(chars, k=size)) + str(time.time())


# @app.before_request
# def csrf_protect():
#     if request.method == "POST":
#         token = session.pop('_csrf_token', None)
#         if not token or token != request.form.get('_csrf_token'):
#             abort(403)
#
# def generate_csrf_token():
#     if '_csrf_token' not in session:
#         session['_csrf_token'] = generate_random_string()
#     return session['_csrf_token']
#
# def generate_random_string():
#     return str(uuid.uuid4())
#
# app.jinja_env.globals['csrf_token'] = generate_csrf_token