import { useState } from 'react';
import {
  getTimingInsights,
  type TimingInsightsResponse,
} from '../api/client';

const MARKET_OPTIONS = [
  { code: 'IT', name: '🇮🇹 Italy' },
  { code: 'FR', name: '🇫🇷 France' },
  { code: 'DE', name: '🇩🇪 Germany' },
  { code: 'ES', name: '🇪🇸 Spain' },
  { code: 'NL', name: '🇳🇱 Netherlands' },
  { code: 'PL', name: '🇵🇱 Poland' },
  { code: 'BE', name: '🇧🇪 Belgium' },
  { code: 'AT', name: '🇦🇹 Austria' },
  { code: 'PT', name: '🇵🇹 Portugal' },
];

function formatCategoryName(category: string): string {
  const name = category.split('/').pop() || category;
  return name
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function TimingInsights() {
  const [market, setMarket] = useState('IT');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<TimingInsightsResponse | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getTimingInsights(market);
      setResults(response.data);
    } catch (err) {
      setError('Failed to load timing insights. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const maxSales = results?.day_breakdown
    ? Math.max(...results.day_breakdown.map((d) => d.sales))
    : 0;

  return (
    <div className="timing-insights">
      <div className="ti-header">
        <h2>Timing Insights</h2>
        <p>Find the best day to list and see what's trending</p>
      </div>

      <div className="ti-controls">
        <div className="ti-field">
          <label>Market</label>
          <select value={market} onChange={(e) => setMarket(e.target.value)}>
            {MARKET_OPTIONS.map((m) => (
              <option key={m.code} value={m.code}>
                {m.name}
              </option>
            ))}
          </select>
        </div>

        <button
          className="ti-analyze-btn"
          onClick={handleAnalyze}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {error && <div className="ti-error">{error}</div>}

      {results && (
        <div className="ti-results">
          {results.best_day ? (
            <>
              {/* Best Day Banner */}
              <div className="ti-best-day">
                <div className="best-day-icon">📅</div>
                <div className="best-day-content">
                  <h3>Best Day to List</h3>
                  <p className="best-day-name">{results.best_day}</p>
                  <span className="best-day-note">
                    Based on {results.total_sales_analyzed} sales
                  </span>
                </div>
              </div>

              {/* Day Breakdown Chart */}
              <div className="ti-section">
                <h3>Sales by Day of Week</h3>
                <div className="day-chart">
                  {results.day_breakdown.map((day) => (
                    <div key={day.day} className="day-bar-container">
                      <div className="day-label">{day.day.slice(0, 3)}</div>
                      <div className="day-bar-wrapper">
                        <div
                          className={`day-bar ${day.day === results.best_day ? 'best' : ''}`}
                          style={{
                            height: `${maxSales > 0 ? (day.sales / maxSales) * 100 : 0}%`,
                          }}
                        />
                      </div>
                      <div className="day-value">{day.sales}</div>
                      <div className="day-pct">{day.percentage}%</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Trending Categories */}
              <div className="ti-trends-grid">
                {/* Trending Up */}
                <div className="ti-section trending-up">
                  <h3>🔥 Trending Up</h3>
                  {results.trending_up.length > 0 ? (
                    <div className="trend-list">
                      {results.trending_up.map((trend) => (
                        <div key={trend.category} className="trend-item up">
                          <span className="trend-category">
                            {formatCategoryName(trend.category)}
                          </span>
                          <span className="trend-change">
                            +{trend.change_percent}%
                          </span>
                          <span className="trend-counts">
                            {trend.last_week} → {trend.this_week}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="no-trends">No significant upward trends</p>
                  )}
                </div>

                {/* Trending Down */}
                <div className="ti-section trending-down">
                  <h3>📉 Trending Down</h3>
                  {results.trending_down.length > 0 ? (
                    <div className="trend-list">
                      {results.trending_down.map((trend) => (
                        <div key={trend.category} className="trend-item down">
                          <span className="trend-category">
                            {formatCategoryName(trend.category)}
                          </span>
                          <span className="trend-change">
                            {trend.change_percent}%
                          </span>
                          <span className="trend-counts">
                            {trend.last_week} → {trend.this_week}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="no-trends">No significant downward trends</p>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="ti-no-data">
              <p>{results.message || 'Not enough sales data to analyze timing patterns.'}</p>
              <p>Try selecting a different market or wait for more data.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
