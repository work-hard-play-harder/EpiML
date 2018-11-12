import random
import string
import time
from urllib.parse import urlparse, urljoin
from flask import request

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
