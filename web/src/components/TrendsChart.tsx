import type { TrendsResponse } from '../api/client';

interface TrendsChartProps {
  data: TrendsResponse;
}

export function TrendsChart({ data }: TrendsChartProps) {
  return (
    <div className="trends-chart">
      <div className="chart-header">
        <h3>Trending Items</h3>
        <span className="chart-subtitle">
          {data.market} · {data.categories?.join(', ') || 'All'} · Last {data.period} · Sorted by favorites
        </span>
      </div>

      <div className="chart-stats">
        <div className="chart-stat">
          <span className="chart-stat-value">{data.total_items}</span>
          <span className="chart-stat-label">Total Items</span>
        </div>
        <div className="chart-stat">
          <span className="chart-stat-value">€{(data.avg_price ?? 0).toFixed(2)}</span>
          <span className="chart-stat-label">Avg Price</span>
        </div>
      </div>

      {data.trending_items?.length > 0 ? (
        <div className="items-grid">
          {data.trending_items.map((item) => (
            <a
              key={item.vinted_id}
              href={item.url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="item-card"
            >
              {item.image_url && (
                <img src={item.image_url} alt={item.title} className="item-image" />
              )}
              <div className="item-info">
                <span className="item-title">{item.title}</span>
                <span className="item-brand">{item.brand || item.title}</span>
                <div className="item-meta">
                  <span className="item-price">€{item.price.toFixed(2)}</span>
                  <span className="item-market">{item.market}</span>
                  <span className="item-favorites">♥ {item.favorites}</span>
                </div>
              </div>
            </a>
          ))}
        </div>
      ) : (
        <p className="no-data">No trending items available</p>
      )}
    </div>
  );
}
