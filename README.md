# AI Portfolio Assistant

An AI-powered portfolio analyzer that extracts data from demat holdings PDFs, fetches real-time stock prices, calculates P&L, and provides an intelligent chatbot for investment insights.

## IMPORTANT TO NOTE ##: #This app currently has been tested with portfolio holding's pdf which you can download from your respective brokers. In future, I would like to add feature to parse multiple types of documents or directly connection with broker through api.# 

## Features

- 📊 **PDF Parsing**: Upload demat holdings PDF and automatically extract portfolio data
- 💰 **Real-time Prices**: Fetches latest stock prices from Yahoo Finance
- 📈 **P&L Analysis**: Calculates profit/loss for each holding and overall portfolio
- 🤖 **AI Chatbot**: Ask questions about your portfolio in natural language
- 📉 **Visual Dashboard**: Interactive charts for sector allocation and top gainers/losers
- 💾 **Session Persistence**: Chat history saved in PostgreSQL (optional)

## Tech Stack

### Frontend (React + Vite)
- React 18 with hooks
- Vite for fast development
- Recharts for data visualization
- Lucide React for icons

### Backend (FastAPI + Python)
- FastAPI for REST API
- LangChain + Groq for LLM integration
- yfinance for stock data
- SQLAlchemy + PostgreSQL for persistence

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL (optional)

### Backend Setup

```bash
cd server

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run server
uvicorn app:app --reload --port 8000
```

### Frontend Setup

```bash
cd client

# Install dependencies
npm install

# Run development server
npm run dev
```

### Environment Variables

See `server/.env.example` for required environment variables:
- `GROQ_API_KEY` - Get from [Groq Console](https://console.groq.com)
- `LANGCHAIN_API_KEY` - Get from [LangSmith](https://smith.langchain.com)
- `DATABASE_URL` - PostgreSQL connection string (optional)

## Usage

1. Open http://localhost:5173 in your browser
2. Upload your demat holdings PDF
3. View your portfolio dashboard with charts and tables
4. Use the chatbot to ask questions about your investments

## Screenshots

*Coming soon*

## License

MIT License
