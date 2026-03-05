import { useState, useEffect, useRef, useCallback } from 'react';
import { LayoutDashboard, MessageCircle } from 'lucide-react';
import PDFUpload from './components/Upload/PDFUpload';
import PortfolioSummary from './components/Dashboard/PortfolioSummary';
import HoldingsTable from './components/Dashboard/HoldingsTable';
import SectorChart from './components/Dashboard/SectorChart';
import PnLChart from './components/Dashboard/PnLChart';
import ChatPanel from './components/Chatbot/ChatPanel';
import { getPortfolio } from './services/api';
import './App.css';

const MIN_DASHBOARD_WIDTH = 480;
const MIN_CHAT_WIDTH = 400;

function App() {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Resizable panel state
  const [chatWidth, setChatWidth] = useState(420);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);
  const dashboardRef = useRef(null);

  useEffect(() => {
    loadPortfolio();
  }, []);

  // Scroll dashboard to top when portfolio loads
  useEffect(() => {
    if (portfolio && dashboardRef.current) {
      dashboardRef.current.scrollTop = 0;
    }
  }, [portfolio]);

  // Drag handlers for resizer
  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e) => {
      if (!containerRef.current) return;
      const containerRect = containerRef.current.getBoundingClientRect();
      const containerWidth = containerRect.width;
      const mouseX = e.clientX - containerRect.left;
      const newChatWidth = containerWidth - mouseX;

      // Enforce min widths
      const maxChatWidth = containerWidth - MIN_DASHBOARD_WIDTH;
      const clampedChatWidth = Math.max(MIN_CHAT_WIDTH, Math.min(maxChatWidth, newChatWidth));
      setChatWidth(clampedChatWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    // Prevent text selection while dragging
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isDragging]);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const data = await getPortfolio();
      setPortfolio(data);
    } catch (err) {
      setPortfolio(null);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = (data) => {
    setPortfolio(data);
  };

  // Loading state
  if (loading) {
    return (
      <div className="app loading-screen">
        <div className="loader"></div>
        <p>Loading portfolio...</p>
      </div>
    );
  }

  // No portfolio - show upload screen
  if (!portfolio) {
    return (
      <div className="app upload-screen">
        <div className="upload-container">
          <div className="upload-header">
            <span className="logo-icon">📊</span>
            <h1>Portfolio Analyzer</h1>
            <p>AI-Powered Investment Insights</p>
          </div>
          <PDFUpload onUploadSuccess={handleUploadSuccess} />
          <p className="upload-hint">Upload your demat holdings PDF to get started</p>
        </div>
      </div>
    );
  }

  // Portfolio loaded - show dashboard with chat
  return (
    <div className="app main-layout" ref={containerRef}>
      {/* Left Panel - Dashboard */}
      <div className={`dashboard-panel ${activeTab === 'dashboard' ? 'active-tab' : ''}`}>
        <header className="dashboard-header">
          <div className="header-left">
            <span className="logo-icon">📊</span>
            <h1>Portfolio Analyzer</h1>
          </div>
          <button className="refresh-btn" onClick={loadPortfolio}>
            ↻ Refresh
          </button>
        </header>

        <div className="dashboard-content" ref={dashboardRef}>
          {/* Summary Cards */}
          <PortfolioSummary portfolio={portfolio} />

          {/* Charts Row */}
          <div className="charts-row">
            <SectorChart holdings={portfolio.holdings} />
            <PnLChart holdings={portfolio.holdings} />
          </div>

          {/* Holdings Table */}
          <HoldingsTable holdings={portfolio.holdings} />

          {/* Update Portfolio */}
          <div className="update-section">
            <h3>Update Portfolio</h3>
            <PDFUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        </div>
      </div>

      {/* Draggable Resizer (desktop only) */}
      <div
        className="panel-resizer"
        onMouseDown={handleMouseDown}
      >
        <div className="resizer-handle" />
      </div>

      {/* Right Panel - Chat */}
      <div
        className={`chat-panel ${activeTab === 'chat' ? 'active-tab' : ''}`}
        style={{ width: chatWidth, minWidth: MIN_CHAT_WIDTH }}
      >
        <ChatPanel />
      </div>

      {/* Mobile Tab Bar */}
      <div className="mobile-tab-bar">
        <div className="tab-buttons">
          <button
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard />
            <span>Dashboard</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageCircle />
            <span>Chat</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
