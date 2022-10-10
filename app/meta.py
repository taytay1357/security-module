"""
Setup "Meta" class,

Contains App definition and database init functionality

# ------ DATABASE FUNC -------
# Taken from from https://flask.palletsprojects.com/en/2.2.x/patterns/sqlite3/

"""



import flask
from flask import g
import sqlite3

DATABASE = 'database.db'
UPLOAD_FOLDER = 'uploads'


app = flask.Flask(__name__)

app.config.update(
    SECRET_KET="secr3t!",
    SESSION_COOKIE_SAMESITE='Strict',
    UPLOAD_FOLDER=UPLOAD_FOLDER
)



def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('../schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
