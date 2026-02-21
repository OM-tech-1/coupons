-- Add brand and discount columns to packages table

ALTER TABLE packages ADD COLUMN IF NOT EXISTS brand VARCHAR(100);
ALTER TABLE packages ADD COLUMN IF NOT EXISTS discount FLOAT;
