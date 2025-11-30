import threading
import secrets
import time
import queue
from datetime import datetime

from config import GLOBAL_STORAGE_BYTES, PER_USER_ALLOCATION, MAX_USERS, OTP_VALIDITY_SECONDS

class UserManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.global_capacity = GLOBAL_STORAGE_BYTES
        self.global_used = 0
        self.users = {}  # email → { name, token, allocated, used }
        self.verified_emails = {}  # email → expiry_time (for OTP window)
        self.event_queue = queue.Queue()
    
    def _emit_event(self, event_type, message, user_email="", storage_change=0):
        """Emit a system event"""
        event = {
            'event_type': event_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': message,
            'user_email': user_email,
            'storage_change': storage_change
        }
        self.event_queue.put(event)
        # Also print to server console for real-time monitoring
        print(f"\n[{event['timestamp']}] {event_type}: {message}")
        if user_email:
            print(f"   User: {user_email}")
        if storage_change != 0:
            print(f"   Storage Change: {storage_change:,} bytes")
    
    def _check_storage_availability(self):
        """Check if storage is available for new user"""
        return (self.global_used + PER_USER_ALLOCATION <= self.global_capacity and 
                len(self.users) < MAX_USERS)
    
    def update_global_capacity(self, new_capacity_gb):
        """Update global storage capacity"""
        with self._lock:
            old_capacity = self.global_capacity
            new_capacity = new_capacity_gb * 1_000_000_000
            
            if new_capacity < self.global_used:
                return False, f"Cannot reduce capacity below currently allocated storage ({self.global_used:,} bytes)", old_capacity, new_capacity
            
            self.global_capacity = new_capacity
            
            # Update max users based on new capacity
            global MAX_USERS
            MAX_USERS = int(new_capacity / PER_USER_ALLOCATION)
            
            self._emit_event(
                'STORAGE_UPDATED',
                f'Global storage capacity updated from {old_capacity:,} to {new_capacity:,} bytes',
                storage_change=new_capacity - old_capacity
            )
            
            return True, f"Storage capacity updated to {new_capacity_gb} GB", old_capacity, new_capacity
    
    def is_email_verified(self, email):
        """Check if email has been verified and is within validity window"""
        with self._lock:
            if email not in self.verified_emails:
                return False
            expiry_time = self.verified_emails[email]
            if time.time() > expiry_time:
                del self.verified_emails[email]
                return False
            return True
    
    def mark_email_verified(self, email):
        """Mark email as verified with 5-minute expiry"""
        with self._lock:
            self.verified_emails[email] = time.time() + OTP_VALIDITY_SECONDS
    
    def can_allocate_new_user(self):
        """Check if there's enough global storage for a new user"""
        with self._lock:
            return self._check_storage_availability()
    
    def login_existing_user(self, email):
        """
        Login an existing user and generate new session token
        Returns: (success, message, token, user_name)
        """
        with self._lock:
            if not self.is_email_verified(email):
                return False, "Email not verified. Please complete OTP verification.", None, None
            
            if email not in self.users:
                return False, "User not enrolled. Please enroll first.", None, None
            
            # Generate new session token
            token = secrets.token_urlsafe(32)
            self.users[email]['token'] = token
            user_name = self.users[email]['name']
            
            # Remove from verified emails (one-time use)
            del self.verified_emails[email]
            
            self._emit_event(
                'USER_LOGIN',
                f'User {user_name} logged in successfully',
                user_email=email
            )
            
            return True, f"Successfully logged in as {user_name}.", token, user_name
    
    def user_exists(self, email):
        """Check if user is already enrolled"""
        with self._lock:
            return email in self.users
    
    def enroll_user(self, email, name):
        """
        Enroll a new user with storage allocation
        Returns: (success, message, token)
        """
        with self._lock:
            if not self.is_email_verified(email):
                return False, "Email not verified. Please login first.", None
            
            if email in self.users:
                return False, "User already enrolled. Please use Login option.", None
            
            if not self._check_storage_availability():
                return False, "System storage exhausted. Cannot allocate storage for new users.", None
            
            # Generate session token
            token = secrets.token_urlsafe(32)
            
            # Allocate storage and create user
            self.global_used += PER_USER_ALLOCATION
            self.users[email] = {
                'name': name,
                'token': token,
                'allocated': PER_USER_ALLOCATION,
                'used': 0
            }
            
            # Remove from verified emails (one-time use)
            del self.verified_emails[email]
            
            self._emit_event(
                'USER_ENROLLED',
                f'New user {name} enrolled successfully',
                user_email=email,
                storage_change=PER_USER_ALLOCATION
            )
            
            return True, f"Successfully enrolled {name}. Allocated 1 GB storage.", token
    
    def get_user_storage_info(self, token):
        """Get storage information for user by token"""
        with self._lock:
            for email, user_data in self.users.items():
                if user_data['token'] == token:
                    allocated = user_data['allocated']
                    used = user_data.get('used', 0)
                    available = allocated - used
                    usage_percentage = (used / allocated * 100) if allocated > 0 else 0
                    
                    return {
                        'success': True,
                        'message': 'Storage info retrieved successfully',
                        'email': email,
                        'name': user_data['name'],
                        'allocated': allocated,
                        'used': used,
                        'available': available,
                        'usage_percentage': usage_percentage
                    }
            return None
    
    def get_system_status(self):
        """Get comprehensive system status"""
        with self._lock:
            total_user_usage = sum(user.get('used', 0) for user in self.users.values())
            allocation_percentage = (self.global_used / self.global_capacity * 100) if self.global_capacity > 0 else 0
            usage_percentage = (total_user_usage / self.global_used * 100) if self.global_used > 0 else 0
            
            return {
                'global_capacity': self.global_capacity,
                'global_allocated': self.global_used,
                'global_available': self.global_capacity - self.global_used,
                'global_used': total_user_usage,
                'total_users': len(self.users),
                'max_users': MAX_USERS,
                'allocation_percentage': allocation_percentage,
                'usage_percentage': usage_percentage
            }
    
    def update_user_storage_usage(self, token, bytes_to_add):
        """Update storage usage for a user"""
        with self._lock:
            for email, user_data in self.users.items():
                if user_data['token'] == token:
                    current_used = user_data.get('used', 0)
                    new_used = current_used + bytes_to_add
                    
                    if new_used > user_data['allocated']:
                        return False, "Storage limit exceeded"
                    
                    user_data['used'] = new_used
                    
                    self._emit_event(
                        'OPERATION_PERFORMED',
                        f'Storage used: {bytes_to_add} bytes',
                        user_email=email,
                        storage_change=bytes_to_add
                    )
                    
                    return True, "Storage updated"
            return False, "User not found"
    
    def get_user_by_token(self, token):
        """Get user information by session token"""
        with self._lock:
            for email, user_data in self.users.items():
                if user_data['token'] == token:
                    return {
                        'email': email,
                        'name': user_data['name'],
                        'allocated': user_data['allocated']
                    }
            return None
    
    def get_user_count(self):
        """Get current user count"""
        with self._lock:
            return len(self.users)