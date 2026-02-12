
import stripe
import os
import sys
from dotenv import load_dotenv

def verify_stripe_test_config():
    """Verify Stripe test configuration"""
    load_dotenv()
    
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    pub_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
    
    print(f"Checking Stripe Configuration...")
    print(f"Secret Key Prefix: {secret_key[:7] if secret_key else 'None'}")
    print(f"Publishable Key Prefix: {pub_key[:7] if pub_key else 'None'}")
    
    if not secret_key or not secret_key.startswith("sk_test_"):
        print("❌ Error: Valid Test Secret Key (sk_test_) not found!")
        return False
        
    if not pub_key or not pub_key.startswith("pk_test_"):
        print("❌ Error: Valid Test Publishable Key (pk_test_) not found!")
        return False
        
    try:
        stripe.api_key = secret_key
        # Simple call to verify credentials
        stripe.Balance.retrieve()
        print("✅ Stripe Test Connection Successful!")
        return True
    except Exception as e:
        print(f"❌ Stripe Connection Failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_stripe_test_config()
    sys.exit(0 if success else 1)
