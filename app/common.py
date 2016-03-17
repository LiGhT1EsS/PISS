import string
from random import Random
from threading import Thread

from flask import render_template
from flask.ext.mail import Message

from app import app, mail


# create random string
def random_str(randomlength=32):
    result = ''
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        result += chars[random.randint(0, length)]
    return result


# send mail async
def send_async_mail(app, msg):
    with app.app_context():
        mail.send(msg)


# send mail function
def send_mail(to, subject, template, **kwargs):
    app.config['PISS_MAIL_SUBJECT_PREFIX'] = '[PISS]'
    app.config['PISS_MAIL_SENDER'] = 'PISS support <lightless@foxmail.com>'

    msg = Message(app.config['PISS_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['PISS_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    thr = Thread(target=send_async_mail, args=[app, msg])
    thr.start()
    return thr
