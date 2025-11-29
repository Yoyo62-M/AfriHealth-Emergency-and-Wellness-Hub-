import socket
import threading
import time
from typing import Dict, Optional

# Import configuration
try:
    from config.default_config import NetworkConfig
except ImportError:
    # Fallback if config import fails
    class NetworkConfig:
        DEFAULT_CLOUD_HOST = 'localhost'
        DEFAULT_CLOUD_PORT = 8888

try:
    from cloud_registry import CloudRegistry
    from enhanced_node import EnhancedRealNode
except ImportError as e:
    print(f"Import error: {e}")
    # Define fallback classes if imports fail
    class CloudRegistry:
        def __init__(self, *args, **kwargs): pass
        def start_registry(self): pass
        def stop(self): pass
        def get_network_status(self): return {}
    
    class EnhancedRealNode:
        def __init__(self, *args, **kwargs): pass
        def start(self): return False
        def stop(self): pass
        def get_status(self): return {}
        def list_connections(self): pass

class EnhancedNetworkManager:
    """Manages the cloud registry and provides node creation interface"""
    
    def __init__(self, cloud_host=NetworkConfig.DEFAULT_CLOUD_HOST, 
                 cloud_port=NetworkConfig.DEFAULT_CLOUD_PORT):
        self.cloud_host = cloud_host
        self.cloud_port = cloud_port
        self.cloud_registry = CloudRegistry(cloud_host, cloud_port)
        self.nodes: Dict[str, EnhancedRealNode] = {}
        
    def start_cloud(self):
        """Start the cloud registry"""
        self.cloud_registry.start_registry()
        print("☁️  Cloud registry started")
        
    def create_node(self, node_name: str, host: str, port: int) -> EnhancedRealNode:
        """Create a new node with manual configuration"""
        if any(node.node_name == node_name for node in self.nodes.values()):
            raise ValueError(f"Node name '{node_name}' already exists")
            
        # Check if port is available
        if not self._is_port_available(host, port):
            raise ValueError(f"Port {port} on {host} is not available")
        
        node = EnhancedRealNode(node_name, host, port, self.cloud_host, self.cloud_port)
        
        if node.start():
            self.nodes[node.node_id] = node
            print(f"🎉 Node '{node_name}' created successfully at {host}:{port}")
            return node
        else:
            raise Exception(f"Failed to start node '{node_name}'")
    
    def _is_port_available(self, host: str, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.bind((host, port))
                return True
        except:
            return False
    
    def get_node(self, node_name: str) -> Optional[EnhancedRealNode]:
        """Get node by name"""
        for node in self.nodes.values():
            if node.node_name == node_name:
                return node
        return None
    
    def transfer_file(self, source_node_name: str, file_path: str, target_node_name: str) -> bool:
        """Transfer file between nodes by name"""
        source_node = self.get_node(source_node_name)
        target_node = self.get_node(target_node_name)
        
        if not source_node:
            print(f"❌ Source node '{source_node_name}' not found")
            return False
            
        if not target_node:
            print(f"❌ Target node '{target_node_name}' not found")
            return False
        
        # Find connection to target node
        target_connection = None
        for conn_id, node_info in source_node.connected_nodes.items():
            if node_info['node_name'] == target_node_name:
                target_connection = conn_id
                break
        
        if not target_connection:
            print(f"❌ No connection found to target node '{target_node_name}'")
            return False
        
        return source_node.send_file(file_path, target_connection)
    
    def get_network_status(self):
        """Get complete network status"""
        cloud_status = self.cloud_registry.get_network_status()
        
        node_statuses = {}
        for node_id, node in self.nodes.items():
            node_statuses[node.node_name] = node.get_status()
        
        return {
            'cloud': cloud_status,
            'local_nodes': node_statuses
        }
    
    def list_all_nodes(self):
        """List all created nodes"""
        print("\n📋 Created Nodes:")
        if not self.nodes:
            print("   No nodes created yet")
        for node in self.nodes.values():
            status = node.get_status()
            print(f"   📍 {node.node_name} - {status['address']} - {status['connected_nodes']} connections")
    
    def stop_all(self):
        """Stop all nodes and cloud"""
        for node in self.nodes.values():
            node.stop()
        self.cloud_registry.stop()
        print("🛑 Network manager stopped")

if __name__ == "__main__":
    # Test the network manager
    manager = EnhancedNetworkManager()
    manager.start_cloud()
    
    try:
        # Create some test nodes
        node1 = manager.create_node("test-node-1", "localhost", 9001)
        node2 = manager.create_node("test-node-2", "localhost", 9002)
        
        print("Waiting for auto-connection...")
        time.sleep(10)
        
        manager.list_all_nodes()
        
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_all()