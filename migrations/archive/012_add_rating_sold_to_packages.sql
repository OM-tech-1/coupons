-- Add avg_rating and total_sold to packages for bundle statistics
ALTER TABLE packages ADD COLUMN IF NOT EXISTS avg_rating FLOAT DEFAULT 0.0;
ALTER TABLE packages ADD COLUMN IF NOT EXISTS total_sold INTEGER DEFAULT 0;
