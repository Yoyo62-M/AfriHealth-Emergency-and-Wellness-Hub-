#!/usr/bin/env python3
"""
Network Node System - Main File
A complete real network node system with automatic discovery
"""

import os
import sys

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

def show_banner():
    """Display system banner"""
    banner = """
    🌐 NETWORK NODE SYSTEM 🌐
    ========================
    
    Features:
    ✅ Real TCP/IP Network Communication
    ✅ Automatic Node Discovery & Connection  
    ✅ Manual Node Creation (Name/Host/Port)
    ✅ Chunked File Transfer (1KB chunks)
    ✅ ACK Every 3 Chunks
    ✅ Real Hard Drive Storage
    ✅ Multi-Threaded Operations
    ✅ Cloud-Based Registry
    
    Run 'python run_system.py' to start the system!
    """
    print(banner)

if __name__ == "__main__":
    show_banner()
    
    # Check if run_system.py exists
    if os.path.exists("run_system.py"):
        print("🚀 Starting system...")
        os.system("python run_system.py")
    else:
        print("❌ run_system.py not found. Please run that file to start the system.")