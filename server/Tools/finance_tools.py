"""
Finance Tools for Portfolio Q&A Chatbot
Enhanced tools for stock analysis, portfolio insights, and market data.
"""
from langchain.tools import tool
import yfinance as yf
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
import json
import numpy as np
from typing import Optional

_news_tool = YahooFinanceNewsTool()

@tool
def get_company_profile(ticker: str) -> str:
    """
    Get company profile including name, sector, industry, and business summary.
    Use this when user asks about what a company does or its background.
    
    Args:
        ticker: NSE stock ticker (e.g., 'RELIANCE', 'TCS', 'INFY')
    """
    try:
        symbol = f"{ticker.upper().replace('.NS', '')}.NS"
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info or 'longName' not in info:
            return json.dumps({"error": f"No data found for {ticker}"})
        
        summary = info.get("longBusinessSummary", "")
        profile = {
            "name": info.get("longName"),
            "ticker": ticker.upper(),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "summary": summary[:300] + "..." if len(summary) > 300 else summary
        }
        return json.dumps(profile, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_key_financial_metrics(ticker: str) -> str:
    """
    Get key financial metrics: P/E ratio, ROE, Debt-to-Equity, EPS, and Dividend Yield.
    Use this for fundamental analysis or valuation questions.
    
    Args:
        ticker: NSE stock ticker (e.g., 'RELIANCE', 'TCS')
    """
    try:
        symbol = f"{ticker.upper().replace('.NS', '')}.NS"
        stock = yf.Ticker(symbol)
        info = stock.info
        
        metrics = {
            "ticker": ticker.upper(),
            "trailing_pe": round(info.get("trailingPE", 0) or 0, 2),
            "forward_pe": round(info.get("forwardPE", 0) or 0, 2),
            "price_to_book": round(info.get("priceToBook", 0) or 0, 2),
            "roe": f"{round((info.get('returnOnEquity', 0) or 0) * 100, 2)}%",
            "debt_to_equity": round(info.get("debtToEquity", 0) or 0, 2),
            "eps": round(info.get("trailingEps", 0) or 0, 2),
            "dividend_yield": f"{round((info.get('dividendYield', 0) or 0) * 100, 2)}%",
            "revenue_growth": f"{round((info.get('revenueGrowth', 0) or 0) * 100, 2)}%"
        }
        return json.dumps(metrics, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def get_technical_analysis(ticker: str) -> str:
    """
    Get technical analysis: current price, 50/200-day moving averages, RSI, and trend status.
    Use this for technical analysis or price trend questions.
    
    Args:
        ticker: NSE stock ticker (e.g., 'HAL', 'IRFC')
    """
    try:
        symbol = f"{ticker.upper().replace('.NS', '')}.NS"
        hist = yf.Ticker(symbol).history(period="1y")
        
        if hist.empty:
            return json.dumps({"error": f"No historical data found for {ticker}"})
        
        # Calculate indicators
        close = hist['Close']
        current_price = close.iloc[-1]
        ma_50 = close.rolling(window=50).mean().iloc[-1]
        ma_200 = close.rolling(window=200).mean().iloc[-1]
        
        # RSI calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))
        
        # 52-week high/low
        high_52w = close.max()
        low_52w = close.min()
        
        # Trend determination
        if ma_50 > ma_200:
            trend = "Bullish (Golden Cross)"
        else:
            trend = "Bearish (Death Cross)"
        
        return json.dumps({
            "ticker": ticker.upper(),
            "current_price": round(current_price, 2),
            "MA_50": round(ma_50, 2),
            "MA_200": round(ma_200, 2),
            "RSI": round(rsi, 2),
            "52_week_high": round(high_52w, 2),
            "52_week_low": round(low_52w, 2),
            "trend": trend,
            "rsi_signal": "Overbought" if rsi > 70 else ("Oversold" if rsi < 30 else "Neutral")
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def calculate_risk_metrics(ticker: str) -> str:
    """
    Calculate risk metrics: Beta (vs Nifty 50), annualized volatility, and Sharpe ratio.
    Use this for risk assessment questions.
    
    Args:
        ticker: NSE stock ticker (e.g., 'RELIANCE', 'TCS')
    """
    try:
        symbol = f"{ticker.upper().replace('.NS', '')}.NS"
        
        stock = yf.Ticker(symbol)
        nifty = yf.Ticker("^NSEI")
        
        stock_hist = stock.history(period="1y")
        nifty_hist = nifty.history(period="1y")
        
        if stock_hist.empty or nifty_hist.empty:
            return json.dumps({"error": "Unable to fetch historical data"})
        
        stock_returns = stock_hist['Close'].pct_change().dropna()
        nifty_returns = nifty_hist['Close'].pct_change().dropna()
        
        common_dates = stock_returns.index.intersection(nifty_returns.index)
        stock_returns = stock_returns[common_dates]
        nifty_returns = nifty_returns[common_dates]
        
        covariance = np.cov(stock_returns, nifty_returns)[0][1]
        market_variance = np.var(nifty_returns)
        beta = covariance / market_variance if market_variance > 0 else 0
        
        volatility = stock_returns.std() * np.sqrt(252) * 100
        
        annual_return = ((stock_hist['Close'].iloc[-1] / stock_hist['Close'].iloc[0]) - 1) * 100
        risk_free_rate = 6.0
        sharpe = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        if beta < 0.8:
            risk_level = "Low (Defensive)"
        elif beta < 1.2:
            risk_level = "Moderate"
        else:
            risk_level = "High (Aggressive)"
        
        return json.dumps({
            "ticker": ticker.upper(),
            "beta": round(beta, 2),
            "annualized_volatility": f"{round(volatility, 2)}%",
            "annual_return": f"{round(annual_return, 2)}%",
            "sharpe_ratio": round(sharpe, 2),
            "risk_level": risk_level
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def get_stock_news(ticker: str) -> str:
    """
    Get latest news for a stock ticker.
    Use this when user asks about news, updates, or recent developments.
    
    Args:
        ticker: Stock ticker (e.g., 'RELIANCE', 'TCS', 'HAL')
    """
    try:
        result = _news_tool.run(ticker.upper())
        return result if result else f"No recent news found for {ticker}"
    except Exception as e:
        return f"Unable to fetch news: {str(e)}"


@tool
def compare_stocks(ticker1: str, ticker2: str) -> str:
    """
    Compare two stocks on key metrics: price, P/E, market cap, and returns.
    Use this when user wants to compare holdings or make investment decisions.
    
    Args:
        ticker1: First stock ticker (e.g., 'IRFC')
        ticker2: Second stock ticker (e.g., 'IREDA')
    """
    try:
        def get_metrics(ticker: str):
            symbol = f"{ticker.upper().replace('.NS', '')}.NS"
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="1y")
            
            annual_return = 0
            if not hist.empty:
                annual_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
            
            return {
                "name": info.get("longName", ticker),
                "current_price": round(info.get("regularMarketPrice", 0) or 0, 2),
                "pe_ratio": round(info.get("trailingPE", 0) or 0, 2),
                "market_cap_cr": round((info.get("marketCap", 0) or 0) / 1e7, 0),
                "52w_return": f"{round(annual_return, 2)}%",
                "dividend_yield": f"{round((info.get('dividendYield', 0) or 0) * 100, 2)}%"
            }
        
        stock1_metrics = get_metrics(ticker1)
        stock2_metrics = get_metrics(ticker2)
        
        return json.dumps({
            ticker1.upper(): stock1_metrics,
            ticker2.upper(): stock2_metrics
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool  
def get_current_price(ticker: str) -> str:
    """
    Get the current/latest price of a stock.
    Use this for simple price queries.
    
    Args:
        ticker: NSE stock ticker (e.g., 'HAL', 'IRFC', 'RELIANCE')
    """
    try:
        symbol = f"{ticker.upper().replace('.NS', '')}.NS"
        stock = yf.Ticker(symbol)
        info = stock.info
        
        price = info.get("regularMarketPrice") or info.get("previousClose", 0)
        change = info.get("regularMarketChange", 0) or 0
        change_pct = info.get("regularMarketChangePercent", 0) or 0
        
        return json.dumps({
            "ticker": ticker.upper(),
            "price": round(price, 2),
            "change": round(change, 2),
            "change_percent": f"{round(change_pct, 2)}%",
            "day_high": round(info.get("dayHigh", 0) or 0, 2),
            "day_low": round(info.get("dayLow", 0) or 0, 2)
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

ALL_FINANCE_TOOLS = [
    get_company_profile, ## working
    get_key_financial_metrics, ##working
    get_technical_analysis, ##working
    calculate_risk_metrics,
    get_stock_news, ## notworking
    compare_stocks,
    get_current_price
]
