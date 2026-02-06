
import requests
import json
import sys

BASE_URL = "https://api.vouchergalaxy.com"

def check_coupons():
    print(f"Checking Coupons on {BASE_URL}...\n")
    try:
        resp = requests.get(f"{BASE_URL}/coupons/?limit=100")
        if resp.status_code == 200:
            coupons = resp.json()
            print(f"Found {len(coupons)} coupons.")
            for c in coupons:
                print(f"ID: {c['id']}, Code: {c['code']}, Price: {c['price']}")
                if c['price'] > 0:
                    print(f"✅ Found paid coupon: {c['id']}")
                    return c['id']
            print("❌ No paid coupons found!")
            return None
        else:
            print(f"Failed to list coupons: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_coupons()
