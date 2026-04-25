import os
from flask import Flask, render_template, request, redirect, url_for, session, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from _common import login_required

FLASKR_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSERVER  = os.path.dirname(FLASKR_DIR)
TEMPLATES  = os.path.join(FLASKR_DIR, 'templates')

app = Flask(
    __name__,
    template_folder=TEMPLATES,
    static_folder=os.path.join(WEBSERVER, 'static'),
)

app.secret_key = 'chiave_segreta_cambia_in_produzione'

# region DATABASE

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://admin:secret@localhost:5432/battiti'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.app_context().push()

# region MODELLI
class Utente(db.Model):
    __tablename__ = 'utente'

    id_utente   = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(80), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    nome        = db.Column(db.String(80))
    cognome     = db.Column(db.String(80))
    eta         = db.Column(db.Integer)
    created_at  = db.Column(db.String(30))

    misurazioni = db.relationship('Misurazione', backref='utente', lazy=True)


class Misurazione(db.Model):
    __tablename__ = 'misurazione'

    id_misurazione = db.Column(db.Integer, primary_key=True)
    bpm_medi       = db.Column(db.Integer)
    bpm_massimi    = db.Column(db.Integer)
    bpm_minimi     = db.Column(db.Integer)
    data           = db.Column(db.String(30))

    id_utente      = db.Column(
        db.Integer,
        db.ForeignKey('utente.id_utente'),
        nullable=False
    )

with app.app_context():
    db.create_all()

# region BEFORE REQUEST (FONDAMENTALE)
@app.before_request
def load_logged_in_user():
    username = session.get('username')

    if username is None:
        g.user = None
    else:
        g.user = Utente.query.filter_by(username=username).first()

# region HELPERS
def get_utente():
    return g.user

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

    if utente is None:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nuova = Misurazione(
            bpm_medi=int(request.form.get('bpm_medi', 0)),
            bpm_massimi=int(request.form.get('bpm_massimi', 0)),
            bpm_minimi=int(request.form.get('bpm_minimi', 0)),
            data=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            id_utente=utente.id_utente
        )

        db.session.add(nuova)
        db.session.commit()

        return redirect(url_for('cronologia'))

    ultima = Misurazione.query.filter_by(
        id_utente=utente.id_utente
    ).order_by(Misurazione.id_misurazione.desc()).first()

    return render_template(
        'misurazione/homepage.html',
        username=utente.username,
        nome=utente.nome,
        cognome=utente.cognome,
        eta=utente.eta,
        created_at=utente.created_at,
        ultima=ultima
    )


@app.route('/cronologia')
@login_required
def cronologia():

    utente = g.user

    if utente is None:
        return redirect(url_for('auth.login'))

    misurazioni = Misurazione.query.filter_by(
        id_utente=utente.id_utente
    ).order_by(Misurazione.id_misurazione.desc()).all()

    return render_template(
        'misurazione/cronologia.html',
        username=utente.username,
        history=misurazioni
    )


@app.route('/delete_misurazione/<int:id_misurazione>', methods=['POST'])
def delete_misurazione():

    if 'username' not in session:
        return redirect(url_for('auth.login'))

    utente = g.user

    if utente is None:
        return redirect(url_for('auth.login'))

    misurazione = Misurazione.query.filter_by(
        id_misurazione=id_misurazione,
        id_utente=utente.id_utente
    ).first()

    if misurazione:
        db.session.delete(misurazione)
        db.session.commit()

    return redirect(url_for('cronologia'))


# region BLUEPRINT AUTH
from auth import bp as auth_bp
app.register_blueprint(auth_bp)

# region RUN
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)