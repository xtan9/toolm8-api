-- Tools table (simplified schema without categories)
CREATE TABLE IF NOT EXISTS tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    pricing_type VARCHAR(50) CHECK (pricing_type IN ('free', 'freemium', 'paid', 'one-time', 'no-pricing')),
    price_range VARCHAR(100),
    has_free_trial BOOLEAN DEFAULT false,
    tags TEXT[],
    features TEXT[],
    quality_score INTEGER DEFAULT 5 CHECK (quality_score >= 1 AND quality_score <= 10),
    popularity_score INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT false,
    click_count INTEGER DEFAULT 0,
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tools_tags ON tools USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_tools_pricing_type ON tools(pricing_type);
CREATE INDEX IF NOT EXISTS idx_tools_is_featured ON tools(is_featured);
CREATE INDEX IF NOT EXISTS idx_tools_quality_score ON tools(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_tools_popularity_score ON tools(popularity_score DESC);
CREATE INDEX IF NOT EXISTS idx_tools_created_at ON tools(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tools_source ON tools(source);
CREATE INDEX IF NOT EXISTS idx_tools_slug ON tools(slug);

-- Updated at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for updated_at
CREATE TRIGGER update_tools_updated_at BEFORE UPDATE ON tools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();