# Soft Delete Guide - Coupons & Packages

## Overview

When you "delete" a coupon or package in the admin panel, it's not actually removed from the database. Instead, it's **soft deleted** by setting `is_active = false`. This preserves data integrity and ensures users who already purchased items can still access them.

---

## How It Works

### What Happens When You Delete?

**Coupons:**
- If the coupon is in someone's cart or has been purchased → Set `is_active = false` (soft delete)
- If the coupon has never been used → Actually delete from database (hard delete)

**Packages:**
- If the package has been purchased → Set `is_active = false` (soft delete)
- If the package has never been purchased → Actually delete from database (hard delete)

### Why Soft Delete?

1. **Preserves order history** - Past orders still show what was purchased
2. **Protects user wallets** - Users keep access to coupons they paid for
3. **Maintains data integrity** - No broken references in the database
4. **Enables analytics** - You can still see historical data for deleted items

---

## API Behavior

### For Regular Users

#### Coupon Listing
```
GET /coupons/
```
- **Default behavior:** Only shows `is_active = true` coupons
- **Result:** Deleted coupons are hidden from users
- **Override:** Add `?active_only=false` to see all (not recommended for users)

**Example:**
```bash
# Users see only active coupons
GET /coupons/

# Admin can see all coupons including deleted ones
GET /coupons/?active_only=false
```

#### Package Listing
```
GET /packages/
```
- **Default behavior:** Only shows `is_active = true` packages
- **Result:** Deleted packages are hidden from users
- **Override:** Add `?is_active=false` to see inactive ones

**Example:**
```bash
# Users see only active packages
GET /packages/

# See inactive packages
GET /packages/?is_active=false
```

#### User Wallet
```
GET /user/wallet/coupons
```
- **Behavior:** Shows ALL owned coupons (active AND inactive)
- **Why:** Users paid for these coupons, they should keep access even if admin deleted them later
- **Result:** Users can still see and use coupons they purchased, even if deleted

**Example:**
```bash
# User's wallet shows all their coupons
GET /user/wallet/coupons

# Response includes both active and inactive coupons
{
  "coupons": [
    {
      "id": "...",
      "title": "50% Off Pizza",
      "is_active": true,  // Still available for purchase
      "status": "available"
    },
    {
      "id": "...",
      "title": "Free Burger",
      "is_active": false,  // Deleted by admin, but user still owns it
      "status": "available"
    }
  ]
}
```

---

### For Admins

#### View All Coupons (Including Deleted)
```
GET /coupons/?active_only=false
```
- Shows both active and inactive coupons
- Use this to see what's been deleted

#### View All Packages (Including Deleted)
```
GET /packages/?is_active=false
```
- Shows only inactive packages
- Or omit the parameter to see active ones

#### Admin Analytics
```
GET /admin/analytics/coupons
```
- **Default behavior:** Shows ALL coupons (active and inactive)
- **Override:** Add `?active_only=true` to see only active ones
- **Use case:** See performance of deleted coupons

**Example:**
```bash
# See analytics for all coupons (including deleted)
GET /admin/analytics/coupons

# See analytics for only active coupons
GET /admin/analytics/coupons?active_only=true
```

---

## Frontend Implementation Guide

### User-Facing Pages

#### 1. Coupon Browse Page
```javascript
// Fetch only active coupons (default)
fetch('/coupons/')
  .then(res => res.json())
  .then(coupons => {
    // Only active coupons are returned
    // Deleted coupons won't appear here
  });
```

#### 2. Package Browse Page
```javascript
// Fetch only active packages (default)
fetch('/packages/')
  .then(res => res.json())
  .then(packages => {
    // Only active packages are returned
  });
```

#### 3. User Wallet Page
```javascript
// Fetch ALL owned coupons (including deleted ones)
fetch('/user/wallet/coupons')
  .then(res => res.json())
  .then(coupons => {
    // User sees all coupons they own
    // Even if admin deleted them
    
    coupons.forEach(coupon => {
      if (!coupon.is_active) {
        // Show a badge: "No longer available for purchase"
        // But user can still use their copy
      }
    });
  });
```

