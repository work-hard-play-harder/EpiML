from flask import render_template, request
from flask_mail import Message

from EpiML import mail, app, celery


@celery.task()
def send_email(recipients, security_code):
    subject = 'Notice from ShiLab'
    sender = app.config['MAIL_USERNAME']

    msg = Message(subject, sender=sender, recipients=recipients)

    msg.body = 'Dear {},\nThank you for using our web sever.\n\nYour job has been submitted. ' \
               'The processing time depends on the scale of your data. You can retrieve result ' \
               'via the following link\n Result Link: http://127.0.0.1:5000/user/jobs\n Security Code: {}\n\n' \
               'Sincerely,\n' \
               'ShiLab'.format(recipients[0], security_code)

    # msg.html=render_template('notice_email.html')
    mail.send(msg)


@celery.task()
def send_submit_job_email(recipients, jobname, jobid, security_code):
    subject = 'Job submitted | EpiML@ShiLab'
    sender = app.config['MAIL_USERNAME']

    msg = Message(subject, sender=sender, recipients=recipients)

    msg.body = 'Dear {},\nThank you for using EpiML web server.\n\nYour job (Job Name: {}) has been submitted. ' \
               'The processing time depends on the scale of your data and selected method. You can check job status ' \
               'and retrieve result via the following link\n Result Link: {}/processing/{}_{}\n\n' \
               'Sincerely,\n' \
               'ShiLab'.format(recipients[0], jobname, request.headers['Host'], jobid, security_code)

    # msg.html=render_template('notice_email.html')
    mail.send(msg)


@celery.task()
def send_job_done_email(recipients, jobname, jobid, security_code):
    subject = 'Job done | EpiML@ShiLab'
    sender = app.config['MAIL_USERNAME']

    msg = Message(subject, sender=sender, recipients=recipients)

    msg.body = 'Dear {},\nThank you for using EpiML web server.\n\nYYour job (Job Name: {}) has been done. ' \
               'You can retrieve result ' \
               'via the following link\n Result Link: {}/processing/{}_{}\n\n' \
               'Sincerely,\n' \
               'ShiLab'.format(recipients[0], jobname, request.headers['Host'], jobid, security_code)

    # msg.html=render_template('notice_email.html')
    mail.send(msg)


@celery.task()
def send_job_error_email(recipients, jobname, jobid, security_code):
    subject = 'Job error | EpiML@ShiLab'
    sender = app.config['MAIL_USERNAME']

    msg = Message(subject, sender=sender, recipients=recipients)

    msg.body = 'Dear {},\nThank you for using EpiML web server.\n\nYYour job (Job Name: {}) is error. ' \
               'You can check error' \
               'via the following link\n Result Link: {}/processing/{}_{}\n\n' \
               'Sincerely,\n' \
               'ShiLab'.format(recipients[0], jobname, request.headers['Host'], jobid, security_code)

    # msg.html=render_template('notice_email.html')
    mail.send(msg)
