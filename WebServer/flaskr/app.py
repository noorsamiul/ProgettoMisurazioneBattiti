import os
import threading
import time
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
from flask_socketio import SocketIO, join_room

from _common import login_required
from db.engine import SessionLocal, engine
from db.base import Base
from db.models.user import User
from db.models.misurazione import Misurazione

from auth import bp as auth_bp

# ─────────────────────────────
#region APP INIT
# ─────────────────────────────

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
)

app.secret_key = os.environ.get("SECRET_KEY", "dev")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

app.register_blueprint(auth_bp)

with app.app_context():
    Base.metadata.create_all(bind=engine)

# ─────────────────────────────
#region COMANDI ESP32
# ─────────────────────────────

_comandi = {}
_lock = threading.Lock()

def set_comando(user_id, cmd):
    with _lock:
        _comandi[user_id] = cmd

def get_e_reset_comando(user_id):
    with _lock:
        cmd = _comandi.get(user_id, "idle")
        if cmd == "start":
            _comandi[user_id] = "idle"
        return cmd

# ─────────────────────────────
#region AUTH ESP32 TOKEN
# ─────────────────────────────

def autentica_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None

    token = auth.split(" ")[1]

    with SessionLocal() as db:
        return User.get_by_token(db, token)

# ─────────────────────────────
#region SESSION USER
# ─────────────────────────────

@app.before_request
def load_user():
    username = session.get("username")
    if username:
        with SessionLocal() as db:
            g.user = User.get_user(db, username)
    else:
        g.user = None

# ─────────────────────────────
#region SOCKET
# ─────────────────────────────

@socketio.on("join")
def on_join(data):
    join_room(str(data.get("user_id")))

# ─────────────────────────────
#region ROUTES BASE
# ─────────────────────────────

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("homepage"))
    return redirect(url_for("auth.login"))


@app.route("/homepage")
@login_required
def homepage():
    return render_template(
        "misurazione/homepage.html",
        username=g.user.username,
        user_id=g.user.id
    )

# ─────────────────────────────
#region CRONOLOGIA
# ─────────────────────────────

@app.route("/cronologia")
@login_required
def cronologia():
    with SessionLocal() as db:
        misurazioni = Misurazione.get_by_user(db, g.user.id)

    tz_italia = ZoneInfo("Europe/Rome")

    history = [
        {
            "id": m.id,
            "bpmMedi": m.bpmMedi,
            "bpmMax": m.bpmMax,
            "bpmMin": m.bpmMin,
            "data": m.data.astimezone(tz_italia),  # ← UTC → ora italiana
        }
        for m in misurazioni
    ]

    return render_template(
        "misurazione/cronologia.html",
        username=g.user.username,
        history=history
    )


@app.route("/cronologia/elimina/<string:id_misurazione>", methods=["POST"])
@login_required
def delete_misurazione(id_misurazione):
    with SessionLocal() as db:
        from sqlalchemy import select
        m = db.execute(
            select(Misurazione).where(
                Misurazione.id == id_misurazione,
                Misurazione.user_id == g.user.id
            )
        ).scalars().first()

        if m:
            db.delete(m)
            db.commit()

    return redirect(url_for("cronologia"))

# ─────────────────────────────
#region PROFILO
# ─────────────────────────────

@app.route("/profilo")
@login_required
def profilo():
    return render_template(
        "misurazione/profilo.html",
        username=g.user.username,
        user=g.user,
        api_token=g.user.api_token
    )

# ─────────────────────────────
#regionESP32 API
# ─────────────────────────────

@app.route("/web/avvia_misurazione", methods=["POST"])
@login_required
def avvia():
    set_comando(g.user.id, "start")

    def stop_after_20s(user_id):
        time.sleep(20)
        set_comando(user_id, "stop")

    threading.Thread(target=stop_after_20s, args=(g.user.id,), daemon=True).start()

    return jsonify({"ok": True, "durata": 30})


@app.route("/api/comando")
def comando():
    user = autentica_token()
    if not user:
        return jsonify({"ok": False}), 401

    return jsonify({"comando": get_e_reset_comando(user.id)})

# ─────────────────────────────
#region BPM LIVE
# ─────────────────────────────

@app.route("/api/bpm_live", methods=["POST"])
def bpm_live():
    user = autentica_token()
    if not user:
        return jsonify({"ok": False}), 401

    data = request.get_json() or {}

    socketio.emit(
        "bpm_live",
        {
            "bpm": data.get("bpm", 0),
            "stato": data.get("stato", "")
        },
        room=str(user.id)
    )

    return jsonify({"ok": True})

@app.route("/api/misura", methods=["POST"])
def misura():
    user = autentica_token()
    if not user:
        return jsonify({"ok": False}), 401

    data = request.get_json() or {}

    bpm_medi = int(data["bpm_medi"])
    bpm_max  = int(data["bpm_max"])
    bpm_min  = int(data["bpm_min"])

    socketio.emit(
        "misura_completata",
        {
            "bpmMedi": bpm_medi,
            "bpmMax":  bpm_max,
            "bpmMin":  bpm_min
        },
        room=str(user.id)
    )

    return jsonify({"ok": True})

# ─────────────────────────────
#region SALVA MISURAZIONE (da web)
# ─────────────────────────────

@app.route("/web/salva_misurazione", methods=["POST"])
@login_required
def salva_misurazione():
    data = request.get_json() or {}

    try:
        m = Misurazione(
            bpmMedi=int(data["bpm_medi"]),
            bpmMax=int(data["bpm_max"]),
            bpmMin=int(data["bpm_min"]),
            user_id=g.user.id
        )
    except (KeyError, ValueError):
        return jsonify({"ok": False, "error": "Dati mancanti o non validi"}), 400

    with SessionLocal() as db:
        db.add(m)
        db.commit()

    return jsonify({"ok": True})


# ─────────────────────────────
#region RUN
# ─────────────────────────────

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)