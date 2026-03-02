"""
Security middleware to protect against scanning attacks and abuse
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Track 404s per IP
not_found_tracker = defaultdict(list)
BLOCK_THRESHOLD = 20  # Block after 20 404s
TIME_WINDOW = 60  # Within 60 seconds
BLOCK_DURATION = 3600  # Block for 1 hour

blocked_ips = {}


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and block scanning attacks based on 404 patterns
    """
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip for localhost/internal IPs in development
        if client_ip in ["127.0.0.1", "localhost", "::1"]:
            return await call_next(request)
        
        # Check if IP is blocked
        if client_ip in blocked_ips:
            if datetime.utcnow() < blocked_ips[client_ip]:
                logger.warning(f"[SECURITY] Blocked IP attempted access: {client_ip} - Path: {request.url.path}")
                raise HTTPException(status_code=403, detail="Access denied due to suspicious activity")
            else:
                # Unblock expired blocks
                del blocked_ips[client_ip]
                logger.info(f"[SECURITY] IP {client_ip} unblocked after timeout")
        
        response = await call_next(request)
        
        # Track 404 responses (potential scanning attack)
        if response.status_code == 404:
            now = datetime.utcnow()
            
            # Clean old entries outside time window
            not_found_tracker[client_ip] = [
                ts for ts in not_found_tracker[client_ip]
                if now - ts < timedelta(seconds=TIME_WINDOW)
            ]
            
            # Add current 404
            not_found_tracker[client_ip].append(now)
            
            count = len(not_found_tracker[client_ip])
            
            # Log suspicious activity
            if count > 10:
                logger.warning(
                    f"[SECURITY] Suspicious activity from {client_ip}: "
                    f"{count} 404s in {TIME_WINDOW}s - Path: {request.url.path}"
                )
            
            # Check if threshold exceeded - block the IP
            if count >= BLOCK_THRESHOLD:
                blocked_ips[client_ip] = now + timedelta(seconds=BLOCK_DURATION)
                logger.error(
                    f"[SECURITY] IP {client_ip} BLOCKED for {BLOCK_DURATION}s "
                    f"after {count} 404s in {TIME_WINDOW}s"
                )
                # Clear tracker for this IP
                not_found_tracker[client_ip] = []
                
                # Return 403 immediately
                raise HTTPException(
                    status_code=403,
                    detail="Access denied due to excessive 404 requests"
                )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Only add HSTS in production (not for localhost)
        if request.url.hostname not in ["localhost", "127.0.0.1"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
