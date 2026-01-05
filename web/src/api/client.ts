import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Simple in-memory cache for API responses
const cache = new Map<string, { data: unknown; expiresAt: number }>();
const CACHE_TTL = 12 * 60 * 60 * 1000; // 12 hours (backend has 5h cache, frontend adds extra layer)

function getCacheKey(url: string, params?: Record<string, unknown>): string {
  return `${url}?${JSON.stringify(params || {})}`;
}

async function cachedGet<T>(url: string, params?: Record<string, unknown>): Promise<{ data: T }> {
  const key = getCacheKey(url, params);
  const cached = cache.get(key);

  if (cached && Date.now() < cached.expiresAt) {
    return { data: cached.data as T };
  }

  const response = await api.get<T>(url, { params });
  cache.set(key, { data: response.data, expiresAt: Date.now() + CACHE_TTL });

  return response;
}

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
  first_seen: string | null;
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
  cachedGet<LookupResponse>('/api/lookup', params as Record<string, unknown>);

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
  cachedGet<TrendsResponse>('/api/trends', {
    market,
    categories: categories?.length ? categories.join(',') : undefined,
    period,
    limit,
    offset,
  });

export const getCategories = () =>
  cachedGet<CategoriesResponse>('/api/categories', {});

export const compare = (brand?: string, category?: string, markets?: string) =>
  cachedGet<CompareResponse>('/api/compare', { brand, category, markets });

export interface HotCategoryInfo {
  category: string;
  total_favorites: number;
  item_count: number;
}

export interface HotCategoriesResponse {
  hot_categories: Record<string, HotCategoryInfo>;
}

export const getHotCategories = () =>
  cachedGet<HotCategoriesResponse>('/api/hot-categories', {});

export interface SoldItem {
  vinted_id: string;
  title: string;
  price: number;
  brand: string | null;
  market: string;
  first_seen: string | null;
  sold_at: string | null;
  days_to_sell: number | null;
}

export interface CategoryBreakdown {
  category: string;
  count: number;
  percentage: number;
}

export interface SoldResponse {
  query: Record<string, string | null>;
  total_sold: number;
  avg_price: number;
  avg_days_to_sell: number | null;
  category_breakdown: CategoryBreakdown[];
  items: SoldItem[];
}

export const getSold = (
  brand?: string,
  category?: string,
  market = 'IT',
  period = '30d',
  limit = 50
) =>
  cachedGet<SoldResponse>('/api/sold', { brand, category, market, period, limit });

export interface ScoreBreakdown {
  price: number;
  speed: number;
  demand: number;
  competition: number;
}

export interface PriceRange {
  min: number;
  max: number;
}

export interface SuggestedPrice {
  quick_sale: PriceRange;
  recommended: PriceRange;
  premium: PriceRange;
  data_points: number;
}

export interface MarketProfitability {
  market: string;
  avg_selling_price: number;
  suggested_price: SuggestedPrice | null;
  avg_days_to_sell: number | null;
  sell_through_rate: number;
  active_listings: number;
  sold_last_period: number;
  competition_level: 'low' | 'medium' | 'high';
  total_data_points: number;
  profitability_score: number;
  score_breakdown: ScoreBreakdown;
}

export interface ProfitabilityRecommendation {
  best_market: string | null;
  score?: number;
  suggested_price?: PriceRange;
  reason: string;
}

export interface MarketProfitabilityResponse {
  category: string;
  brand: string | null;
  markets: MarketProfitability[];
  recommendation: ProfitabilityRecommendation;
}

export const getMarketProfitability = (category: string, brand?: string) =>
  cachedGet<MarketProfitabilityResponse>('/api/market-profitability', { category, brand });


// Timing Insights
export interface DayBreakdown {
  day: string;
  sales: number;
  percentage: number;
}

export interface CategoryTrend {
  category: string;
  this_week: number;
  last_week: number;
  change_percent: number;
}

export interface TimingInsightsResponse {
  market: string;
  best_day: string | null;
  day_breakdown: DayBreakdown[];
  trending_up: CategoryTrend[];
  trending_down: CategoryTrend[];
  total_sales_analyzed: number;
  message?: string;
}

export const getTimingInsights = (market: string, category?: string) =>
  cachedGet<TimingInsightsResponse>('/api/timing-insights', { market, category });

// Arbitrage
export interface ArbitrageOpportunity {
  category: string;
  buy_market: string;
  buy_price: number;
  buy_count: number;
  sell_market: string;
  sell_price: number;
  sell_count: number;
  price_gap_percent: number;
  potential_profit: number;
}

export interface ArbitrageResponse {
  opportunities: ArbitrageOpportunity[];
  total_found: number;
  min_gap_threshold: number;
  message?: string;
}

export const getArbitrageOpportunities = (category?: string, minGap: number = 20) =>
  cachedGet<ArbitrageResponse>('/api/arbitrage', { category, min_gap: minGap });