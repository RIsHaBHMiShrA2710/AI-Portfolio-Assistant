import { useState, useEffect, useRef } from 'react';
import { Send, Plus, Trash2, Loader2, MessageSquare, Wrench, Zap, LogOut } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { GoogleLogin, googleLogout } from '@react-oauth/google';
import { sendMessageStream, getSessions, createSession, getSessionMessages, deleteSession, authGoogle } from '../../services/api';
import './ChatPanel.css';

export default function ChatPanel() {
    const [sessions, setSessions] = useState([]);
    const [currentSession, setCurrentSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showSidebar, setShowSidebar] = useState(false);
    const [activeTools, setActiveTools] = useState([]);

    // Auth state
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [freeChatsUsed, setFreeChatsUsed] = useState(0);

    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadSessions();
        const storedAuth = localStorage.getItem('isAuthenticated') === 'true';
        setIsAuthenticated(storedAuth);
        if (storedAuth) {
            const userData = localStorage.getItem('user');
            if (userData) setUser(JSON.parse(userData));
        }
        const usedChats = parseInt(localStorage.getItem('freeChatsUsed') || '0', 10);
        setFreeChatsUsed(usedChats);
    }, []);

    const handleLoginSuccess = async (credentialResponse) => {
        try {
            // Verify token with our backend
            const data = await authGoogle(credentialResponse.credential);

            setIsAuthenticated(true);
            setUser(data.user);
            localStorage.setItem('isAuthenticated', 'true');
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
        } catch (error) {
            console.error('Login failed', error);
        }
    };

    const handleLogout = () => {
        googleLogout();
        setIsAuthenticated(false);
        setUser(null);
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    };

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }, [messages, activeTools]);

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

        if (!isAuthenticated && freeChatsUsed >= 5) {
            return; // Chat locked
        }

        const userMessage = inputValue.trim();

        if (!isAuthenticated) {
            const newCount = freeChatsUsed + 1;
            setFreeChatsUsed(newCount);
            localStorage.setItem('freeChatsUsed', newCount.toString());
        }

        setInputValue('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);
        setActiveTools([]);

        try {
            await sendMessageStream(
                userMessage,
                currentSession,
                // onToolCall
                (toolName) => {
                    setActiveTools(prev => [...prev, toolName]);
                },
                // onComplete
                (response, toolsUsed, sessionId) => {
                    if (!currentSession) {
                        setCurrentSession(sessionId);
                        loadSessions();
                    }
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: response,
                        toolsUsed: toolsUsed,
                        toolCount: toolsUsed.length
                    }]);
                    setActiveTools([]);
                    setIsLoading(false);
                },
                // onError
                (errorMsg) => {
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: errorMsg || 'Sorry, I encountered an error. Please try again.'
                    }]);
                    setActiveTools([]);
                    setIsLoading(false);
                }
            );
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            }]);
            setActiveTools([]);
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const isLocked = !isAuthenticated && freeChatsUsed >= 5;

    return (
        <div className="chat-container">
            {/* Header */}
            <div className="chat-header">
                <button className="sidebar-toggle" onClick={() => setShowSidebar(!showSidebar)}>
                    <MessageSquare size={18} />
                </button>
                <h2>Portfolio Assistant</h2>
                <div className="header-actions">
                    {isAuthenticated ? (
                        <div className="user-profile">
                            <span className="user-name">{user?.name}</span>
                            <button className="logout-btn" onClick={handleLogout} title="Sign Out">
                                <LogOut size={16} />
                            </button>
                        </div>
                    ) : (
                        <div className="auth-btn-container">
                            <GoogleLogin
                                onSuccess={handleLoginSuccess}
                                onError={() => console.log('Login Failed')}
                                shape="pill"
                                size="small"
                                text="signin"
                            />
                        </div>
                    )}
                    <button className="new-chat-btn" onClick={handleNewChat}>
                        <Plus size={18} />
                    </button>
                </div>
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
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                                ) : (
                                    msg.content
                                )}
                            </div>
                            {/* Tools summary badge */}
                            {msg.role === 'assistant' && msg.toolCount > 0 && (
                                <div className="tools-summary">
                                    <Wrench />
                                    {msg.toolCount} tool{msg.toolCount !== 1 ? 's' : ''} used
                                </div>
                            )}
                        </div>
                    ))
                )}

                {/* Live tool progress */}
                {isLoading && (
                    <div className="message assistant">
                        <div className="tool-progress">
                            <div className="tool-progress-header">
                                <Loader2 className="spinning" size={16} />
                                {activeTools.length > 0
                                    ? 'Using tools...'
                                    : 'Thinking...'}
                            </div>
                            {activeTools.length > 0 && (
                                <div className="tool-chips">
                                    {activeTools.map((tool, idx) => (
                                        <span key={idx} className="tool-chip">
                                            <Zap className="chip-icon" />
                                            {tool}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className={`chat-input-wrapper ${isLocked ? 'locked' : ''}`}>
                {isLocked && (
                    <div className="locked-overlay">
                        <div className="locked-content">
                            <h3>Free Limit Reached</h3>
                            <p>You've used your 5 free messages. Sign in to continue chatting.</p>
                            <GoogleLogin
                                onSuccess={handleLoginSuccess}
                                onError={() => console.log('Login Failed')}
                            />
                        </div>
                    </div>
                )}
                <div className="chat-input">
                    <textarea
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={isLocked ? "Sign in to continue..." : `Ask about your portfolio... ${!isAuthenticated ? `(${5 - freeChatsUsed} free left)` : ''}`}
                        rows={1}
                        disabled={isLocked || isLoading}
                    />
                    <button
                        className="send-btn"
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isLoading || isLocked}
                    >
                        <Send size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
}
