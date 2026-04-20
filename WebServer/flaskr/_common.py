# _common.py
from flask import redirect, g, url_for
from functools import wraps

def login_required(func):
    @wraps(func)  #mantiene il nome, il docstring e l’endpoint della funzione originale. Senza questo, Flask registra wrapper invece di films, e non funziona il redirect.
    def wrapper(*args, **kwargs):
        out = None
        if g.user:
            out = func(*args, **kwargs)
        else:
            out = redirect(url_for('auth.login'))
        return out
    return wrapper