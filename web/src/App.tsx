import { useState } from 'react';
import { SearchForm } from './components/SearchForm';
import { ResultsCard } from './components/ResultsCard';
import { ItemsList } from './components/ItemsList';
import { TrendsChart } from './components/TrendsChart';
import { lookup, getTrends, type LookupResponse, type TrendsResponse } from './api/client';
import './App.css';

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<LookupResponse | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'search' | 'trends'>('search');

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

  const handleLoadTrends = async (market = 'IT') => {
    setLoading(true);
    setError(null);
    try {
      const response = await getTrends(market, undefined, '7d');
      setTrends(response.data);
    } catch (err) {
      setError('Failed to fetch trends. Make sure the API is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
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
            if (!trends) handleLoadTrends();
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
              <label>Market:</label>
              <select onChange={(e) => handleLoadTrends(e.target.value)} defaultValue="IT">
                {['IT', 'FR', 'DE', 'ES', 'NL', 'PL', 'BE', 'AT', 'PT'].map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            {trends && <TrendsChart data={trends} />}

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
