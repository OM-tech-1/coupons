# Postman Collection Guide

Complete guide for using the VoucherGalaxy API Postman collection.

## Import Collection

1. Open Postman
2. Click "Import" button
3. Select `VoucherGalaxy_Complete_API.postman_collection.json`
4. Collection will be imported with all endpoints

## Environment Variables

Set these variables in your Postman environment:

| Variable | Description | Example |
|----------|-------------|---------|
| `base_url` | API base URL | `https://api.vouchergalaxy.com` |
| `access_token` | JWT token from login | Auto-set after login |

### Quick Setup

1. Create new environment in Postman
2. Add variable `base_url` with value `https://api.vouchergalaxy.com`
3. Add variable `access_token` (leave empty, will be set after login)

## Authentication Flow

### Step 1: Register or Login

**Register (Unified)**
- Endpoint: `POST /auth/register`
- Payload requires both email and phone number
- Returns user object

**Login (Unified)**
- Endpoint: `POST /auth/login`
- Payload requires both email and phone number
- Returns `access_token`

### Step 2: Set Token

After login, copy the `access_token` from response and:
1. Go to your environment
2. Set `access_token` variable
3. Or use the collection-level auth (already configured)

### Step 3: Make Authenticated Requests

All endpoints marked with 🔒 require authentication.

## API Endpoints Overview

### 🔓 Authentication (No Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register with email and phone |
| `/auth/login` | POST | Login with email and phone |
| `/auth/forgot-password` | POST | Request magic link for password reset |
| `/auth/reset-password` | POST | Reset password with token from magic link |

### 🔒 Authentication (Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/change-password` | POST | Change password (logged in) |

### 🔒 User Profile

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/me` | GET | Get current user profile |
| `/users/me` | PUT | Update profile |
| `/users/wallet` | GET | Get wallet summary |
| `/users/wallet/coupons` | GET | Get wallet coupons |
| `/users/coupons` | GET | Get my coupons |
| `/users/coupons/:id` | GET | Get coupon detail |
| `/users/coupons/:id/mark-used` | POST | Mark coupon as used |

### 🔓 Packages (Public)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/packages` | GET | List packages with filters |
| `/packages/:id` | GET | Get package by ID |
| `/packages/:id/coupons` | GET | Get package coupons |

### 🔒 Packages (Admin Only)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/packages` | POST | Create package |
| `/packages/:id` | PUT | Update package |
| `/packages/:id` | DELETE | Delete package |

### 🔒 Cart

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cart` | GET | Get cart |
| `/cart/add` | POST | Add item to cart |
| `/cart/:id` | DELETE | Remove item |
| `/cart` | DELETE | Clear cart |

### 🔒 Orders

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/orders/checkout` | POST | Checkout cart |
| `/orders` | GET | Get my orders |
| `/orders/:id` | GET | Get order by ID |
| `/orders/:id/invoice` | GET | Download invoice PDF |

### 🔓 Contact Messages

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/contact` | POST | Submit contact message (public) |

### 🔒 Contact Messages (Admin)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/contact/admin` | GET | List messages with filters |
| `/contact/admin/:id` | GET | Get message by ID |
| `/contact/admin/:id` | PATCH | Update message status |

### 🔓 Coupons (Public)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/coupons` | GET | List coupons with filters |
| `/coupons/:id` | GET | Get coupon by ID |

### 🔓 Categories (Public)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/categories` | GET | List categories |
| `/categories/:id` | GET | Get category by ID |

### 🔓 Regions & Countries (Public)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/regions` | GET | List regions |
| `/countries` | GET | List countries |

### 🔓 Payments

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/payments/create-link` | POST | Create payment link |

### 🔒 Stripe Payments

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stripe/create-payment-intent` | POST | Create Stripe payment intent |

## Complete Request Examples

### 1. Register (Unified)

```json
POST /auth/register

{
  "email": "user@example.com",
  "country_code": "+971",
  "number": "501234567",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "phone_number": "+971501234567",
  "full_name": "John Doe",
  "role": "USER",
  "is_active": true,
  "created_at": "2024-03-10T10:30:00Z"
}
```

### 2. Login (Unified)

```json
POST /auth/login

{
  "email": "user@example.com",
  "country_code": "+971",
  "number": "501234567",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Update Profile

```json
PUT /users/me
Authorization: Bearer {{access_token}}

{
  "full_name": "John Doe Updated",
  "second_name": "Smith",
  "email": "john.doe@example.com",
  "date_of_birth": "1990-01-15",
  "gender": "Male",
  "country_of_residence": "United Arab Emirates",
  "home_address": "123 Main Street, Apt 4B",
  "town": "Dubai",
  "state_province": "Dubai",
  "postal_code": "12345",
  "address_country": "United Arab Emirates"
}
```

### 4. List Packages with Filters

```
GET /packages?skip=0&limit=20&is_active=true&filter=highest_saving&country=UAE&brands=Nike,Adidas
```

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Items per page (default: 100, max: 100)
- `category_id`: Filter by category UUID
- `is_active`: Filter by active status (true/false)
- `is_featured`: Filter by featured status (true/false)
- `filter`: Sort by (highest_saving, newest, avg_rating, bundle_sold)
- `country`: Filter by country (UAE, KSA, etc.)
- `brands`: Comma-separated brand names

### 5. Create Package (Admin)

```json
POST /packages
Authorization: Bearer {{access_token}}

