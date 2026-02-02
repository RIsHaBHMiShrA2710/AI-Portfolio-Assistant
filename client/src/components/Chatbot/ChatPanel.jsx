import { useState, useEffect, useRef } from 'react';
import { Send, Plus, Trash2, Loader2, MessageSquare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { sendMessage, getSessions, createSession, getSessionMessages, deleteSession } from '../../services/api';
import './ChatPanel.css';

export default function ChatPanel() {
    const [sessions, setSessions] = useState([]);
    const [currentSession, setCurrentSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showSidebar, setShowSidebar] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadSessions();
    }, []);

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }, [messages]);

    const loadSessions = async () => {
        try {
            const data = await getSessions();
            setSessions(data);
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    };

    const loadSessionMessages = async (sessionId) => {
        try {
            const data = await getSessionMessages(sessionId);
            setMessages(data.messages || []);
            setCurrentSession(sessionId);
            setShowSidebar(false);
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    };

    const handleNewChat = async () => {
        try {
            const data = await createSession();
            setCurrentSession(data.session_id);
            setMessages([]);
            setShowSidebar(false);
            loadSessions();
        } catch (error) {
            console.error('Failed to create session:', error);
        }
    };

    const handleDeleteSession = async (sessionId, e) => {
        e.stopPropagation();
        try {
            await deleteSession(sessionId);
            if (currentSession === sessionId) {
                setCurrentSession(null);
                setMessages([]);
            }
            loadSessions();
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const response = await sendMessage(userMessage, currentSession);

            if (!currentSession) {
                setCurrentSession(response.session_id);
                loadSessions();
            }

            setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className="chat-container">
            {/* Header */}
            <div className="chat-header">
                <button className="sidebar-toggle" onClick={() => setShowSidebar(!showSidebar)}>
                    <MessageSquare size={18} />
                </button>
                <h2>Portfolio Assistant</h2>
                <button className="new-chat-btn" onClick={handleNewChat}>
                    <Plus size={18} />
                </button>
            </div>

            {/* Sidebar */}
            {showSidebar && (
                <div className="chat-sidebar">
                    <div className="sidebar-header">Chat History</div>
                    <div className="sessions-list">
                        {sessions.length === 0 ? (
                            <div className="no-sessions">No previous chats</div>
                        ) : (
                            sessions.map(session => (
                                <div
                                    key={session.id}
                                    className={`session-item ${currentSession === session.id ? 'active' : ''}`}
                                    onClick={() => loadSessionMessages(session.id)}
                                >
                                    <span className="session-title">{session.title}</span>
                                    <button
                                        className="delete-btn"
                                        onClick={(e) => handleDeleteSession(session.id, e)}
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Messages */}
            <div className="chat-messages">
                {messages.length === 0 ? (
                    <div className="welcome">
                        <h3>👋 Hello!</h3>
                        <p>I'm your portfolio assistant. Ask me anything about your investments!</p>
                        <div className="suggestions">
                            <button onClick={() => setInputValue("What's my portfolio summary?")}>
                                Portfolio summary
                            </button>
                            <button onClick={() => setInputValue("Which stocks are in profit?")}>
                                Stocks in profit
                            </button>
                            <button onClick={() => setInputValue("Analyze my sector allocation")}>
                                Sector analysis
                            </button>
                        </div>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className={`message ${msg.role}`}>
                            <div className="message-content">
                                {msg.role === 'assistant' ? (
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                ) : (
                                    msg.content
                                )}
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="message assistant">
                        <div className="message-content loading">
                            <Loader2 className="spinning" size={16} />
                            Thinking...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="chat-input">
                <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about your portfolio..."
                    rows={1}
                />
                <button
                    className="send-btn"
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || isLoading}
                >
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
}
