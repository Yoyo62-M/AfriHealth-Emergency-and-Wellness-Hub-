# CloudGrpc - Secure gRPC Calculator with Storage Management

A complete, thread-safe Python gRPC microservice that provides authenticated calculator operations with a strict global storage budget of 6 GB.

## 🎯 Features

- **Authentication System**: Email-based OTP verification
- **Storage Management**: 6 GB global limit, 1 GB per user allocation
- **Calculator Operations**: Add, Subtract, Multiply, Divide, Modulo
- **Thread-Safe**: Concurrent request handling with ThreadPoolExecutor
- **Strict Limits**: Maximum 6 users, enforced at enrollment

## 📁 Project Structure

```
CloudGrpc/
├── proto/
│   └── calculator.proto          # Protocol definitions
├── generated/                     # Auto-generated (do not edit)
│   ├── calculator_pb2.py
│   └── calculator_pb2_grpc.py
├── server/
│   └── calculator_service.py     # Server implementation
├── client/
│   └── calculator_client.py      # Client demonstration
├── auth/
│   └── gmail_otp.py              # OTP generation & email
├── user/
│   └── user_manager.py           # Storage & user management
├── generate_proto.py             # Proto compilation script
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your Gmail credentials (optional)
# If not configured, system runs in TEST MODE with OTP printed to console
```

To use real Gmail OTP:

1. Enable 2-Step Verification in Google Account
2. Generate App Password (Google Account → Security → App Passwords)
3. Add credentials to `.env`

### 3. Generate Protocol Buffers

```bash
python generate_proto.py
```

This creates:

- `generated/calculator_pb2.py`
- `generated/calculator_pb2_grpc.py`

### 4. Create Directory Structure

```bash
mkdir -p proto server client auth user generated
```

Place the files in their respective directories as shown in the project structure.

## 🎮 Running the Application

### Start the Server

```bash
python server/calculator_service.py
```

Expected output:

```
CloudGrpc Server starting on port 50051...
Global storage: 6 GB | Per-user allocation: 1 GB | Max users: 6
Server started successfully!
```

### Run the Client

In a new terminal:

```bash
python client/calculator_client.py
```

The client will:

1. Login with email (sends OTP)
2. Ask you to enter OTP
3. Enroll the user (allocates 1 GB storage)
4. Perform calculator operations
5. Demonstrate concurrent operations
6. Test storage exhaustion (7th user rejection)

## 🔒 Storage Policy

- **Global Capacity**: 6 GB (6,000,000,000 bytes)
- **Per-User Allocation**: 1 GB (1,000,000,000 bytes)
- **Maximum Users**: 6
- **Allocation**: Reserved at enrollment, not on usage
- **7th User**: Rejected with `RESOURCE_EXHAUSTED` error

### Error Message for Storage Exhaustion

```
RESOURCE_EXHAUSTED: System storage exhausted. Cannot allocate storage for new users.
```

## 📝 API Usage Examples

### Authentication Flow

```python
from client.calculator_client import CloudGrpcClient

client = CloudGrpcClient()

# Step 1: Login (sends OTP)
client.login("user@example.com")

# Step 2: Verify OTP
client.verify_otp("user@example.com", "123456")

# Step 3: Enroll
client.enroll("user@example.com", "John Doe")
```

### Calculator Operations

```python
# All operations require session_token
client.add(100, 50)    # Returns 150
client.sub(100, 50)    # Returns 50
client.mul(100, 50)    # Returns 5000
client.div(100, 50)    # Returns 2
client.mod(100, 50)    # Returns 0
```

### Concurrent Operations

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(client.add, 633, 27),
        executor.submit(client.sub, 633, 27),
        executor.submit(client.div, 633, 27),
        executor.submit(client.mod, 633, 27)
    ]
```

## ⚠️ Error Handling

### Authentication Errors

- `UNAUTHENTICATED`: Invalid or missing session token
- `FAILED_PRECONDITION`: Email not verified before enrollment

### Operation Errors

- `INVALID_ARGUMENT`: Division or modulo by zero
- `RESOURCE_EXHAUSTED`: No storage available for new users

### Example Error Response

```python
try:
    client.div(100, 0)
except grpc.RpcError as e:
    print(f"Error: [{e.code().name}] {e.details()}")
    # Output: Error: [INVALID_ARGUMENT] Division by zero is not allowed.
```

## 🧪 Testing Storage Limits

The client includes a demonstration that enrolls 7 users to show the storage limit enforcement:

```python
def demo_storage_exhaustion():
    # Enrolls users 1-6 successfully
    # User 7 is rejected with RESOURCE_EXHAUSTED
```

## 🔧 Configuration

### Storage Constants

In `user/user_manager.py`:

```python
GLOBAL_STORAGE_BYTES = 6_000_000_000  # 6 GB
PER_USER_ALLOCATION = 1_000_000_000   # 1 GB
MAX_USERS = 6
```

### OTP Settings

In `auth/gmail_otp.py`:

```python
OTP_VALIDITY_SECONDS = 300  # 5 minutes
```

### Server Settings

In `server/calculator_service.py`:

```python
# Port configuration
server.add_insecure_port('[::]:50051')

# Thread pool size
futures.ThreadPoolExecutor(max_workers=10)
```

## 📊 System Behavior

### Enrollment Process

1. User calls `Login(email)` → OTP sent to email
2. User calls `VerifyOtp(email, otp)` → OTP validated
3. User calls `Enroll(email, name)`:
   - Checks email verification (must be done within 5 min)
   - Checks global storage availability
   - Allocates 1 GB immediately
   - Returns session token

### Storage Allocation

- **Immediate**: Storage reserved at enrollment, not on first use
- **Atomic**: Either full 1 GB allocated or enrollment fails
- **Non-Negotiable**: No partial allocations

## 🐛 Troubleshooting

### "Module not found" errors

```bash
# Make sure you're in the project root directory
cd CloudGrpc

# Regenerate proto files
python generate_proto.py
```

### OTP not received

- Check `.env` file configuration
- Verify Gmail App Password is correct
- System falls back to TEST MODE if email fails (OTP printed in console)

### Port already in use

```bash
# Find process using port 50051
lsof -i :50051

# Kill the process
kill -9 <PID>
```

## 📜 License

This project is provided as-is for educational purposes.

## 🤝 Contributing

This is a demonstration project. Feel free to extend it with:

- Persistent storage (database)
- TLS/SSL encryption
- Additional calculator operations
- Web interface
- Monitoring and logging

## ⚡ Quick Start Summary

```bash
# 1. Install
pip install -r requirements.txt

# 2. Generate proto
python generate_proto.py

# 3. Start server (Terminal 1)
python server/calculator_service.py

# 4. Run client (Terminal 2)
python client/calculator_client.py
```

---

**Note**: The 7th user enrollment attempt will always fail with the message:

```
RESOURCE_EXHAUSTED: System storage exhausted. Cannot allocate storage for new users.
```

This is the expected behavior demonstrating the strict 6 GB limit.
