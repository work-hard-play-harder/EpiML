from flask import render_template
from flask_mail import Message

from EpiMap import mail, app, celery


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
def send_submit_job_email(recipients, security_code):
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


def send_job_done_email():
    pass


def send_delete_job_email():
    pass
