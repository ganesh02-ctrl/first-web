"""Authorization decorators. Every protected route uses one of these."""
from functools import wraps

from flask_jwt_extended import current_user, verify_jwt_in_request

from app.utils.errors import Forbidden, Unauthorized


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if current_user is None:
            raise Unauthorized("Authentication required")
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            # Role is read from the database user, not trusted from the token claim.
            if current_user is None:
                raise Unauthorized("Authentication required")
            if current_user.role not in roles:
                raise Forbidden("You do not have permission to perform this action")
            return fn(*args, **kwargs)
        return wrapper
    return decorator


admin_required = roles_required("admin")
student_required = roles_required("student")


def get_current_user():
    return current_user
