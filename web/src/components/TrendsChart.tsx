import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { TrendsResponse } from '../api/client';

interface TrendsChartProps {
  data: TrendsResponse;
}

const COLORS = ['#8b5cf6', '#6366f1', '#3b82f6', '#0ea5e9', '#06b6d4', '#14b8a6', '#22c55e', '#84cc16', '#eab308', '#f97316'];

export function TrendsChart({ data }: TrendsChartProps) {
  const chartData = data.trending_brands.slice(0, 10).map((brand) => ({
    name: brand.brand.length > 12 ? brand.brand.slice(0, 12) + '...' : brand.brand,
    count: brand.count,
    avgPrice: brand.avg_price,
  }));

  return (
    <div className="trends-chart">
      <div className="chart-header">
        <h3>Trending Brands</h3>
        <span className="chart-subtitle">
          {data.market} · {data.category} · Last {data.period}
        </span>
      </div>

      <div className="chart-stats">
        <div className="chart-stat">
          <span className="chart-stat-value">{data.total_items}</span>
          <span className="chart-stat-label">Total Items</span>
        </div>
        <div className="chart-stat">
          <span className="chart-stat-value">€{data.avg_price.toFixed(2)}</span>
          <span className="chart-stat-label">Avg Price</span>
        </div>
      </div>

      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
            <XAxis type="number" />
            <YAxis type="category" dataKey="name" width={100} />
            <Tooltip
              formatter={(value, name) => {
                const numValue = Number(value) || 0;
                return [
                  name === 'count' ? `${numValue} items` : `€${numValue.toFixed(2)}`,
                  name === 'count' ? 'Items' : 'Avg Price',
                ];
              }}
            />
            <Bar dataKey="count" name="count">
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <p className="no-data">No trend data available</p>
      )}
    </div>
  );
}
