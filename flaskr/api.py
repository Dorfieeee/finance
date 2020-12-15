from flask import (
    Blueprint, flash, g, redirect, render_template, request, session,
    url_for, jsonify, make_response
)

from flaskr.db import get_db
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
    pass

@bp.route('/history')
@auth.login_required
def api_history():
    ''' return array of all transactions(trades) in descending order by date '''
    db = get_db()
    trades = db.execute(
        'SELECT *, ROUND(qty * price, 2) AS total FROM trade WHERE user = ? ORDER BY created DESC;', (g.user['id'], )
    ).fetchall()
    if trades is None:
        return []
    return jsonify([{
        'type': t['dir'],
        'date': t['created'],
        'symbol': t['symbol'],
        'name': t['name'],
        'qty': t['qty'],
        'price': t['price'],
        'total': t['total'],
    } for t in trades])

def account_details(user):
    blocked_funds = 0
    live_result = 0
    updated_stocks = None

    # Get all user's currently owned stocks
    owned_stocks = currently_owned_stocks(user['id'])

    if owned_stocks is not None:
        # Obtain price sum of owned stocks
        blocked_funds = sum([s['qt'] * s['avgPrice'] for s in owned_stocks])
        # Update stocks with current prices
        updated_stocks = update_stocks(owned_stocks)
        # Total result of opened trades
        live_result = sum([s['result'] for s in updated_stocks])

    acc_balance = get_acc_balance(user['id'])
    balance = acc_balance + blocked_funds
    free_funds = balance - blocked_funds
    most_active_list = most_active()

    news_symbols = set([x['symbol'] for x in owned_stocks] + [x['symbol'] for x in most_active_list])
    news_list = news(news_symbols)

    return {'account': {
                'balance': round(balance, 2),
                'blockedFunds': round(blocked_funds, 2),
                'freeFunds': round(free_funds, 2),
                'liveResult': round(live_result, 2),
            },
            'stocks': updated_stocks,
            'mostActive': most_active_list,
            'news': news_list}

def get_acc_balance(user_id):
    db = get_db()
    return db.execute(
        'SELECT balance FROM account WHERE user = ?;', (user_id, )
    ).fetchone()[0]

def get_deposits(user_id):
    db = get_db()
    return db.execute(
        'SELECT * FROM deposit WHERE user = ?;', (user_id, )
    ).fetchall()

def currently_owned_stocks(user_id):
    ''' 
    Returns [{symbol, qt, avgPrice, sum}...] for all currently owned stocks
    symbol = stock symbol; qt = quantity per owned stock;
    avgPrice = average buying price per stock; sum = buying price sum per stock
    '''
    db = get_db()
    stocks = db.execute(
        'SELECT symbol, SUM(qty * dir * -1) AS qt, ROUND(AVG(price),2) AS avgPrice FROM trade WHERE user = ? GROUP BY symbol HAVING qt > 0;', (user_id, )
    ).fetchall()
    if stocks is None:
        return None
    return [dict(s) for s in stocks]

def update_stocks(stocks):
    # Reduce to 'symbol' list only
    symbols = [s['symbol'] for s in stocks]
    # API Call for all symbols quotes => [SYMBOL: {name, price, symbol},...]    
    quotes = lookup_batch(symbols)

    updated_stocks = []

    # Parse stocks, append other details
    for s in stocks:
        symbol = s['symbol']
        s['currentPrice'] = quotes[symbol]['price']
        s['name'] = quotes[symbol]['name']
        #s['change'] = round(s['currentPrice'] - s['avg_price'], 2)
        s['result'] = round((s['currentPrice'] - s['avgPrice']) * s['qt'], 2)
        s['total'] = round(s['avgPrice'] * s['qt'], 2)

        updated_stocks.append(s)

    return updated_stocks

    