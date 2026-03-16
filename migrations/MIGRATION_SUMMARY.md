# Database Migration Summary

This document lists all database migrations needed for the VoucherGalaxy application.

## Migration Order

Run these migrations in order:

### 1. Contact Messages Feature (016)
**File:** `016_create_contact_messages.sql`

Creates the contact messages table for user support requests.

```sql
-- Already exists in migrations folder
-- Creates: contact_messages table with status tracking
```

### 2. User Profile & Email Features (018)
**File:** `018_add_user_profile_fields.sql`

Adds user profile fields, email support, and OTP for password reset.

**New columns added to `users` table:**
- `email` - User email address (unique, indexed)
- `otp` - One-time password for password reset
- `otp_expiry` - OTP expiration timestamp
- `date_of_birth` - User date of birth
- `gender` - User gender
- `country_of_residence` - Country where user resides
- `home_address` - Home address line
- `town` - Town/city
- `state_province` - State or province
- `postal_code` - Postal/ZIP code
- `address_country` - Country for address

## Quick Apply Commands

### For Development/Staging
```bash
# Apply contact messages migration
psql -U your_user -d your_database -f migrations/016_create_contact_messages.sql

# Apply user profile fields migration
psql -U your_user -d your_database -f migrations/018_add_user_profile_fields.sql
```

### For Production (with Docker)
```bash
# Copy migration files to container
docker cp migrations/016_create_contact_messages.sql container_name:/tmp/
docker cp migrations/018_add_user_profile_fields.sql container_name:/tmp/

# Execute migrations
docker exec -it container_name psql -U postgres -d vouchergalaxy -f /tmp/016_create_contact_messages.sql
docker exec -it container_name psql -U postgres -d vouchergalaxy -f /tmp/018_add_user_profile_fields.sql
```

## Verification Queries

After running migrations, verify with these queries:

### Check Contact Messages Table
```sql
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'contact_messages'
ORDER BY ordinal_position;
```

### Check User Profile Fields
```sql
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('email', 'otp', 'otp_expiry', 'date_of_birth', 'gender', 
                     'country_of_residence', 'home_address', 'town', 
                     'state_province', 'postal_code', 'address_country')
ORDER BY ordinal_position;
```

### Check Indexes
```sql
-- Check email index
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'users' 
AND indexname = 'idx_users_email';

-- Check contact messages indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'contact_messages';
```

## Rollback Commands (if needed)

### Rollback User Profile Fields (018)
```sql
ALTER TABLE users DROP COLUMN IF EXISTS email;
ALTER TABLE users DROP COLUMN IF EXISTS otp;
ALTER TABLE users DROP COLUMN IF EXISTS otp_expiry;
ALTER TABLE users DROP COLUMN IF EXISTS date_of_birth;
ALTER TABLE users DROP COLUMN IF EXISTS gender;
ALTER TABLE users DROP COLUMN IF EXISTS country_of_residence;
ALTER TABLE users DROP COLUMN IF EXISTS home_address;
ALTER TABLE users DROP COLUMN IF EXISTS town;
ALTER TABLE users DROP COLUMN IF EXISTS state_province;
ALTER TABLE users DROP COLUMN IF EXISTS postal_code;
ALTER TABLE users DROP COLUMN IF EXISTS address_country;
```

### Rollback Contact Messages (016)
```sql
DROP TRIGGER IF EXISTS trigger_update_contact_messages_updated_at ON contact_messages;
DROP FUNCTION IF EXISTS update_contact_messages_updated_at();
DROP TABLE IF EXISTS contact_messages;
```

## Notes

- All migrations use `IF NOT EXISTS` or `IF EXISTS` clauses for safety
- Migrations are idempotent and can be run multiple times
- Email field is unique and indexed for performance
- OTP fields support password reset functionality
- Contact messages include automatic timestamp updates via trigger
- Profile fields are all nullable to support gradual user profile completion
