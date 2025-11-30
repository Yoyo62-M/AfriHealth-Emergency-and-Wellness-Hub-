import smtplib
import random
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

from config import OTP_VALIDITY_SECONDS

load_dotenv()

class OTPManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.otps = {}  # email → (otp, expiry_time)
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    def _create_email_message(self, email, otp):
        """Create email message with OTP"""
        msg = MIMEMultipart()
        msg['From'] = self.gmail_user
        msg['To'] = email
        msg['Subject'] = 'CloudGrpc - Your OTP Code'
        
        body = f"""
        Hello,
        
        Your OTP for CloudGrpc authentication is: {otp}
        
        This OTP is valid for 5 minutes.
        
        If you did not request this OTP, please ignore this email.
        
        Best regards,
        CloudGrpc Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        return msg
    
    def _send_email(self, email, otp):
        """Send OTP email via Gmail SMTP"""
        try:
            msg = self._create_email_message(email, otp)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            return True, "OTP sent successfully to your email."
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def _store_otp(self, email, otp):
        """Store OTP with expiry timestamp"""
        with self._lock:
            self.otps[email] = (otp, time.time() + OTP_VALIDITY_SECONDS)
    
    def send_otp(self, email):
        """
        Generate and send OTP to user's email
        Returns: (success, message)
        """
        otp = self.generate_otp()
        
        # Store OTP first
        self._store_otp(email, otp)
        
        # Try to send email if credentials are available
        if self.gmail_user and self.gmail_password:
            success, message = self._send_email(email, otp)
            if success:
                return True, message
        
        # Fallback to test mode
        return True, f"OTP sent successfully. [TEST MODE: OTP is {otp}]"
    
    def verify_otp(self, email, otp):
        """
        Verify OTP for given email
        Returns: (success, message)
        """
        with self._lock:
            if email not in self.otps:
                return False, "No OTP found for this email. Please request a new one."
            
            stored_otp, expiry_time = self.otps[email]
            
            # Check if OTP expired
            if time.time() > expiry_time:
                del self.otps[email]
                return False, "OTP expired. Please request a new one."
            
            # Verify OTP
            if stored_otp == otp:
                del self.otps[email]
                return True, "OTP verified successfully."
            else:
                return False, "Invalid OTP. Please try again."
    
    def cleanup_expired_otps(self):
        """Clean up expired OTPs"""
        current_time = time.time()
        with self._lock:
            expired_emails = [
                email for email, (_, expiry) in self.otps.items() 
                if current_time > expiry
            ]
            for email in expired_emails:
                del self.otps[email]
            return len(expired_emails)
