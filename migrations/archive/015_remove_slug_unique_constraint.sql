-- Remove unique constraint from packages.slug
-- This allows multiple packages to have the same slug
-- Only package.id remains the unique identifier

-- Drop the unique constraint on slug
ALTER TABLE packages DROP CONSTRAINT IF EXISTS packages_slug_key;

-- Drop the unique index on slug if it exists
DROP INDEX IF EXISTS ix_packages_slug;

-- Create a non-unique index for performance (optional but recommended)
CREATE INDEX IF NOT EXISTS ix_packages_slug_non_unique ON packages(slug);

-- Verify the change
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'packages' AND indexname LIKE '%slug%';
