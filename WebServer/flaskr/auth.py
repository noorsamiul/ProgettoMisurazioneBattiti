
from flask import (Flask, render_template)

app=Flask(__name__)

app.route("/login")
def login():
    render_template("auth/login.html")