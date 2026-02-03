from app.utils.security import get_password_hash

try:
    print("Hashing 'securepassword'...")
    h = get_password_hash("securepassword")
    print(f"Success: {h}")
except Exception as e:
    print(f"Error: {e}")
