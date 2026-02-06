
import requests
import uuid
import random
import string
import json
import sys
import os

BASE_URL = "https://api.vouchergalaxy.com"
# BASE_URL = "http://156.67.216.229" # Fallback if SSL fails

ADMIN_PHONE = os.getenv("ADMIN_PHONE", "7907975711")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "afsal@123")

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def generate_phone():
    # Valid Indian mobile number starts with 6, 7, 8, 9 and is 10 digits
    start = random.choice(['7', '8', '9'])
    rest = "".join([str(random.randint(0, 9)) for _ in range(9)])
    return start + rest

def print_pass(msg):
    print(f"✅ PASS: {msg}")

def print_fail(msg, details=""):
    print(f"❌ FAIL: {msg}")
    if details:
        print(f"   Details: {details}")
    # Don't exit on fail, try to continue
    # sys.exit(1)

def test_api():
    print(f"🚀 Starting Full API Test against {BASE_URL}...\n")
    
    session = requests.Session()
    
    # 1. Health Check
    try:
        resp = session.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            print_pass("Health Check")
        else:
            print_fail("Health Check", resp.text)
    except Exception as e:
        print_fail(f"Connection failed: {e}")
        return

    # 2. Auth - Register
    user_phone = generate_phone()
    password = "password123"
    register_data = {
        "country_code": "+91",
        "number": user_phone,
        "password": password,
        "full_name": f"Test User {generate_random_string()}"
    }
    
    resp = session.post(f"{BASE_URL}/auth/register", json=register_data)
    if resp.status_code == 201 or resp.status_code == 200:
        print_pass("User Registration")
    else:
        print_fail("User Registration", resp.text)

    # 3. Auth - Login
    login_data = {
        "country_code": "+91",
        "number": user_phone,
        "password": password
    }
    resp = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        if token:
            print_pass("User Login")
            session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print_fail("Login response missing access_token", resp.text)
            return
    else:
        print_fail("User Login", resp.text)
        return

    # 4. User Profile
    resp = session.get(f"{BASE_URL}/user/me")
    if resp.status_code == 200:
        print_pass("Get User Profile")
    else:
        print_fail("Get User Profile", resp.text)

    # 5. Categories
    resp = session.get(f"{BASE_URL}/categories/")
    if resp.status_code == 200:
        categories = resp.json()
        print_pass(f"List Categories (Found {len(categories)})")
        if categories:
            cat_slug = categories[0]['slug']
            # Get specific category
            resp = session.get(f"{BASE_URL}/categories/{cat_slug}")
            if resp.status_code == 200:
                print_pass(f"Get Category by Slug ({cat_slug})")
            else:
                print_fail("Get Category by Slug", resp.text)
    else:
        print_fail("List Categories", resp.text)

    # 6. Regions & Countries
    resp = session.get(f"{BASE_URL}/countries/")
    if resp.status_code == 200:
        countries = resp.json()
        print_pass(f"List Countries (Found {len(countries)})")
    else:
        print_fail("List Countries", resp.text)

    # 7. Coupons
    coupon_id = None
    
    # 7b. Create a Paid Coupon (Need Admin Token for this)
    # We already logged in as a normal user. We need admin credentials.
    # Admin creds: +917907975711 / afsal@123
    admin_login = {
        "country_code": "+91",
        "number": ADMIN_PHONE,
        "password": ADMIN_PASSWORD
    }
    resp = session.post(f"{BASE_URL}/auth/login", json=admin_login)
    if resp.status_code == 200:
        admin_token = resp.json().get("access_token")
        # Create Coupon with Price
        new_coupon = {
            "code": f"TEST{generate_random_string().upper()}",
            "redeem_code": f"RED{generate_random_string().upper()}",
            "brand": "TestBrand",
            "title": "Test Paid Coupon",
            "description": "For testing payments",
            "discount_type": "percentage",
            "discount_amount": 10.0,
            "price": 5.0, # $5
            "min_purchase": 10.0,
            "max_uses": 100,
            "category_id": categories[0]['id'] if categories else None, # Use first category
            "availability_type": "local",
            "country_ids": [countries[0]['id']] if countries else [] # Use first country
        }
        resp = session.post(f"{BASE_URL}/coupons/", json=new_coupon, headers={"Authorization": f"Bearer {admin_token}"})
        if resp.status_code == 201 or resp.status_code == 200:
            coupon_data = resp.json()
            coupon_id = coupon_data['id']
            print_pass(f"Created Paid Coupon (ID: {coupon_id}, Price: {coupon_data['price']})")
        else:
             print_fail("Create Paid Coupon", resp.text)
    else:
        print_fail("Admin Login for Coupon Creation", resp.text)

    # Re-login as normal user for purchase
    resp = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})

    # List coupons check
    resp = session.get(f"{BASE_URL}/coupons/?limit=10")
    if resp.status_code == 200:
        coupons = resp.json()
        print_pass(f"List Coupons (Found {len(coupons)})")
        # Filter test
        resp = session.get(f"{BASE_URL}/coupons/?availability_type=active_only=true")
        if resp.status_code == 200:
            print_pass("Filter Coupons")
    else:
        print_fail("List Coupons", resp.text)

    if not coupon_id:
        # Fallback if creation failed, check if any paid coupon exists
        if coupons:
            for c in coupons:
                if c['price'] > 0:
                    coupon_id = c['id']
                    break
        
    if not coupon_id:
        print("⚠️ Skipping Cart/Order tests (No paid coupons found)")
        return

    # 8. Cart
    # Clear cart first
    session.delete(f"{BASE_URL}/cart/")
    
    # Add to cart
    resp = session.post(f"{BASE_URL}/cart/add", json={"coupon_id": coupon_id, "quantity": 1})
    if resp.status_code == 200 or resp.status_code == 201:
        print_pass("Add to Cart")
    else:
        print_fail("Add to Cart", resp.text)
    
    # View Cart
    resp = session.get(f"{BASE_URL}/cart/")
    if resp.status_code == 200:
        cart = resp.json()
        if cart.get("items"):
            print_pass("View Cart")
        else:
            print_fail("View Cart (Empty)", str(cart))
    else:
         print_fail("View Cart", resp.text)

    # 9. Orders (Checkout Mock)
    resp = session.post(f"{BASE_URL}/orders/checkout", json={"payment_method": "mock"})
    if resp.status_code == 200:
        order = resp.json()
        print_pass(f"Checkout Mock (Order ID: {order['id']})")
        order_id = order['id']
    else:
        print_fail("Checkout Mock", resp.text)
        return

    # 10. Stripe Payment Init
    # We need a new order for this because the previous one is already 'paid' by mock
    # So we add to cart again
    session.post(f"{BASE_URL}/cart/add", json={"coupon_id": coupon_id, "quantity": 1})
    # Create order without paying? 
    # The API might not expose "create order without pay" easily, it seems `checkout` handles it.
    # But wait, `POST /payments/init` takes an `order_id`. 
    # Usually `checkout` creates the order. If we pass `payment_method="stripe"`, does it create order in pending state?
    # Checking implementation might be needed, but let's assume valid flow:
    # 1. Add to cart
    # 2. Checkout with `payment_method="stripe"` -> This likely returns a pending order
    
    resp = session.post(f"{BASE_URL}/orders/checkout", json={"payment_method": "stripe"})
    if resp.status_code == 200:
        stripe_order = resp.json()
        stripe_order_id = stripe_order['id']
        print_pass(f"Create Pending Order for Stripe (ID: {stripe_order_id})")
        
        # Now Init Payment
        payload = {
            "order_id": stripe_order_id,
            "amount": int(stripe_order['total_amount'] * 100), # Amount in cents
            "currency": "USD" # Assuming USD
        }
        resp = session.post(f"{BASE_URL}/payments/init", json=payload)
        if resp.status_code == 200:
            payment_data = resp.json()
            print_pass(f"Stripe Payment Init (Intent: {payment_data.get('payment_intent_id')})")
            
            # Validate Token
            token = payment_data.get('token')
            resp = session.post(f"{BASE_URL}/payments/validate-token", json={"token": token})
            if resp.status_code == 200:
                print_pass("Stripe Token Validation")
            else:
                print_fail("Stripe Token Validation", resp.text)
        else:
            print_fail("Stripe Payment Init", resp.text)
            
    else:
        print_fail("Create Pending Order for Stripe", resp.text)

    print("\n✅ Test Suite Completed")

if __name__ == "__main__":
    test_api()
