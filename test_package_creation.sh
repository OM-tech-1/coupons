#!/bin/bash

# VoucherGalaxy Package Creation Test Script
# This script logs in as admin and creates a test package

BASE_URL="https://api.vouchergalaxy.com"

echo "=========================================="
echo "Step 1: Login as Admin"
echo "=========================================="

# Login with admin credentials
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "+91",
    "number": "8943657095",
    "password": "8943657095"
  }')

echo "Login Response:"
echo "$LOGIN_RESPONSE" | jq '.'

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo ""
  echo "❌ ERROR: Failed to get access token"
  echo "Please check your credentials"
  exit 1
fi

echo ""
echo "✅ Successfully logged in!"
echo "Access Token: ${ACCESS_TOKEN:0:50}..."

echo ""
echo "=========================================="
echo "Step 2: Create Test Package"
echo "=========================================="

# Create a test package
PACKAGE_RESPONSE=$(curl -s -X POST "${BASE_URL}/packages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "name": "Test Bundle - Nike Sports Pack",
    "slug": "test-nike-sports-pack",
    "description": "Amazing test bundle with multiple sports coupons for testing",
    "picture_url": "https://example.com/nike-bundle.jpg",
    "brand": "Nike",
    "brand_url": "https://nike.com",
    "discount": 25.5,
    "category_id": "c1cf11f3-a5fb-4c75-827b-2aa2287e6b4d",
    "is_active": true,
    "is_featured": false,
    "expiration_date": "2025-12-31",
    "country": "UAE",
    "coupon_ids": []
  }')

echo "Package Creation Response:"
echo "$PACKAGE_RESPONSE" | jq '.'

# Check if package was created successfully
PACKAGE_ID=$(echo "$PACKAGE_RESPONSE" | jq -r '.id')

if [ "$PACKAGE_ID" == "null" ] || [ -z "$PACKAGE_ID" ]; then
  echo ""
  echo "❌ ERROR: Failed to create package"
  echo "Response details:"
  echo "$PACKAGE_RESPONSE"
  exit 1
fi

echo ""
echo "✅ Successfully created package!"
echo "Package ID: $PACKAGE_ID"
echo "Package Name: $(echo "$PACKAGE_RESPONSE" | jq -r '.name')"
echo "Package Slug: $(echo "$PACKAGE_RESPONSE" | jq -r '.slug')"

echo ""
echo "=========================================="
echo "Step 3: Verify Package Creation"
echo "=========================================="

# Get the created package
VERIFY_RESPONSE=$(curl -s -X GET "${BASE_URL}/packages/${PACKAGE_ID}")

echo "Package Details:"
echo "$VERIFY_RESPONSE" | jq '.'

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
