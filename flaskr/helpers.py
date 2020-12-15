import os
import urllib
import requests
from flask import request

def lookup(symbol):
    """Look up quote for symbol."""
    
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()

        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None

def lookup_batch(symbols):
    """Look up batch of quotes for symbols."""

    try:
        if isinstance(symbols, str):
            symbols = [s.upper() for s in symbols.split(',')]
        else:
            symbols = [s.upper() for s in symbols]

        symbols_safe = ','.join([urllib.parse.quote_plus(symbol) for symbol in symbols])
        types = "quote"
    except TypeError:
        return None

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/market/batch?symbols={(symbols_safe)}&types={types}&token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quotes = response.json()
        obj = {}
        for symbol in symbols:
            obj[symbol] = {
            "name": quotes[symbol][types]["companyName"],
            "price": float(quotes[symbol][types]["latestPrice"]),
            "symbol": quotes[symbol][types]["symbol"]
        }
        return obj

    except (KeyError, TypeError, ValueError):
        return None

def most_active():
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/market/list/mostactive?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    quotes = response.json()
    return [{
        'symbol': q['symbol'],
        'name': q['companyName'],
        'price': q['latestPrice'],
        'change': q['change'],
        'logo': logo(q['symbol']),
    } for q in quotes]

def news(symbols):
    """Look up for the latest news(1) of each givem symbol"""
    try:
        if isinstance(symbols, str):
            symbols = [s.upper() for s in symbols.split(',')]
        else:
            symbols = [s.upper() for s in symbols]

        symbols_safe = ','.join([urllib.parse.quote_plus(symbol) for symbol in symbols])
        types = "news"
    except TypeError:
        return None

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/market/batch?symbols={(symbols_safe)}&types={types}&last=1&token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        news = response.json()        
    except (KeyError, TypeError, ValueError):
        return None

    dicts = [news[n]['news'] for n in news]
    list = []
    for d in dicts:
        if len(d):
            list.append(d[0])

    return list[:10]

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def logo(symbol):
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/logo?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        logo = response.json()

        return logo['url']
    except (KeyError, TypeError, ValueError):
        return None
    

# ONLY FOR PAID SUBSCRIPTION PLAN :-(
# def symbols_search(symbol):
#     '''Returns an array of symbols up to the top 10 matches'''
#     # Contact API
#     try:
#         api_key = os.environ.get("API_KEY")
#         response = requests.get(f"https://cloud.iexapis.com/stable/search/{urllib.parse.quote_plus(symbol)}?token={api_key}")
#         response.raise_for_status()
#     except requests.RequestException:
#         return None

#     # Parse response
#     try:
#         quotes = response.json()
#         return [q['symbol'] for q in quotes]
#     except (KeyError, TypeError, ValueError):
#         return None

