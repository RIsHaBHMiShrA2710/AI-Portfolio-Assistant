import { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import './Dashboard.css';

const COLORS = [
    '#FA8112', '#E06B00', '#C2884E', '#A0522D', '#D97706',
    '#F59E0B', '#B45309', '#92400E', '#78350F', '#D4A76A',
    '#E8B960', '#C49A3C', '#8B6914', '#6D5A00', '#A67C52',
];

export default function SectorChart({ holdings = [] }) {
    const sectorData = useMemo(() => {
        const sectors = {};

        holdings.forEach(h => {
            const sector = h.sector || 'Unknown';
            const value = h.current_value || 0;
            sectors[sector] = (sectors[sector] || 0) + value;
        });

        return Object.entries(sectors)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 8); // Limit to top 8 sectors
    }, [holdings]);

    const totalValue = sectorData.reduce((sum, s) => sum + s.value, 0);

    const formatCurrency = (value) => {
        if (value >= 100000) {
            return `₹${(value / 100000).toFixed(1)}L`;
        }
        return `₹${value.toFixed(0)}`;
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            const percentage = ((data.value / totalValue) * 100).toFixed(1);
            return (
                <div className="chart-tooltip">
                    <p className="tooltip-label">{data.name}</p>
                    <p className="tooltip-value">{formatCurrency(data.value)}</p>
                    <p className="tooltip-percentage">{percentage}% of portfolio</p>
                </div>
            );
        }
        return null;
    };

    if (!holdings.length) {
        return (
            <div className="chart-card">
                <h3>Sector Allocation</h3>
                <div className="no-data">No sector data available</div>
            </div>
        );
    }

    return (
        <div className="chart-card">
            <h3>Sector Allocation</h3>
            <div className="chart-content">
                <div className="pie-container">
                    <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                            <Pie
                                data={sectorData}
                                cx="50%"
                                cy="50%"
                                innerRadius={50}
                                outerRadius={80}
                                paddingAngle={2}
                                dataKey="value"
                            >
                                {sectorData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip content={<CustomTooltip />} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
                <div className="legend-container">
                    {sectorData.map((item, index) => (
                        <div key={index} className="legend-item">
                            <span
                                className="legend-color"
                                style={{ backgroundColor: COLORS[index % COLORS.length] }}
                            />
                            <span className="legend-label">{item.name}</span>
                            <span className="legend-value">
                                {((item.value / totalValue) * 100).toFixed(0)}%
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
