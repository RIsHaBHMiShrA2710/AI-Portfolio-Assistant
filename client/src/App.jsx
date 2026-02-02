import { useState, useEffect, useRef } from 'react';
import PDFUpload from './components/Upload/PDFUpload';
import PortfolioSummary from './components/Dashboard/PortfolioSummary';
import HoldingsTable from './components/Dashboard/HoldingsTable';
import SectorChart from './components/Dashboard/SectorChart';
import PnLChart from './components/Dashboard/PnLChart';
import ChatPanel from './components/Chatbot/ChatPanel';
import { getPortfolio } from './services/api';
import './App.css';

function App() {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
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
    <div className="app main-layout">
      {/* Left Panel - Dashboard */}
      <div className="dashboard-panel">
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

      {/* Right Panel - Chat */}
      <div className="chat-panel">
        <ChatPanel />
      </div>
    </div>
  );
}

export default App;
