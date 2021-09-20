from flask.templating import render_template
from flask_mail import Message
from . import mail
from threading import Thread
from flask import current_app


def send_async_mail(app, msg):
    with app.app_context():
        mail.send(msg)


def send_mail(to, subject, template, *args, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject=current_app.config['UIMAGE_MAIL_HEADER']+ subject, 
                        recipients=[to], sender=current_app.config['UIMAGE_MAIL_SENDER'])
    msg.body = render_template(template + '.txt', *args, **kwargs)
    msg.html = render_template(template + '.html', *args, **kwargs)
    thr = Thread(target=send_async_mail, args=[app, msg])
    thr.start()
    return thr