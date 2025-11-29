import socket
import threading
import time
import json
import os
import uuid
import hashlib
from datetime import datetime

class RealNode:
    def __init__(self, node_id, host='localhost', port=8000, storage_path=None):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.storage_path = storage_path or f"node_storage/{node_id}"
        self.connected_nodes = {}  # node_id -> (host, port)
        self.file_transfers = {}
        self.running = False
        self.server_socket = None
        self.server_thread = None
        
        # Create storage directory
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Generate unique MAC address for this node
        self.mac_address = self._generate_mac_address()
        
    def _generate_mac_address(self):
        """Generate a unique MAC address based on node ID"""
        return f"02:00:00:{uuid.uuid4().hex[:6]:02x}"

    def start_server(self):
        """Start the node's server to listen for incoming connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"🟢 Node {self.node_id} started on {self.host}:{self.port}")
            print(f"   MAC: {self.mac_address}")
            print(f"   Storage: {self.storage_path}")
            
            # Start listening for connections
            self.server_thread = threading.Thread(target=self._listen_for_connections)
            self.server_thread.daemon = True
            self.server_thread.start()
            
        except Exception as e:
            print(f"❌ Failed to start node {self.node_id}: {e}")
            return False
        return True

    def _listen_for_connections(self):
        """Listen for incoming connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"🔗 Incoming connection from {address}")
                
                # Handle each connection in a separate thread
                client_thread = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"❌ Error accepting connection: {e}")

    def _handle_client_connection(self, client_socket, address):
        """Handle incoming client connections and messages"""
        try:
            while self.running:
                # Receive message
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Parse message
                try:
                    message = json.loads(data.decode('utf-8'))
                    self._process_message(message, client_socket, address)
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON received from {address}")
                    
        except Exception as e:
            print(f"❌ Error handling client {address}: {e}")
        finally:
            client_socket.close()

    def _process_message(self, message, client_socket, address):
        """Process incoming messages"""
        msg_type = message.get('type')
        
        if msg_type == 'connect_request':
            self._handle_connect_request(message, client_socket)
        elif msg_type == 'file_chunk':
            self._handle_file_chunk(message, client_socket)
        elif msg_type == 'ack':
            self._handle_ack(message)
        elif msg_type == 'ping':
            self._handle_ping(client_socket)
        else:
            print(f"❌ Unknown message type: {msg_type}")

    def _handle_connect_request(self, message, client_socket):
        """Handle connection request from another node"""
        node_id = message['node_id']
        host = message['host']
        port = message['port']
        
        # Add to connected nodes
        self.connected_nodes[node_id] = (host, port)
        
        # Send acknowledgment
        response = {
            'type': 'connect_ack',
            'node_id': self.node_id,
            'status': 'connected'
        }
        client_socket.send(json.dumps(response).encode('utf-8'))
        
        print(f"🔗 Connected to node {node_id} at {host}:{port}")

    def _handle_file_chunk(self, message, client_socket):
        """Handle incoming file chunks"""
        file_name = message['file_name']
        chunk_index = message['chunk_index']
        total_chunks = message['total_chunks']
        chunk_data = message['data']
        transfer_id = message['transfer_id']
        
        print(f"📥 Receiving chunk {chunk_index + 1}/{total_chunks} of {file_name}")
        
        # Initialize transfer if first chunk
        if transfer_id not in self.file_transfers:
            self.file_transfers[transfer_id] = {
                'file_name': file_name,
                'total_chunks': total_chunks,
                'received_chunks': [None] * total_chunks,
                'start_time': datetime.now()
            }
        
        # Store chunk
        transfer = self.file_transfers[transfer_id]
        transfer['received_chunks'][chunk_index] = chunk_data
        
        # Check if all chunks received
        received_count = sum(1 for chunk in transfer['received_chunks'] if chunk is not None)
        
        # Send ACK every 3 chunks or when complete
        if (chunk_index + 1) % 3 == 0 or received_count == total_chunks:
            ack_message = {
                'type': 'ack',
                'transfer_id': transfer_id,
                'last_chunk_received': chunk_index,
                'total_received': received_count,
                'status': 'success'
            }
            client_socket.send(json.dumps(ack_message).encode('utf-8'))
            print(f"✅ Sent ACK for chunks up to {chunk_index + 1}")
        
        # If transfer complete, save file
        if received_count == total_chunks:
            self._save_complete_file(transfer_id)
            print(f"🎉 File {file_name} received completely!")

    def _save_complete_file(self, transfer_id):
        """Save completed file to storage"""
        transfer = self.file_transfers[transfer_id]
        file_path = os.path.join(self.storage_path, transfer['file_name'])
        
        try:
            with open(file_path, 'wb') as f:
                for chunk_data in transfer['received_chunks']:
                    if chunk_data:
                        f.write(bytes.fromhex(chunk_data))
            
            file_size = os.path.getsize(file_path)
            transfer_time = (datetime.now() - transfer['start_time']).total_seconds()
            
            print(f"💾 File saved: {file_path} ({file_size} bytes)")
            print(f"⏱️  Transfer time: {transfer_time:.2f} seconds")
            
            # Clean up transfer
            del self.file_transfers[transfer_id]
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")

    def _handle_ack(self, message):
        """Handle acknowledgment messages"""
        transfer_id = message['transfer_id']
        last_chunk = message['last_chunk_received']
        print(f"✅ Received ACK for transfer {transfer_id}, last chunk: {last_chunk + 1}")

    def _handle_ping(self, client_socket):
        """Handle ping requests"""
        response = {
            'type': 'pong',
            'node_id': self.node_id,
            'timestamp': datetime.now().isoformat()
        }
        client_socket.send(json.dumps(response).encode('utf-8'))

    def connect_to_node(self, node_id, host, port):
        """Connect to another node"""
        try:
            # Create connection socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            
            # Send connection request
            connect_message = {
                'type': 'connect_request',
                'node_id': self.node_id,
                'host': self.host,
                'port': self.port
            }
            sock.send(json.dumps(connect_message).encode('utf-8'))
            
            # Wait for acknowledgment
            response_data = sock.recv(1024)
            response = json.loads(response_data.decode('utf-8'))
            
            if response.get('status') == 'connected':
                self.connected_nodes[node_id] = (host, port)
                print(f"🔗 Successfully connected to {node_id} at {host}:{port}")
                return True
            else:
                print(f"❌ Failed to connect to {node_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error connecting to {node_id}: {e}")
            return False

    def send_file(self, target_node_id, file_path, chunk_size=1024):
        """Send file to another node in chunks with acknowledgment"""
        if target_node_id not in self.connected_nodes:
            print(f"❌ Not connected to node {target_node_id}")
            return False
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        target_host, target_port = self.connected_nodes[target_node_id]
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        transfer_id = str(uuid.uuid4())
        
        print(f"\n=== Starting File Transfer ===")
        print(f"From: {self.node_id}")
        print(f"To: {target_node_id}")
        print(f"File: {file_name} ({file_size} bytes)")
        print(f"Chunks: {total_chunks} of {chunk_size} bytes each")
        print(f"ACK every: 3 chunks")
        
        try:
            with open(file_path, 'rb') as file:
                chunk_count = 0
                chunks_sent = 0
                
                while chunk_count < total_chunks:
                    # Connect to target node for this batch
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((target_host, target_port))
                    
                    # Send chunks in batches of 3
                    for i in range(3):
                        if chunk_count >= total_chunks:
                            break
                        
                        # Read chunk
                        chunk_data = file.read(chunk_size)
                        if not chunk_data:
                            break
                        
                        # Prepare chunk message
                        chunk_message = {
                            'type': 'file_chunk',
                            'transfer_id': transfer_id,
                            'file_name': file_name,
                            'chunk_index': chunk_count,
                            'total_chunks': total_chunks,
                            'data': chunk_data.hex(),
                            'source_node': self.node_id
                        }
                        
                        # Send chunk
                        sock.send(json.dumps(chunk_message).encode('utf-8'))
                        chunks_sent += 1
                        print(f"📤 Sent chunk {chunk_count + 1}/{total_chunks}")
                        chunk_count += 1
                    
                    # Wait for ACK
                    try:
                        ack_data = sock.recv(1024)
                        if ack_data:
                            ack_message = json.loads(ack_data.decode('utf-8'))
                            if ack_message.get('type') == 'ack':
                                print(f"✅ Received ACK for chunks up to {ack_message['last_chunk_received'] + 1}")
                    except socket.timeout:
                        print("❌ ACK timeout")
                        return False
                    finally:
                        sock.close()
                    
                    # Small delay between batches
                    time.sleep(0.1)
                
                print(f"\n🎉 File transfer completed!")
                print(f"Total chunks sent: {chunks_sent}")
                return True
                
        except Exception as e:
            print(f"❌ Error during file transfer: {e}")
            return False

    def create_test_file(self, file_name="test_file.txt", size_kb=10):
        """Create a test file for transfer demonstrations"""
        file_path = os.path.join(self.storage_path, file_name)
        try:
            with open(file_path, 'w') as f:
                content = f"Test file created by {self.node_id} at {datetime.now()}. "
                content *= (size_kb * 100)  # Generate enough content
                f.write(content[:size_kb * 1024])  # Trim to exact size
            
            file_size = os.path.getsize(file_path)
            print(f"📄 Created test file: {file_path} ({file_size} bytes)")
            return file_path
        except Exception as e:
            print(f"❌ Error creating test file: {e}")
            return None

    def get_node_info(self):
        """Get node information"""
        return {
            'node_id': self.node_id,
            'host': self.host,
            'port': self.port,
            'mac_address': self.mac_address,
            'storage_path': self.storage_path,
            'connected_nodes': list(self.connected_nodes.keys()),
            'status': 'running' if self.running else 'stopped'
        }

    def stop(self):
        """Stop the node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print(f"🔴 Node {self.node_id} stopped")

def create_and_start_node(node_id, port, storage_path=None):
    """Helper function to create and start a node"""
    node = RealNode(node_id, port=port, storage_path=storage_path)
    if node.start_server():
        return node
    else:
        print(f"❌ Failed to create node {node_id}")
        return None

def demo_multiple_nodes():
    """Demonstrate multiple nodes communicating"""
    print("🚀 Creating real nodes with actual network communication...")
    
    # Create nodes on different ports
    nodes = {}
    
    # Node 1
    node1 = create_and_start_node("node_1", port=8001)
    if node1:
        nodes["node_1"] = node1
    
    # Node 2  
    node2 = create_and_start_node("node_2", port=8002)
    if node2:
        nodes["node_2"] = node2
    
    # Node 3
    node3 = create_and_start_node("node_3", port=8003)
    if node3:
        nodes["node_3"] = node3
    
    time.sleep(2)  # Wait for servers to start
    
    # Connect nodes
    print("\n🔗 Connecting nodes...")
    if "node_1" in nodes and "node_2" in nodes:
        nodes["node_1"].connect_to_node("node_2", "localhost", 8002)
    
    if "node_2" in nodes and "node_3" in nodes:
        nodes["node_2"].connect_to_node("node_3", "localhost", 8003)
    
    # Create test file and transfer
    time.sleep(1)
    if "node_1" in nodes:
        test_file = nodes["node_1"].create_test_file("demo_file.txt", 5)
        if test_file and "node_2" in nodes:
            print("\n📤 Starting file transfer...")
            nodes["node_1"].send_file("node_2", test_file)
    
    return nodes

if __name__ == "__main__":
    # Demo with multiple nodes
    nodes = demo_multiple_nodes()
    
    try:
        print("\n🏃 Nodes are running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all nodes...")
        for node_id, node in nodes.items():
            node.stop()