import os
import time
import socket
from network_manager import EnhancedNetworkManager

def interactive_node_creator():
    """Interactive CLI for creating nodes manually"""
    manager = EnhancedNetworkManager()
    
    print("🌐 Starting Cloud Registry...")
    manager.start_cloud()
    time.sleep(1)
    
    print("\n🎮 Interactive Node Creator")
    print("==========================")
    print("Create nodes manually and watch them auto-connect!")
    
    nodes_created = []
    
    while True:
        print("\nOptions:")
        print("1. Create new node")
        print("2. List all nodes")
        print("3. Network status")
        print("4. Transfer file")
        print("5. Stop all and exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            print("\nCreate New Node:")
            node_name = input("Node name: ").strip()
            host = input("Host (default: localhost): ").strip() or "localhost"
            port_input = input("Port (default: auto): ").strip()
            
            try:
                if port_input:
                    port = int(port_input)
                else:
                    # Find available port automatically
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('localhost', 0))
                        port = s.getsockname()[1]
                
                node = manager.create_node(node_name, host, port)
                nodes_created.append(node_name)
                print(f"✅ Node '{node_name}' created at {host}:{port}")
                
            except Exception as e:
                print(f"❌ Failed to create node: {e}")
        
        elif choice == '2':
            manager.list_all_nodes()
        
        elif choice == '3':
            status = manager.get_network_status()
            print("\n🌐 Network Status:")
            print(f"   Cloud: {status['cloud']['online_nodes']} nodes online")
            print(f"   Local: {len(status['local_nodes'])} nodes managed")
            
            for node_name, node_status in status['local_nodes'].items():
                print(f"   📍 {node_name}: {node_status['connected_nodes']} connections, "
                      f"{node_status['active_transfers']} active transfers")
        
        elif choice == '4':
            if len(nodes_created) < 2:
                print("❌ Need at least 2 nodes for file transfer")
                continue
                
            print("\n📤 File Transfer:")
            print(f"Available nodes: {', '.join(nodes_created)}")
            source_node = input("Source node: ").strip()
            target_node = input("Target node: ").strip()
            file_path = input("File path: ").strip()
            
            if source_node in nodes_created and target_node in nodes_created:
                if os.path.exists(file_path):
                    print("🔄 Starting file transfer...")
                    success = manager.transfer_file(source_node, file_path, target_node)
                    if success:
                        print("✅ Transfer initiated successfully")
                    else:
                        print("❌ Transfer failed")
                else:
                    print("❌ File not found")
            else:
                print("❌ Invalid node names")
        
        elif choice == '5':
            print("\n🛑 Shutting down...")
            manager.stop_all()
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    interactive_node_creator()