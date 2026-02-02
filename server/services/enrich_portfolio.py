import time
import yfinance as yf
from typing import Optional, Tuple
from services.isin_resolver import get_yfinance_symbol


def get_latest_price(ticker: str, fallback_price: float = 0.0) -> Tuple[float, bool]:
    """
    Fetches the latest/last trading day price using yfinance.
    
    Args:
        ticker: NSE ticker symbol (with or without .NS suffix)
        fallback_price: Fallback price if fetch fails
        
    Returns:
        Tuple of (price, success_flag)
        - If successful: (current_price, True)
        - If failed: (fallback_price, False)
    """
    if not ticker or ticker == "UNKNOWN":
        return (fallback_price, False)
    
    # Get yfinance compatible symbol
    symbol = get_yfinance_symbol(ticker)
    
    try:
        stock = yf.Ticker(symbol)
        try:
            info = stock.info
            if info:
                for field in ['regularMarketPrice', 'currentPrice', 'previousClose']:
                    price = info.get(field)
                    if price and price > 0:
                        return (round(float(price), 2), True)
        except Exception:
            pass

        try:
            fast = stock.fast_info
            if fast:
                for attr in ['lastPrice', 'previousClose', 'regularMarketPrice']:
                    price = getattr(fast, attr, None) or fast.get(attr)
                    if price and price > 0:
                        return (round(float(price), 2), True)
        except Exception:
            pass

        try:
            hist = stock.history(period="5d")
            if not hist.empty and 'Close' in hist.columns:
                price = hist['Close'].iloc[-1]
                if price and price > 0:
                    return (round(float(price), 2), True)
        except Exception:
            pass
        
        if symbol.endswith(".NS"):
            bse_symbol = symbol.replace(".NS", ".BO")
            try:
                stock_bse = yf.Ticker(bse_symbol)
                hist_bse = stock_bse.history(period="5d")
                if not hist_bse.empty and 'Close' in hist_bse.columns:
                    price = hist_bse['Close'].iloc[-1]
                    if price and price > 0:
                        return (round(float(price), 2), True)
            except Exception:
                pass
                
    except Exception as e:
        print(f"⚠️ yfinance error for {symbol}: {str(e)[:50]}")
    
    return (fallback_price, False)


def enrich_portfolio(data: dict) -> dict:
    """
    Enriches portfolio with current prices and calculates P&L.
    
    Dynamically populates:
    - current_price: Latest market price (falls back to avg_buy_price if unavailable)
    - current_value: quantity * current_price 
    - pnl_absolute: current_value - invested_value
    - pnl_percentage: ((current_price - avg_buy_price) / avg_buy_price) * 100
    Args:
        data: Portfolio dict with holdings list
    Returns:
        Enriched portfolio with current prices and P&L calculations
    """
    holdings = data.get('holdings', [])
    total_investment = 0.0
    total_current_value = 0.0
    
    print(f"\n📈 Fetching latest prices for {len(holdings)} holdings...")
    
    success_count = 0
    fail_count = 0
    
    for item in holdings:
        ticker = item.get('ticker_symbol', '')
        quantity = float(item.get('quantity', 0))
        avg_buy_price = float(item.get('avg_buy_price', 0) or item.get('buy_price', 0))
        invested_value = float(item.get('invested_value', 0))
        if invested_value == 0:
            invested_value = quantity * avg_buy_price
        
        total_investment += invested_value
        current_price, fetch_success = get_latest_price(ticker, avg_buy_price)
        current_value = quantity * current_price
        total_current_value += current_value
        pnl_absolute = current_value - invested_value
        pnl_percentage = ((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0.0
        
        item['current_price'] = round(current_price, 2)
        item['current_value'] = round(current_value, 2)
        item['invested_value'] = round(invested_value, 2)
        item['pnl_absolute'] = round(pnl_absolute, 2)
        item['pnl_percentage'] = round(pnl_percentage, 2)
        
        if fetch_success:
            indicator = "🟢" if pnl_percentage >= 0 else "🔴"
            print(f"{indicator} {ticker:15} ₹{current_price:>10,.2f} ({pnl_percentage:+.2f}%)")
            success_count += 1
        else:
           
            print(f"  ⚪ {ticker:15} ₹{current_price:>10,.2f} (using buy price)")
            fail_count += 1
        time.sleep(0.5)
    
    total_pnl = total_current_value - total_investment
    total_pnl_percentage = ((total_current_value - total_investment) / total_investment * 100) if total_investment > 0 else 0.0
    
    data['total_investment'] = round(total_investment, 2)
    data['total_current_value'] = round(total_current_value, 2)
    data['total_pnl'] = round(total_pnl, 2)
    data['total_pnl_percentage'] = round(total_pnl_percentage, 2)
    
    print(f"\n📊 Price fetch complete: {success_count} succeeded, {fail_count} failed")
    
    return data