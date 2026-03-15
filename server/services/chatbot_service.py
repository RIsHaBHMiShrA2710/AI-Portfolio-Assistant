import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, Generator
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from services.memory_manager import memory_manager
from Tools.finance_tools import ALL_FINANCE_TOOLS
from Tools.portfolio_tools import ALL_PORTFOLIO_TOOLS, _get_latest_portfolio

load_dotenv()

class PortfolioChatbot:
    def __init__(self):
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.tools = ALL_FINANCE_TOOLS + ALL_PORTFOLIO_TOOLS
        
        # Build a human-readable name map from tool function names
        self.tool_name_map = {}
        for t in self.tools:
            func_name = t.name if hasattr(t, 'name') else str(t)
            # Convert snake_case to Title Case
            readable = func_name.replace('_', ' ').title()
            self.tool_name_map[func_name] = readable
        
        self.system_prompt = """You are a helpful Portfolio Assistant for an Indian stock market investor.
            PORTFOLIO DATA:
            {portfolio_context}

            GUIDELINES:
            - Always be helpful and provide actionable insights
            - Use tools to fetch live prices, news, or detailed analysis when needed
            - Reference specific holdings when relevant
            - Format numbers in Indian style (₹ and lakhs/crores)
            - If portfolio data shows 0% P&L, it may be due to market being closed

            RELEVANT PAST CONTEXT:
            {rag_context}

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
    
    def _build_messages(self, user_message: str, session_id: str):
        """Build the message list for the agent."""
        chat_history = memory_manager.get_history_for_context(session_id, last_n=6)
        portfolio_context = self._get_portfolio_context()
        
        rag_chunks = memory_manager.retrieve_similar(session_id, user_message, top_k=5)
        rag_context = "\n\n".join(rag_chunks) if rag_chunks else "No relevant past context."
        print(f"RAG chunks retrieved: {len(rag_chunks)}")
        
        formatted_system = self.system_prompt.format(
            portfolio_context=portfolio_context,
            rag_context=rag_context,
            chat_history=chat_history or "No previous conversation."
        )

        return [
            SystemMessage(content=formatted_system),
            HumanMessage(content=user_message)
        ]

    def chat(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        session_id = memory_manager.get_or_create_session(session_id)
        messages = self._build_messages(user_message, session_id)
        
        try:
            result = self.agent.invoke({"messages": messages})
            final_response = result["messages"][-1].content
            
            # Count tools used
            tools_used = []
            for msg in result["messages"]:
                if isinstance(msg, ToolMessage):
                    tool_name = msg.name if hasattr(msg, 'name') else "unknown_tool"
                    readable = self.tool_name_map.get(tool_name, tool_name.replace('_', ' ').title())
                    tools_used.append(readable)
            
            memory_manager.add_message(session_id, "user", user_message)
            memory_manager.add_message(session_id, "assistant", final_response)
            try:
                memory_manager.store_embedding(session_id, f"User: {user_message}\nAssistant: {final_response}")
                print(f"✅ Embedding stored for session: {session_id}")
            except Exception as embed_err:
                print(f"❌ store_embedding failed: {embed_err}")
            
            return {
                "response": final_response, 
                "session_id": session_id,
                "success": True,
                "tools_used": tools_used,
                "tool_count": len(tools_used)
            }
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "session_id": session_id,
                "success": False,
                "error": str(e)
            }
    
    def chat_stream(self, user_message: str, session_id: Optional[str] = None) -> Generator[str, None, None]:
        """Stream chat response with tool-call events via SSE."""
        session_id = memory_manager.get_or_create_session(session_id)
        messages = self._build_messages(user_message, session_id)
        
        tools_used = []
        final_response = ""
        
        try:
            for chunk in self.agent.stream({"messages": messages}, stream_mode="updates"):
                # Each chunk is a dict with node name as key
                for node_name, node_output in chunk.items():
                    if "messages" in node_output:
                        for msg in node_output["messages"]:
                            if isinstance(msg, ToolMessage):
                                tool_name = msg.name if hasattr(msg, 'name') else "unknown_tool"
                                readable = self.tool_name_map.get(tool_name, tool_name.replace('_', ' ').title())
                                tools_used.append(readable)
                                # Send tool event
                                yield f"data: {json.dumps({'event': 'tool', 'tool_name': readable})}\n\n"
                            
                            elif isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                                final_response = msg.content
            
            # Save to memory
            memory_manager.add_message(session_id, "user", user_message)
            memory_manager.add_message(session_id, "assistant", final_response)
            try:
                memory_manager.store_embedding(session_id, f"User: {user_message}\nAssistant: {final_response}")
                print(f"✅ Embedding stored for session: {session_id}")
            except Exception as embed_err:
                print(f"❌ store_embedding failed: {embed_err}")
            
            # Send final done event
            yield f"data: {json.dumps({'event': 'done', 'response': final_response, 'session_id': session_id, 'tools_used': tools_used, 'tool_count': len(tools_used)})}\n\n"
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            yield f"data: {json.dumps({'event': 'error', 'response': error_msg, 'session_id': session_id})}\n\n"
    
    def reset_session(self, session_id: str) -> bool:
        return memory_manager.clear_session(session_id)


chatbot = PortfolioChatbot()