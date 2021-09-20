from functools import wraps
from flask import g, abort

def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not g.current_user.can(perm):
                abort(401)
            return f(*args, **kwargs)
        return wrapper
    return decorator

