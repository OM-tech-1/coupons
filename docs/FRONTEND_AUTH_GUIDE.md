# Frontend Authentication Guide - Email & Password Reset

Complete guide for implementing email-based authentication and password reset functionality.

## Table of Contents
1. [Email Signup](#email-signup)
2. [Email Login](#email-login)
3. [Forgot Password Flow](#forgot-password-flow)
4. [Reset Password](#reset-password)
5. [Change Password (Authenticated)](#change-password-authenticated)
6. [Error Handling](#error-handling)
7. [Complete Examples](#complete-examples)

---

## Base URL

```
Production: https://api.vouchergalaxy.com
Development: http://localhost:8000
```

All endpoints are prefixed with `/auth`

---

## Unified Signup

Register a new user providing both email and phone number details.

### Endpoint
```
POST /auth/register
```

### Request Body
```json
{
  "email": "user@example.com",
  "country_code": "+91",
  "number": "9876543210",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |
| `country_code` | string | Yes | E.g., +91 |
| `number` | string | Yes | Mobile number |
| `password` | string | Yes | Minimum 8 characters |
| `full_name` | string | No | User's full name |

### Success Response (201 Created)
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

### Frontend Example (React)
```javascript
const signup = async (email, countryCode, number, password, fullName) => {
  try {
    const response = await fetch('https://api.vouchergalaxy.com/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        country_code: countryCode,
        number,
        password,
        full_name: fullName
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    const user = await response.json();
    return user;
  } catch (error) {
    console.error('Signup error:', error.message);
    throw error;
  }
};
```

---

## Unified Login

Authenticate user with their credentials (Email, Country Code, and Number are all mandatory).

### Endpoint
```
POST /auth/login
```

### Request Body
```json
{
  "email": "user@example.com",
  "country_code": "+91",
  "number": "9876543210",
  "password": "SecurePass123!"
}
```

### Success Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Frontend Example (React)
```javascript
const login = async (email, countryCode, number, password) => {
  try {
    const response = await fetch('https://api.vouchergalaxy.com/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, country_code: countryCode, number, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const { access_token } = await response.json();
    localStorage.setItem('access_token', access_token);
    return access_token;
  } catch (error) {
    console.error('Login error:', error.message);
    throw error;
  }
};
```

---

## Forgot Password Flow

Request a **Magic Link** to reset password. 
1. Request Link (this endpoint)
2. User clicks link and is redirected to your frontend
3. Reset password with Token (next section)

### Endpoint
```
POST /auth/forgot-password
```

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "If that email is registered, a password reset link has been sent."
}
```

### Magic Link Email
User will receive an email with a button pointing to:
`https://frontend.com/reset-password?token=JWT_TOKEN_HERE`

### Frontend Example (React)
```javascript
const requestMagicLink = async (email) => {
  try {
    const response = await fetch('https://api.vouchergalaxy.com/auth/forgot-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email })
    });

    const result = await response.json();
    console.log(result.message);
    return result;
  } catch (error) {
    console.error('Forgot password error:', error.message);
    throw error;
  }
};
```

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

### Frontend Example (React)
```javascript
const confirmReset = async (token, newPassword) => {
  try {
    const response = await fetch('https://api.vouchergalaxy.com/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token,
        new_password: newPassword
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Reset failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Reset password error:', error.message);
    throw error;
  }
};
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

### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current_password` | string | Yes | Current password |
| `new_password` | string | Yes | New password (must meet requirements) |
| `confirm_password` | string | Yes | Must match new_password |

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Password updated successfully"
}
```

### Error Responses

**401 Unauthorized** - Not authenticated
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden** - Wrong current password
```json
{
  "detail": "Current password is incorrect"
}
```

**422 Validation Error** - Password doesn't meet requirements
```json
{
  "detail": [
    {
      "loc": ["body", "new_password"],
      "msg": "New password must contain at least one uppercase letter",
      "type": "value_error"
    }
  ]
}
```

### Frontend Example (React)
```javascript
const changePassword = async (currentPassword, newPassword, confirmPassword) => {
  try {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch('https://api.vouchergalaxy.com/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Change password failed');
    }

    const result = await response.json();
    console.log(result.message);
    
    return result;
  } catch (error) {
    console.error('Change password error:', error.message);
    throw error;
  }
};
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 201 | Created | User registered successfully |
| 400 | Bad Request | Show validation error to user |
| 401 | Unauthorized | Invalid credentials or token |
| 403 | Forbidden | User doesn't have permission |
| 422 | Validation Error | Show field-specific errors |
| 429 | Rate Limited | Ask user to wait and retry |
| 500 | Server Error | Show generic error message |

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/register` | 10 requests | per minute |
| `/auth/login` | 10 requests | per minute |
| `/auth/forgot-password` | 5 requests | per minute |
| `/auth/reset-password` | 5 requests | per minute |
| `/auth/change-password` | 5 requests | per minute |

### Error Response Format

All errors follow this structure:
```json
{
  "detail": "Error message" 
}
```

Or for validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

---

## Complete Examples

### Complete Password Reset Flow (React)

```javascript
import { useState } from 'react';

// Step 1: Forgot Password Page
function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('https://api.vouchergalaxy.com/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const result = await response.json();
      setMessage(result.message);
      
      // Redirect to OTP page after 2 seconds
      setTimeout(() => {
        window.location.href = `/reset-password?email=${encodeURIComponent(email)}`;
      }, 2000);
    } catch (error) {
      setMessage('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Forgot Password</h2>
      <input
        type="email"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Sending...' : 'Send OTP'}
      </button>
      {message && <p>{message}</p>}
    </form>
  );
}

// Step 2: Reset Password Page
function ResetPasswordPage() {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('https://api.vouchergalaxy.com/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp, new_password: newPassword })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }

      const result = await response.json();
      alert(result.message);
      
      // Redirect to login
      window.location.href = '/login';
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Reset Password</h2>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="text"
        placeholder="Enter 6-digit OTP"
        value={otp}
        onChange={(e) => setOtp(e.target.value)}
        maxLength={6}
        required
      />
      <input
        type="password"
        placeholder="New Password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Resetting...' : 'Reset Password'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </form>
  );
}
```

### Complete Auth Context (React)

```javascript
import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // Fetch user profile
      fetchUserProfile(token);
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUserProfile = async (token) => {
    try {
      const response = await fetch('https://api.vouchergalaxy.com/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        logout();
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email, password, fullName) => {
    const response = await fetch('https://api.vouchergalaxy.com/auth/signup-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    return await response.json();
  };

  const login = async (email, password) => {
    const response = await fetch('https://api.vouchergalaxy.com/auth/login-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const { access_token } = await response.json();
    localStorage.setItem('access_token', access_token);
    setToken(access_token);
    await fetchUserProfile(access_token);
    
    return access_token;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    signup,
    login,
    logout,
    isAuthenticated: !!token
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
```

### Usage in Components

```javascript
import { useAuth } from './AuthContext';

function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit">Login</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <a href="/forgot-password">Forgot Password?</a>
    </form>
  );
}
```

---

## Testing

### Test Credentials (Development Only)

Use these for testing in development:

```
Email: test@vouchergalaxy.com
Password: TestPass123!
```

### Postman Collection

Import this collection to test all endpoints:

```json
{
  "info": {
    "name": "VoucherGalaxy Auth",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Register",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/auth/register",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"test@example.com\",\n  \"country_code\": \"+91\",\n  \"number\": \"9876543210\",\n  \"password\": \"TestPass123!\",\n  \"full_name\": \"Test User\"\n}"
        }
      }
    },
    {
      "name": "Login",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/auth/login",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"test@example.com\",\n  \"country_code\": \"+91\",\n  \"number\": \"9876543210\",\n  \"password\": \"TestPass123!\"\n}"
        }
      }
    },
    {
      "name": "Forgot Password",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/auth/forgot-password",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"test@example.com\"\n}"
        }
      }
    },
    {
      "name": "Reset Password",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/auth/reset-password",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"token\": \"JWT_TOKEN_HERE\",\n  \"new_password\": \"NewPass123!\"\n}"
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "https://api.vouchergalaxy.com"
    }
  ]
}
```

---

## Support

For issues or questions:
- Backend API: Contact backend team
- Email delivery: Check SMTP configuration
- Rate limiting: Wait and retry after cooldown period

## Changelog

- **v1.0** - Initial email authentication and password reset implementation
