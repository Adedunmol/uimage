from . import main
from flask import render_template, request, jsonify


@main.app_errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400


@main.app_errorhandler(401)
def bad_request(e):
    return render_template('401.html'), 401


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main.errorhandler(405)
def not_allowed(e):
    return render_template('405.html'), 405

@main.app_errorhandler(413)
def too_large(e):
    return render_template('413.html'), 413

@main.app_errorhandler(500)
def server_error(e):
    response = jsonify({'error': 'Server error'})
    response.status_code = 500
    return response