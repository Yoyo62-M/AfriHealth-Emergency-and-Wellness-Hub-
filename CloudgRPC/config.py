
"""
Configuration settings for CloudGrpc application
"""

# Server Configuration
SERVER_HOST = 'localhost:50051'

# Storage Configuration
GLOBAL_STORAGE_BYTES = 6_000_000_000  # 6 GB
PER_USER_ALLOCATION = 1_000_000_000   # 1 GB
MAX_USERS = 6

# Security Configuration
ADMIN_KEY = "admin123"
OTP_VALIDITY_SECONDS = 300  # 5 minutes

# Email Configuration
GMAIL_SMTP_SERVER = 'smtp.gmail.com'
GMAIL_SMTP_PORT = 587