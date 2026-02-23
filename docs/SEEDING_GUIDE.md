# Database Seeding Guide

## Overview

This guide explains how to populate your database with initial data for regions and countries.

## Quick Start

### Local Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the seed script
python scripts/seed_regions_countries.py
```

### Production (Docker)

```bash
# Using Makefile
make seed-data

# Or directly
docker exec -it coupon-api-container python scripts/seed_regions_countries.py
```

## What Gets Seeded

### Regions (9 total)

1. **Middle East** - 8 countries
2. **South Asia** - 6 countries
3. **Southeast Asia** - 6 countries
4. **East Asia** - 5 countries
5. **North America** - 3 countries
6. **Europe** - 10 countries
7. **Oceania** - 2 countries
8. **Africa** - 5 countries
9. **South America** - 5 countries

### Countries (50 total)

All countries are created with:
- Proper ISO 3166-1 alpha-2 country codes
- SEO-friendly slugs
- Active status (`is_active=true`)
- Linked to their respective regions

**Sample countries:**
- United Arab Emirates (AE)
- Saudi Arabia (SA)
- India (IN)
- United States (US)
- United Kingdom (GB)
- And 45 more...

## Features

### Idempotent Operation

The script is safe to run multiple times:
- Skips existing regions and countries
- Only creates new entries
- No duplicate data issues

### Detailed Logging

```
INFO:__main__:✓ Created region: Middle East
INFO:__main__:  ✓ Created country: United Arab Emirates (AE)
INFO:__main__:  ✓ Created country: Saudi Arabia (SA)
...
INFO:__main__:Regions created: 9
INFO:__main__:Countries created: 50
```

### Verification

After seeding, the script automatically verifies:
- Total regions count
- Total countries count
- Active countries count
- Sample data display

## API Endpoints After Seeding

Once seeded, you can access:

### List All Regions
```http
GET /regions/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Middle East",
    "slug": "middle-east",
    "is_active": true,
    "country_count": 8
  }
]
```

### List All Countries
```http
GET /countries/
```

### List Active Countries Only
```http
GET /countries/?active_only=true
```

### Filter Countries by Region
```http
GET /countries/?region_id=<region-uuid>
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "United Arab Emirates",
    "slug": "united-arab-emirates",
    "country_code": "AE",
    "region_id": "uuid",
    "is_active": true
  }
]
```

## Customization

### Adding More Countries

Edit `scripts/seed_regions_countries.py` and add to the `REGIONS_DATA` structure:

```python
{
    "name": "Your Region",
    "slug": "your-region",
    "is_active": True,
    "countries": [
        {"name": "Country Name", "slug": "country-slug", "code": "CC"},
    ]
}
```

Then run the script again - it will only add new entries.

### Deactivating Countries

To deactivate a country without deleting it:

```http
PUT /countries/{country_id}
Authorization: Bearer <admin-token>

{
  "is_active": false
}
```

## Troubleshooting

### Empty Response from `/countries/?active_only=true`

**Problem:** Getting `[]` empty array

**Solution:** Run the seed script:
```bash
python scripts/seed_regions_countries.py
```

### "IntegrityError: duplicate key"

**Problem:** Data already exists

**Solution:** This is normal - the script skips existing entries. Check the logs to see what was skipped.

### "No module named 'app'"

**Problem:** Script can't find the app module

**Solution:** 
- Make sure you're in the project root directory
- Activate your virtual environment: `source .venv/bin/activate`

### "Database connection failed"

**Problem:** Can't connect to database

**Solution:** Check your `DATABASE_URL` environment variable:
```bash
echo $DATABASE_URL
```

## Integration with Coupons

After seeding, you can:

1. **Assign coupons to countries:**
```http
POST /coupons/
{
  "title": "UAE Special Offer",
  "country_ids": ["<uae-country-uuid>"],
  ...
}
```

2. **Filter coupons by country:**
```http
GET /coupons/?country_id=<country-uuid>
```

3. **Browse coupons in a country:**
```http
GET /countries/united-arab-emirates/coupons
```

## Best Practices

1. **Run seeding early** - Seed regions and countries before creating coupons
2. **Use in CI/CD** - Add seeding to your deployment pipeline for new environments
3. **Backup first** - Always backup production database before seeding
4. **Test locally** - Test seed scripts in development before production
5. **Version control** - Keep seed data in version control for consistency

## Production Deployment

### First Time Setup

```bash
# 1. Deploy your application
make deploy

# 2. Create admin user
make create-admin

# 3. Seed regions and countries
make seed-data

# 4. Verify
curl https://api.vouchergalaxy.com/countries/?active_only=true
```

### Updating Seed Data

```bash
# 1. Update scripts/seed_regions_countries.py
# 2. Commit changes
git add scripts/seed_regions_countries.py
git commit -m "Add new countries"
git push

# 3. Deploy
make deploy

# 4. Run seed script (will only add new entries)
make seed-data
```

## Related Documentation

- [API Documentation](./API_DOCUMENTATION.md)
- [Database Scripts README](../scripts/README.md)
- [Deployment Guide](../README.md)
