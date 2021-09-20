from re import U
from flask.json import jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User
from flask import g, request
from . import api
from .errors import forbidden, unauthorized, method_not_allowed


auth = HTTPBasicAuth()
auth.__doc__ = """
Pass your email and password to authenticate.
"""


@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user 
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.confirm_password(password)


@auth.error_handler
def error():
    return unauthorized('Invalid Credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('Unconfirmed account')

@api.route('/tokens/', methods=['POST'])
def send_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid Credentials')
    return jsonify({'token': g.current_user.generate_auth_token(expires=3600), 'expires': 3600})
