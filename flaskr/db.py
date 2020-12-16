import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        uri = urlparse(current_app.config.get('DATABASE'))
        g.db = psycopg2.connect(host=uri.hostname,
                                dbname=uri.path[1:],
                                password=uri.password,
                                user=uri.username)

        g.db.cursor_factory=psycopg2.extras.NamedTupleCursor

    return g.db 

def query_db(query, args=(), one=False):
    db_conn = get_db()
    db_cursor = db_conn.cursor()

    db_cursor.execute(query, args)
    rv = db_cursor.fetchall()
    
    db_cursor.close()
    return (rv[0] if rv else None) if one else rv

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db_cursor = db.cursor()

    with current_app.open_resource('schema.sql') as f:
        db_cursor.execute(f.read().decode('utf8'))

    db.commit()
    db_cursor.close()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables"""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)