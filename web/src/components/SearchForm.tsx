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

// Organized categories by section
const CATEGORIES = {
  "Women's Clothing": [
    'women/dresses',
    'women/tops-and-t-shirts',
    'women/jumpers-and-sweaters',
    'women/jeans',
    'women/trousers-and-leggings',
    'women/skirts',
    'women/shorts-and-cropped-trousers',
    'women/outerwear',
    'women/suits-and-blazers',
    'women/jumpsuits-and-playsuits',
    'women/activewear',
    'women/swimwear',
    'women/lingerie-and-nightwear',
  ],
  "Women's Shoes": [
    'women/boots',
    'women/heels',
    'women/trainers',
    'women/sandals',
    'women/ballerinas',
    'women/slippers',
    'women/sports-shoes',
  ],
  "Women's Bags": [
    'women/handbags',
    'women/backpacks',
    'women/shoulder-bags',
    'women/tote-bags',
    'women/clutches',
    'women/wallets-and-purses',
  ],
  "Women's Accessories": [
    'women/jewellery',
    'women/watches',
    'women/sunglasses',
    'women/belts',
    'women/hats-and-caps',
    'women/scarves-and-shawls',
    'women/gloves',
    'women/hair-accessories',
    'women/umbrellas',
    'women/keyrings',
  ],
  "Men's Clothing": [
    'men/tops-and-t-shirts',
    'men/jumpers-and-sweaters',
    'men/jeans',
    'men/trousers',
    'men/shorts',
    'men/outerwear',
    'men/suits-and-blazers',
    'men/activewear',
    'men/swimwear',
  ],
  "Men's Shoes": [
    'men/boots',
    'men/trainers',
    'men/formal-shoes',
    'men/sandals',
    'men/sports-shoes',
    'men/slippers',
  ],
  "Men's Accessories": [
    'men/bags-and-backpacks',
    'men/jewellery',
    'men/watches',
    'men/sunglasses',
    'men/belts',
    'men/hats-and-caps',
    'men/ties-and-bow-ties',
  ],
};

// Format category slug for display
const formatCategory = (cat: string) => {
  const name = cat.split('/')[1] || cat;
  return name.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
};

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
            <option value="">All categories</option>
            {Object.entries(CATEGORIES).map(([group, cats]) => (
              <optgroup key={group} label={group}>
                {cats.map((cat) => (
                  <option key={cat} value={cat}>
                    {formatCategory(cat)}
                  </option>
                ))}
              </optgroup>
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
