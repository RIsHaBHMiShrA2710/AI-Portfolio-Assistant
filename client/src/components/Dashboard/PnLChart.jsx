import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './Dashboard.css';

export default function PnLChart({ holdings = [] }) {
    const pnlData = useMemo(() => {
        return holdings
            .filter(h => h.pnl_percentage !== 0)
            .map(h => ({
                name: h.ticker_symbol || 'N/A',
                pnl: h.pnl_percentage || 0,
                value: h.pnl_absolute || 0,
            }))
            .sort((a, b) => b.pnl - a.pnl)
            .slice(0, 8);
    }, [holdings]);

    const formatCurrency = (value) => {
        if (Math.abs(value) >= 100000) {
            return `₹${(value / 100000).toFixed(1)}L`;
        }
        return `₹${value.toFixed(0)}`;
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="chart-tooltip">
                    <p className="tooltip-label">{data.name}</p>
                    <p className={`tooltip-value ${data.pnl >= 0 ? 'profit' : 'loss'}`}>
                        {data.pnl >= 0 ? '+' : ''}{data.pnl.toFixed(2)}%
                    </p>
                    <p className="tooltip-percentage">{formatCurrency(data.value)}</p>
                </div>
            );
        }
        return null;
    };

    if (!pnlData.length) {
        return (
            <div className="chart-card">
                <h3>Top Performers</h3>
                <div className="no-data">No P&L data available</div>
            </div>
        );
    }

    return (
        <div className="chart-card">
            <h3>Top Performers</h3>
            <ResponsiveContainer width="100%" height={200}>
                <BarChart data={pnlData} layout="vertical" margin={{ left: 50, right: 20 }}>
                    <XAxis type="number" tickFormatter={(v) => `${v}%`} fontSize={11} />
                    <YAxis type="category" dataKey="name" width={45} fontSize={11} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                        {pnlData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={entry.pnl >= 0 ? '#10b981' : '#ef4444'}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
