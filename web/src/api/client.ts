import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export interface LookupParams {
  brand?: string;
  category?: string;
  size?: string;
  market?: string;
  limit?: number;
}

export interface LookupResponse {
  query: Record<string, string | null>;
  total_items: number;
  avg_price: number;
  min_price: number;
  max_price: number;
  price_range: string;
  demand_score: string;
  best_markets: Array<{
    market: string;
    count: number;
    avg_price: number;
    avg_favorites: number;
  }>;
  recent_items: Array<{
    vinted_id: string;
    title: string;
    price: number;
    brand: string | null;
    url: string;
    image_url: string | null;
    favorites: number | null;
    market: string;
  }>;
}

export interface TrendingItem {
  vinted_id: string;
  title: string;
  price: number;
  brand: string | null;
  url: string | null;
  image_url: string | null;
  favorites: number;
  market: string;
  category: string | null;
}

export interface TrendsResponse {
  market: string;
  categories: string[];
  period: string;
  total_items: number;
  avg_price: number;
  trending_items: TrendingItem[];
  has_more: boolean;
}

export interface CompareResponse {
  query: Record<string, string | null>;
  markets: Array<{
    market: string;
    item_count: number;
    avg_price: number;
    min_price: number;
    max_price: number;
    sold_count: number;
    avg_favorites: number;
  }>;
  best_market: string;
  reason: string;
}

export const lookup = (params: LookupParams) =>
  api.get<LookupResponse>('/api/lookup', { params });

export interface CategoriesResponse {
  categories: {
    women_clothing: string[];
    women_shoes: string[];
    women_bags: string[];
    women_accessories: string[];
    men_clothing: string[];
    men_shoes: string[];
    men_accessories: string[];
  };
  markets: string[];
}

export const getTrends = (
  market: string,
  categories?: string[],
  period = '7d',
  limit = 20,
  offset = 0
) =>
  api.get<TrendsResponse>('/api/trends', {
    params: {
      market,
      categories: categories?.length ? categories.join(',') : undefined,
      period,
      limit,
      offset,
    },
  });

export const getCategories = () =>
  api.get<CategoriesResponse>('/api/categories');

export const compare = (brand?: string, category?: string, markets?: string) =>
  api.get<CompareResponse>('/api/compare', { params: { brand, category, markets } });
