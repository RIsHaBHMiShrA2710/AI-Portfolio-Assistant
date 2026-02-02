import { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Plus, Trash2, Loader2 } from 'lucide-react';
import { sendMessage, getSessions, createSession, getSessionMessages, deleteSession } from '../../services/api';
import './Chatbot.css';

export default function FloatingChat() {
    const [isOpen, setIsOpen] = useState(false);
    const [sessions, setSessions] = useState([]);
    const [currentSession, setCurrentSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showSessions, setShowSessions] = useState(false);
    const messagesEndRef = useRef(null);

    // Load sessions on mount
    useEffect(() => {
        loadSessions();
    }, []);

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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
            setShowSessions(false);
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    };

    const handleNewChat = async () => {
        try {
            const data = await createSession();
            setCurrentSession(data.session_id);
            setMessages([]);
            setShowSessions(false);
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

        // Add user message immediately
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const response = await sendMessage(userMessage, currentSession);

            // Update session ID if new
            if (!currentSession) {
                setCurrentSession(response.session_id);
                loadSessions();
            }

            // Add assistant response
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
        <>
            {/* Floating Button */}
            <button
                className={`chat-fab ${isOpen ? 'hidden' : ''}`}
                onClick={() => setIsOpen(true)}
            >
                <MessageCircle size={24} />
            </button>

            {/* Chat Window */}
            <div className={`chat-window ${isOpen ? 'open' : ''}`}>
                {/* Header */}
                <div className="chat-header">
                    <div className="header-left">
                        <button
                            className="sessions-btn"
                            onClick={() => setShowSessions(!showSessions)}
                            title="Chat history"
                        >
                            ☰
                        </button>
                        <h3>Portfolio Assistant</h3>
                    </div>
                    <div className="header-right">
                        <button className="new-chat-btn" onClick={handleNewChat} title="New chat">
                            <Plus size={18} />
                        </button>
                        <button className="close-btn" onClick={() => setIsOpen(false)}>
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {/* Sessions Panel */}
                {showSessions && (
                    <div className="sessions-panel">
                        <div className="sessions-header">
                            <span>Chat History</span>
                        </div>
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
                                            className="delete-session"
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
                        <div className="welcome-message">
                            <h4>👋 Hello!</h4>
                            <p>I'm your portfolio assistant. Ask me anything about your investments!</p>
                            <div className="suggestions">
                                <button onClick={() => setInputValue("What's my portfolio summary?")}>
                                    Portfolio summary
                                </button>
                                <button onClick={() => setInputValue("Which stocks are in profit?")}>
                                    Stocks in profit
                                </button>
                                <button onClick={() => setInputValue("Show me sector allocation")}>
                                    Sector allocation
                                </button>
                            </div>
                        </div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div key={idx} className={`message ${msg.role}`}>
                                <div className="message-content">
                                    {msg.content}
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
        </>
    );
}
