from flask.helpers import url_for
from flask.json import jsonify
from app.models import User
from . import api
from flask import jsonify, request, current_app


@api.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, True')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response


@api.route('/users/<int:id>/')
def get_user(id):
    """Return a user 
    This endpoint returns a user by its id. """
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


@api.route('/users/')
def get_users():
    """Return a list of users
    This endpoint returns a list of users."""
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.date_joined.desc()).paginate(page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False)
    users = [user.to_json() for user in pagination.items]
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_users', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_users', page=page+1)
    return jsonify({
        'users': users,
        'prev_url': prev,
        'next_url': next,
        'total': pagination.total
    })