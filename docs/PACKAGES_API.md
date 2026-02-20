# Packages API — Frontend Guide

Base URL: `/packages`

All admin endpoints require `Authorization: Bearer <token>` header.

> **Pricing is auto-computed** — the package price is the sum of all its coupons' prices, calculated per currency. You don't set it manually.

---

## How It Works

1. **Create coupons first** — coupons are created normally using `POST /coupons/`, just like before.

2. **Create a package** — call `POST /packages/` with a name, slug, and a list of coupon IDs. The backend links those coupons to the package.

3. **Coupons get flagged** — when a coupon is added to a package, it gets marked as `is_package_coupon = true`. This hides it from the regular `GET /coupons/` listing so it only shows up inside its package.

4. **Pricing is automatic** — you don't set a price on the package. The backend adds up each coupon's price per currency and returns the total as the package price.

5. **Fetching a package** — call `GET /packages/{package_id}` to get the package details along with its coupons and computed pricing. Or call `GET /packages/{package_id}/coupons` to get just the full coupon list.

6. **Adding/removing coupons later** — use `POST /packages/{package_id}/coupons` to add more coupons, or `DELETE /packages/{package_id}/coupons/{coupon_id}` to remove one. Pricing recalculates automatically each time.

---

## 1. Create Package

`POST /packages/` — **Admin only**

**Request Body:**

```json
{
  "name": "Holiday Bundle",
  "slug": "holiday-bundle",
  "description": "Get 5 top coupons at a discounted price",
  "picture_url": "https://cdn.example.com/holiday-bundle.jpg",
  "category_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "is_active": true,
  "is_featured": false,
  "coupon_ids": [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222"
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | ✅ | 2–200 chars |
| `slug` | string | ✅ | Lowercase, numbers, hyphens only |
| `description` | string | ❌ | |
| `picture_url` | string | ❌ | |
| `category_id` | UUID | ❌ | Link to an existing category |
| `is_active` | boolean | ❌ | Default `true` |
| `is_featured` | boolean | ❌ | Default `false` |
| `coupon_ids` | UUID[] | ❌ | Coupons to include in this package |

**Response:** `201 Created`

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "Holiday Bundle",
  "slug": "holiday-bundle",
  "description": "Get 5 top coupons at a discounted price",
  "picture_url": "https://cdn.example.com/holiday-bundle.jpg",
  "category_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "is_active": true,
  "is_featured": false,
  "created_at": "2026-02-20T09:00:00",
  "pricing": {
    "USD": { "price": 5.98, "discount_amount": 100.0 },
    "INR": { "price": 499, "discount_amount": 8000 }
  },
  "category": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "Electronics",
    "slug": "electronics"
  },
  "coupons": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "title": "50% Off Electronics",
      "brand": "TechStore",
      "discount_type": "percentage",
      "discount_amount": 50.0,
      "picture_url": "https://cdn.example.com/coupon1.jpg"
    }
  ]
}
```

> **`pricing` is read-only** — it's the sum of each coupon's prices grouped by currency. If a coupon only has a base `price` (no multi-currency `pricing` JSON), it sums under a `"DEFAULT"` currency key.

---

## 2. List All Packages

`GET /packages/` — **Public**

**Query Parameters:**

| Param | Type | Default | Notes |
|---|---|---|---|
| `skip` | int | `0` | Pagination offset |
| `limit` | int | `100` | Max 100 |
| `category_id` | UUID | — | Filter by category |
| `is_active` | boolean | — | Filter active/inactive |
| `is_featured` | boolean | — | Filter featured |

**Response:** `200 OK` — Array of packages (lightweight, no nested coupons)

```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Holiday Bundle",
    "slug": "holiday-bundle",
    "description": "Get 5 top coupons at a discounted price",
    "picture_url": "https://cdn.example.com/holiday-bundle.jpg",
    "category_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "is_active": true,
    "is_featured": false,
    "created_at": "2026-02-20T09:00:00",
    "pricing": {
      "USD": { "price": 5.98 }
    },
    "category": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Electronics",
      "slug": "electronics"
    },
    "coupon_count": 3
  }
]
```

