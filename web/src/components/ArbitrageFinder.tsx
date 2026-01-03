import { useState } from 'react';
import {
  getArbitrageOpportunities,
  type ArbitrageResponse,
  type CategoriesResponse,
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

export function ArbitrageFinder({ categories }: Props) {
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [minGap, setMinGap] = useState<number>(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ArbitrageResponse | null>(null);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getArbitrageOpportunities(
        selectedCategory || undefined,
        minGap
      );
      setResults(response.data);
    } catch (err) {
      setError('Failed to find opportunities. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getProfitColor = (percent: number): string => {
    if (percent >= 50) return '#22c55e';
    if (percent >= 30) return '#84cc16';
    return '#eab308';
  };

  return (
    <div className="arbitrage-finder">
      <div className="af-header">
        <h2>Arbitrage Finder</h2>
        <p>Find items that are cheap in one market but expensive in another</p>
      </div>

      <div className="af-controls">
        <div className="af-field">
          <label>Category (optional)</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
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

        <div className="af-field">
          <label>Min Price Gap %</label>
          <input
            type="number"
            value={minGap}
            onChange={(e) => setMinGap(Number(e.target.value))}
            min={5}
            max={100}
          />
        </div>

        <button
          className="af-search-btn"
          onClick={handleSearch}
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Find Opportunities'}
        </button>
      </div>

      {error && <div className="af-error">{error}</div>}

      {results && (
        <div className="af-results">
          <div className="af-summary">
            Found <strong>{results.total_found}</strong> opportunities with ≥{results.min_gap_threshold}% price gap
          </div>

          {results.opportunities.length > 0 ? (
            <div className="af-opportunities">
              {results.opportunities.map((opp, index) => (
                <div key={`${opp.category}-${index}`} className="af-card">
                  <div className="af-card-header">
                    <span className="af-category">{formatCategoryName(opp.category)}</span>
                    <span
                      className="af-profit-badge"
                      style={{ backgroundColor: getProfitColor(opp.price_gap_percent) }}
                    >
                      +{opp.price_gap_percent}%
                    </span>
                  </div>

                  <div className="af-flow">
                    <div className="af-market buy">
                      <div className="af-market-label">Buy in</div>
                      <div className="af-market-name">
                        {MARKET_NAMES[opp.buy_market] || opp.buy_market}
                      </div>
                      <div className="af-market-price">€{opp.buy_price}</div>
                      <div className="af-market-count">{opp.buy_count} listings</div>
                    </div>

                    <div className="af-arrow">
                      <span>→</span>
                      <span className="af-profit">+€{opp.potential_profit}</span>
                    </div>

                    <div className="af-market sell">
                      <div className="af-market-label">Sell in</div>
                      <div className="af-market-name">
                        {MARKET_NAMES[opp.sell_market] || opp.sell_market}
                      </div>
                      <div className="af-market-price">€{opp.sell_price}</div>
                      <div className="af-market-count">{opp.sell_count} listings</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="af-no-data">
              <p>No arbitrage opportunities found with {minGap}%+ price gap.</p>
              <p>Try lowering the minimum gap or selecting a different category.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
