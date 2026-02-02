import json
from pathlib import Path
from typing import Optional, Dict

# Load ISIN mapping at module level for efficiency
_ISIN_MAPPING: Dict[str, str] = {}
_MAPPING_LOADED = False

TICKER_FIXES = {
    "ART": "ANANDRATHI",
    "BARODA": "BANKBARODA",
    "BOB": "BANKBARODA",
    "CANB": "CANBK",
    "JFS": "JIOFIN",
    "JIOFINANCE": "JIOFIN",
    "ONE97": "PAYTM",
    "LIC": "LICI",
    "BHSL": "BAJAJHIND",
    "BFIL": "BALUFORGE",
    "AZE": "AZAD",
    "ETNL": "ETERNAL",
    "MOFSL": "MOTILALOFS",
    "NSDL": "NSDL",  
    "ARATHI": "ANANDRATHI",
}

ETF_MAPPING = {
    "INF247L01DJ0": "MODEFENCE.NS",  
    "INF247L01EV3": "MOCAPITAL.NS",  
    "INF204KB17I5": "GOLDBEES.NS",   
    "INF204KC1402": "SILVERBEES.NS", 
}


def _load_isin_mapping() -> Dict[str, str]:
    """Load ISIN mapping from JSON file."""
    global _ISIN_MAPPING, _MAPPING_LOADED
    
    if _MAPPING_LOADED:
        return _ISIN_MAPPING
    
    mapping_path = Path(__file__).parent.parent / "isin_mapping.json"
    
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            _ISIN_MAPPING = json.load(f)
            _MAPPING_LOADED = True
            print(f"📂 Loaded {len(_ISIN_MAPPING)} ISIN mappings")
    except Exception as e:
        print(f"⚠️ Failed to load ISIN mapping: {e}")
        _ISIN_MAPPING = {}
        _MAPPING_LOADED = True
        
    return _ISIN_MAPPING


def resolve_ticker(isin: Optional[str] = None, ticker_hint: Optional[str] = None) -> Optional[str]:
    """
    Resolve ISIN or ticker hint to a valid NSE ticker symbol.
    
    Priority:
    1. If ISIN is an ETF/MF, use ETF_MAPPING (returns full symbol with .NS)
    2. If ISIN is a stock, use isin_mapping.json
    3. Apply TICKER_FIXES for common LLM mistakes
    4. Return ticker_hint as-is if nothing else matches
    
    Returns:
        NSE ticker symbol (without .NS suffix for stocks, with .NS for ETFs)
    """
    mapping = _load_isin_mapping()
    
    if isin and isin in ETF_MAPPING:
        return ETF_MAPPING[isin]
    
    if isin and isin in mapping:
        return mapping[isin]
    
    if ticker_hint:
        clean_hint = ticker_hint.strip().upper().replace(".NS", "").replace(".BO", "")
        if clean_hint in TICKER_FIXES:
            return TICKER_FIXES[clean_hint]
        return clean_hint
    
    return None


def get_yfinance_symbol(ticker: str) -> str:
    """
    Convert a ticker to yfinance format.
    Adds .NS suffix for NSE stocks if not already present.
    """
    if not ticker:
        return ""
    
    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        return ticker
    
    return f"{ticker}.NS"
