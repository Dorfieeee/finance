from flask import (
    Blueprint, flash, g, redirect, render_template, request, session,
    url_for, jsonify, make_response
)

from flaskr.db import get_db, query_db
from . import auth
from flaskr.helpers import lookup, lookup_batch, most_active, news


bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/news')
@auth.login_required
def api_news():
    pass

@bp.route('/my-stocks')
@auth.login_required
def api_my_stocks():
    pass

@bp.route('/stocks')
@auth.login_required
def api_stocks():
    pass

@bp.route('/account')
@auth.login_required
def api_account():
    from .dash import account_details_only
    return jsonify(account_details_only(g.user))

@bp.route('/history')
@auth.login_required
def api_history():
    ''' return array of all transactions(trades) in descending order by date '''
    trades = query_db(
        'SELECT *, ROUND(qty::numeric * price::numeric, 2)::float AS total FROM trade WHERE person = %s ORDER BY created DESC;', (g.user.id, )
    )
    if trades is None:
        return []
    return jsonify([{
        'type': t.dir,
        'date': t.created,
        'symbol': t.symbol,
        'name': t.name,
        'qty': t.qty,
        'price': t.price,
        'total': t.total,
    } for t in trades])

