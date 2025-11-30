import os
import sys
import re

def fix_grpc_imports():
    """Fix the import statement in generated gRPC file"""
    grpc_file = 'generated/calculator_pb2_grpc.py'
    
    if not os.path.exists(grpc_file):
        print("✗ calculator_pb2_grpc.py not found")
        return
    
    with open(grpc_file, 'r') as f:
        content = f.read()
    
    # Replace: import calculator_pb2 as calculator__pb2
    # With: from . import calculator_pb2 as calculator__pb2
    original_content = content
    content = re.sub(
        r'^import calculator_pb2 as calculator__pb2',
        'from . import calculator_pb2 as calculator__pb2',
        content,
        flags=re.MULTILINE
    )
    
    if content != original_content:
        with open(grpc_file, 'w') as f:
            f.write(content)
        print("✓ Fixed imports in calculator_pb2_grpc.py")
    else:
        print("⚠ No import fix needed or pattern not found")

def generate_proto():
    """Generate Python code from proto file"""
    
    # Create generated directory if it doesn't exist
    if not os.path.exists('generated'):
        os.makedirs('generated')
        print("✓ Created 'generated' directory")
    
    # Create __init__.py in generated directory
    init_file = os.path.join('generated', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('')
        print("✓ Created generated/__init__.py")
    
    # Generate protobuf files
    cmd = (
        "python -m grpc_tools.protoc "
        "-I./proto "
        "--python_out=./generated "
        "--grpc_python_out=./generated "
        "./proto/calculator.proto"
    )
    
    print("\nGenerating protobuf files...")
    print(f"Command: {cmd}\n")
    
    result = os.system(cmd)
    
    if result == 0:
        print("\n✓ Protobuf files generated successfully!")
        print("  - generated/calculator_pb2.py")
        print("  - generated/calculator_pb2_grpc.py")
        
        
        fix_grpc_imports()
    else:
        print("\n✗ Failed to generate protobuf files")
        print("Make sure grpcio-tools is installed:")
        print("  pip install grpcio-tools")
        sys.exit(1)

if __name__ == '__main__':
    generate_proto()