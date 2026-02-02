from langchain.tools import tool
import json
from typing import Optional, Dict, List, Any
from pathlib import Path
import glob


def _get_latest_portfolio() -> Optional[Dict]:
    """Load the most recent portfolio JSON file."""
    portfolio_dir = Path(__file__).parent.parent
    files = list(portfolio_dir.glob("portfolio_analysis_*.json"))
    
    if not files:
        return None
    
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@tool
def get_portfolio_summary() -> str:
    """
    Get overall portfolio summary: total investment, current value, P&L, and key stats.
    Use this when user asks about portfolio overview, total value, or overall performance.
    """
    try:
        portfolio = _get_latest_portfolio()
        if not portfolio:
            return json.dumps({"error": "No portfolio data found"})
        
        holdings = portfolio.get('holdings', [])

        sorted_by_pnl = sorted(holdings, key=lambda x: x.get('pnl_percentage', 0), reverse=True)
        top_gainers = sorted_by_pnl[:3]
        top_losers = sorted_by_pnl[-3:]
        
        sectors = {}
        for h in holdings:
            sector = h.get('sector', 'Unknown')
            sectors[sector] = sectors.get(sector, 0) + h.get('current_value', 0)
        
        summary = {
            "total_holdings": len(holdings),
            "total_investment": f"₹{portfolio.get('total_investment', 0):,.2f}",
            "current_value": f"₹{portfolio.get('total_current_value', 0):,.2f}",
            "total_pnl": f"₹{portfolio.get('total_pnl', 0):+,.2f}",
            "total_pnl_percentage": f"{portfolio.get('total_pnl_percentage', 0):+.2f}%",
            "top_gainers": [
                {"name": h.get('stock_name', '')[:30], "pnl": f"{h.get('pnl_percentage', 0):+.2f}%"}
                for h in top_gainers if h.get('pnl_percentage', 0) > 0
            ],
            "top_losers": [
                {"name": h.get('stock_name', '')[:30], "pnl": f"{h.get('pnl_percentage', 0):+.2f}%"}
                for h in top_losers if h.get('pnl_percentage', 0) < 0
            ]
        }
        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_holding_details(stock_name: str) -> str:
    """
    Get detailed information about a specific stock in the portfolio.
    Use this when user asks about a specific stock they own.
    
    Args:
        stock_name: Stock name or ticker (e.g., 'HAL', 'HINDUSTAN AERONAUTICS', 'IRFC')
    """
    try:
        portfolio = _get_latest_portfolio()
        if not portfolio:
            return json.dumps({"error": "No portfolio data found"})
        
        search_term = stock_name.upper()
        holdings = portfolio.get('holdings', [])
        
        matching = []
        for h in holdings:
            ticker = h.get('ticker_symbol', '').upper()
            name = h.get('stock_name', '').upper()
            if search_term in ticker or search_term in name:
                matching.append(h)
        
        if not matching:
            return json.dumps({"error": f"No holding found matching '{stock_name}'"})
        
        results = []
        for h in matching:
            results.append({
                "stock_name": h.get('stock_name'),
                "ticker": h.get('ticker_symbol'),
                "sector": h.get('sector', 'N/A'),
                "quantity": h.get('quantity'),
                "avg_buy_price": f"₹{h.get('avg_buy_price', 0):,.2f}",
                "current_price": f"₹{h.get('current_price', 0):,.2f}",
                "invested_value": f"₹{h.get('invested_value', 0):,.2f}",
                "current_value": f"₹{h.get('current_value', 0):,.2f}",
                "pnl_absolute": f"₹{h.get('pnl_absolute', 0):+,.2f}",
                "pnl_percentage": f"{h.get('pnl_percentage', 0):+.2f}%"
            })
        
        return json.dumps(results[0] if len(results) == 1 else results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_sector_allocation() -> str:
    """
    Get portfolio breakdown by sector with allocation percentages.
    Use this when user asks about diversification or sector exposure.
    """
    try:
        portfolio = _get_latest_portfolio()
        if not portfolio:
            return json.dumps({"error": "No portfolio data found"})
        
        holdings = portfolio.get('holdings', [])
        total_value = portfolio.get('total_current_value', 0)
        
        sectors = {}
        for h in holdings:
            sector = h.get('sector', 'Unknown') or 'Unknown'
            current_value = h.get('current_value', 0)
            if sector not in sectors:
                sectors[sector] = {"value": 0, "stocks": []}
            sectors[sector]["value"] += current_value
            sectors[sector]["stocks"].append(h.get('ticker_symbol', 'N/A'))
        t
        allocation = []
        for sector, data in sectors.items():
            pct = (data["value"] / total_value * 100) if total_value > 0 else 0
            allocation.append({
                "sector": sector,
                "value": f"₹{data['value']:,.2f}",
                "allocation": f"{pct:.1f}%",
                "stocks": data["stocks"]
            })
        
        allocation.sort(key=lambda x: float(x["allocation"].replace('%', '')), reverse=True)
        
        return json.dumps({
            "total_portfolio_value": f"₹{total_value:,.2f}",
            "sector_breakdown": allocation
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_stocks_in_profit() -> str:
    """
    Get list of all stocks currently in profit.
    Use this when user asks which stocks are doing well or are profitable.
    """
    try:
        portfolio = _get_latest_portfolio()
        if not portfolio:
            return json.dumps({"error": "No portfolio data found"})
        
        holdings = portfolio.get('holdings', [])
        profitable = [h for h in holdings if h.get('pnl_percentage', 0) > 0]
        profitable.sort(key=lambda x: x.get('pnl_percentage', 0), reverse=True)
        
        result = []
        for h in profitable:
            result.append({
                "stock": h.get('ticker_symbol'),
                "name": h.get('stock_name', '')[:35],
                "pnl_percentage": f"{h.get('pnl_percentage', 0):+.2f}%",
                "pnl_absolute": f"₹{h.get('pnl_absolute', 0):+,.2f}"
            })
        
        return json.dumps({
            "count": len(result),
            "stocks_in_profit": result
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_stocks_in_loss() -> str:
    """
    Get list of all stocks currently in loss.
    Use this when user asks which stocks are losing money or underperforming.
    """
    try:
        portfolio = _get_latest_portfolio()
        if not portfolio:
            return json.dumps({"error": "No portfolio data found"})
        
        holdings = portfolio.get('holdings', [])
        losers = [h for h in holdings if h.get('pnl_percentage', 0) < 0]
        losers.sort(key=lambda x: x.get('pnl_percentage', 0))
        
        result = []
        for h in losers:
            result.append({
                "stock": h.get('ticker_symbol'),
                "name": h.get('stock_name', '')[:35],
                "pnl_percentage": f"{h.get('pnl_percentage', 0):+.2f}%",
                "pnl_absolute": f"₹{h.get('pnl_absolute', 0):+,.2f}"
            })
        
        return json.dumps({
            "count": len(result),
            "stocks_in_loss": result
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_largest_holdings() -> str:
    """
    Get the largest holdings by current value.
    Use this when user asks about biggest positions or where most money is invested.
    """
    try:
        portfolio = _get_latest_portfolio()
        if not portfolio:
            return json.dumps({"error": "No portfolio data found"})
        
        holdings = portfolio.get('holdings', [])
        total_value = portfolio.get('total_current_value', 0)
        
        # Sort by current value
        sorted_holdings = sorted(holdings, key=lambda x: x.get('current_value', 0), reverse=True)
        top_10 = sorted_holdings[:10]
        
        result = []
        for h in top_10:
            value = h.get('current_value', 0)
            pct = (value / total_value * 100) if total_value > 0 else 0
            result.append({
                "stock": h.get('ticker_symbol'),
                "name": h.get('stock_name', '')[:30],
                "current_value": f"₹{value:,.2f}",
                "portfolio_weight": f"{pct:.1f}%"
            })
        
        return json.dumps({
            "top_holdings": result
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

ALL_PORTFOLIO_TOOLS = [
    get_portfolio_summary, ## working
    get_holding_details, ## working
    get_sector_allocation, ## Not working currently
    get_stocks_in_profit, ## working
    get_stocks_in_loss, ## working
    get_largest_holdings ## working
]
