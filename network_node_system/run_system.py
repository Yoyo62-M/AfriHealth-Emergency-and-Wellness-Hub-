#!/usr/bin/env python3
"""
Main entry point for the Network Node System
Run this file to start the complete system
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point"""
    print("🌐 Network Node System")
    print("=====================")
    print("Choose mode:")
    print("1. Interactive CLI (Create nodes manually)")
    print("2. Auto-Discovery Demo")
    print("3. Single Transfer Demo")
    print("4. Cloud Registry Only")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    try:
        if choice == '1':
            from interactive_cli import interactive_node_creator
            interactive_node_creator()
        elif choice == '2':
            from demo import demo_auto_discovery
            demo_auto_discovery()
        elif choice == '3':
            from demo import demo_single_transfer
            demo_single_transfer()
        elif choice == '4':
            from cloud_registry import CloudRegistry
            registry = CloudRegistry()
            try:
                registry.start_registry()
                print("Cloud Registry started. Press Ctrl+C to stop.")
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                registry.stop()
        else:
            print("❌ Invalid choice")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all files are in the same directory:")
        print("   - interactive_cli.py")
        print("   - demo.py") 
        print("   - cloud_registry.py")
        print("   - enhanced_node.py")
        print("   - network_manager.py")
        print("   - config/default_config.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()