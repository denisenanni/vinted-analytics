import { useState, useEffect } from 'react';
import { SearchForm } from './components/SearchForm';
import { ResultsCard } from './components/ResultsCard';
import { ItemsList } from './components/ItemsList';
import { TrendsChart } from './components/TrendsChart';
import {
  lookup,
  getTrends,
  getCategories,
  type LookupResponse,
  type TrendsResponse,
  type TrendingItem,
  type CategoriesResponse,
} from './api/client';
import './App.css';

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

function App() {
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [results, setResults] = useState<LookupResponse | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [trendItems, setTrendItems] = useState<TrendingItem[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'search' | 'trends'>('search');

  // Trends filters
  const [categories, setCategories] = useState<CategoriesResponse | null>(null);
  const [selectedMarket, setSelectedMarket] = useState('IT');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [offset, setOffset] = useState(0);
  const ITEMS_PER_PAGE = 20;

  useEffect(() => {
    getCategories()
      .then((res) => setCategories(res.data))
      .catch(console.error);
  }, []);

  const handleSearch = async (params: {
    brand?: string;
    category?: string;
    size?: string;
    market?: string;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const response = await lookup({ ...params, limit: 20 });
      setResults(response.data);
    } catch (err) {
      setError('Failed to fetch results. Make sure the API is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadTrends = async (market: string, cats: string[], resetItems = true) => {
    if (resetItems) {
      setLoading(true);
      setOffset(0);
      setTrendItems([]);
    } else {
      setLoadingMore(true);
    }
    setError(null);

    const currentOffset = resetItems ? 0 : offset;

    try {
      const response = await getTrends(
        market,
        cats.length > 0 ? cats : undefined,
        '7d',
        ITEMS_PER_PAGE,
        currentOffset
      );
      const data = response.data;

      if (resetItems) {
        setTrendItems(data.trending_items);
      } else {
        setTrendItems((prev) => [...prev, ...data.trending_items]);
      }

      setTrends(data);
      setHasMore(data.has_more);
      setOffset(currentOffset + ITEMS_PER_PAGE);
    } catch (err) {
      setError('Failed to fetch trends. Make sure the API is running.');
      console.error(err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleMarketChange = (market: string) => {
    setSelectedMarket(market);
    handleLoadTrends(market, selectedCategories, true);
  };

  const handleCategoryToggle = (category: string) => {
    const newSelected = selectedCategories.includes(category)
      ? selectedCategories.filter((c) => c !== category)
      : [...selectedCategories, category];
    setSelectedCategories(newSelected);
    handleLoadTrends(selectedMarket, newSelected, true);
  };

  const handleLoadMore = () => {
    handleLoadTrends(selectedMarket, selectedCategories, false);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Vinted Analytics</h1>
        <p>Cross-market analytics for Vinted sellers</p>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'search' ? 'active' : ''}
          onClick={() => setActiveTab('search')}
        >
          Search
        </button>
        <button
          className={activeTab === 'trends' ? 'active' : ''}
          onClick={() => {
            setActiveTab('trends');
            if (!trends) handleLoadTrends(selectedMarket, selectedCategories, true);
          }}
        >
          Trends
        </button>
      </nav>

      <main className="main">
        {error && <div className="error">{error}</div>}

        {activeTab === 'search' && (
          <>
            <SearchForm onSearch={handleSearch} loading={loading} />

            {results && (
              <div className="results">
                <ResultsCard data={results} />
                <ItemsList items={results.recent_items} />
              </div>
            )}

            {!results && !loading && (
              <div className="placeholder">
                <p>Search for items to see pricing insights</p>
              </div>
            )}
          </>
        )}

        {activeTab === 'trends' && (
          <div className="trends-section">
            <div className="trends-controls">
              <div className="control-group">
                <label>Market:</label>
                <select
                  onChange={(e) => handleMarketChange(e.target.value)}
                  value={selectedMarket}
                >
                  {[
                    { code: 'IT', name: 'Italy' },
                    { code: 'FR', name: 'France' },
                    { code: 'DE', name: 'Germany' },
                    { code: 'ES', name: 'Spain' },
                    { code: 'NL', name: 'Netherlands' },
                    { code: 'PL', name: 'Poland' },
                    { code: 'BE', name: 'Belgium' },
                    { code: 'AT', name: 'Austria' },
                    { code: 'PT', name: 'Portugal' },
                  ].map((m) => (
                    <option key={m.code} value={m.code}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {categories && (
              <div className="category-filter">
                <label>Filter by Category:</label>
                <div className="category-groups">
                  {Object.entries(categories.categories).map(([groupKey, groupCategories]) => (
                    <div key={groupKey} className="category-group">
                      <span className="group-label">{CATEGORY_LABELS[groupKey]}</span>
                      <div className="category-options">
                        {groupCategories.map((cat) => (
                          <label key={cat} className="category-option">
                            <input
                              type="checkbox"
                              checked={selectedCategories.includes(cat)}
                              onChange={() => handleCategoryToggle(cat)}
                            />
                            <span>{formatCategoryName(cat)}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                {selectedCategories.length > 0 && (
                  <button
                    className="clear-filters"
                    onClick={() => {
                      setSelectedCategories([]);
                      handleLoadTrends(selectedMarket, [], true);
                    }}
                  >
                    Clear filters ({selectedCategories.length})
                  </button>
                )}
              </div>
            )}

            {trends && (
              <TrendsChart data={{ ...trends, trending_items: trendItems }} />
            )}

            {hasMore && !loading && (
              <button
                className="load-more"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? 'Loading...' : `Load More (${trendItems.length} of ${trends?.total_items})`}
              </button>
            )}

            {!trends && loading && <p className="loading">Loading trends...</p>}
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Vinted Analytics - Data updates every 12 hours</p>
      </footer>
    </div>
  );
}

export default App;
