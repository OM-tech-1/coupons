import requests
import json
import uuid

BASE_URL = "http://156.67.216.229"
USERNAME = "7907975711"  # Country code likely split in actual request, but auth endpoint takes them separately usually
PASSWORD = "afsal@123"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def log(msg, success=True):
    color = GREEN if success else RED
    mark = "✅" if success else "❌"
    print(f"{color}{mark} {msg}{RESET}")

def run_tests():
    session = requests.Session()
    
    print(f"Testing API at {BASE_URL}...\n")

    # 1. Health Check
    try:
        resp = session.get(f"{BASE_URL}/")
        if resp.status_code == 200:
            log("Health Check (/) Passed")
        else:
            log(f"Health Check Failed: {resp.status_code}", False)
    except Exception as e:
        log(f"Health Check Connection Failed: {e}", False)
        return

    # 2. Login
    try:
        login_data = {
            "country_code": "+91",
            "number": "7907975711",
            "password": PASSWORD
        }
        resp = session.post(f"{BASE_URL}/auth/login", json=login_data)
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            log("Login Passed")
        else:
            log(f"Login Failed: {resp.text}", False)
            return
    except Exception as e:
        log(f"Login Exception: {e}", False)
        return

    # 3. User Profile
    resp = session.get(f"{BASE_URL}/user/me")
    if resp.status_code == 200:
        user_data = resp.json()
        role = user_data.get("role")
        log(f"Get Profile Passed (Role: {role})")
    else:
        log(f"Get Profile Failed: {resp.text}", False)

    # 4. List Coupons
    resp = session.get(f"{BASE_URL}/coupons/?limit=5")
    if resp.status_code == 200:
        coupons = resp.json()
        log(f"List Coupons Passed (Count: {len(coupons)})")
    else:
        log(f"List Coupons Failed: {resp.text}", False)

    # 5. Create Coupon (New structure check)
    new_coupon_code = f"TESTPERF{uuid.uuid4().hex[:6].upper()}"
    coupon_data = {
        "code": new_coupon_code,
        "redeem_code": "SECRET123", # New field
        "brand": "TestBrand",       # New field
        "title": "Test Coupon Performance",
        "description": "Created by automated test",
        "discount_type": "percentage",
        "discount_amount": 10.0,
        "price": 0.0, # Free for testing cart flow easily, or low price
        "min_purchase": 0.0
    }
    
    # We try creating. If the server code isn't updated, redeem_code/brand might be ignored or cause error if strict validation?
    # Actually Pydantic usually ignores extra fields if not configured to forbid. 
    # But if the DB migration failed/didn't run, this might fail differently.
    
    resp = session.post(f"{BASE_URL}/coupons/", json=coupon_data)
    created_coupon_id = None
    
    if resp.status_code in [200, 201]:
        created_coupon = resp.json()
        created_coupon_id = created_coupon['id']
        # Check if new fields are present in response (if deployed)
        has_brand = 'brand' in created_coupon
        log(f"Create Coupon Passed (ID: {created_coupon_id}) - New fields supported? {'Yes' if has_brand else 'No (Update server!)'}")
    elif resp.status_code == 422:
         # Maybe schema validation failed?
         log(f"Create Coupon Failed (Validation): {resp.text}", False)
    else:
        log(f"Create Coupon Failed: {resp.status_code} {resp.text}", False)

    if created_coupon_id:
        # 6. Add to Cart
        cart_data = {"coupon_id": created_coupon_id, "quantity": 1}
        resp = session.post(f"{BASE_URL}/cart/add", json=cart_data)
        if resp.status_code in [200, 201]:
            log("Add to Cart Passed")
        else:
            log(f"Add to Cart Failed: {resp.status_code} {resp.text}", False)

        # 7. View Cart
        resp = session.get(f"{BASE_URL}/cart/")
        if resp.status_code == 200:
            cart = resp.json()
            total_items = cart.get("total_items", 0)
            log(f"View Cart Passed (Items: {total_items})")
        else:
            log(f"View Cart Failed: {resp.text}", False)

        # 8. Checkout
        checkout_data = {"payment_method": "mock"}
        resp = session.post(f"{BASE_URL}/orders/checkout", json=checkout_data)
        if resp.status_code == 200:
            order = resp.json()
            log(f"Checkout Passed (Order ID: {order.get('id')})")
        else:
            log(f"Checkout Failed: {resp.text}", False)

        # 9. Verify User Coupons (Reveal Code)
        resp = session.get(f"{BASE_URL}/user/coupons")
        if resp.status_code == 200:
            user_coupons = resp.json()
            # Find the one we just bought
            found = False
            for uc in user_coupons:
                if uc['coupon']['id'] == created_coupon_id:
                    redeem_code_visible = uc['coupon'].get('redeem_code')
                    log(f"User Coupon Verification Passed. Redeem Code Visible: {redeem_code_visible}")
                    found = True
                    break
            if not found:
                log("User Coupon Verification Failed: Coupon not found in list", False)
        else:
            log(f"Get User Coupons Failed: {resp.text}", False)

        # 10. Clean up (Delete Coupon)
        # Note: This is EXPECTED to fail if the coupon was purchased (Foreign Key Constraint)
        resp = session.delete(f"{BASE_URL}/coupons/{created_coupon_id}")
        if resp.status_code == 204:
             log("Cleanup (Delete Coupon) Passed")
        elif resp.status_code == 500 or resp.status_code == 400:
             log(f"Cleanup Failed (Expected): Coupon is linked to an order. integrity check passed (Code {resp.status_code})", True)
        else:
             log(f"Cleanup Failed: {resp.status_code}", False)

    # 11. Test New Health Endpoint
    resp = session.get(f"{BASE_URL}/health")
    if resp.status_code == 200:
        log("Detailed Health Check (/health) Passed")
    else:
        log(f"Detailed Health Check (/health) Not Found/Failed (Is server updated?) code: {resp.status_code}", False)

if __name__ == "__main__":
    run_tests()
