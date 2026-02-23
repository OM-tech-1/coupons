# Multi-Currency Coupon Response

## Overview

All coupon endpoints now return multi-currency pricing information in the response, allowing the frontend to switch currencies without additional API calls.

## Response Structure

### New Fields Added to Coupons

- `prices`: Object containing price in all supported currencies
- `discounts`: Object containing discount amounts in all supported currencies

### New Fields Added to Packages

- `prices`: Object containing package base price in all supported currencies
- `final_prices`: Object containing final price after discount in all supported currencies
- Each coupon within the package also includes `prices` and `discounts` fields

### Example Coupon Response

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "50% Off Amazon Gift Card",
  "brand": "Amazon",
  "description": "Get 50% off on Amazon gift cards",
  "discount_type": "percentage",
  "discount_amount": 10.0,
  "price": 100.0,
  "min_purchase": 0.0,
  "is_active": true,
  "stock": 100,
  "stock_sold": 25,
  "is_featured": true,
  "created_at": "2024-01-15T10:30:00Z",
  "picture_url": "https://example.com/image.jpg",
  "category": {
    "id": "cat-123",
    "name": "E-commerce",
    "slug": "e-commerce"
  },
  "countries": [
    {
      "id": "country-123",
      "name": "United States",
      "slug": "united-states",
      "country_code": "US"
    }
  ],
  "prices": {
    "USD": 100.0,
    "INR": 8000.0,
    "AED": 367.0,
    "SAR": 375.0,
    "OMR": 38.5
  },
  "discounts": {
    "USD": 10.0,
    "INR": 800.0,
    "AED": 36.7,
    "SAR": 37.5,
    "OMR": 3.85
  }
}
```

### Example Package Response

```json
{
  "id": "pkg-123",
  "name": "Premium Bundle",
  "slug": "premium-bundle",
  "brand": "Amazon",
  "discount": 15.0,
  "avg_rating": 4.5,
  "total_sold": 150,
  "is_featured": true,
  "prices": {
    "USD": 300.0,
    "INR": 24000.0,
    "AED": 1101.0,
    "SAR": 1125.0
  },
  "final_prices": {
    "USD": 255.0,
    "INR": 20400.0,
    "AED": 935.85,
    "SAR": 956.25
  },
  "coupons": [
    {
      "id": "coupon-1",
      "title": "Coupon 1",
      "price": 100.0,
      "prices": {
        "USD": 100.0,
        "INR": 8000.0,
        "AED": 367.0,
        "SAR": 375.0
      },
      "discounts": {
        "USD": 10.0,
        "INR": 800.0,
        "AED": 36.7,
        "SAR": 37.5
      }
    }
  ]
}
```

## Supported Currencies

- `USD` - US Dollar
- `INR` - Indian Rupee
- `AED` - UAE Dirham
- `SAR` - Saudi Riyal
- `OMR` - Omani Rial

## Frontend Usage

### Switching Currency Display for Coupons

```javascript
// Get coupon data from API
const coupon = await fetch('/coupons/123').then(r => r.json());

// User selects currency
const selectedCurrency = 'INR';

// Display price in selected currency
const displayPrice = coupon.prices[selectedCurrency] || coupon.prices.USD;
const displayDiscount = coupon.discounts[selectedCurrency] || coupon.discounts.USD;

console.log(`Price: ${displayPrice} ${selectedCurrency}`);
console.log(`Discount: ${displayDiscount} ${selectedCurrency}`);
```

### Switching Currency Display for Packages

```javascript
// Get package data from API
const package = await fetch('/packages/123').then(r => r.json());

// User selects currency
const selectedCurrency = 'AED';

// Display package price in selected currency
const basePrice = package.prices[selectedCurrency] || package.prices.USD;
const finalPrice = package.final_prices[selectedCurrency] || package.final_prices.USD;
const savings = basePrice - finalPrice;

console.log(`Original Price: ${basePrice} ${selectedCurrency}`);
console.log(`Final Price: ${finalPrice} ${selectedCurrency}`);
console.log(`You Save: ${savings} ${selectedCurrency}`);

// Display individual coupon prices
package.coupons.forEach(coupon => {
  const couponPrice = coupon.prices[selectedCurrency] || coupon.prices.USD;
  console.log(`${coupon.title}: ${couponPrice} ${selectedCurrency}`);
});
```

### React Example for Coupons

```jsx
function CouponCard({ coupon, currency = 'USD' }) {
  const price = coupon.prices[currency] || coupon.prices.USD;
  const discount = coupon.discounts[currency] || coupon.discounts.USD;
  
  return (
    <div className="coupon-card">
      <h3>{coupon.title}</h3>
      <p className="price">{price} {currency}</p>
      <p className="discount">Save {discount} {currency}</p>
    </div>
  );
}
```

### React Example for Packages

```jsx
function PackageCard({ package, currency = 'USD' }) {
  const basePrice = package.prices[currency] || package.prices.USD;
  const finalPrice = package.final_prices[currency] || package.final_prices.USD;
  const savings = basePrice - finalPrice;
  const savingsPercent = package.discount || 0;
  
  return (
    <div className="package-card">
      <h3>{package.name}</h3>
      <div className="pricing">
        <span className="original-price">{basePrice} {currency}</span>
        <span className="final-price">{finalPrice} {currency}</span>
        <span className="savings">Save {savings} {currency} ({savingsPercent}%)</span>
      </div>
      <div className="coupons">
        <h4>Includes {package.coupons.length} coupons:</h4>
        {package.coupons.map(coupon => (
          <div key={coupon.id}>
            {coupon.title} - {coupon.prices[currency] || coupon.prices.USD} {currency}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Affected Endpoints

All coupon and package endpoints now return multi-currency data:

### Coupon Endpoints
- `GET /coupons` - List all coupons
- `GET /coupons/{id}` - Get single coupon
- `GET /coupons/featured` - Get featured coupons
- `GET /coupons/trending` - Get trending coupons
- `GET /coupons/recently-viewed` - Get recently viewed coupons

### Package Endpoints
- `GET /packages` - List all packages
- `GET /packages/{id}` - Get single package
- `GET /packages/featured` - Get featured packages (if available)
- `GET /packages/{id}/coupons` - Get coupons in a package

## Backward Compatibility

The existing fields remain in the response for backward compatibility:

### For Coupons
- `price` and `discount_amount` fields represent the base USD values
- `pricing` JSON field contains the raw multi-currency data structure

### For Packages
- `pricing` and `total_price` fields contain the raw multi-currency data structure
- New `prices` and `final_prices` provide flattened access

## Fallback Behavior

If a coupon or package doesn't have multi-currency pricing configured:

### Coupons
- `prices` will contain only USD: `{"USD": 100.0}`
- `discounts` will contain only USD: `{"USD": 10.0}`

### Packages
- `prices` will be empty: `{}`
- `final_prices` will be empty: `{}`
- Frontend should check if the selected currency exists and fallback to USD

Frontend should always check if the selected currency exists in the `prices` object and fallback to USD if not available.
