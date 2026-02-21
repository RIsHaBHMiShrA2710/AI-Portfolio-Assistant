import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from services.memory_manager import memory_manager
from Tools.finance_tools import ALL_FINANCE_TOOLS
from Tools.portfolio_tools import ALL_PORTFOLIO_TOOLS, _get_latest_portfolio

load_dotenv()

class PortfolioChatbot:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.tools = ALL_FINANCE_TOOLS + ALL_PORTFOLIO_TOOLS
        
        self.system_prompt = """You are a helpful Portfolio Assistant for an Indian stock market investor.
            PORTFOLIO DATA:
            {portfolio_context}

            GUIDELINES:
            - Always be helpful and provide actionable insights
            - Use tools to fetch live prices, news, or detailed analysis when needed
            - Reference specific holdings when relevant
            - Format numbers in Indian style (₹ and lakhs/crores)
            - If portfolio data shows 0% P&L, it may be due to market being closed

            RECENT CONVERSATION:
            {chat_history}
        """
        
        # Agent is created once; system prompt is injected per-call
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
        )
    
    def _get_portfolio_context(self) -> str:
        """Load and format portfolio data for context."""
        portfolio = _get_latest_portfolio()
        if not portfolio:
            return "No portfolio data available."
        
        holdings = portfolio.get('holdings', [])
        summary_lines = [
            f"Total Investment: ₹{portfolio.get('total_investment', 0):,.2f}",
            f"Current Value: ₹{portfolio.get('total_current_value', 0):,.2f}",
            f"Total P&L: ₹{portfolio.get('total_pnl', 0):+,.2f} ({portfolio.get('total_pnl_percentage', 0):+.2f}%)",
            f"Number of Holdings: {len(holdings)}",
            "",
            "Holdings Summary:"
        ]
        for h in holdings:
            line = f"- {h.get('ticker_symbol', 'N/A')}: {h.get('quantity')} shares @ ₹{h.get('avg_buy_price', 0):.2f}, P&L: {h.get('pnl_percentage', 0):+.2f}%"
            summary_lines.append(line)
        
        return "\n".join(summary_lines)
    
    def chat(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        session_id = memory_manager.get_or_create_session(session_id)
        chat_history = memory_manager.get_history_for_context(session_id, last_n=10)
        portfolio_context = self._get_portfolio_context()

        formatted_system = self.system_prompt.format(
            portfolio_context=portfolio_context,
            chat_history=chat_history or "No previous conversation."
        )

        # Build message list — agent handles the tool loop internally
        messages = [
            SystemMessage(content=formatted_system),
            HumanMessage(content=user_message)
        ]
        
        try:
            # Agent runs the ReAct loop: Reason → Act (tool call) → Observe → repeat until done
            result = self.agent.invoke({"messages": messages})
            
            # Final response is always the last AIMessage
            final_response = result["messages"][-1].content
            
            memory_manager.add_message(session_id, "user", user_message)
            memory_manager.add_message(session_id, "assistant", final_response)
            
            return {
                "response": final_response,
                "session_id": session_id,
                "success": True
            }
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "session_id": session_id,
                "success": False,
                "error": str(e)
            }
    
    def reset_session(self, session_id: str) -> bool:
        return memory_manager.clear_session(session_id)


chatbot = PortfolioChatbot()