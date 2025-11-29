import socket
import threading
import json
import time
from typing import Dict

# Import configuration
try:
    from config.default_config import NetworkConfig
except ImportError:
    # Fallback if config import fails
    class NetworkConfig:
        CHUNK_SIZE = 1024
        ACK_INTERVAL = 3
        BUFFER_SIZE = 4096
        TIMEOUT = 30
        DISCOVERY_PORT = 8888
        HEARTBEAT_INTERVAL = 10
        DEFAULT_CLOUD_HOST = 'localhost'
        DEFAULT_CLOUD_PORT = 8888
        MAX_CONNECTIONS = 50

class CloudRegistry:
    """Central registry for automatic node discovery"""
    
    def __init__(self, host=NetworkConfig.DEFAULT_CLOUD_HOST, port=NetworkConfig.DISCOVERY_PORT):
        self.host = host
        self.port = port
        self.registered_nodes: Dict[str, Dict] = {}
        self.running = False
        self.server_socket = None
        
    def start_registry(self):
        """Start the cloud registry server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(NetworkConfig.MAX_CONNECTIONS)
            self.running = True
            
            print(f"🔍 Cloud Registry running on {self.host}:{self.port}")
            
            # Start accepting connections
            accept_thread = threading.Thread(target=self._accept_registry_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=self._cleanup_loop)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
        except Exception as e:
            print(f"❌ Failed to start registry: {e}")
            
    def _accept_registry_connections(self):
        """Accept connections from nodes wanting to register"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                thread = threading.Thread(
                    target=self._handle_registration,
                    args=(client_socket, client_address)
                )
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"Registry connection error: {e}")
    
    def _handle_registration(self, client_socket: socket.socket, client_address: tuple):
        """Handle node registration and discovery requests"""
        try:
            data = client_socket.recv(NetworkConfig.BUFFER_SIZE)
            if not data:
                return
                
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type')
            
            if msg_type == 'register':
                self._register_node(message, client_socket)
            elif msg_type == 'discover':
                self._provide_node_list(message, client_socket)
            elif msg_type == 'heartbeat':
                self._update_heartbeat(message, client_socket)
            elif msg_type == 'unregister':
                self._unregister_node(message, client_socket)
                
        except Exception as e:
            print(f"Registration error: {e}")
        finally:
            client_socket.close()
    
    def _register_node(self, message: Dict, client_socket: socket.socket):
        """Register a new node with the cloud"""
        node_info = message['node_info']
        node_id = node_info['node_id']
        
        # Add registration timestamp and last heartbeat
        node_info['registered_at'] = time.time()
        node_info['last_heartbeat'] = time.time()
        node_info['status'] = 'online'
        
        self.registered_nodes[node_id] = node_info
        
        print(f"✅ Node registered: {node_id} at {node_info['ip_address']}:{node_info['port']}")
        
        # Send confirmation
        response = {
            'type': 'registration_ack',
            'status': 'success',
            'message': f'Node {node_id} registered successfully'
        }
        client_socket.send(json.dumps(response).encode('utf-8'))
    
    def _provide_node_list(self, message: Dict, client_socket: socket.socket):
        """Provide list of all registered nodes to requesting node"""
        requester_id = message.get('requester_id')
        
        # Filter out the requester itself and offline nodes
        available_nodes = {
            node_id: info for node_id, info in self.registered_nodes.items()
            if node_id != requester_id and info.get('status') == 'online'
        }
        
        response = {
            'type': 'discovery_response',
            'available_nodes': available_nodes,
            'total_nodes': len(available_nodes)
        }
        
        client_socket.send(json.dumps(response).encode('utf-8'))
        print(f"🔍 Provided node list to {requester_id} ({len(available_nodes)} nodes available)")
    
    def _update_heartbeat(self, message: Dict, client_socket: socket.socket):
        """Update node heartbeat"""
        node_id = message['node_id']
        
        if node_id in self.registered_nodes:
            self.registered_nodes[node_id]['last_heartbeat'] = time.time()
            self.registered_nodes[node_id]['status'] = 'online'
            
            response = {'type': 'heartbeat_ack'}
            client_socket.send(json.dumps(response).encode('utf-8'))
    
    def _unregister_node(self, message: Dict, client_socket: socket.socket):
        """Remove node from registry"""
        node_id = message['node_id']
        
        if node_id in self.registered_nodes:
            del self.registered_nodes[node_id]
            print(f"❌ Node unregistered: {node_id}")
            
            response = {'type': 'unregistration_ack'}
            client_socket.send(json.dumps(response).encode('utf-8'))
    
    def _cleanup_loop(self):
        """Continuously clean up offline nodes"""
        while self.running:
            time.sleep(60)  # Cleanup every minute
            self.cleanup_offline_nodes()
    
    def cleanup_offline_nodes(self):
        """Remove nodes that haven't sent heartbeats"""
        current_time = time.time()
        offline_nodes = []
        
        for node_id, info in self.registered_nodes.items():
            if current_time - info['last_heartbeat'] > NetworkConfig.HEARTBEAT_INTERVAL * 3:
                offline_nodes.append(node_id)
        
        for node_id in offline_nodes:
            del self.registered_nodes[node_id]
            print(f"🧹 Removed offline node: {node_id}")
    
    def get_network_status(self):
        """Get current network status"""
        online_nodes = [node_id for node_id, info in self.registered_nodes.items() 
                       if info.get('status') == 'online']
        
        return {
            'total_registered': len(self.registered_nodes),
            'online_nodes': len(online_nodes),
            'nodes': self.registered_nodes
        }
    
    def stop(self):
        """Stop the registry"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("🛑 Cloud Registry stopped")

if __name__ == "__main__":
    # Run cloud registry standalone
    registry = CloudRegistry()
    try:
        registry.start_registry()
        print("Cloud Registry started. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        registry.stop()