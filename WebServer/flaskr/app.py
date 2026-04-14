import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

FLASKR_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSERVER  = os.path.dirname(FLASKR_DIR)
TEMPLATES  = os.path.join(FLASKR_DIR, 'templates')

app = Flask(
    __name__,
    template_folder=TEMPLATES,
    static_folder=os.path.join(WEBSERVER, 'static'),
)

app.secret_key = 'chiave_segreta_cambia_in_produzione'

# ── DATABASE ─────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://admin:secret@localhost:5432/battiti'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── MODELLI ──────────────────────────────

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

# ── HELPERS ──────────────────────────────

def get_utente():
    return Utente.query.filter_by(username=session.get('username')).first()

# ── ROUTES ───────────────────────────────

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('homepage'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('homepage'))

    error = None

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        utente = Utente.query.filter_by(username=username).first()

        if utente and check_password_hash(utente.password, password):
            session['username'] = username
            return redirect(url_for('homepage'))
        else:
            error = 'Username o password non corretti.'

    return render_template('auth/login.html', error=error)


@app.route('/registrazione', methods=['GET', 'POST'])
def registrazione():
    if 'username' in session:
        return redirect(url_for('homepage'))

    error = None
    success = None

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm  = request.form['confirm']
        nome     = request.form['nome'].strip()
        cognome  = request.form['cognome'].strip()
        eta      = request.form['eta'].strip()

        if not username or not password or not nome or not cognome or not eta:
            error = 'Tutti i campi sono obbligatori.'

        elif len(username) < 3:
            error = 'Username troppo corto.'

        elif len(password) < 6:
            error = 'Password troppo corta.'

        elif password != confirm:
            error = 'Password non coincidono.'

        elif not eta.isdigit() or not (1 <= int(eta) <= 120):
            error = "Età non valida."

        elif Utente.query.filter_by(username=username).first():
            error = 'Username già in uso.'

        else:
            nuovo = Utente(
                username=username,
                password=generate_password_hash(password),
                nome=nome,
                cognome=cognome,
                eta=int(eta),
                created_at=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            )

            db.session.add(nuovo)
            db.session.commit()

            success = "Registrazione completata!"

    return render_template('auth/registrazione.html', error=error, success=success)


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    if 'username' not in session:
        return redirect(url_for('login'))

    utente = get_utente()
    if not utente:
        session.pop('username', None)
        return redirect(url_for('login'))

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
def cronologia():
    if 'username' not in session:
        return redirect(url_for('login'))

    utente = get_utente()
    if not utente:
        session.pop('username', None)
        return redirect(url_for('login'))

    misurazioni = Misurazione.query.filter_by(
        id_utente=utente.id_utente
    ).order_by(Misurazione.id_misurazione.desc()).all()

    return render_template(
        'misurazione/cronologia.html',
        username=utente.username,
        history=misurazioni
    )


# ── DELETE MISURAZIONE ───────────────────

@app.route('/delete_misurazione/<int:id_misurazione>', methods=['POST'])
def delete_misurazione(id_misurazione):
    if 'username' not in session:
        return redirect(url_for('login'))

    utente = get_utente()
    if not utente:
        session.pop('username', None)
        return redirect(url_for('login'))

    misurazione = Misurazione.query.filter_by(
        id_misurazione=id_misurazione,
        id_utente=utente.id_utente
    ).first()

    if misurazione:
        db.session.delete(misurazione)
        db.session.commit()

    return redirect(url_for('cronologia'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)