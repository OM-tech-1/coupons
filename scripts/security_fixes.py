#!/usr/bin/env python3
"""
Security Fixes Script
Applies critical security patches to the codebase
"""
import os
import secrets
import sys

def generate_secure_secret(length=64):
    """Generate a cryptographically secure random secret"""
    return secrets.token_hex(length)

def create_env_template():
    """Create a secure .env.template file"""
    template = """# Environment Configuration Template
# Copy this to .env and fill in your actual values
# NEVER commit .env to git!

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# JWT Configuration
JWT_SECRET=<GENERATE_WITH: python -c "import secrets; print(secrets.token_hex(32))">
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Redis
REDIS_URL=rediss://:password@host:6379/0

# Stripe (use test keys for development)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Payment Token
PAYMENT_TOKEN_SECRET=<GENERATE_WITH: python -c "import secrets; print(secrets.token_hex(32))">
PAYMENT_TOKEN_TTL_MINUTES=5

# External API
EXTERNAL_API_KEY=<GENERATE_WITH: python -c "import secrets; print(secrets.token_hex(32))">

# Domain Configuration
PAYMENT_UI_DOMAIN=https://payment.vouchergalaxy.com
MAIN_SITE_DOMAIN=https://vouchergalaxy.com
API_BASE_URL=https://api.vouchergalaxy.com

# AWS S3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-southeast-2
S3_BUCKET_NAME=your-bucket
S3_PREFIX=coupons

# Environment
ENVIRONMENT=development
"""
    
    with open('.env.template', 'w') as f:
        f.write(template)
    
    print("✅ Created .env.template")
    print("⚠️  Copy this to .env and fill in your actual values")

def update_gitignore():
    """Ensure .env is in .gitignore"""
    gitignore_path = '.gitignore'
    
    # Read existing .gitignore
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            content = f.read()
    else:
        content = ""
    
    # Check if .env is already ignored
    if '.env' not in content:
        with open(gitignore_path, 'a') as f:
            f.write('\n# Environment variables (SECURITY: Never commit!)\n')
            f.write('.env\n')
            f.write('.env.local\n')
            f.write('.env.*.local\n')
        print("✅ Added .env to .gitignore")
    else:
        print("✅ .env already in .gitignore")

def check_env_in_git():
    """Check if .env is tracked by git"""
    result = os.system('git ls-files .env 2>/dev/null')
    if result == 0:
        print("⚠️  WARNING: .env is tracked by git!")
        print("   Run: git rm --cached .env")
        print("   Then: git commit -m 'Remove .env from tracking'")
        return False
    else:
        print("✅ .env is not tracked by git")
        return True

def generate_new_secrets():
    """Generate new secrets for rotation"""
    print("\n🔐 NEW SECRETS (save these securely):")
    print("=" * 60)
    print(f"JWT_SECRET={generate_secure_secret(32)}")
    print(f"PAYMENT_TOKEN_SECRET={generate_secure_secret(32)}")
    print(f"EXTERNAL_API_KEY={generate_secure_secret(32)}")
    print("=" * 60)
    print("\n⚠️  Also rotate:")
    print("   - Database password")
    print("   - Redis password")
    print("   - AWS keys")
    print("   - Stripe keys (if compromised)")

def create_security_middleware():
    """Create security headers middleware"""
    middleware_code = '''"""
Security Headers Middleware
Adds security headers to all responses
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import os

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (only in production)
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
'''
    
    os.makedirs('app/middleware', exist_ok=True)
    with open('app/middleware/security_headers.py', 'w') as f:
        f.write(middleware_code)
    
    print("✅ Created app/middleware/security_headers.py")
    print("   Add to main.py: app.add_middleware(SecurityHeadersMiddleware)")

def create_audit_logger():
    """Create audit logging configuration"""
    audit_config = '''"""
Audit Logger Configuration
Logs security-sensitive events for compliance and investigation
"""
import logging
import os
from datetime import datetime

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Configure audit logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# File handler for audit logs
audit_handler = logging.FileHandler('logs/audit.log')
audit_handler.setLevel(logging.INFO)

# Format: timestamp | level | user_id | action | details
audit_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)

def log_auth_event(event_type: str, user_id: str = None, phone: str = None, ip: str = None, success: bool = True):
    """Log authentication events"""
    status = "SUCCESS" if success else "FAILED"
    audit_logger.info(f"{status} | {event_type} | user_id={user_id} | phone={phone} | ip={ip}")

def log_admin_action(admin_id: str, action: str, target_id: str = None, details: str = None):
    """Log admin actions"""
    audit_logger.info(f"ADMIN_ACTION | admin_id={admin_id} | action={action} | target={target_id} | details={details}")

def log_payment_event(event_type: str, order_id: str, amount: float, currency: str, status: str):
    """Log payment events"""
    audit_logger.info(f"PAYMENT | {event_type} | order_id={order_id} | amount={amount} | currency={currency} | status={status}")

def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    """Log security events"""
    audit_logger.log(
        logging.WARNING if severity == "WARNING" else logging.INFO,
        f"SECURITY | {event_type} | {details}"
    )
'''
    
    with open('app/utils/audit_logger.py', 'w') as f:
        f.write(audit_config)
    
    print("✅ Created app/utils/audit_logger.py")
    print("   Import and use in your endpoints")

def main():
    print("🔒 Security Fixes Script")
    print("=" * 60)
    
    # Check current directory
    if not os.path.exists('app'):
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    
    print("\n1. Checking .gitignore...")
    update_gitignore()
    
    print("\n2. Checking if .env is tracked by git...")
    check_env_in_git()
    
    print("\n3. Creating .env.template...")
    create_env_template()
    
    print("\n4. Creating security middleware...")
    create_security_middleware()
    
    print("\n5. Creating audit logger...")
    create_audit_logger()
    
    print("\n6. Generating new secrets...")
    generate_new_secrets()
    
    print("\n" + "=" * 60)
    print("✅ Security fixes applied!")
    print("\n📋 NEXT STEPS:")
    print("1. Copy .env.template to .env and fill in values")
    print("2. Rotate all credentials (use generated secrets above)")
    print("3. Run: git rm --cached .env (if tracked)")
    print("4. Add SecurityHeadersMiddleware to main.py")
    print("5. Integrate audit logging in sensitive endpoints")
    print("6. Review SECURITY_AUDIT_REPORT.md for full details")
    print("=" * 60)

if __name__ == "__main__":
    main()
