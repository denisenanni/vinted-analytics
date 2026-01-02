import { useState } from 'react';
import {
  getMarketProfitability,
  type MarketProfitabilityResponse,
  type CategoriesResponse,
  type SuggestedPrice,
} from '../api/client';

const MARKET_NAMES: Record<string, string> = {
  IT: '🇮🇹 Italy',
  FR: '🇫🇷 France',
  DE: '🇩🇪 Germany',
  ES: '🇪🇸 Spain',
  NL: '🇳🇱 Netherlands',
  PL: '🇵🇱 Poland',
  BE: '🇧🇪 Belgium',
  AT: '🇦🇹 Austria',
  PT: '🇵🇹 Portugal',
};

const CATEGORY_LABELS: Record<string, string> = {
  women_clothing: "Women's Clothing",
  women_shoes: "Women's Shoes",
  women_bags: "Women's Bags",
  women_accessories: "Women's Accessories",
  men_clothing: "Men's Clothing",
  men_shoes: "Men's Shoes",
  men_accessories: "Men's Accessories",
};

function formatCategoryName(category: string): string {
  const name = category.split('/').pop() || category;
  return name
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

interface Props {
  categories: CategoriesResponse | null;
}

export function WhereToSell({ categories }: Props) {
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [brand, setBrand] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<MarketProfitabilityResponse | null>(null);

  const handleAnalyze = async () => {
    if (!selectedCategory) {
      setError('Please select a category');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await getMarketProfitability(
        selectedCategory,
        brand || undefined
      );
      setResults(response.data);
    } catch (err) {
      setError('Failed to analyze markets. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 70) return '#22c55e';
    if (score >= 50) return '#eab308';
    if (score >= 30) return '#f97316';
    return '#ef4444';
  };

  const getCompetitionBadge = (level: string) => {
    const colors: Record<string, string> = {
      low: '#22c55e',
      medium: '#eab308',
      high: '#ef4444',
    };
    return (
      <span
        className="competition-badge"
        style={{ backgroundColor: colors[level] || '#6b7280' }}
      >
        {level}
      </span>
    );
  };

  const renderPriceGuide = (suggestedPrice: SuggestedPrice | null) => {
    if (!suggestedPrice) return null;

    return (
      <div className="price-guide">
        <div className="price-guide-header">Suggested Price</div>
        <div className="price-tiers">
          <div className="price-tier quick">
            <span className="tier-icon">💨</span>
            <span className="tier-label">Quick Sale</span>
            <span className="tier-range">
              €{suggestedPrice.quick_sale.min} - €{suggestedPrice.quick_sale.max}
            </span>
          </div>
          <div className="price-tier recommended">
            <span className="tier-icon">✨</span>
            <span className="tier-label">Recommended</span>
            <span className="tier-range">
              €{suggestedPrice.recommended.min} - €{suggestedPrice.recommended.max}
            </span>
          </div>
          <div className="price-tier premium">
            <span className="tier-icon">💎</span>
            <span className="tier-label">Premium</span>
            <span className="tier-range">
              €{suggestedPrice.premium.min} - €{suggestedPrice.premium.max}
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="where-to-sell">
      <div className="wts-header">
        <h2>Where Should I Sell?</h2>
        <p>Find the most profitable market and optimal price for your item</p>
      </div>

      <div className="wts-form">
        <div className="wts-field">
          <label>Category *</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">Select a category...</option>
            {categories &&
              Object.entries(categories.categories).map(([groupKey, cats]) => (
                <optgroup key={groupKey} label={CATEGORY_LABELS[groupKey]}>
                  {cats.map((cat) => (
                    <option key={cat} value={cat}>
                      {formatCategoryName(cat)}
                    </option>
                  ))}
                </optgroup>
              ))}
          </select>
        </div>

        <div className="wts-field">
          <label>Brand (optional)</label>
          <input
            type="text"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder="e.g., Zara, Nike, H&M"
          />
        </div>

        <button
          className="wts-analyze-btn"
          onClick={handleAnalyze}
          disabled={loading || !selectedCategory}
        >
          {loading ? 'Analyzing...' : 'Analyze Markets'}
        </button>
      </div>

      {error && <div className="wts-error">{error}</div>}

      {results && results.markets.length > 0 && (
        <div className="wts-results">
          <div className="wts-recommendation">
            <div className="rec-icon">🎯</div>
            <div className="rec-content">
              <h3>
                Sell in{' '}
                <strong>
                  {MARKET_NAMES[results.recommendation.best_market || ''] ||
                    results.recommendation.best_market}
                </strong>
                {results.recommendation.suggested_price && (
                  <span className="rec-price">
                    {' '}at €{results.recommendation.suggested_price.min} - €{results.recommendation.suggested_price.max}
                  </span>
                )}
              </h3>
              <p>{results.recommendation.reason}</p>
            </div>
            {results.recommendation.score && (
              <div
                className="rec-score"
                style={{
                  backgroundColor: getScoreColor(results.recommendation.score),
                }}
              >
                {results.recommendation.score}
              </div>
            )}
          </div>

          <div className="wts-markets-grid">
            {results.markets.map((market, index) => (
              <div
                key={market.market}
                className={`wts-market-card ${index === 0 ? 'best' : ''}`}
              >
                <div className="market-header">
                  <span className="market-name">
                    {MARKET_NAMES[market.market] || market.market}
                  </span>
                  <span
                    className="market-score"
                    style={{ backgroundColor: getScoreColor(market.profitability_score) }}
                  >
                    {market.profitability_score}
                  </span>
                </div>

                {renderPriceGuide(market.suggested_price)}

                <div className="market-stats">
                  <div className="stat">
                    <span className="stat-label">Avg Price</span>
                    <span className="stat-value">€{market.avg_selling_price}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Avg Days to Sell</span>
                    <span className="stat-value">
                      {market.avg_days_to_sell !== null
                        ? `${market.avg_days_to_sell}d`
                        : '-'}
                    </span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Sell-Through</span>
                    <span className="stat-value">
                      {(market.sell_through_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Competition</span>
                    {getCompetitionBadge(market.competition_level)}
                  </div>
                </div>

                <div className="score-breakdown">
                  <div className="breakdown-bar">
                    <div
                      className="bar-segment price"
                      style={{ width: `${market.score_breakdown.price}%` }}
                      title={`Price: ${market.score_breakdown.price}`}
                    />
                    <div
                      className="bar-segment speed"
                      style={{ width: `${market.score_breakdown.speed}%` }}
                      title={`Speed: ${market.score_breakdown.speed}`}
                    />
                    <div
                      className="bar-segment demand"
                      style={{ width: `${market.score_breakdown.demand}%` }}
                      title={`Demand: ${market.score_breakdown.demand}`}
                    />
                    <div
                      className="bar-segment competition"
                      style={{ width: `${market.score_breakdown.competition}%` }}
                      title={`Competition: ${market.score_breakdown.competition}`}
                    />
                  </div>
                  <div className="breakdown-legend">
                    <span className="legend-item">
                      <span className="dot price" /> Price
                    </span>
                    <span className="legend-item">
                      <span className="dot speed" /> Speed
                    </span>
                    <span className="legend-item">
                      <span className="dot demand" /> Demand
                    </span>
                    <span className="legend-item">
                      <span className="dot competition" /> Competition
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="wts-footer">
            <p>
              Based on {results.markets.reduce((sum, m) => sum + m.total_data_points, 0)}{' '}
              items tracked across {results.markets.length} markets
            </p>
          </div>
        </div>
      )}

      {results && results.markets.length === 0 && (
        <div className="wts-no-data">
          <p>No data available for this category yet.</p>
          <p>Try selecting a different category or removing the brand filter.</p>
        </div>
      )}
    </div>
  );
}