{
  "name": "Premium Bundle",
  "slug": "premium-bundle",
  "description": "Amazing bundle with multiple coupons",
  "picture_url": "https://example.com/image.jpg",
  "brand": "Nike",
  "brand_url": "https://nike.com",
  "discount": 25.5,
  "category_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": true,
  "is_featured": false,
  "expiration_date": "2025-12-31",
  "country": "UAE",
  "coupon_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

### 6. Add to Cart

**Add Coupon:**
```json
POST /cart/add
Authorization: Bearer {{access_token}}

{
  "coupon_id": "550e8400-e29b-41d4-a716-446655440000",
  "quantity": 2
}
```

**Add Package:**
```json
POST /cart/add
Authorization: Bearer {{access_token}}

{
  "package_id": "550e8400-e29b-41d4-a716-446655440000",
  "quantity": 1
}
```

### 7. Checkout

```json
POST /orders/checkout
Authorization: Bearer {{access_token}}

{
  "payment_method": "stripe"
}
```

### 8. Submit Contact Message

```json
POST /contact

{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "subject": "Question about my order",
  "message": "I have a question regarding my recent order. Can you please help me?"
}
```

### 9. List Contact Messages (Admin)

```
GET /contact/admin?skip=0&limit=20&status=pending&search=john
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `skip`: Pagination offset
- `limit`: Items per page
- `status`: Filter by status (pending, resolved)
- `search`: Search by name, email, or subject

### 10. Forgot Password Flow

**Step 1: Request Magic Link**
```json
POST /auth/forgot-password

{
  "email": "user@example.com"
}
```

**Step 2: Reset Password**
```json
POST /auth/reset-password

{
  "token": "JWT_TOKEN_FROM_EMAIL",
  "new_password": "NewSecurePass123!"
}
```

## Field Descriptions

### User Profile Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | No | User's full name |
| `second_name` | string | No | User's second/last name |
| `email` | string | No | Email address (unique) |
| `date_of_birth` | date | No | Format: YYYY-MM-DD |
| `gender` | string | No | Male, Female, Other |
| `country_of_residence` | string | No | Country name |
| `home_address` | string | No | Street address |
| `town` | string | No | City/town |
| `state_province` | string | No | State or province |
| `postal_code` | string | No | ZIP/postal code |
| `address_country` | string | No | Country for address |

### Package Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Package name |
| `slug` | string | Yes | URL-friendly identifier |
| `description` | string | No | Package description |
| `picture_url` | string | No | Image URL |
| `brand` | string | No | Brand name |
| `brand_url` | string | No | Brand website URL |
| `discount` | float | No | Discount percentage (0-100) |
| `category_id` | UUID | No | Category reference |
| `is_active` | boolean | No | Active status (default: true) |
| `is_featured` | boolean | No | Featured status (default: false) |
| `expiration_date` | date | No | Format: YYYY-MM-DD |
| `country` | string | No | Country code (UAE, KSA, etc.) |
| `coupon_ids` | array | No | Array of coupon UUIDs |

### Contact Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Sender's name (max 100 chars) |
| `email` | string | Yes | Sender's email (max 150 chars) |
| `subject` | string | Yes | Message subject (max 255 chars) |
| `message` | string | Yes | Message content |
| `status` | string | No | pending or resolved (admin only) |

## Testing Workflow

### Complete User Journey

1. **Register**
   - Use "Register (Unified)" endpoint
   - Provided both email and phone
   - Save user ID

2. **Login**
   - Use "Login (Unified)" endpoint
   - Copy `access_token` to environment variable

3. **Browse Packages**
   - Use "List Packages" endpoint
   - Note package IDs

4. **Add to Cart**
   - Use "Add Package to Cart" endpoint
   - Verify with "Get Cart" endpoint

5. **Checkout**
   - Use "Checkout" endpoint
   - Get order ID

6. **View Order**
   - Use "Get Order by ID" endpoint
   - Download invoice

7. **View Wallet**
   - Use "Get My Wallet Summary" endpoint
   - Use "Get My Wallet Coupons" endpoint

### Admin Testing

1. **Login as Admin**
   - Use admin credentials
   - Set token

2. **Create Package**
   - Use "Create Package" endpoint

3. **Manage Contact Messages**
   - Use "List Contact Messages" endpoint
   - Update status to "resolved"

## Common Issues

### 401 Unauthorized
- Token expired or invalid
- Re-login and update `access_token`

### 403 Forbidden
- Endpoint requires admin role
- Current user doesn't have permission

### 422 Validation Error
- Check request body format
- Verify all required fields
- Check field types and constraints

### 429 Rate Limited
- Too many requests
- Wait and retry

## Rate Limits

| Endpoint Pattern | Limit |
|-----------------|-------|
| `/auth/register` | 10/minute |
| `/auth/login*` | 10/minute |
| `/auth/forgot-password` | 5/minute |
| `/auth/reset-password` | 5/minute |
| `/auth/change-password` | 5/minute |

## Support

For API issues:
- Check response error messages
- Verify request format matches examples
- Ensure authentication token is valid
- Check rate limits

## Changelog

- **v2.1.0** - Updated for unified auth endpoints and magic link password reset
- **v2.0.0** - Complete collection with all endpoints and full payloads
- **v1.0.0** - Initial collection
