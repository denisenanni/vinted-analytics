import { useState, useEffect } from 'react';
import { SearchForm } from './components/SearchForm';
import { ResultsCard } from './components/ResultsCard';
import { ItemsList } from './components/ItemsList';
import { TrendsChart } from './components/TrendsChart';
import { WhereToSell } from './components/WhereToSell';
import { TimingInsights } from './components/TimingInsights';
import { ArbitrageFinder } from './components/ArbitrageFinder';
import {
  lookup,
  getTrends,
  getCategories,
  getHotCategories,
  getSold,
  type LookupResponse,
  type TrendsResponse,
  type TrendingItem,
  type CategoriesResponse,
  type HotCategoriesResponse,
  type SoldResponse,
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

function getInitialTab(): 'search' | 'trends' | 'sold' | 'where-to-sell' | 'timing' | 'arbitrage' {
  const hash = window.location.hash.replace('#', '');
  if (hash === 'trends') return 'trends';
  if (hash === 'sold') return 'sold';
  if (hash === 'where-to-sell') return 'where-to-sell';
  if (hash === 'timing') return 'timing';
  if (hash === 'arbitrage') return 'arbitrage';
  return 'search';
}

function App() {
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [results, setResults] = useState<LookupResponse | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [trendItems, setTrendItems] = useState<TrendingItem[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'search' | 'trends' | 'sold' | 'where-to-sell' | 'timing' | 'arbitrage'>(getInitialTab);
  const [sold, setSold] = useState<SoldResponse | null>(null);
  const [soldMarket, setSoldMarket] = useState('IT');
  const [soldPeriod, setSoldPeriod] = useState('30d');

  // Update URL hash when tab changes
  const handleTabChange = (tab: 'search' | 'trends' | 'sold' | 'where-to-sell' | 'timing' | 'arbitrage') => {
    setActiveTab(tab);
    window.location.hash = tab;
  };

  // Trends filters
  const [categories, setCategories] = useState<CategoriesResponse | null>(null);
  const [hotCategories, setHotCategories] = useState<HotCategoriesResponse | null>(null);
  const [selectedMarket, setSelectedMarket] = useState('IT');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [offset, setOffset] = useState(0);
  const [filterOpen, setFilterOpen] = useState(false);
  const ITEMS_PER_PAGE = 20;

  useEffect(() => {
    getCategories()
      .then((res) => setCategories(res.data))
      .catch(console.error);
    getHotCategories()
      .then((res) => setHotCategories(res.data))
      .catch(console.error);
  }, []);

  // Load trends data on mount if starting on trends tab
  useEffect(() => {
    if (activeTab === 'trends' && !trends) {
      handleLoadTrends(selectedMarket, selectedCategories, true);
    }
    if (activeTab === 'sold' && !sold) {
      handleLoadSold(soldMarket, soldPeriod);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setTrends(null);
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
      const newItems = data.trending_items || [];

      if (resetItems) {
        setTrendItems(newItems);
      } else {
        setTrendItems((prev) => [...prev, ...newItems]);
      }

      setTrends(data);
      setHasMore(data.has_more ?? false);
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
    setSelectedCategories([]); // Reset filters when changing market
    handleLoadTrends(market, [], true);
  };

  const handleCategoryToggle = (category: string) => {
    const newSelected = selectedCategories.includes(category)
      ? selectedCategories.filter((c) => c !== category)
      : [...selectedCategories, category];
    setSelectedCategories(newSelected);
    handleLoadTrends(selectedMarket, newSelected, true);
  };

  const handleGroupToggle = (groupCategories: string[]) => {
    // Check if all categories in the group are currently selected
    const allSelected = groupCategories.every((c) => selectedCategories.includes(c));

    let newSelected: string[];
    if (allSelected) {
      // Deselect all in group
      newSelected = selectedCategories.filter((c) => !groupCategories.includes(c));
    } else {
      // Select all in group (add missing ones)
      const toAdd = groupCategories.filter((c) => !selectedCategories.includes(c));
      newSelected = [...selectedCategories, ...toAdd];
    }

    setSelectedCategories(newSelected);
    handleLoadTrends(selectedMarket, newSelected, true);
  };

  const handleLoadMore = () => {
    handleLoadTrends(selectedMarket, selectedCategories, false);
  };

  const handleLoadSold = async (market: string, period: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await getSold(undefined, undefined, market, period, 50);
      setSold(response.data);
    } catch (err) {
      setError('Failed to fetch sold items. Make sure the API is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSoldMarketChange = (market: string) => {
    setSoldMarket(market);
    handleLoadSold(market, soldPeriod);
  };

  const handleSoldPeriodChange = (period: string) => {
    setSoldPeriod(period);
    handleLoadSold(soldMarket, period);
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
          onClick={() => handleTabChange('search')}
        >
          Search
        </button>
        <button
          className={activeTab === 'trends' ? 'active' : ''}
          onClick={() => {
            handleTabChange('trends');
            if (!trends) handleLoadTrends(selectedMarket, selectedCategories, true);
          }}
        >
          Trends
        </button>
        <button
          className={activeTab === 'sold' ? 'active' : ''}
          onClick={() => {
            handleTabChange('sold');
            if (!sold) handleLoadSold(soldMarket, soldPeriod);
          }}
        >
          Sold
        </button>
        <button
          className={activeTab === 'where-to-sell' ? 'active' : ''}
          onClick={() => handleTabChange('where-to-sell')}
        >
          Where to Sell
        </button>
        <button
          className={activeTab === 'timing' ? 'active' : ''}
          onClick={() => handleTabChange('timing')}
        >
          Timing
        </button>
        <button
          className={activeTab === 'arbitrage' ? 'active' : ''}
          onClick={() => handleTabChange('arbitrage')}
        >
          Arbitrage
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
                <div className="market-selector">
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
                  ].map((m) => {
                    const hotCat = hotCategories?.hot_categories[m.code];
                    const categoryName = hotCat ? formatCategoryName(hotCat.category) : '';
                    return (
                      <button
                        key={m.code}
                        className={`market-btn ${selectedMarket === m.code ? 'active' : ''}`}
                        onClick={() => handleMarketChange(m.code)}
                        title={hotCat ? `${hotCat.total_favorites} favorites` : m.name}
                      >
                        <span className="market-name">{m.name}</span>
                        {hotCat && (
                          <span className="hot-category">{categoryName}</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {categories && (
              <div className={`category-filter ${filterOpen ? 'open' : ''}`}>
                <button
                  className="filter-toggle"
                  onClick={() => setFilterOpen(!filterOpen)}
                >
                  <span>
                    Filter by Category
                    {selectedCategories.length > 0 && ` (${selectedCategories.length} selected)`}
                  </span>
                  <span className="toggle-icon">{filterOpen ? '▲' : '▼'}</span>
                </button>
                {filterOpen && (
                  <>
                    <div className="category-groups">
                      {Object.entries(categories.categories).map(([groupKey, groupCategories]) => {
                        const allSelected = groupCategories.every((c) =>
                          selectedCategories.includes(c)
                        );
                        const someSelected = groupCategories.some((c) =>
                          selectedCategories.includes(c)
                        );
                        return (
                          <div key={groupKey} className="category-group">
                            <label className="group-label clickable">
                              <input
                                type="checkbox"
                                checked={allSelected}
                                ref={(el) => {
                                  if (el) el.indeterminate = someSelected && !allSelected;
                                }}
                                onChange={() => handleGroupToggle(groupCategories)}
                              />
                              <span>{CATEGORY_LABELS[groupKey]}</span>
                            </label>
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
                        );
                      })}
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
                  </>
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

        {activeTab === 'sold' && (
          <div className="sold-section">
            <div className="sold-controls">
              <div className="control-group">
                <label>Market:</label>
                <select
                  value={soldMarket}
                  onChange={(e) => handleSoldMarketChange(e.target.value)}
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
              <div className="control-group">
                <label>Period:</label>
                <select
                  value={soldPeriod}
                  onChange={(e) => handleSoldPeriodChange(e.target.value)}
                >
                  <option value="7d">Last 7 days</option>
                  <option value="30d">Last 30 days</option>
                  <option value="90d">Last 90 days</option>
                </select>
              </div>
            </div>

            {sold && (
              <div className="sold-results">
                <div className="sold-stats">
                  <div className="stat-card">
                    <span className="stat-value">{sold.total_sold}</span>
                    <span className="stat-label">Items Sold</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{sold.avg_price.toFixed(2)}</span>
                    <span className="stat-label">Avg Price</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">
                      {sold.avg_days_to_sell !== null ? sold.avg_days_to_sell.toFixed(1) : '-'}
                    </span>
                    <span className="stat-label">Avg Days to Sell</span>
                  </div>
                </div>

                <div className="sold-items-list">
                  {sold.items.map((item) => (
                    <div key={item.vinted_id} className="sold-item">
                      <div className="sold-item-info">
                        <span className="sold-item-title">{item.title}</span>
                        {item.brand && <span className="sold-item-brand">{item.brand}</span>}
                      </div>
                      <div className="sold-item-details">
                        <span className="sold-item-price">{item.price.toFixed(2)}</span>
                        {item.days_to_sell !== null && (
                          <span className="sold-item-days">{item.days_to_sell}d to sell</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!sold && loading && <p className="loading">Loading sold items...</p>}
            {sold && sold.items.length === 0 && (
              <p className="no-data">No sold items found for this period.</p>
            )}
          </div>
        )}

        {activeTab === 'where-to-sell' && (
          <WhereToSell categories={categories} />
        )}

        {activeTab === 'timing' && <TimingInsights />}

        {activeTab === 'arbitrage' && <ArbitrageFinder categories={categories} />}
      </main>

      <footer className="footer">
        <p>Vinted Analytics - Data updates every 12 hours</p>
      </footer>
    </div>
  );
}

export default App;
