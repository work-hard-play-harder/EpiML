from flask import render_template, request, url_for
from flask_mail import Message

from EpiML import mail, app, celery


@celery.task()
def send_submit_job_email(email, jobname, processing_url):
    subject = 'Job submitted | EpiML@ShiLab'
    sender = app.config['MAIL_USERNAME']

    msg = Message(subject, sender=sender, recipients=[email])

    msg.body = 'Dear {},\nThank you for using EpiML web server.\n\nYour job (Job Name: {}) has been submitted. ' \
               'The processing time depends on the scale of your data and selected method. You can check job status ' \
               'and retrieve result via the following link.\n Result Link: {}\n\n' \
               'Sincerely,\n' \
               'ShiLab'.format(email, jobname, processing_url)

    # print(msg.body)
    # msg.html=render_template('notice_email.html')
    with app.app_context():
        mail.send(msg)


@celery.task()
def send_job_done_email(email, jobname, processing_url):
    subject = 'Job done | EpiML@ShiLab'
    sender = app.config['MAIL_USERNAME']

    msg = Message(subject, sender=sender, recipients=[email])

    msg.body = 'Dear {},\nThank you for using EpiML web server.\n\nYour job (Job Name: {}) has been done. ' \
               'You can retrieve result via the following link\n Result Link: {}\n\n' \
               'Sincerely,\n' \
               'ShiLab'.format(email, jobname, processing_url)

    # print(msg.body)
    # msg.html=render_template('notice_email.html')
    with app.app_context():
        mail.send(msg)


@celery.task()
def send_job_error_email(email, jobname, processing_url):
    subject = 'Job error | EpiML@ShiLab'
    sender = app.config['MAIL_USERNAME']

    msg = Message(subject, sender=sender, recipients=[email])

    msg.body = 'Dear {},\nThank you for using EpiML web server.\n\nYour job (Job Name: {}) is error. ' \
               'You can check error via the following link\n Result Link: {}\n\n' \
               'Sincerely,\n' \
               'ShiLab'.format(email, jobname, processing_url)

    # print(msg.body)
    # msg.html=render_template('notice_email.html')
    with app.app_context():
        mail.send(msg)
