"""
Load Testing for Coupon API

Run with: locust -f tests/load_test.py --host=https://api.vouchergalaxy.com

Or use the Makefile:
    make load-test          # Interactive mode
    make load-test-headless # Headless mode (2000 users, 100/sec spawn rate)
"""
from locust import HttpUser, task, between, events
import random
import json
import os


class CouponAPIUser(HttpUser):
    """Simulates a user interacting with the Coupon API"""
    
    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts - login and get token"""
        # Try to login (you'll need valid test credentials)
        self.token = None
        self.user_id = None
        
        # For public endpoints, we don't need auth
        # For authenticated endpoints, uncomment below:
        # self.login()
    
    def login(self):
        """Login and get JWT token"""
        response = self.client.post("/auth/login", json={
            "phone_number": os.getenv("TEST_PHONE", "+971501234567"),
            "password": os.getenv("TEST_PASSWORD", "testpass123")
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
    
    @property
    def headers(self):
        """Get auth headers if token exists"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    # === Public Endpoints (No Auth Required) ===
    
    @task(10)
    def get_coupons_list(self):
        """GET /coupons/ - Most common endpoint"""
        self.client.get("/coupons/", name="GET /coupons/")
    
    @task(5)
    def get_coupons_with_filters(self):
        """GET /coupons/ with filters"""
        params = {
            "category_id": random.choice(["", "some-uuid"]),
            "min_discount": random.choice([0, 10, 20, 50]),
            "limit": random.choice([10, 20, 50])
        }
        self.client.get("/coupons/", params=params, name="GET /coupons/ (filtered)")
    
    @task(8)
    def get_packages_list(self):
        """GET /packages/ - Popular endpoint"""
        self.client.get("/packages/", name="GET /packages/")
    
    @task(3)
    def get_categories(self):
        """GET /categories/"""
        self.client.get("/categories/", name="GET /categories/")
    
    @task(2)
    def get_regions(self):
        """GET /regions/"""
        self.client.get("/regions/", name="GET /regions/")
    
    @task(1)
    def health_check(self):
        """GET /health - Health check endpoint"""
        self.client.get("/health", name="GET /health")
    
    # === Authenticated Endpoints ===
    
    @task(4)
    def get_cart(self):
        """GET /cart/ - Requires auth"""
        if self.token:
            self.client.get("/cart/", headers=self.headers, name="GET /cart/")
    
    @task(2)
    def add_to_cart(self):
        """POST /cart/add - Requires auth"""
        if self.token:
            # This will fail without valid coupon_id, but tests the endpoint
            self.client.post("/cart/add", 
                json={"coupon_id": "00000000-0000-0000-0000-000000000000", "quantity": 1},
                headers=self.headers,
                name="POST /cart/add")
    
    @task(3)
    def get_user_wallet(self):
        """GET /user/wallet - Requires auth"""
        if self.token:
            self.client.get("/user/wallet", headers=self.headers, name="GET /user/wallet")


class AdminUser(HttpUser):
    """Simulates admin operations"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Admin login"""
        self.token = None
        # Uncomment and set admin credentials for admin testing
        # self.admin_login()
    
    @task(1)
    def get_admin_dashboard(self):
        """GET /admin/dashboard"""
        if self.token:
            self.client.get("/admin/dashboard", 
                headers={"Authorization": f"Bearer {self.token}"},
                name="GET /admin/dashboard")


# === Event Handlers for Reporting ===

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("\n" + "="*60)
    print("🚀 Load Test Starting")
    print(f"Target: {environment.host}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - print summary"""
    print("\n" + "="*60)
    print("📊 Load Test Complete")
    print("="*60)
    
    stats = environment.stats
    
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    
    if stats.total.num_failures > 0:
        failure_rate = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"Failure Rate: {failure_rate:.2f}%")
    
    print("\n" + "="*60 + "\n")
