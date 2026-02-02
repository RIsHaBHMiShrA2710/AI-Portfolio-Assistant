import { TrendingUp, TrendingDown, Wallet, PiggyBank, BarChart3 } from 'lucide-react';
import './Dashboard.css';

export default function PortfolioSummary({ portfolio }) {
    if (!portfolio) return null;

    const {
        total_investment = 0,
        total_current_value = 0,
        total_pnl = 0,
        total_pnl_percentage = 0,
        holdings = []
    } = portfolio;

    const isProfit = total_pnl >= 0;

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(value);
    };

    return (
        <div className="summary-cards">
            <div className="summary-card">
                <div className="card-icon invested">
                    <Wallet size={24} />
                </div>
                <div className="card-content">
                    <span className="card-label">Total Invested</span>
                    <span className="card-value">{formatCurrency(total_investment)}</span>
                </div>
            </div>

            <div className="summary-card">
                <div className="card-icon current">
                    <PiggyBank size={24} />
                </div>
                <div className="card-content">
                    <span className="card-label">Current Value</span>
                    <span className="card-value">{formatCurrency(total_current_value)}</span>
                </div>
            </div>

            <div className={`summary-card ${isProfit ? 'profit' : 'loss'}`}>
                <div className={`card-icon ${isProfit ? 'profit' : 'loss'}`}>
                    {isProfit ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
                </div>
                <div className="card-content">
                    <span className="card-label">Total P&L</span>
                    <span className={`card-value ${isProfit ? 'profit' : 'loss'}`}>
                        {formatCurrency(total_pnl)}
                        <span className="pnl-percentage">
                            ({total_pnl_percentage >= 0 ? '+' : ''}{total_pnl_percentage.toFixed(2)}%)
                        </span>
                    </span>
                </div>
            </div>

            <div className="summary-card">
                <div className="card-icon holdings">
                    <BarChart3 size={24} />
                </div>
                <div className="card-content">
                    <span className="card-label">Holdings</span>
                    <span className="card-value">{holdings.length}</span>
                </div>
            </div>
        </div>
    );
}
