# Gunicorn configuration for production deployment
# Optimized for handling 1000 users/minute

import multiprocessing

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1  # Typically 4-9 workers
worker_class = "uvicorn.workers.UvicornWorker"  # ASGI workers

# Binding
bind = "0.0.0.0:8000"

# Timeouts
timeout = 120           # Worker timeout (seconds)
graceful_timeout = 30   # Graceful shutdown timeout
keepalive = 5           # Keep-alive connections (seconds)

# Logging
accesslog = "-"         # Log to stdout
errorlog = "-"          # Log to stdout
loglevel = "info"

# Performance tuning
max_requests = 1000         # Recycle workers after N requests
max_requests_jitter = 50    # Random jitter to prevent thundering herd

# Process naming
proc_name = "coupon_api"
