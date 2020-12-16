from flask import (
    Blueprint, flash, g, redirect, render_template, request, session,
    url_for, jsonify, make_response
)

from flaskr.db import get_db, query_db
from . import auth
from flaskr.helpers import lookup, lookup_batch, most_active, news, logo


bp = Blueprint('dashboard', __name__, url_prefix='/')

@bp.route('/')
def dashboard():
    if g.user is None:
        return render_template('index.html')

    return render_template('dashboard.html')

@bp.route('/search')
@auth.login_required
def search():
    return render_template('search.html')

@bp.route('/update')
@auth.login_required
def update():
    return jsonify(account_details(g.user))

@bp.route('/buy', methods=('POST', 'GET' ))
@auth.login_required
def buy():
    symbol = request.args['symbol']
    qty = request.args['qty']
    error = None

    try:
        qty = int(qty)
    except TypeError:
        error = "Quantity must be a numeric value(int)."

    if qty <= 0:
        error = "Quantity must be an positive integer."

    stock = lookup(symbol)
    if stock is None:
        error = f"Stock with symbol {symbol.upper()} was not found."

    if not error:
        account = account_details(g.user)['account']
        total_price = stock["price"] * qty

        if total_price <= account["freeFunds"]:
            buy_stock(g.user, stock, qty)
            return {'msg': f"Purchase was successfull. You've just bought {qty}x {symbol} for total of ${round(total_price, 2)}."}
        
        error = "Not sufficient funds for this purchase. You must sell some shares or top up your account."

    return jsonify({'error': error}), 400

@bp.route('/sell', methods=('POST', 'GET'))
@auth.login_required
def sell():
    symbol = request.args.get('symbol')
    qty = request.args.get('qty')

    if not symbol or not qty:
        return {'error': "Missing arguments."}, 400

    symbol = symbol.upper()

    try:
        qty = int(qty)
    except TypeError:
        return {'error': "Quantity must be an positive integer."}, 400

    trade = query_db(
        'SELECT *, SUM(qty * dir * -1) AS qt FROM trade WHERE person = %s AND symbol = %s GROUP BY trade.id, symbol;', (g.user.id, symbol)
    , one=True)

    if not trade:
        return {'error': 'Trade does not exists'}, 400
    elif qty == 0:
        return {'error': "Quantity must be higher than 0."}, 400
    elif qty > trade.qt:
        return {'error': "Trying to sell higher quantity then owned."}, 400
    elif trade.person != g.user.id:
        return {'error': "Unauthorized access."}, 403

    stock = lookup(symbol)
    sell_stock(g.user, stock, qty)

    return {'msg': f"Transaction successfull. You sold {qty}x of {stock['symbol']} for total of ${round(stock['price'] * qty, 2)}"}

@bp.route('/quote', methods=('GET', ))
@auth.login_required
def quote():
    symbol = request.args.get('symbol')
    if symbol is None:
        return {"error": f"Missing symbol argument."}, 400
    # Single quote
    q = lookup(symbol)
    # ONLY FOR PAID SUBSCRIPTION PLAN :-(
    # if q is None:
    #     # If not found, make search for up to 10 most similar symbols 
    #     s = symbols_search(symbol)
    #     # Batch lookup
    #     q = lookup_batch(s)
    # Return error if no results for both queries
    if q is None:
        return {"error": f"No results found for {symbol}."}, 404
    # Add quote img
    q['image'] = logo(symbol)
    # Return quote object
    return jsonify(q)

@bp.route('/history', methods=('GET', ))
@auth.login_required
def history():
    return render_template('history.html')

def account_details(user):
    blocked_funds = 0
    live_result = 0
    updated_stocks = None

    # Get all user's currently owned stocks
    owned_stocks = currently_owned_stocks(user.id)

    if owned_stocks is not None:
        # Obtain price sum of owned stocks
        blocked_funds = sum([s.qt * s.avgprice for s in owned_stocks])
        # Update stocks with current prices
        updated_stocks = update_stocks(owned_stocks)
        # Total result of opened trades
        live_result = sum([s['result'] for s in updated_stocks])

    acc_balance = get_acc_balance(user.id)
    balance = acc_balance + blocked_funds
    free_funds = balance - blocked_funds
    most_active_list = most_active()

    news_symbols = set([x.symbol for x in owned_stocks] + [x['symbol'] for x in most_active_list])
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
    return query_db(
        'SELECT balance FROM account WHERE person = %s;', (user_id, )
    , one=True)[0]

def get_deposits(user_id):
    return query_db(
        'SELECT * FROM deposit WHERE person = %s;', (user_id, )
    )

def currently_owned_stocks(user_id):
    ''' 
    Returns [{symbol, qt, avgPrice, sum}...] for all currently owned stocks
    symbol = stock symbol; qt = quantity per owned stock;
    avgPrice = average buying price per stock; sum = buying price sum per stock
    '''
    stocks = query_db(
        'SELECT symbol, SUM(qty * dir * -1) AS qt, ROUND(AVG(price::numeric),2)::float AS avgprice FROM trade WHERE person = %s GROUP BY symbol HAVING SUM(qty * dir * -1) > 0;', (user_id, )
    )
    if stocks is None:
        return None
    return stocks

def update_stocks(stocks):
    # Reduce to 'symbol' list only
    symbols = [s.symbol for s in stocks]
    # API Call for all symbols quotes => [SYMBOL: {name, price, symbol},...]    
    quotes = lookup_batch(symbols)

    updated_stocks = []

    # Parse stocks, append other details
    for s in stocks:
        s = s._asdict()
        symbol = s['symbol']
        s['currentprice'] = quotes[symbol]['price']
        s['name'] = quotes[symbol]['name']
        s['result'] = round((s['currentprice'] - s['avgprice']) * s['qt'], 2)
        s['total'] = round(s['avgprice'] * s['qt'], 2)

        updated_stocks.append(s)

    return updated_stocks

def buy_stock(user, stock, qty): 
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO trade (person, price, qty, name, symbol, dir) VALUES (%s, %s, %s, %s, %s, %s)',
        (user.id, stock["price"], qty, stock["name"], stock["symbol"], -1)
    )
    db_cursor.execute(
        'UPDATE account SET balance = balance - %s WHERE person = %s;', 
        (stock["price"] * qty, user.id)
    )
    db_cursor.close()
    db.commit()

def sell_stock(user, stock, qty): 
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO trade (person, price, qty, name, symbol, dir) VALUES (%s, %s, %s, %s, %s, %s)',
        (user.id, stock["price"], qty, stock["name"], stock["symbol"], 1)
    )
    db_cursor.execute(
        'UPDATE account SET balance = balance + %s WHERE person = %s;', 
        (stock["price"] * qty, user.id)
    )
    db_cursor.close()
    db.commit()

def account_details_only(user):
    blocked_funds = 0
    live_result = 0
    updated_stocks = None

    # Get all user's currently owned stocks
    owned_stocks = currently_owned_stocks(user.id)

    if owned_stocks is not None:
        # Obtain price sum of owned stocks
        blocked_funds = sum([s.qt * s.avgprice for s in owned_stocks])
        # Update stocks with current prices
        updated_stocks = update_stocks(owned_stocks)
        # Total result of opened trades
        live_result = sum([s['result'] for s in updated_stocks])

    acc_balance = get_acc_balance(user.id)
    balance = acc_balance + blocked_funds
    free_funds = balance - blocked_funds

    return {
            'balance': round(balance, 2),
            'blockedFunds': round(blocked_funds, 2),
            'freeFunds': round(free_funds, 2),
            'liveResult': round(live_result, 2),
            }