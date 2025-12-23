-- =============================================================================
-- GreenThumb Database Initialization
-- =============================================================================
-- This script is executed on first database startup
-- Creates PostGIS extension and initial schema
-- =============================================================================

-- Enable PostGIS extension for geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create updated_at trigger function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create initial tables (migrations will handle schema changes)
-- This is just a placeholder for the extension setup
