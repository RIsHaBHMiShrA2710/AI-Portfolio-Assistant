import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from services.llmservice import get_groq_llama_3_8b
from services.enrich_portfolio import enrich_portfolio
from services.isin_resolver import resolve_ticker, get_yfinance_symbol
from typing import List, Optional

load_dotenv()

os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
llm = get_groq_llama_3_8b()


class Holding(BaseModel):
    """A single stock or ETF holding."""
    stock_name: str = Field(description="Full company/fund name as shown in the statement")
    isin: str = Field(default="", description="ISIN code like INE... or INF...")
    quantity: float = Field(description="Number of shares/units held")
    avg_buy_price: float = Field(description="Average purchase price per share")
    # These will be filled later by enrichment
    ticker_symbol: str = Field(default="", description="NSE ticker symbol")
    sector: str = Field(default="", description="Industry sector")
    invested_value: float = Field(default=0.0)
    current_price: float = Field(default=0.0)
    current_value: float = Field(default=0.0)
    pnl_absolute: float = Field(default=0.0)
    pnl_percentage: float = Field(default=0.0)


class Portfolio(BaseModel):
    """A collection of stock holdings extracted from a demat statement."""
    holdings: List[Holding]


def parse_holdings(file_path: Optional[str] = None):
    """
    Parse holdings from PDF, resolve ISIN to ticker, and enrich with current prices.
    """
    if file_path is None:
        file_path = "D:\\Rishabh Mishra\\Projects\\GEN_AI\\OnDemandNews\\server\\Tools\\Portfolio_Holdings.pdf"
    
    print(f"📄 Loading PDF from: {file_path}")
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    structured_llm = llm.with_structured_output(Portfolio)

    system_prompt = """You are a specialized financial data extractor for Indian Demat statements.

TASK: Extract all holdings from the provided statement.

CRITICAL RULES:
1. Extract the ISIN code (starts with INE or INF) for EVERY holding. This is mandatory.
2. Keep the full stock_name exactly as shown in the statement.
3. Extract the quantity (number of shares/units).
4. Extract the average buy price (Avg Unit Cost).
5. Leave ticker_symbol EMPTY - it will be resolved later using ISIN.
6. Extract sector, current_price, current_value, pnl_absolute (Unrealized P&L).
7. Return ONLY the tool call. No conversational text.

Example extraction:
- stock_name: "HINDUSTAN AERONAUTICS LIMITED"
- isin: "INE066F01020"
- quantity: 27
- avg_buy_price: 3740.59
- ticker_symbol: "" (leave empty)
- sector: "Engineering"
- invested_value: 100995.84
- current_price: 0
- current_value:  0
- pnl_absolute: 0
- pnl_percentage: 0
"""
    
    full_text = "\n".join([doc.page_content for doc in docs])
    
    try:
        result = structured_llm.invoke(f"{system_prompt}\n\nStatement Content:\n{full_text}")
        raw_portfolio = result.model_dump()
    except Exception as e:
        print(f"❌ LLM parsing failed: {e}")
        return None

    holdings = raw_portfolio.get('holdings', [])
    print(f"\n Resolving {len(holdings)} ISIN codes to tickers...")
    
    for holding in holdings:
        isin = holding.get('isin', '')
        ticker_hint = holding.get('ticker_symbol', '')
        
        resolved_ticker = resolve_ticker(isin=isin, ticker_hint=ticker_hint)
        
        if resolved_ticker:
            holding['ticker_symbol'] = resolved_ticker
            print(f"  ✅ {isin[:12] if isin else 'N/A':15} → {resolved_ticker}")
        else:
            print(f"  ⚠️ {isin[:12] if isin else 'N/A':15} → UNRESOLVED (using hint: {ticker_hint})")
            holding['ticker_symbol'] = ticker_hint if ticker_hint else 'UNKNOWN'

    final_portfolio = enrich_portfolio(raw_portfolio)
    return final_portfolio
