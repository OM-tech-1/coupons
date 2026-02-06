
import requests
import uuid
import sys
import json

import os

BASE_URL = "https://api.vouchergalaxy.com"

ADMIN_PHONE = os.getenv("ADMIN_PHONE", "7907975711")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "afsal@123")

def print_pass(msg):
    print(f"✅ PASS: {msg}")

def print_fail(msg, details=""):
    print(f"❌ FAIL: {msg}")
    if details:
        print(f"   Details: {details}")

def run_repro():
    print(f"🚀 Starting Postman Flow Reproduction on {BASE_URL}...\n")
    session = requests.Session()

    # 1. Login to get token
    print("1. Logging in...")
    login_data = {
        "country_code": "+91",
        "number": ADMIN_PHONE,
        "password": ADMIN_PASSWORD
    }
    resp = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print_fail("Login failed", resp.text)
        return
    token = resp.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    print_pass("Logged in")

    # 2. Get a valid coupon ID (creating one if needed, or picking existing)
    print("\n2. Finding a paid coupon...")
    resp = session.get(f"{BASE_URL}/coupons/?limit=50")
    coupons = resp.json()
    coupon_id = None
    for c in coupons:
        if c.get('price', 0) > 0:
            coupon_id = c['id']
            print_pass(f"Found paid coupon: {c['title']} (Price: {c['price']})")
            break
    
    if not coupon_id:
        print_fail("No paid coupons found to test payment!")
        return

    # 3. Add to Cart
    print("\n3. Adding to Cart...")
    session.delete(f"{BASE_URL}/cart/") # Clear first
    resp = session.post(f"{BASE_URL}/cart/add", json={"coupon_id": coupon_id, "quantity": 1})
    if resp.status_code not in [200, 201]:
        print_fail("Add to Cart failed", resp.text)
        return
    print_pass("Added to Cart")

    # 4. Checkout (Stripe) -> Get Order ID
    print("\n4. Checking out (payment_method='stripe')...")
    resp = session.post(f"{BASE_URL}/orders/checkout", json={"payment_method": "stripe"})
    if resp.status_code != 200:
        print_fail("Checkout failed", resp.text)
        return
    order_data = resp.json()
    order_id = order_data['id']
    total_amount = int(order_data['total_amount'] * 100)
    print_pass(f"Order Created: {order_id} (Amount: {total_amount} cents)")

    # 5. Init Payment (Valid Order)
    print(f"\n5. Initializing Payment for Valid Order {order_id}...")
    payload = {
        "order_id": order_id,
        "amount": total_amount,
        "currency": "USD"
    }
    resp = session.post(f"{BASE_URL}/payments/init", json=payload)
    if resp.status_code == 200:
        print_pass("Payment Init Successful")
        print(f"   Response: {json.dumps(resp.json(), indent=2)}")
    else:
        print_fail("Payment Init Failed", resp.text)

    # 6. Negative Test: Init Payment (Invalid Order)
    fake_id = str(uuid.uuid4())
    print(f"\n6. Testing Invalid Order ID {fake_id}...")
    payload["order_id"] = fake_id
    resp = session.post(f"{BASE_URL}/payments/init", json=payload)
    if resp.status_code == 400 or resp.status_code == 404:
        print_pass(f"Correctly failed with {resp.status_code}")
        print(f"   Error: {resp.text}")
    else:
        print_fail(f"Expected 400/404, got {resp.status_code}", resp.text)

if __name__ == "__main__":
    run_repro()
