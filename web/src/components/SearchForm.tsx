import { useState } from 'react';

interface SearchFormProps {
  onSearch: (params: {
    brand?: string;
    category?: string;
    size?: string;
    market?: string;
  }) => void;
  loading?: boolean;
}

const MARKETS = ['', 'IT', 'FR', 'DE', 'ES', 'NL', 'PL', 'BE', 'AT', 'PT'];
const CATEGORIES = ['', 'women/dresses', 'women/shirts', 'men/jeans'];

export function SearchForm({ onSearch, loading }: SearchFormProps) {
  const [brand, setBrand] = useState('');
  const [category, setCategory] = useState('');
  const [size, setSize] = useState('');
  const [market, setMarket] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      brand: brand || undefined,
      category: category || undefined,
      size: size || undefined,
      market: market || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="brand">Brand</label>
          <input
            id="brand"
            type="text"
            placeholder="e.g. Zara, Nike"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="category">Category</label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat || 'All categories'}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="size">Size</label>
          <input
            id="size"
            type="text"
            placeholder="e.g. M, 42"
            value={size}
            onChange={(e) => setSize(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="market">Market</label>
          <select
            id="market"
            value={market}
            onChange={(e) => setMarket(e.target.value)}
          >
            {MARKETS.map((m) => (
              <option key={m} value={m}>
                {m || 'All markets'}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
}
