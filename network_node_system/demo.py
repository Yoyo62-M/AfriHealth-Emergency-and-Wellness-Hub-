import os
import time
import threading
import socket
from network_manager import EnhancedNetworkManager

def demo_auto_discovery():
    """Demonstrate automatic node discovery and connection"""
    print("🚀 Starting Auto-Discovery Demo")
    print("================================\n")
    
    manager = EnhancedNetworkManager()
    manager.start_cloud()
    
    # Create nodes with manual configuration
    nodes_config = [
        {"name": "office-pc", "host": "localhost", "port": 9001},
        {"name": "laptop", "host": "localhost", "port": 9002},
        {"name": "server", "host": "localhost", "port": 9003},
        {"name": "mobile", "host": "localhost", "port": 9004},
    ]
    
    nodes = []
    print("Creating nodes...")
    for config in nodes_config:
        try:
            node = manager.create_node(config["name"], config["host"], config["port"])
            nodes.append(node)
            time.sleep(0.5)  # Small delay between node creation
        except Exception as e:
            print(f"Failed to create {config['name']}: {e}")
    
    print("\n⏳ Waiting for nodes to auto-discover and connect...")
    time.sleep(10)
    
    # Show network status
    status = manager.get_network_status()
    print(f"\n✅ Network ready! {status['cloud']['online_nodes']} nodes online")
    
    # Show connections for each node
    for node in nodes:
        node.list_connections()
    
    # Create test files
    print("\n📁 Creating test files...")
    test_files = []
    for i in range(3):
        test_file = f"test_document_{i}.txt"
        with open(test_file, 'w') as f:
            f.write(f"This is test document {i} for automatic network transfer! " * 50)
        test_files.append(test_file)
        print(f"Created: {test_file} ({os.path.getsize(test_file)} bytes)")
    
    # Perform file transfers
    print("\n📤 Starting file transfers...")
    
    def transfer_files():
        # Transfer from office-pc to laptop
        if len(nodes) >= 2:
            print("Transferring file from office-pc to laptop...")
            success = manager.transfer_file("office-pc", test_files[0], "laptop")
            if success:
                print("✅ Transfer 1 initiated")
        
        time.sleep(5)
        
        # Transfer from laptop to server
        if len(nodes) >= 3:
            print("Transferring file from laptop to server...")
            success = manager.transfer_file("laptop", test_files[1], "server")
            if success:
                print("✅ Transfer 2 initiated")
    
    # Start transfers in background
    transfer_thread = threading.Thread(target=transfer_files)
    transfer_thread.daemon = True
    transfer_thread.start()
    
    # Monitor network for a while
    print("\n📊 Monitoring network activity (Ctrl+C to stop)...")
    try:
        monitor_count = 0
        while monitor_count < 30:  # Monitor for 30 seconds
            time.sleep(2)
            monitor_count += 2
            
            # Show brief status every 10 seconds
            if monitor_count % 10 == 0:
                status = manager.get_network_status()
                active_transfers = sum(node.get_status()['active_transfers'] 
                                     for node in nodes)
                print(f"\n📈 Status update: {active_transfers} active transfers, "
                      f"{status['cloud']['online_nodes']} nodes online")
                
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    for test_file in test_files:
        if os.path.exists(test_file):
            os.remove(test_file)
    
    manager.stop_all()
    print("Demo completed!")

def demo_single_transfer():
    """Demo simple file transfer between two nodes"""
    print("\n💾 Single Transfer Demo")
    print("======================\n")
    
    manager = EnhancedNetworkManager()
    manager.start_cloud()
    
    try:
        # Create two nodes
        node1 = manager.create_node("sender", "localhost", 9101)
        node2 = manager.create_node("receiver", "localhost", 9102)
        
        print("Waiting for connection...")
        time.sleep(5)
        
        # Create test file
        test_file = "large_test_file.dat"
        with open(test_file, 'wb') as f:
            f.write(os.urandom(50000))  # 50KB random file
        
        print(f"Created test file: {test_file} ({os.path.getsize(test_file)} bytes)")
        
        # Transfer file
        print("Starting file transfer...")
        success = manager.transfer_file("sender", test_file, "receiver")
        
        if success:
            print("✅ File transfer initiated successfully!")
            print("Waiting for transfer to complete...")
            time.sleep(10)
        else:
            print("❌ File transfer failed")
        
        # Show final status
        node1_status = node1.get_status()
        node2_status = node2.get_status()
        
        print(f"\nFinal status:")
        print(f"Sender: {node1_status['storage']['total_files']} files")
        print(f"Receiver: {node2_status['storage']['total_files']} files")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print(f"Demo error: {e}")
    finally:
        manager.stop_all()

if __name__ == "__main__":
    # Run both demos
    demo_auto_discovery()
    demo_single_transfer()