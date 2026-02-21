# Workflows — Coupon App

## Table of Contents
- [Coupon CRUD](#coupon-crud)
- [Package CRUD](#package-crud)
- [Package ↔ Coupon Management](#package--coupon-management)

---

## Coupon CRUD

### Create a Coupon (Admin)

```
POST /coupons/
Authorization: Bearer <admin_token>
```

```json
{
  "code": "SUMMER2026",
  "redeem_code": "ACTUAL-CODE-123",
  "brand": "Nike",
  "title": "20% Off All Shoes",
  "description": "Valid on all footwear",
  "discount_type": "percentage",
  "discount_amount": 20.0,
  "price": 5.0,
  "min_purchase": 50.0,
  "stock": 100,
  "is_featured": true,
  "is_active": true,
  "category_id": "<uuid>",
  "country_ids": ["<uuid>", "<uuid>"],
  "availability_type": "online",
  "pricing": {
    "INR": { "price": 400, "discount_amount": 500 },
    "AED": { "price": 20, "discount_amount": 25 },
    "USD": { "price": 5, "discount_amount": 7 }
  }
}
```

**Key rules:**
- `code` — internal identifier (unique, 3-50 chars)
- `redeem_code` — actual coupon code revealed to buyer after purchase
- `pricing` — multi-currency map. If not set, `price` is used as default
- `stock: null` = unlimited stock
- `is_package_coupon` — automatically set by Package operations, don't set manually

### Update a Coupon (Admin)

```
PUT /coupons/<coupon_id>
Authorization: Bearer <admin_token>
```

All fields are optional. Only send the ones you want to change:

```json
{
  "title": "25% Off All Shoes — Updated",
  "discount_amount": 25.0,
  "pricing": {
    "INR": { "price": 350, "discount_amount": 450 }
  }
}
```

### Delete a Coupon (Admin)

```
DELETE /coupons/<coupon_id>
Authorization: Bearer <admin_token>
```

Returns `204 No Content` on success. The coupon is permanently deleted.

> ⚠️ If the coupon belongs to a package, delete it from the package **first** to keep `is_package_coupon` flags consistent.

### List / Browse Coupons (Public)

```
GET /coupons/?skip=0&limit=20&category_id=<uuid>&active_only=true
```

No auth required. Returns `CouponPublicResponse` (no `code` or `redeem_code`).

### Get Coupon Details (Public)

```
GET /coupons/<coupon_id>
```

Records a view for analytics. Returns public coupon info.

---

## Package CRUD

A **Package** is a curated bundle of coupons with auto-computed pricing (sum of coupon prices per currency).

### Create a Package (Admin)

```
POST /packages/
Authorization: Bearer <admin_token>
```

```json
{
  "name": "Summer Travel Bundle",
  "slug": "summer-travel-bundle",
  "description": "Best deals for your summer vacation",
  "picture_url": "https://example.com/package.jpg",
  "category_id": "<uuid>",
  "is_active": true,
  "is_featured": false,
  "coupon_ids": ["<coupon_uuid_1>", "<coupon_uuid_2>"]
}
```

**What happens:**
1. Package record is created
2. Each coupon in `coupon_ids` is linked to the package
3. Those coupons are marked `is_package_coupon = true`
4. `pricing` is auto-computed (sum of each coupon's `pricing` per currency)
5. Package cache is invalidated

**Slug rules:** lowercase letters, numbers, and hyphens only (`^[a-z0-9-]+$`).

### Update a Package (Admin)

```
PUT /packages/<package_id>
Authorization: Bearer <admin_token>
```

All fields optional. Example — update name and swap coupons:

```json
{
  "name": "Winter Travel Bundle",
  "coupon_ids": ["<new_coupon_1>", "<new_coupon_2>"]
}
```

**When `coupon_ids` is provided:**
1. **All existing coupon associations are removed**
2. New associations are created from the provided list
3. `is_package_coupon = true` is set on new coupons
4. Removed coupons that don't belong to **any** other package get `is_package_coupon = false`
5. Pricing is recomputed

> ⚠️ `coupon_ids` is a **full replacement**, not an append. If you want to add coupons without removing existing ones, use the dedicated "Add Coupons" endpoint instead.

### Delete a Package (Admin)

```
DELETE /packages/<package_id>
Authorization: Bearer <admin_token>
```

Returns `204 No Content`.

**What happens:**
1. All coupon ↔ package associations are removed
2. Coupons not in any other package get `is_package_coupon = false`
3. Package record is deleted
4. **Coupons themselves are NOT deleted**

### List Packages (Public)

```
GET /packages/?skip=0&limit=100&is_active=true&is_featured=true&category_id=<uuid>
```

Returns lightweight `PackageListResponse` with `coupon_count` (no nested coupons).

### Get Package Details (Public)

```
GET /packages/<package_id>
```

Returns full `PackageResponse` with nested coupons and computed pricing.

---

## Package ↔ Coupon Management

### Add Coupons to a Package

```
POST /packages/<package_id>/coupons
Authorization: Bearer <admin_token>
```

```json
["<coupon_uuid_1>", "<coupon_uuid_2>"]
```

- Duplicates are silently ignored (no error)
- New coupons are marked `is_package_coupon = true`
- Returns the updated package

### Remove a Coupon from a Package

```
DELETE /packages/<package_id>/coupons/<coupon_id>
Authorization: Bearer <admin_token>
```

- Only removes the association
- If the coupon is no longer in **any** package → `is_package_coupon = false`
- Returns the updated package

### Get Package Coupons

```
GET /packages/<package_id>/coupons
```

Returns the full `CouponPublicResponse` for every coupon in the package.

---

## Common Workflows

### 1. Create a Package with Coupons (from scratch)

```
Step 1: POST /coupons/         → create coupon A   → save coupon_id_A
Step 2: POST /coupons/         → create coupon B   → save coupon_id_B
Step 3: POST /packages/        → body includes coupon_ids: [A, B]
```

### 2. Add an Existing Coupon to a Package

```
Step 1: POST /packages/<pkg_id>/coupons   → body: ["<coupon_id>"]
```

### 3. Replace All Coupons in a Package

```
Step 1: PUT /packages/<pkg_id>   → body: { "coupon_ids": ["<new_1>", "<new_2>"] }
```

Old coupons are unlinked. `is_package_coupon` is reset for orphaned coupons.

### 4. Remove a Single Coupon from a Package

```
Step 1: DELETE /packages/<pkg_id>/coupons/<coupon_id>
```

### 5. Delete a Package (keep coupons)

```
Step 1: DELETE /packages/<pkg_id>
```

Coupons remain in the database. Their `is_package_coupon` flag is cleaned up automatically.

### 6. Delete a Coupon That's in a Package

```
Step 1: DELETE /packages/<pkg_id>/coupons/<coupon_id>   (remove from package first)
Step 2: DELETE /coupons/<coupon_id>                     (then delete the coupon)
```

> Deleting a coupon directly without removing it from the package will leave stale associations and the `is_package_coupon` flag won't be cleaned up properly.
