import { useState, useMemo } from 'react';
import { ArrowUpDown, TrendingUp, TrendingDown } from 'lucide-react';
import './Dashboard.css';

export default function HoldingsTable({ holdings = [] }) {
    const [sortConfig, setSortConfig] = useState({ key: 'current_value', direction: 'desc' });
    const [searchTerm, setSearchTerm] = useState('');

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 2,
        }).format(value);
    };

    const sortedHoldings = useMemo(() => {
        let filtered = holdings.filter(h =>
            h.stock_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            h.ticker_symbol?.toLowerCase().includes(searchTerm.toLowerCase())
        );

        return [...filtered].sort((a, b) => {
            const aVal = a[sortConfig.key] ?? 0;
            const bVal = b[sortConfig.key] ?? 0;

            if (sortConfig.direction === 'asc') {
                return aVal > bVal ? 1 : -1;
            }
            return aVal < bVal ? 1 : -1;
        });
    }, [holdings, sortConfig, searchTerm]);

    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
        }));
    };

    if (!holdings.length) {
        return <div className="no-data">No holdings data available</div>;
    }

    return (
        <div className="holdings-table-container">
            <div className="table-header">
                <h3>Holdings</h3>
                <input
                    type="text"
                    placeholder="Search stocks..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input"
                />
            </div>

            <div className="table-wrapper">
                <table className="holdings-table">
                    <thead>
                        <tr>
                            <th onClick={() => handleSort('stock_name')}>
                                Stock <ArrowUpDown size={14} />
                            </th>
                            <th onClick={() => handleSort('quantity')}>
                                Qty <ArrowUpDown size={14} />
                            </th>
                            <th onClick={() => handleSort('avg_buy_price')}>
                                Avg Price <ArrowUpDown size={14} />
                            </th>
                            <th onClick={() => handleSort('current_price')}>
                                LTP <ArrowUpDown size={14} />
                            </th>
                            <th onClick={() => handleSort('invested_value')}>
                                Invested <ArrowUpDown size={14} />
                            </th>
                            <th onClick={() => handleSort('current_value')}>
                                Current <ArrowUpDown size={14} />
                            </th>
                            <th onClick={() => handleSort('pnl_percentage')}>
                                P&L % <ArrowUpDown size={14} />
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedHoldings.map((holding, index) => {
                            const isProfit = (holding.pnl_percentage || 0) >= 0;
                            return (
                                <tr key={index}>
                                    <td className="stock-cell">
                                        <span className="ticker">{holding.ticker_symbol || 'N/A'}</span>
                                        <span className="name">{holding.stock_name?.substring(0, 30) || 'Unknown'}</span>
                                    </td>
                                    <td>{holding.quantity || 0}</td>
                                    <td>{formatCurrency(holding.avg_buy_price || 0)}</td>
                                    <td>{formatCurrency(holding.current_price || 0)}</td>
                                    <td>{formatCurrency(holding.invested_value || 0)}</td>
                                    <td>{formatCurrency(holding.current_value || 0)}</td>
                                    <td className={isProfit ? 'profit' : 'loss'}>
                                        <span className="pnl-cell">
                                            {isProfit ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                            {(holding.pnl_percentage || 0).toFixed(2)}%
                                        </span>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
