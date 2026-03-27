from functools import wraps
from flask import (Flask, render_template, request, g, url_for, session)
import sqlalchemy
import auth

app=Flask (__name__)

@app.route("/")
def hello():
    return "Hello world!"

@app.route("/cardiaco")
def login():
    render_template("misurazione/hompage")

if __name__=="__main__":
    app.run(debug=True)