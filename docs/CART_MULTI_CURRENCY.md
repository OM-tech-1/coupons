# Cart Multi-Currency Support

## Overview
Cart responses now include multi-currency pricing for all items and totals, making it easy for the frontend to display prices in any supported currency without additional API calls.

## Response Structure

### Cart Item Response
Each cart item includes:
- `prices`: Base prices in all currencies (before package discount)
- `final_prices`: Final prices after package discount (quantity included)

### Cart Total Response
The cart response includes:
- `prices`: Sum of all item base prices across all currencies
- `final_prices`: Sum of all item final prices across all currencies

## Example Response

```json
{
  "items": [
    {
      "id": "uuid",
      "package_id": "uuid",
      "quantity": 2,
      "added_at": "2024-01-01T00:00:00",
      "package": {
        "id": "uuid",
        "name": "Premium Bundle",
        "discount": 10.0,
        "prices": {
          "USD": 100.0,
          "INR": 8000.0,
          "AED": 367.0
        },
        "final_prices": {
          "USD": 90.0,
          "INR": 7200.0,
          "AED": 330.3
        }
      },
      "prices": {
        "USD": 200.0,
        "INR": 16000.0,
        "AED": 734.0
      },
      "final_prices": {
        "USD": 180.0,
        "INR": 14400.0,
        "AED": 660.6
      }
    }
  ],
  "total_items": 2,
  "total_amount": 180.0,
  "prices": {
    "USD": 200.0,
    "INR": 16000.0,
    "AED": 734.0
  },
  "final_prices": {
    "USD": 180.0,
    "INR": 14400.0,
    "AED": 660.6
  }
}
```

## Implementation Details

### Schema Updates
- `CouponInCart`: Added `prices` and `discounts` fields extracted from `pricing` JSON
- `PackageInCart`: Added `prices` and `final_prices` computed from package pricing
- `CartItemResponse`: Added `prices` and `final_prices` (unit price × quantity)
- `CartResponse`: Added `prices` and `final_prices` (sum of all items)

### Price Calculation
1. Individual coupons: Extract from `pricing` JSON field
2. Packages: Sum individual coupon prices, apply package discount
3. Cart items: Multiply unit price by quantity
4. Cart total: Sum all item prices

### Frontend Usage
The frontend can now:
1. Display cart in user's preferred currency without API calls
2. Switch currencies instantly using the `prices`/`final_prices` objects
3. Show accurate totals including package discounts and quantities

## Related Documentation
- [Multi-Currency Coupon Response](./MULTI_CURRENCY_RESPONSE.md)
- [Package API Documentation](./PACKAGES_API.md)
