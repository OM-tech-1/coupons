import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_registration():
    print("Testing Registration...")
    payload = {
        "country_code": "+91",
        "number": "7012967432", # Example valid US number
        "password": "securepassword",
        "full_name": "Test User",
        "second_name": "User Second Name"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    if response.status_code == 200:
        print("✅ Registration Successful")
        print(json.dumps(response.json(), indent=2))
        return True
    elif response.status_code == 400 and "already registered" in response.text:
         print("⚠️ User already registered (Expected if running twice)")
         return True
    else:
        print(f"❌ Registration Failed: {response.status_code} - {response.text}")
        return False

def test_login():
    print("\nTesting Login...")
    payload = {
        "country_code": "+1",
        "number": "2025550100",
        "password": "securepassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    if response.status_code == 200:
        print("✅ Login Successful")
        token = response.json().get("access_token")
        print(f"Token: {token[:10]}...")
        return token
    else:
        print(f"❌ Login Failed: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    if test_registration():
        test_login()
