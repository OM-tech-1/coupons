"""
Stripe SDK Client Initialization

This module provides a configured Stripe client for use throughout the application.
The API key is loaded from environment variables.
"""
import stripe
import os
from functools import lru_cache


class StripeConfig:
    """Stripe configuration settings"""
    
    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.api_version = "2023-10-16"  # Stripe API version
        self.environment = os.getenv("ENVIRONMENT", "test")
        
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        return bool(self.secret_key and self.publishable_key)


@lru_cache()
def get_stripe_config() -> StripeConfig:
    """Get cached Stripe configuration"""
    return StripeConfig()


def get_stripe_client():
    """
    Get configured Stripe client.
    
    Returns the stripe module with API key configured.
    This should be called when making Stripe API calls.
    """
    config = get_stripe_config()
    stripe.api_key = config.secret_key
    stripe.api_version = config.api_version
    return stripe


def verify_stripe_configuration() -> dict:
    """
    Verify Stripe configuration is valid.
    
    Returns dict with configuration status.
    """
    config = get_stripe_config()
    
    result = {
        "configured": config.is_configured(),
        "has_secret_key": bool(config.secret_key),
        "has_publishable_key": bool(config.publishable_key),
        "has_webhook_secret": bool(config.webhook_secret),
        "api_version": config.api_version,
    }
    
    if config.is_configured():
        result["mode"] = "test" if config.secret_key.startswith("sk_test_") else "live"
    
    return result
