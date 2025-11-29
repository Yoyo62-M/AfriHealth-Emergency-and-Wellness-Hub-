import socket
import threading
import json
import os
import time
import uuid
import random
from typing import Dict, Optional

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
        DEFAULT_STORAGE_PATH = "node_storage"
        TRANSFER_DELAY = 0.01

class EnhancedRealNode:
    def __init__(self, node_name: str, host: str, port: int, 
                 cloud_host: str = NetworkConfig.DEFAULT_CLOUD_HOST, 
                 cloud_port: int = NetworkConfig.DEFAULT_CLOUD_PORT):
        self.node_name = node_name
        self.node_id = f"{node_name}_{str(uuid.uuid4())[:8]}"
        self.host = host
        self.port = port
        self.mac_address = self._generate_mac_address()
        
        # Cloud registry configuration
        self.cloud_host = cloud_host
        self.cloud_port = cloud_port
        
        # Storage management
        self.storage_path = f"{NetworkConfig.DEFAULT_STORAGE_PATH}/{self.node_name}"
        self._setup_storage()
        
        # Network components
        self.server_socket = None
        self.connections: Dict[str, socket.socket] = {}
        self.running = False
        
        # File transfer state
        self.active_transfers: Dict[str, Dict] = {}
        self.transfer_lock = threading.Lock()
        
        # Connected nodes and discovered nodes
        self.connected_nodes: Dict[str, Dict] = {}
        self.discovered_nodes: Dict[str, Dict] = {}
        
        # Auto-connect thread
        self.auto_connect_thread = None
        self.auto_connect_running = False
        
        print(f"🟢 Node '{self.node_name}' initialized:")
        print(f"   ID: {self.node_id}")
        print(f"   Address: {self.host}:{self.port}")
        print(f"   MAC: {self.mac_address}")
        print(f"   Storage: {self.storage_path}")

    def _generate_mac_address(self) -> str:
        """Generate a unique MAC address"""
        return "02:{}:{}:{}:{}:{}".format(
            *([random.randint(0x00, 0xff) for _ in range(5)])
        )

    def _setup_storage(self):
        """Create storage directory for the node"""
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(f"{self.storage_path}/incoming", exist_ok=True)
        os.makedirs(f"{self.storage_path}/outgoing", exist_ok=True)
        os.makedirs(f"{self.storage_path}/completed", exist_ok=True)

    def start(self):
        """Start the node and connect to cloud"""
        # Start TCP server
        self._start_server()
        
        # Register with cloud
        if self._register_with_cloud():
            # Start heartbeat thread
            self._start_heartbeat()
            
            # Start auto-discovery and connection
            self._start_auto_connect()
            
            print(f"🚀 Node '{self.node_name}' fully operational and connected to cloud")
            return True
        return False

    def _start_server(self):
        """Start the TCP server to listen for incoming connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            # Start accepting connections
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            print(f"📡 Node '{self.node_name}' listening on {self.host}:{self.port}")
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            self.running = False

    def _register_with_cloud(self) -> bool:
        """Register this node with the cloud registry"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((self.cloud_host, self.cloud_port))
                
                registration_msg = {
                    'type': 'register',
                    'node_info': {
                        'node_id': self.node_id,
                        'node_name': self.node_name,
                        'ip_address': self.host,
                        'port': self.port,
                        'mac_address': self.mac_address,
                        'storage_path': self.storage_path
                    }
                }
                
                s.send(json.dumps(registration_msg).encode('utf-8'))
                response_data = s.recv(NetworkConfig.BUFFER_SIZE)
                response = json.loads(response_data.decode('utf-8'))
                
                if response.get('status') == 'success':
                    print(f"☁️  Successfully registered with cloud registry")
                    return True
                else:
                    print(f"❌ Failed to register with cloud: {response.get('message')}")
                    return False
                    
        except Exception as e:
            print(f"❌ Cloud registration failed: {e}")
            return False

    def _start_heartbeat(self):
        """Start periodic heartbeat to cloud"""
        def heartbeat_loop():
            while self.running:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(5)
                        s.connect((self.cloud_host, self.cloud_port))
                        
                        heartbeat_msg = {
                            'type': 'heartbeat',
                            'node_id': self.node_id
                        }
                        
                        s.send(json.dumps(heartbeat_msg).encode('utf-8'))
                        # Wait for ACK
                        s.recv(NetworkConfig.BUFFER_SIZE)
                        
                except Exception as e:
                    print(f"💓 Heartbeat failed: {e}")
                
                time.sleep(NetworkConfig.HEARTBEAT_INTERVAL)
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

    def _start_auto_connect(self):
        """Start automatic discovery and connection to other nodes"""
        self.auto_connect_running = True
        self.auto_connect_thread = threading.Thread(target=self._auto_connect_loop)
        self.auto_connect_thread.daemon = True
        self.auto_connect_thread.start()

    def _auto_connect_loop(self):
        """Continuously discover and connect to other nodes"""
        while self.running and self.auto_connect_running:
            try:
                # Discover available nodes from cloud
                available_nodes = self._discover_nodes()
                
                # Connect to new nodes
                for node_id, node_info in available_nodes.items():
                    if node_id not in self.connected_nodes and node_id != self.node_id:
                        self._connect_to_node(node_info)
                
                # Update discovered nodes list
                self.discovered_nodes = available_nodes
                
                # Wait before next discovery cycle
                time.sleep(15)  # Discover every 15 seconds
                
            except Exception as e:
                print(f"🔍 Auto-connect error: {e}")
                time.sleep(30)  # Wait longer on error

    def _discover_nodes(self) -> Dict[str, Dict]:
        """Discover available nodes from cloud registry"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((self.cloud_host, self.cloud_port))
                
                discover_msg = {
                    'type': 'discover',
                    'requester_id': self.node_id
                }
                
                s.send(json.dumps(discover_msg).encode('utf-8'))
                response_data = s.recv(NetworkConfig.BUFFER_SIZE)
                response = json.loads(response_data.decode('utf-8'))
                
                return response.get('available_nodes', {})
                
        except Exception as e:
            print(f"❌ Node discovery failed: {e}")
            return {}

    def _connect_to_node(self, node_info: Dict):
        """Connect to another node"""
        target_ip = node_info['ip_address']
        target_port = node_info['port']
        target_node_id = node_info['node_id']
        connection_id = f"{target_ip}:{target_port}"
        
        if connection_id in self.connections:
            return True
            
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((target_ip, target_port))
            
            # Send handshake
            handshake = {
                'type': 'handshake',
                'node_info': {
                    'node_id': self.node_id,
                    'node_name': self.node_name,
                    'mac_address': self.mac_address,
                    'ip_address': self.host,
                    'port': self.port
                }
            }
            
            client_socket.send(json.dumps(handshake).encode('utf-8'))
            
            # Wait for response
            response_data = client_socket.recv(NetworkConfig.BUFFER_SIZE)
            response = json.loads(response_data.decode('utf-8'))
            
            if response['type'] == 'handshake_ack':
                self.connections[connection_id] = client_socket
                self.connected_nodes[connection_id] = response['node_info']
                
                # Start listening for messages from this connection
                thread = threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, (target_ip, target_port))
                )
                thread.daemon = True
                thread.start()
                
                print(f"🔗 Auto-connected to {node_info['node_name']} ({target_ip}:{target_port})")
                return True
                
        except Exception as e:
            print(f"❌ Auto-connect failed to {target_node_id}: {e}")
            
        return False

    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"🔄 New connection from {client_address}")
                
                thread = threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, client_address)
                )
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"❌ Connection acceptance error: {e}")

    def _handle_connection(self, client_socket: socket.socket, client_address: tuple):
        """Handle individual client connection"""
        connection_id = f"{client_address[0]}:{client_address[1]}"
        
        try:
            while self.running:
                data = client_socket.recv(NetworkConfig.BUFFER_SIZE)
                if not data:
                    break
                    
                message = json.loads(data.decode('utf-8'))
                self._process_message(message, client_socket, client_address)
                
        except Exception as e:
            print(f"❌ Connection error with {connection_id}: {e}")
        finally:
            client_socket.close()
            if connection_id in self.connections:
                del self.connections[connection_id]
                if connection_id in self.connected_nodes:
                    del self.connected_nodes[connection_id]
            print(f"🔌 Disconnected from {connection_id}")

    def _process_message(self, message: Dict, client_socket: socket.socket, client_address: tuple):
        """Process incoming messages"""
        msg_type = message.get('type')
        
        if msg_type == 'handshake':
            self._handle_handshake(message, client_socket, client_address)
        elif msg_type == 'file_transfer_start':
            self._handle_file_transfer_start(message, client_socket)
        elif msg_type == 'file_chunk':
            self._handle_file_chunk(message, client_socket)
        elif msg_type == 'ack':
            self._handle_ack(message)

    def _handle_handshake(self, message: Dict, client_socket: socket.socket, client_address: tuple):
        """Handle node handshake"""
        node_info = message['node_info']
        connection_id = f"{client_address[0]}:{client_address[1]}"
        
        self.connections[connection_id] = client_socket
        self.connected_nodes[connection_id] = node_info
        
        response = {
            'type': 'handshake_ack',
            'node_info': {
                'node_id': self.node_id,
                'node_name': self.node_name,
                'mac_address': self.mac_address,
                'ip_address': self.host,
                'port': self.port
            }
        }
        
        client_socket.send(json.dumps(response).encode('utf-8'))
        print(f"🤝 Handshake completed with {node_info['node_name']}")

    def send_file(self, file_path: str, target_connection_id: str) -> bool:
        """Send a file to another node using chunked transfer"""
        if target_connection_id not in self.connections:
            print(f"❌ No connection to {target_connection_id}")
            return False
            
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
            
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        transfer_id = str(uuid.uuid4())[:8]
        
        # Initialize transfer state
        with self.transfer_lock:
            self.active_transfers[transfer_id] = {
                'file_name': file_name,
                'file_size': file_size,
                'chunks_sent': 0,
                'chunks_acked': 0,
                'total_chunks': (file_size + NetworkConfig.CHUNK_SIZE - 1) // NetworkConfig.CHUNK_SIZE,
                'start_time': time.time(),
                'target_connection': target_connection_id
            }
        
        # Send transfer start message
        start_message = {
            'type': 'file_transfer_start',
            'transfer_id': transfer_id,
            'file_name': file_name,
            'file_size': file_size,
            'total_chunks': (file_size + NetworkConfig.CHUNK_SIZE - 1) // NetworkConfig.CHUNK_SIZE
        }
        
        try:
            self.connections[target_connection_id].send(
                json.dumps(start_message).encode('utf-8')
            )
            
            # Start sending chunks in a separate thread
            transfer_thread = threading.Thread(
                target=self._send_file_chunks,
                args=(file_path, transfer_id, target_connection_id)
            )
            transfer_thread.daemon = True
            transfer_thread.start()
            
            print(f"📤 Started file transfer: {file_name} -> {target_connection_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start file transfer: {e}")
            with self.transfer_lock:
                if transfer_id in self.active_transfers:
                    del self.active_transfers[transfer_id]
            return False

    def _send_file_chunks(self, file_path: str, transfer_id: str, target_connection_id: str):
        """Send file in 1KB chunks with ACK every 3 chunks"""
        try:
            with open(file_path, 'rb') as file:
                chunk_index = 0
                chunks_since_ack = 0
                
                while True:
                    chunk = file.read(NetworkConfig.CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    # Create chunk message
                    chunk_message = {
                        'type': 'file_chunk',
                        'transfer_id': transfer_id,
                        'chunk_index': chunk_index,
                        'chunk_data': chunk.hex(),
                        'is_last': len(chunk) < NetworkConfig.CHUNK_SIZE
                    }
                    
                    # Send chunk
                    self.connections[target_connection_id].send(
                        json.dumps(chunk_message).encode('utf-8')
                    )
                    
                    # Update transfer state
                    with self.transfer_lock:
                        if transfer_id in self.active_transfers:
                            self.active_transfers[transfer_id]['chunks_sent'] += 1
                    
                    chunk_index += 1
                    chunks_since_ack += 1
                    
                    # Wait for ACK every 3 chunks
                    if chunks_since_ack >= NetworkConfig.ACK_INTERVAL:
                        self._wait_for_ack(transfer_id, chunk_index)
                        chunks_since_ack = 0
                    
                    time.sleep(NetworkConfig.TRANSFER_DELAY)
                
                # Final ACK wait
                if chunks_since_ack > 0:
                    self._wait_for_ack(transfer_id, chunk_index)
                
                print(f"✅ File transfer {transfer_id} completed")
                
        except Exception as e:
            print(f"❌ Error during file transfer {transfer_id}: {e}")
        finally:
            with self.transfer_lock:
                if transfer_id in self.active_transfers:
                    del self.active_transfers[transfer_id]

    def _wait_for_ack(self, transfer_id: str, expected_chunk: int):
        """Wait for acknowledgment of chunks"""
        start_time = time.time()
        while time.time() - start_time < NetworkConfig.TIMEOUT:
            with self.transfer_lock:
                if transfer_id in self.active_transfers:
                    if self.active_transfers[transfer_id]['chunks_acked'] >= expected_chunk:
                        return
            time.sleep(0.1)
        
        print(f"⏰ Timeout waiting for ACK in transfer {transfer_id}")

    def _handle_file_transfer_start(self, message: Dict, client_socket: socket.socket):
        """Handle incoming file transfer start"""
        transfer_id = message['transfer_id']
        file_name = message['file_name']
        file_size = message['file_size']
        total_chunks = message['total_chunks']
        
        with self.transfer_lock:
            self.active_transfers[transfer_id] = {
                'file_name': file_name,
                'file_size': file_size,
                'chunks_received': 0,
                'total_chunks': total_chunks,
                'chunks': {},
                'start_time': time.time()
            }
        
        ack_message = {
            'type': 'ack',
            'transfer_id': transfer_id,
            'chunk_index': -1,
            'status': 'started'
        }
        
        client_socket.send(json.dumps(ack_message).encode('utf-8'))
        print(f"📥 Started receiving file: {file_name}")

    def _handle_file_chunk(self, message: Dict, client_socket: socket.socket):
        """Handle incoming file chunk"""
        transfer_id = message['transfer_id']
        chunk_index = message['chunk_index']
        chunk_data = bytes.fromhex(message['chunk_data'])
        is_last = message.get('is_last', False)
        
        with self.transfer_lock:
            if transfer_id not in self.active_transfers:
                return
                
            transfer = self.active_transfers[transfer_id]
            transfer['chunks'][chunk_index] = chunk_data
            transfer['chunks_received'] += 1
            
            if (transfer['chunks_received'] % NetworkConfig.ACK_INTERVAL == 0) or is_last:
                ack_message = {
                    'type': 'ack',
                    'transfer_id': transfer_id,
                    'chunk_index': chunk_index,
                    'status': 'received'
                }
                client_socket.send(json.dumps(ack_message).encode('utf-8'))
            
            if transfer['chunks_received'] >= transfer['total_chunks']:
                self._reassemble_file(transfer_id)
                
    def _handle_ack(self, message: Dict):
        """Handle acknowledgment message"""
        transfer_id = message['transfer_id']
        chunk_index = message['chunk_index']
        
        with self.transfer_lock:
            if transfer_id in self.active_transfers:
                self.active_transfers[transfer_id]['chunks_acked'] = chunk_index + 1

    def _reassemble_file(self, transfer_id: str):
        """Reassemble file from chunks and save to storage"""
        with self.transfer_lock:
            if transfer_id not in self.active_transfers:
                return
            transfer = self.active_transfers[transfer_id]
            
        try:
            output_path = f"{self.storage_path}/completed/{transfer['file_name']}"
            
            with open(output_path, 'wb') as output_file:
                for i in range(transfer['total_chunks']):
                    if i in transfer['chunks']:
                        output_file.write(transfer['chunks'][i])
                    else:
                        print(f"❌ Missing chunk {i} in transfer {transfer_id}")
                        return
            
            actual_size = os.path.getsize(output_path)
            if actual_size == transfer['file_size']:
                print(f"✅ File {transfer['file_name']} successfully received ({actual_size} bytes)")
            else:
                print(f"⚠️  File size mismatch: expected {transfer['file_size']}, got {actual_size}")
                
        except Exception as e:
            print(f"❌ Error reassembling file {transfer_id}: {e}")
        finally:
            with self.transfer_lock:
                if transfer_id in self.active_transfers:
                    del self.active_transfers[transfer_id]

    def get_status(self):
        """Get node status"""
        return {
            'node_name': self.node_name,
            'node_id': self.node_id,
            'address': f"{self.host}:{self.port}",
            'connected_nodes': len(self.connected_nodes),
            'discovered_nodes': len(self.discovered_nodes),
            'active_transfers': len(self.active_transfers),
            'storage': self.get_storage_info()
        }

    def get_storage_info(self) -> Dict:
        """Get storage information"""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.storage_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        return {
            'total_files': file_count,
            'total_size': total_size,
            'storage_path': self.storage_path
        }

    def list_connections(self):
        """List all connected nodes"""
        print(f"\n🔗 Connections for '{self.node_name}':")
        if not self.connected_nodes:
            print("   No active connections")
        for conn_id, node_info in self.connected_nodes.items():
            print(f"   📍 {node_info['node_name']} - {conn_id}")

    def stop(self):
        """Stop the node and clean up"""
        self.running = False
        self.auto_connect_running = False
        
        # Unregister from cloud
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((self.cloud_host, self.cloud_port))
                
                unregister_msg = {
                    'type': 'unregister',
                    'node_id': self.node_id
                }
                s.send(json.dumps(unregister_msg).encode('utf-8'))
        except:
            pass
        
        if self.server_socket:
            self.server_socket.close()
        
        for conn in self.connections.values():
            conn.close()
        
        self.connections.clear()
        self.connected_nodes.clear()
        print(f"🛑 Node '{self.node_name}' stopped")