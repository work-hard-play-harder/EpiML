from flask import render_template
from flask_mail import Message

from EpiMap import mail, app


def send_email(recipients, result_link, security_code):
    subject = 'Notice from ShiLab'
    sender = app.config['MAIL_USERNAME']

    msg = Message(subject, sender=sender, recipients=recipients)

    msg.body = 'Dear {},\nThank you for using our web sever.\n\nYour job has been submitted. ' \
               'The processing time depends on the scale of your data. You can retrieve result ' \
               'via the following link\n Result Link: http://127.0.0.1:5000{}\n Security Code: {}\n\nß' \
               'Sincerely,\n' \
               'ShiLab' \
               '\n '.format(recipients[0], result_link, security_code)

    # msg.html=render_template('notice_email.html')
    mail.send(msg)
