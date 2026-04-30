# auth.py
from flask import Blueprint, g, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db.engine import SessionLocal
from db.models.user import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


# region LOGIN 
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('homepage'))

    error = None

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        with SessionLocal() as db_session:
            utente = User.get_user(db_session, username)

        if utente and utente.login(password):
            session['username'] = username
            return redirect(url_for('homepage'))
        else:
            error = 'Username o password non corretti.'

    return render_template('auth/login.html', error=error, show_modal=error)


# region REGISTER 
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('homepage'))

    error = None
    success = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        if not username or not password:
            error = 'Tutti i campi sono obbligatori.'
        elif len(username) < 3:
            error = 'Username troppo corto.'
        elif len(password) < 6:
            error = 'Password troppo corta.'
        elif password != confirm:
            error = 'Le password non coincidono.'
        else:
            with SessionLocal() as db_session:
                esistente = User.get_user(db_session, username)
                if esistente:
                    error = 'Username già in uso.'
                else:
                    nuovo = User(
                        username=username,
                        password=generate_password_hash(password),
                    )
                    db_session.add(nuovo)
                    db_session.commit()
                    success = 'Registrazione completata! Puoi effettuare il login.'

    return render_template('auth/register.html', error=error, success=success)


# region LOGOUT 
@bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('auth.login'))