### Admin Panel

#### 1. Coupon Management Page
```javascript
// Show all coupons including deleted ones
fetch('/coupons/?active_only=false')
  .then(res => res.json())
  .then(coupons => {
    coupons.forEach(coupon => {
      if (!coupon.is_active) {
        // Show "DELETED" badge
        // Add "Restore" button to set is_active = true
      }
    });
  });
```

#### 2. Package Management Page
```javascript
// Show all packages
fetch('/packages/?is_active=false')
  .then(res => res.json())
  .then(packages => {
    // These are deleted packages
    // Show with "DELETED" badge
  });

// Or show both active and inactive
Promise.all([
  fetch('/packages/?is_active=true'),
  fetch('/packages/?is_active=false')
]).then(([active, inactive]) => {
  // Combine and display with different styling
});
```

#### 3. Analytics Dashboard
```javascript
// Get analytics for all coupons (including deleted)
fetch('/admin/analytics/coupons')
  .then(res => res.json())
  .then(analytics => {
    // Shows performance of all coupons
    // Including ones that were deleted
  });
```

---

## Visual Indicators (Frontend Recommendations)

### User Wallet
When showing coupons in user wallet:

```
✅ Active Coupon
   "50% Off Pizza"
   Status: Available
   
⚠️ Inactive Coupon (Deleted by Admin)
   "Free Burger"
   Status: Available (Your copy is still valid)
   Note: No longer available for new purchases
```

### Admin Panel
When showing coupons/packages in admin:

```
✅ ACTIVE
   "50% Off Pizza"
   [Edit] [Delete]
   
❌ DELETED
   "Free Burger"
   [Restore] [Permanently Delete]
   Note: 15 users still own this coupon
```

---

## API Quick Reference

| Endpoint | Default Behavior | Who Sees What |
|----------|------------------|---------------|
| `GET /coupons/` | `active_only=true` | Users: Active only<br>Admin: Can override with `?active_only=false` |
| `GET /packages/` | `is_active=true` | Users: Active only<br>Admin: Can override with `?is_active=false` |
| `GET /user/wallet/coupons` | All owned | Users: ALL their coupons (active + inactive) |
| `GET /admin/analytics/coupons` | `active_only=false` | Admin: All coupons including deleted |

---

## Common Questions

**Q: If I delete a coupon, will users lose access to it?**
A: No! Users who already purchased it will keep it in their wallet and can still use it.

**Q: How do I permanently delete a coupon?**
A: The system automatically does a hard delete if the coupon has never been purchased or added to a cart. Otherwise, it's soft deleted to protect user data.

**Q: Can I restore a deleted coupon?**
A: Yes! Use the update endpoint to set `is_active = true`:
```bash
PUT /coupons/{coupon_id}
{
  "is_active": true
}
```

**Q: How do users know if a coupon in their wallet is deleted?**
A: The API returns `is_active: false`. Show a message like "This coupon is no longer available for purchase, but your copy is still valid."

**Q: Will deleted coupons show in search results?**
A: No, only active coupons appear in public search results.

---

## Testing Checklist

- [ ] Delete a coupon that's in someone's cart → Should soft delete
- [ ] Delete a coupon that's been purchased → Should soft delete
- [ ] Delete a coupon that's never been used → Should hard delete
- [ ] User wallet shows deleted coupons they own
- [ ] Public coupon list doesn't show deleted coupons
- [ ] Admin can see deleted coupons with `?active_only=false`
- [ ] Restore a deleted coupon by setting `is_active = true`

---

## Summary

✅ **Soft delete protects user data**
✅ **Users keep what they paid for**
✅ **Admins can see everything**
✅ **Public listings stay clean**
✅ **Data integrity is maintained**
