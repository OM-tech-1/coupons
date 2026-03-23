# Frontend Authentication Guide - Unified Auth & Password Reset

Complete guide for implementing registration, login, and password reset functionality.

## Table of Contents
1. [Unified Signup](#unified-signup)
2. [Unified Login](#unified-login)
3. [Forgot Password Flow](#forgot-password-flow)
4. [Reset Password](#reset-password)
5. [Change Password (Authenticated)](#change-password-authenticated)
6. [Error Handling](#error-handling)

---

## Base URL

```
Production: https://api.vouchergalaxy.com
Development: http://localhost:8000
```

All endpoints are prefixed with `/auth`

---

## Unified Signup

Register a new user. The `email` field is **optional**. Phone details are required.

### Endpoint
```
POST /auth/register
```

### Request Body
```json
{
  "country_code": "+91",
  "number": "9876543210",
  "password": "SecurePass123!",
  "email": "user@example.com", (Optional)
  "full_name": "John Doe" (Optional)
}
```

### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `country_code` | string | Yes | E.g., +91 or 91 |
| `number` | string | Yes | Mobile number without country code |
| `password` | string | Yes | Minimum 8 characters |
| `email` | string | No | Valid email address |
| `full_name` | string | No | User's full name |

### Success Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "phone_number": "+919876543210",
  "full_name": "John Doe",
  "role": "USER",
  "is_active": true,
  "created_at": "2024-03-10T10:30:00Z"
}
```

---

## Unified Login

Authenticate user with their credentials. You can identify the user via Phone Number.

### Endpoint
```
POST /auth/login
```

### Request Body
```json
{
  "country_code": "+91",
  "number": "9876543210",
  "password": "SecurePass123!",
  "email": "user@example.com" (Optional)
}
```

> [!NOTE]
> Authentication currently prioritizes the phone number. Even if `email` is provided, the system validates the `country_code` and `number` fields.

### Success Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Forgot Password Flow

Request a **Magic Link** to reset password. 
1. The user provides their email.
2. The server sends an email with a unique link.
3. The user clicks the link and is redirected to your frontend with a `token`.

### Endpoint
```
POST /auth/forgot-password
```

### Request Body
```json
{
  "email": "user@example.com"
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "If that email is registered, a password reset link has been sent."
}
```

### Magic Link Details
The user will receive an email containing a link:
`https://vouchergalaxy.com/reset-password?token=JWT_TOKEN_HERE`

The frontend must capture the `token` from the query parameter.

---

## Reset Password

Reset password using the `token` received via the magic link.

### Endpoint
```
POST /auth/reset-password
```

### Request Body
```json
{
  "token": "JWT_TOKEN_FROM_URL",
  "new_password": "NewSecurePass123!"
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Password successfully reset."
}
```

---

## Change Password (Authenticated)

Change password for logged-in users. Requires authentication token.

### Endpoint
```
POST /auth/change-password
```

### Headers
```
Authorization: Bearer <access_token>
```

### Request Body
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | User already exists or validation failed |
| 401 | Unauthorized | Invalid credentials |
| 422 | Validation Error | Missing fields or malformed data |
| 429 | Rate Limited | Too many requests |

### Validation Errors
If a phone number is invalid according to international standards, the API returns:
```json
{
  "detail": [
    {
      "loc": ["body"],
      "msg": "Value error, Invalid phone number",
      "type": "value_error"
    }
  ]
}
```
