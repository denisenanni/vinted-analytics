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

export interface TrendsResponse {
  market: string;
  category: string;
  period: string;
  total_items: number;
  avg_price: number;
  trending_brands: Array<{
    brand: string;
    count: number;
    avg_price: number;
    trend: string;
  }>;
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

export const getTrends = (market: string, category?: string, period = '7d') =>
  api.get<TrendsResponse>('/api/trends', { params: { market, category, period } });

export const compare = (brand?: string, category?: string, markets?: string) =>
  api.get<CompareResponse>('/api/compare', { params: { brand, category, markets } });
