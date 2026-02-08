# 🌐 Voucher Galaxy Production API Summary

This document provides a high-level overview of all available API endpoints currently deployed in production.

---

## 🔐 1. Authentication
**Base URL:** `https://api.vouchergalaxy.com/auth`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/register` | `POST` | Create a new user account. |
| `/login` | `POST` | Authenticate and receive a JWT access token. |

---

## 🎟️ 2. Coupons & Catalog
**Base URL:** `https://api.vouchergalaxy.com`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/coupons/` | `GET` | List all available coupons (paginated). |
| `/coupons/{id}` | `GET` | Get detailed information about a specific coupon. |
| `/categories/` | `GET` | List coupon categories (Food, Travel, etc.). |
| `/countries/` | `GET` | List supported countries. |
| `/regions/` | `GET` | List supported geographic regions. |

---

## 🛒 3. Shopping Cart & Orders
**Base URL:** `https://api.vouchergalaxy.com`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/cart/` | `GET` | View items currently in the user's cart. |
| `/cart/add` | `POST` | Add a coupon to the cart. |
| `/cart/remove/{item_id}` | `DELETE` | Remove an item from the cart. |
| `/cart/` | `DELETE` | Clear the entire cart. |
| `/orders/checkout` | `POST` | Initialize checkout and create a pending order. |
| `/orders/` | `GET` | View user's order history. |

---

## 💳 4. Payments (Stripe & Redirection)
**Base URL:** `https://api.vouchergalaxy.com`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/payments/init` | `POST` | Initialize a payment session for an internal order. |
| `/payments/validate-token` | `POST` | Validate a payment token and return Stripe secrets. |
| `/payments/status/{order_id}`| `GET` | Check the current status of a payment/order. |
| `/payments/mark-token-used` | `POST` | Invalidate a token after successful payment. |

---

## 🔌 5. External Integrations (Third-Party)
**Base URL:** `https://api.vouchergalaxy.com/api/v1/external`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/payment-link` | `POST` | **Signed Request**: Generate a hosted payment link. |

---

## 🛠️ 6. Admin Dashboard
**Base URL:** `https://api.vouchergalaxy.com/admin`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/stats` | `GET` | Get platform-wide statistics (active users, orders). |
| `/users` | `GET` | Manage site users. |
| `/coupons` | `POST/PUT` | Create or update coupon inventory. |

---

## 🏥 7. System Health
**Base URL:** `https://api.vouchergalaxy.com`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Basic service status check. |
| `/health` | `GET` | Detailed check (API + Database status). |

---

## 📘 Developer Resources
- **Swagger Documentation**: `https://api.vouchergalaxy.com/docs` (Interactive UI)
- **Redoc Documentation**: `https://api.vouchergalaxy.com/redoc` (Clean Reference)
- **Security Guide**: [API_PAYMENT_LINK_GUIDE.md](file:///Users/jihane/Documents/coupons/API_PAYMENT_LINK_GUIDE.md)
