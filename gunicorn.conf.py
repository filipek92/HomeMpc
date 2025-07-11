# Gunicorn configuration file
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '26781')}"
backlog = 2048

# Worker processes
workers = 1  # Pro scheduler a optimalizaci používáme pouze 1 worker
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "powerplan_server"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Preload application (doporučuje se pro výkon)
preload_app = True

# Graceful timeout
graceful_timeout = 30

# Capture output from app
capture_output = True
