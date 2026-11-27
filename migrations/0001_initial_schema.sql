-- 0001_initial_schema.sql
-- Version-controlled baseline schema for FractalVision Lab (Postgres / Supabase compatible).

CREATE TABLE IF NOT EXISTS specimens (
    id                       TEXT PRIMARY KEY,
    name                     TEXT NOT NULL,
    category                 TEXT NOT NULL
                             CHECK (category IN ('leaf', 'coastline', 'standard-fractal')),
    description              TEXT,
    image_url                TEXT NOT NULL DEFAULT '',
    binary_image_url         TEXT DEFAULT '',
    fractal_dimension        DOUBLE PRECISION NOT NULL,
    r_squared                DOUBLE PRECISION NOT NULL,
    intercept                DOUBLE PRECISION,
    standard_error           DOUBLE PRECISION,
    confidence_interval_low  DOUBLE PRECISION,
    confidence_interval_high DOUBLE PRECISION,
    complexity_class         TEXT,
    interpretation           TEXT NOT NULL,
    notes                    TEXT,
    box_sizes                INTEGER[] NOT NULL DEFAULT '{}',
    box_counts               INTEGER[] NOT NULL DEFAULT '{}',
    log_inverse_sizes        DOUBLE PRECISION[] DEFAULT '{}',
    log_counts               DOUBLE PRECISION[] DEFAULT '{}',
    display_order            INTEGER DEFAULT 0,
    created_at               TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS standard_fractals (
    id                       TEXT PRIMARY KEY,
    name                     TEXT NOT NULL,
    theoretical_dimension    DOUBLE PRECISION NOT NULL,
    max_iterations           INTEGER NOT NULL,
    description              TEXT NOT NULL,
    formula                  TEXT,
    display_order            INTEGER DEFAULT 0,
    created_at               TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_specimens_category  ON specimens(category);
CREATE INDEX IF NOT EXISTS idx_specimens_dimension ON specimens(fractal_dimension);
CREATE INDEX IF NOT EXISTS idx_specimens_order     ON specimens(display_order);
CREATE INDEX IF NOT EXISTS idx_fractals_order      ON standard_fractals(display_order);

-- Public read-only Row Level Security policies (used by Supabase anon access; valid PostgreSQL).
ALTER TABLE specimens ENABLE ROW LEVEL SECURITY;
ALTER TABLE standard_fractals ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'specimens'
          AND policyname = 'Public read access for specimens'
    ) THEN
        CREATE POLICY "Public read access for specimens"
            ON specimens FOR SELECT
            USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'standard_fractals'
          AND policyname = 'Public read access for standard_fractals'
    ) THEN
        CREATE POLICY "Public read access for standard_fractals"
            ON standard_fractals FOR SELECT
            USING (true);
    END IF;
END
$$;
