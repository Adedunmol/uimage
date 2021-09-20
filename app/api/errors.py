
from app.errors import ValidationError
from app import api
from flask import jsonify, request, render_template
from . import api
from ..main import main


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response

def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response

def forbidden(message):
    response = jsonify({'error': 'Forbidden', 'message': message})
    response.status_code = 403
    return response

    
@api.errorhandler(404)
def page_not_found(e):
    response = jsonify({'error': 'Not found'})
    response.status_code = 404
    return response

@api.errorhandler(405)
def method_not_allowed(e):
    response = jsonify({'error': 'Method not allowed'})
    return response, 405
