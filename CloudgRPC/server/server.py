import grpc
from concurrent import futures
import sys
import os

# Add parent directory to path to import generated modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from generated import calculator_pb2
from generated import calculator_pb2_grpc
from auth.gmail_otp import OTPManager
from user.user_manager import UserManager
from config import ADMIN_KEY, SERVER_HOST

# Initialize managers
otp_manager = OTPManager()
user_manager = UserManager()

class AuthServiceServicer(calculator_pb2_grpc.AuthServiceServicer):
    """Implementation of AuthService"""
    
    def _validate_email(self, email):
        """Validate email format"""
        return email and '@' in email
    
    def SendOtp(self, request, context):
        """Send OTP to user's email"""
        email = request.email
        
        if not self._validate_email(email):
            return calculator_pb2.SendOtpResponse(
                success=False,
                message="Invalid email address."
            )
        
        success, message = otp_manager.send_otp(email)
        
        if success:
            user_manager.mark_email_verified(email)
        
        return calculator_pb2.SendOtpResponse(
            success=success,
            message=message
        )
    
    def VerifyOtp(self, request, context):
        """Verify OTP entered by user"""
        email = request.email
        otp = request.otp
        
        success, message = otp_manager.verify_otp(email, otp)
        
        return calculator_pb2.VerifyOtpResponse(
            success=success,
            message=message
        )
    
    def Login(self, request, context):
        """Login existing user and return session token"""
        email = request.email
        
        if not user_manager.user_exists(email):
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                "User not found. Please enroll first."
            )
        
        if not user_manager.is_email_verified(email):
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Email not verified. Please complete OTP verification first."
            )
        
        success, message, token, user_name = user_manager.login_existing_user(email)
        
        if not success:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, message)
        
        return calculator_pb2.LoginResponse(
            success=True,
            message=message,
            session_token=token
        )
    
    def Enroll(self, request, context):
        """Enroll a new user with storage allocation"""
        email = request.email
        full_name = request.full_name
        
        if not user_manager.is_email_verified(email):
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Email not verified. Please complete login and OTP verification first."
            )
        
        if user_manager.user_exists(email):
            context.abort(
                grpc.StatusCode.ALREADY_EXISTS,
                "User already enrolled. Please use Login option instead."
            )
        
        if not user_manager.can_allocate_new_user():
            context.abort(
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                "System storage exhausted. Cannot allocate storage for new users."
            )
        
        success, message, token = user_manager.enroll_user(email, full_name)
        
        if not success:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, message)
        
        return calculator_pb2.EnrollResponse(
            success=True,
            message=message,
            session_token=token
        )
    
    def GetStorageInfo(self, request, context):
        """Get storage information for the authenticated user"""
        token = request.session_token
        
        if not token:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Session token is required."
            )
        
        storage_info = user_manager.get_user_storage_info(token)
        
        if not storage_info:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Invalid session token."
            )
        
        return calculator_pb2.StorageInfoResponse(
            success=True,
            message=storage_info['message'],
            allocated_bytes=storage_info['allocated'],
            used_bytes=storage_info['used'],
            available_bytes=storage_info['available'],
            usage_percentage=storage_info['usage_percentage']
        )


