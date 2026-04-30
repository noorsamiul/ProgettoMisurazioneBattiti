# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, g
from _common import login_required
from db.engine import SessionLocal, engine
from db.base import Base
from db.models.user import User
from db.models.misurazione import Misurazione

FLASKR_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSERVER   = os.path.dirname(FLASKR_DIR)
TEMPLATES   = os.path.join(FLASKR_DIR, 'templates')

app = Flask(
    __name__,
    template_folder=TEMPLATES,
    static_folder=os.path.join(WEBSERVER, 'static'),
)

app.secret_key = os.environ.get('SECRET_KEY', 'chiave_segreta_cambia_in_produzione')

with app.app_context():
    Base.metadata.create_all(bind=engine)


# region BEFORE REQUEST 
@app.before_request
def load_logged_in_user():
    username = session.get('username')
    if username is None:
        g.user = None
    else:
        with SessionLocal() as db_session:
            g.user = User.get_user(db_session, username)


# region HELPERS 
def misurazione_to_dict(m):
    return {
        'id':      m.id,
        'bpmMedi': m.bpmMedi,
        'bpmMax':  m.bpmMax,
        'bpmMin':  m.bpmMin,
        'data':    m.data,
    }


# region ROUTES 
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('homepage'))
    return redirect(url_for('auth.login'))


@app.route('/homepage', methods=['GET', 'POST'])
@login_required
def homepage():
    utente = g.user

    if request.method == 'POST':
        with SessionLocal() as db_session:
            nuova = Misurazione(
                bpmMedi=int(request.form.get('bpm_medi', 0)),
                bpmMax=int(request.form.get('bpm_massimi', 0)),
                bpmMin=int(request.form.get('bpm_minimi', 0)),
                user_id=utente.id,
            )
            db_session.add(nuova)
            db_session.commit()
        return redirect(url_for('cronologia'))

    with SessionLocal() as db_session:
        misurazioni = Misurazione.get_by_user(db_session, utente.id)
        ultima = misurazione_to_dict(misurazioni[0]) if misurazioni else None

    return render_template(
        'misurazione/homepage.html',
        username=utente.username,
        created_at=utente.created_at,
        ultima=ultima,
    )


@app.route('/cronologia')
@login_required
def cronologia():
    utente = g.user

    with SessionLocal() as db_session:
        misurazioni = Misurazione.get_by_user(db_session, utente.id)
        history = [misurazione_to_dict(m) for m in misurazioni]

    return render_template(
        'misurazione/cronologia.html',
        username=utente.username,
        history=history,
    )


@app.route('/delete_misurazione/<string:id_misurazione>', methods=['POST'])
@login_required
def delete_misurazione(id_misurazione):
    utente = g.user

    with SessionLocal() as db_session:
        misurazione = db_session.get(Misurazione, id_misurazione)
        if misurazione and misurazione.user_id == utente.id:
            db_session.delete(misurazione)
            db_session.commit()

    return redirect(url_for('cronologia'))


# region BLUEPRINT AUTH 
from auth import bp as auth_bp
app.register_blueprint(auth_bp)

# region RUN 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)