-- Stats Daily table for aggregated metrics
-- Run this in Supabase SQL Editor

-- Create stats_daily table
CREATE TABLE IF NOT EXISTS stats_daily (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    market TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT,  -- nullable for category-wide stats

    active_count INT,
    sold_count INT,
    avg_price DECIMAL(10,2),
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    avg_time_to_sell_days DECIMAL(5,1),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(date, market, category, brand)
);

-- Indexes for stats_daily queries
CREATE INDEX IF NOT EXISTS idx_stats_daily_lookup ON stats_daily(date, market, category);
CREATE INDEX IF NOT EXISTS idx_stats_daily_date ON stats_daily(date);

-- Additional indexes for cleanup performance
CREATE INDEX IF NOT EXISTS idx_items_sold_at ON items(sold_at);
CREATE INDEX IF NOT EXISTS idx_price_history_recorded_at ON price_history(recorded_at);

-- Enable RLS for stats_daily
ALTER TABLE stats_daily ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public access to stats_daily" ON stats_daily FOR ALL USING (true);