> The list endpoint returns `coupon_count` (integer) instead of the full `coupons` array. Use the detail endpoint for full coupon data.

---

## 3. Get Package by ID

`GET /packages/{package_id}` — **Public**

**Response:** `200 OK` — Full package with nested coupons and computed pricing (same shape as Create response)

**Error:** `404` if package not found

---

## 4. Get Coupons in Package

`GET /packages/{package_id}/coupons` — **Public**

Returns the full coupon objects (same shape as `/coupons/` listing).

**Response:** `200 OK`

```json
[
  {
    "id": "11111111-1111-1111-1111-111111111111",
    "brand": "TechStore",
    "title": "50% Off Electronics",
    "description": "Half price on all electronics",
    "discount_type": "percentage",
    "discount_amount": 50.0,
    "price": 2.99,
    "min_purchase": 0.0,
    "max_uses": null,
    "expiration_date": null,
    "stock": 100,
    "is_featured": false,
    "is_active": true,
    "is_package_coupon": true,
    "picture_url": "https://cdn.example.com/coupon1.jpg",
    "pricing": { "USD": { "price": 2.99, "discount_amount": 50.0 } },
    "category_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "availability_type": "online",
    "country_ids": [],
    "current_uses": 0,
    "stock_sold": 0,
    "created_at": "2026-02-20T09:00:00",
    "category": { "id": "...", "name": "Electronics", "slug": "electronics" },
    "countries": []
  }
]
```

---

## 5. Update Package

`PUT /packages/{package_id}` — **Admin only**

Send only the fields you want to update. If `coupon_ids` is provided, it **replaces** the entire coupon list (and pricing recalculates automatically).

**Request Body (partial update):**

```json
{
  "name": "Updated Bundle Name",
  "coupon_ids": [
    "33333333-3333-3333-3333-333333333333"
  ]
}
```

**Response:** `200 OK` — Full package response with recalculated pricing

---

## 6. Delete Package

`DELETE /packages/{package_id}` — **Admin only**

**Response:** `204 No Content`

> Deleting a package removes the package and its coupon associations. The coupons themselves are **not** deleted.

---

## 7. Add Coupons to Package

`POST /packages/{package_id}/coupons` — **Admin only**

Adds coupons to an existing package without removing existing ones. Duplicates are silently ignored. Pricing recalculates automatically.

**Request Body:**

```json
[
  "44444444-4444-4444-4444-444444444444",
  "55555555-5555-5555-5555-555555555555"
]
```

**Response:** `200 OK` — Full package response with updated coupons and recalculated pricing

---

## 8. Remove Coupon from Package

`DELETE /packages/{package_id}/coupons/{coupon_id}` — **Admin only**

**Response:** `200 OK` — Full package response with the coupon removed and pricing recalculated

---

## Pricing Computation

Package pricing is **never set manually**. It is always computed as:

```
For each currency in the coupons' pricing JSON:
  package.pricing[currency][key] = SUM of coupon.pricing[currency][key]

For coupons without multi-currency pricing:
  package.pricing["DEFAULT"]["price"] = SUM of coupon.price
```

**Example:** If a package has 2 coupons:
- Coupon A: `pricing: { "USD": { "price": 2.99 }, "INR": { "price": 249 } }`
- Coupon B: `pricing: { "USD": { "price": 4.99 }, "INR": { "price": 399 } }`

The package response will contain:
```json
"pricing": {
  "USD": { "price": 7.98 },
  "INR": { "price": 648 }
}
```

---

## Coupon Changes

Coupons now have an additional field:

| Field | Type | Notes |
|---|---|---|
| `is_package_coupon` | boolean | `true` if the coupon belongs to a package |

This field appears in all coupon responses (`/coupons/`, `/coupons/{id}`, etc.). Package coupons are **hidden** from the regular `GET /coupons/` listing — they only appear through the package endpoints above.

---

## Error Responses

All errors follow the standard format:

```json
{
  "detail": "Error message here"
}
```

| Status | Meaning |
|---|---|
| `400` | Validation error |
| `403` | Non-admin trying to access admin endpoint |
| `404` | Package or coupon not found |
| `422` | Invalid request body |
