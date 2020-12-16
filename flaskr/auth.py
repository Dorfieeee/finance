import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db, query_db

from psycopg2 import OperationalError

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']
        db = get_db()
        db_cursor = db.cursor()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password1 or not password2:
            error = 'Password is required.'
        elif password1 != password2:
            error = 'Passwords don\'t match.'
        elif query_db(
            'SELECT id FROM person WHERE username = %s', (username,)
            , one=True) is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            # Insert new user and deposit $10.000 to his account
            try:
                db_cursor.execute(
                    'INSERT INTO person (username, password) VALUES (%s, %s)',
                    (username, generate_password_hash(password1))
                )
                user_id = query_db(
                    'SELECT id FROM person WHERE username = %s', (username,)
                , one=True)[0]
                db_cursor.execute(
                    'INSERT INTO deposit (person, value) VALUES (%s, %s)',
                    (user_id, 10000.0)
                )
                db_cursor.execute(
                    'INSERT INTO account (person, balance) VALUES (%s, %s)',
                    (user_id, 10000.0)
                )
            except OperationalError:
                db.rollback()
                flash('There was an issues with your registration. Please, try again.', 'error')
                return redirect(url_for('auth.register'))

            db.commit()
            db_cursor.close()

            return redirect(url_for('auth.login'))

        flash(error, category='error')

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = query_db(
            'SELECT * FROM person WHERE username = %s', (username,)
        , one=True)

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('dashboard.dashboard'))

        flash(error, category='error')

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = query_db(
            'SELECT * FROM person WHERE id = %s', (user_id,)
        , one=True)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard.dashboard'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view