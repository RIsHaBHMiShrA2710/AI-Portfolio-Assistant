import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from services.memory_manager import memory_manager
from Tools.finance_tools import ALL_FINANCE_TOOLS
from Tools.portfolio_tools import ALL_PORTFOLIO_TOOLS, _get_latest_portfolio

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY",)
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT",)

if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print(f"🔍 LangSmith tracing enabled for project: {os.getenv('LANGSMITH_PROJECT', 'default')}")


class PortfolioChatbot:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.tools = ALL_FINANCE_TOOLS + ALL_PORTFOLIO_TOOLS
        
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
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
    
    def _process_tool_calls(self, ai_message) -> str:
        """Process tool calls from the AI response."""
        if not ai_message.tool_calls:
            return ai_message.content
        
        # Execute each tool call
        tool_results = []
        tool_map = {tool.name: tool for tool in self.tools}
        
        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name in tool_map:
                try:
                    result = tool_map[tool_name].invoke(tool_args)
                    tool_results.append(f"[{tool_name}]: {result}")
                except Exception as e:
                    tool_results.append(f"[{tool_name}]: Error - {str(e)}")
        
        if tool_results:
            tool_context = "\n".join(tool_results)
            follow_up = self.llm.invoke([
                SystemMessage(content="Based on the tool results below, provide a helpful response to the user."),
                HumanMessage(content=f"Tool Results:\n{tool_context}\n\nProvide a clear, formatted response.")
            ])
            return follow_up.content
        
        return ai_message.content
    
    def chat(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a chat message and return response.
        
        Args:
            user_message: The user's question or message
            session_id: Optional session ID for maintaining conversation
            
        Returns:
            Dict with response, session_id, and metadata
        """
        # Get or create session
        session_id = memory_manager.get_or_create_session(session_id)
        
        # Get chat history
        chat_history = memory_manager.get_history_for_context(session_id, last_n=10)
        
        # Get portfolio context
        portfolio_context = self._get_portfolio_context()
        
        # Format system prompt
        formatted_system = self.system_prompt.format(
            portfolio_context=portfolio_context,
            chat_history=chat_history if chat_history else "No previous conversation."
        )
        
        # Build messages
        messages = [
            SystemMessage(content=formatted_system),
            HumanMessage(content=user_message)
        ]
        
        try:
            # Get response from LLM with tools
            ai_response = self.llm_with_tools.invoke(messages)
            
            # Process any tool calls
            final_response = self._process_tool_calls(ai_response)
            
            # Save to memory
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
        """Reset a chat session."""
        return memory_manager.clear_session(session_id)


chatbot = PortfolioChatbot()