class CalculatorServicer(calculator_pb2_grpc.CalculatorServicer):
    """Implementation of Calculator service"""
    
    def _validate_token(self, token, context):
        """Validate session token and return user"""
        if not token:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Session token is required."
            )
        
        user = user_manager.get_user_by_token(token)
        if not user:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Invalid session token."
            )
        
        return user
    
    def _perform_operation(self, context, operation_func, a, b, token):
        """Common method to perform calculator operations"""
        user = self._validate_token(token, context)
        result = operation_func(a, b)
        user_manager.update_user_storage_usage(token, 100)
        return result, user['name']
    
    def Add(self, request, context):
        """Add two numbers"""
        result, user_name = self._perform_operation(
            context, lambda a, b: a + b, request.a, request.b, request.session_token
        )
        
        return calculator_pb2.AddResponse(
            success=True,
            message=f"Addition performed successfully for user {user_name}",
            result=result
        )
    
    def Sub(self, request, context):
        """Subtract two numbers"""
        result, user_name = self._perform_operation(
            context, lambda a, b: a - b, request.a, request.b, request.session_token
        )
        
        return calculator_pb2.SubResponse(
            success=True,
            message=f"Subtraction performed successfully for user {user_name}",
            result=result
        )
    
    def Mul(self, request, context):
        """Multiply two numbers"""
        result, user_name = self._perform_operation(
            context, lambda a, b: a * b, request.a, request.b, request.session_token
        )
        
        return calculator_pb2.MulResponse(
            success=True,
            message=f"Multiplication performed successfully for user {user_name}",
            result=result
        )
    
    def Div(self, request, context):
        """Divide two numbers"""
        if request.b == 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Division by zero is not allowed."
            )
        
        result, user_name = self._perform_operation(
            context, lambda a, b: a // b, request.a, request.b, request.session_token
        )
        
        return calculator_pb2.DivResponse(
            success=True,
            message=f"Division performed successfully for user {user_name}",
            result=result
        )
    
    def Mod(self, request, context):
        """Modulo operation"""
        if request.b == 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Modulo by zero is not allowed."
            )
        
        result, user_name = self._perform_operation(
            context, lambda a, b: a % b, request.a, request.b, request.session_token
        )
        
        return calculator_pb2.ModResponse(
            success=True,
            message=f"Modulo performed successfully for user {user_name}",
            result=result
        )


class AdminServiceServicer(calculator_pb2_grpc.AdminServiceServicer):
    """Implementation of AdminService for system monitoring and management"""
    
    def _validate_admin_key(self, admin_key, context):
        """Validate admin key"""
        if admin_key != ADMIN_KEY:
            context.abort(
                grpc.StatusCode.PERMISSION_DENIED,
                "Invalid admin key"
            )
    
    def GetSystemStatus(self, request, context):
        """Get comprehensive system status"""
        self._validate_admin_key(request.admin_key, context)
        
        status = user_manager.get_system_status()
        
        return calculator_pb2.SystemStatusResponse(
            success=True,
            message="System status retrieved successfully",
            global_capacity_bytes=status['global_capacity'],
            global_allocated_bytes=status['global_allocated'],
            global_available_bytes=status['global_available'],
            global_used_bytes=status['global_used'],
            total_users=status['total_users'],
            max_users=status['max_users'],
            allocation_percentage=status['allocation_percentage'],
            usage_percentage=status['usage_percentage']
        )
    
    def UpdateGlobalStorage(self, request, context):
        """Update global storage capacity"""
        self._validate_admin_key(request.admin_key, context)
        
        success, message, old_cap, new_cap = user_manager.update_global_capacity(request.new_capacity_gb)
        
        if not success:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, message)
        
        return calculator_pb2.UpdateStorageResponse(
            success=True,
            message=message,
            old_capacity_bytes=old_cap,
            new_capacity_bytes=new_cap
        )
    
    def StreamSystemEvents(self, request, context):
        """Stream real-time system events"""
        self._validate_admin_key(request.admin_key, context)
        
        print("\n[Admin Monitor] Event streaming started...")
        
        try:
            while context.is_active():
                try:
                    event = user_manager.event_queue.get(timeout=1.0)
                    yield calculator_pb2.SystemEvent(
                        event_type=event['event_type'],
                        timestamp=event['timestamp'],
                        message=event['message'],
                        user_email=event['user_email'],
                        storage_change=event['storage_change']
                    )
                except queue.Empty:
                    continue
        except Exception as e:
            print(f"[Admin Monitor] Stream ended: {e}")


def serve():
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add servicers
    calculator_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
    calculator_pb2_grpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    calculator_pb2_grpc.add_AdminServiceServicer_to_server(AdminServiceServicer(), server)
    
    # Bind to port
    server.add_insecure_port(f'[::]:{SERVER_HOST.split(":")[-1]}')
    
    print("="*60)
    print("CloudGrpc Server Starting...")
    print("="*60)
    status = user_manager.get_system_status()
    print(f"Global Storage: {status['global_capacity'] / 1e9:.1f} GB")
    print(f"Per-User Allocation: 1 GB")
    print(f"Max Users: {status['max_users']}")
    print(f"Admin Key: {ADMIN_KEY}")
    print("="*60)
    print(f"Server started on {SERVER_HOST}")
    print("Monitoring for real-time events...")
    print("="*60)
    
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()