-- Vinted Analytics Database Schema
-- Run this in Supabase SQL Editor

-- Items table
CREATE TABLE IF NOT EXISTS items (
    id BIGSERIAL PRIMARY KEY,
    vinted_id TEXT UNIQUE NOT NULL,
    title TEXT,
    price DECIMAL(10, 2),
    currency TEXT DEFAULT 'EUR',
    brand TEXT,
    size TEXT,
    url TEXT,
    image_url TEXT,
    favorites INTEGER,
    market TEXT NOT NULL,
    category TEXT NOT NULL,
    scraped_at TIMESTAMPTZ,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'active',
    sold_at TIMESTAMPTZ
);

-- Price history table
CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    vinted_id TEXT REFERENCES items(vinted_id),
    price DECIMAL(10, 2),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_items_vinted_id ON items(vinted_id);
CREATE INDEX IF NOT EXISTS idx_items_market_category ON items(market, category);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_last_seen ON items(last_seen);
CREATE INDEX IF NOT EXISTS idx_price_history_vinted_id ON price_history(vinted_id);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;

-- Allow public read/write for now (adjust for production)
CREATE POLICY "Allow public access to items" ON items FOR ALL USING (true);
CREATE POLICY "Allow public access to price_history" ON price_history FOR ALL USING (true);
