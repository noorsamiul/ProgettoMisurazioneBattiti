# _common.py
from flask import redirect, g, url_for
from functools import wraps

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if getattr(g, "user", None) is None:
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return wrapper