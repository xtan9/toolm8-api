-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tools table
CREATE TABLE IF NOT EXISTS tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    pricing_type VARCHAR(50) CHECK (pricing_type IN ('free', 'freemium', 'paid', 'one-time')),
    price_range VARCHAR(100),
    has_free_trial BOOLEAN DEFAULT false,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
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
CREATE INDEX IF NOT EXISTS idx_tools_category_id ON tools(category_id);
CREATE INDEX IF NOT EXISTS idx_tools_pricing_type ON tools(pricing_type);
CREATE INDEX IF NOT EXISTS idx_tools_is_featured ON tools(is_featured);
CREATE INDEX IF NOT EXISTS idx_tools_quality_score ON tools(quality_score);
CREATE INDEX IF NOT EXISTS idx_tools_popularity_score ON tools(popularity_score DESC);
CREATE INDEX IF NOT EXISTS idx_tools_created_at ON tools(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_categories_display_order ON categories(display_order);
CREATE INDEX IF NOT EXISTS idx_categories_is_featured ON categories(is_featured);

-- Updated at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tools_updated_at BEFORE UPDATE ON tools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();