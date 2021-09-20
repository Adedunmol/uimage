from app.models import Permissions
from flask_login import current_user
from functools import wraps
from flask import abort

#This decorator checks if the current user has the permission
def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.can(perm):
                abort(401)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(f):
    return permission_required(Permissions.ADMIN)(f)