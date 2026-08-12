-- ============================================================================
-- FractalVision Lab — Supabase SQL Migration
-- Phase 0 Scaffolding
-- 
-- Instructions: Paste this entire script into the Supabase SQL Editor and run.
-- It creates the specimens and standard_fractals tables, seeds all 12 specimens
-- and 5 standard fractals, and configures read-only public access.
-- ============================================================================

-- ============================================================================
-- 1. CREATE TABLES
-- ============================================================================

-- Dissertation specimens (leaves, coastlines, standard fractals)
CREATE TABLE IF NOT EXISTS specimens (
    id                      TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    category                TEXT NOT NULL 
                            CHECK (category IN ('leaf', 'coastline', 'standard-fractal')),
    description             TEXT,
    
    -- Images (stored in Supabase Storage, public bucket)
    image_url               TEXT NOT NULL DEFAULT '',
    binary_image_url        TEXT DEFAULT '',
    
    -- Analysis results from dissertation
    fractal_dimension       DOUBLE PRECISION NOT NULL,
    r_squared               DOUBLE PRECISION NOT NULL,
    intercept               DOUBLE PRECISION,
    standard_error          DOUBLE PRECISION,
    confidence_interval_low  DOUBLE PRECISION,
    confidence_interval_high DOUBLE PRECISION,
    
    -- Interpretation
    complexity_class        TEXT,
    interpretation          TEXT NOT NULL,
    notes                   TEXT,
    
    -- Raw data for charting
    box_sizes               INTEGER[] NOT NULL DEFAULT '{}',
    box_counts              INTEGER[] NOT NULL DEFAULT '{}',
    log_inverse_sizes       DOUBLE PRECISION[] DEFAULT '{}',
    log_counts              DOUBLE PRECISION[] DEFAULT '{}',
    
    -- Display
    display_order           INTEGER DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Standard mathematical fractals (reference metadata)
CREATE TABLE IF NOT EXISTS standard_fractals (
    id                      TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    theoretical_dimension   DOUBLE PRECISION NOT NULL,
    max_iterations          INTEGER NOT NULL,
    description             TEXT NOT NULL,
    formula                 TEXT,
    display_order           INTEGER DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 2. INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_specimens_category   ON specimens(category);
CREATE INDEX IF NOT EXISTS idx_specimens_dimension   ON specimens(fractal_dimension);
CREATE INDEX IF NOT EXISTS idx_specimens_order       ON specimens(display_order);
CREATE INDEX IF NOT EXISTS idx_fractals_order        ON standard_fractals(display_order);


-- ============================================================================
-- 3. SEED DATA — Specimens (12 total: 7 leaves + 5 coastlines)
-- ============================================================================

INSERT INTO specimens (id, name, category, fractal_dimension, r_squared, complexity_class, interpretation, notes, display_order, image_url, box_sizes, box_counts) VALUES
(
    'spc_guava', 'Guava', 'leaf',
    1.8110, 0.9976, 'High',
    'High complexity — dense leaf structure with irregular venation',
    'Fresh guava leaf specimen, analyzed using full-mask mode with Otsu threshold',
    1, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_lamiaceae', 'Lamiaceae', 'leaf',
    1.9493, 0.9999, 'Near space-filling',
    'Highest leaf complexity in the dataset — extensive branching and surface texture',
    'Lamiaceae family specimen showing near space-filling behavior',
    2, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_mango', 'Mango', 'leaf',
    1.7599, 0.9953, 'Complex',
    'Complex leaf structure with moderate irregularity and clear venation',
    NULL,
    3, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_monoon', 'Monoon Longifolium', 'leaf',
    1.7505, 0.9961, 'Complex',
    'Complex elongated leaf pattern with smooth boundary but textured interior',
    NULL,
    4, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_peepal', 'Peepal', 'leaf',
    1.8043, 0.9977, 'High',
    'High complexity — broad leaf with fine venation network',
    NULL,
    5, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_maple', 'Maple', 'leaf',
    1.5061, 0.9815, 'Complex',
    'Lower score due to noisy background in original image — demonstrates preprocessing sensitivity',
    'R² is noticeably lower due to background artifacts',
    6, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_akondo', 'Akondo', 'leaf',
    1.8727, 0.9988, 'High',
    'High complexity — densely textured leaf surface with irregular edge',
    NULL,
    7, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast1', 'Coastline 1', 'coastline',
    1.7613, 0.9991, 'Complex',
    'Complex coastline with moderate irregularity and some smooth sections',
    NULL,
    8, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast2', 'Coastline 2', 'coastline',
    1.9141, 0.9999, 'Highly irregular',
    'Highly irregular coastline boundary with deep indentations',
    NULL,
    9, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast3', 'Coastline 3', 'coastline',
    1.9626, 1.0000, 'Near space-filling',
    'Highest coastline complexity — near space-filling boundary with maximum irregularity',
    'R² = 1.0000 indicates near-perfect linear fit in log-log space',
    10, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast4', 'Coastline 4', 'coastline',
    1.7108, 0.9996, 'Complex',
    'Lower coastline complexity — smoother boundary sections reduce overall D',
    NULL,
    11, '', '{4,8,16,32,64,128,256}', '{}'
),
(
    'spc_coast5', 'Coastline 5', 'coastline',
    1.9531, 1.0000, 'Highly irregular',
    'Highly irregular coastline with complex indentations and fjord-like structures',
    NULL,
    12, '', '{4,8,16,32,64,128,256}', '{}'
)
ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- 4. SEED DATA — Standard Fractals (5 total)
-- ============================================================================

INSERT INTO standard_fractals (id, name, theoretical_dimension, max_iterations, description, formula, display_order) VALUES
(
    'cantor_set', 'Cantor Set',
    0.6309, 8,
    'Created by repeatedly removing the middle third of line segments',
    'D = log(2) / log(3) ≈ 0.6309',
    1
),
(
    'koch_curve', 'Koch Curve',
    1.2619, 7,
    'Each line segment is replaced by four segments of one-third length',
    'D = log(4) / log(3) ≈ 1.2619',
    2
),
(
    'koch_snowflake', 'Koch Snowflake',
    1.2619, 7,
    'Three Koch curves forming a closed snowflake boundary',
    'D = log(4) / log(3) ≈ 1.2619',
    3
),
(
    'sierpinski_triangle', 'Sierpiński Triangle',
    1.5850, 8,
    'Equilateral triangle subdivided recursively, removing central triangle',
    'D = log(3) / log(2) ≈ 1.5850',
    4
),
(
    'sierpinski_carpet', 'Sierpiński Carpet',
    1.8928, 6,
    'Square subdivided into 9 equal squares, removing center square recursively',
    'D = log(8) / log(3) ≈ 1.8928',
    5
)
ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- 5. ACCESS CONTROL — Public read-only via anon key
-- ============================================================================

-- Enable Row Level Security (required by Supabase)
ALTER TABLE specimens ENABLE ROW LEVEL SECURITY;
ALTER TABLE standard_fractals ENABLE ROW LEVEL SECURITY;

-- Public read policies (anyone with anon key can SELECT)
CREATE POLICY "Public read access for specimens"
    ON specimens FOR SELECT
    USING (true);

CREATE POLICY "Public read access for standard_fractals"
    ON standard_fractals FOR SELECT
    USING (true);

-- No INSERT/UPDATE/DELETE policies = writes are blocked for anon users


-- ============================================================================
-- 6. VERIFY
-- ============================================================================

-- Run these queries to verify the seed data:
-- SELECT count(*) FROM specimens;          -- Should return 12
-- SELECT count(*) FROM standard_fractals;  -- Should return 5
-- SELECT name, fractal_dimension, r_squared FROM specimens ORDER BY display_order;
