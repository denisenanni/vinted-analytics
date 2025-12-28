import type { LookupResponse } from '../api/client';

interface ResultsCardProps {
  data: LookupResponse;
}

export function ResultsCard({ data }: ResultsCardProps) {
  const demandColor = {
    high: '#22c55e',
    medium: '#eab308',
    low: '#ef4444',
    unknown: '#6b7280',
  }[data.demand_score] || '#6b7280';

  return (
    <div className="results-card">
      <div className="stats-grid">
        <div className="stat-box">
          <span className="stat-label">Total Items</span>
          <span className="stat-value">{data.total_items}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Avg Price</span>
          <span className="stat-value">€{data.avg_price.toFixed(2)}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Price Range</span>
          <span className="stat-value">{data.price_range}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Demand</span>
          <span className="stat-value" style={{ color: demandColor }}>
            {data.demand_score.toUpperCase()}
          </span>
        </div>
      </div>

      {data.best_markets.length > 0 && (
        <div className="best-markets">
          <h3>Best Markets</h3>
          <div className="markets-list">
            {data.best_markets.slice(0, 5).map((m) => (
              <div key={m.market} className="market-item">
                <span className="market-code">{m.market}</span>
                <span className="market-stats">
                  {m.count} items · €{m.avg_price.toFixed(2)} avg
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
