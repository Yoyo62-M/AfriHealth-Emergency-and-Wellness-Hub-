import os
import threading
import asyncio
import uuid
from datetime import datetime
from network.protocol import FileTransferProtocol

class Node:
    def __init__(self, node_id, ip_address, mac_address, storage_gb, bandwidth_mbps, cpu_cores, storage_path=None):
        self.node_id = node_id
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.storage_gb = storage_gb
        self.bandwidth_mbps = bandwidth_mbps
        self.cpu_cores = cpu_cores
        self.storage_path = storage_path or f"storage/virtual_drives/{node_id}"
        self.connected_nodes = {}
        self.running = False
        self.file_transfer_protocol = FileTransferProtocol(self)
        self.socket_port = 8000  # Default port
        
        # Create storage directory
        os.makedirs(self.storage_path, exist_ok=True)
        
    def start(self):
        """Start the node"""
        self.running = True
        print(f"Node {self.node_id} started at {self.ip_address}:{self.socket_port}")
        
    def stop(self):
        """Stop the node"""
        self.running = False
        print(f"Node {self.node_id} stopped")
        
    def connect_to_node(self, target_node):
        """Connect to another node"""
        if target_node.node_id not in self.connected_nodes:
            self.connected_nodes[target_node.node_id] = target_node
            print(f"Node {self.node_id} connected to {target_node.node_id}")
            
    def send_file(self, target_node_id, file_path, chunk_size=1024):
        """Send file to another node in chunks with acknowledgment"""
        if target_node_id not in self.connected_nodes:
            print(f"Error: Not connected to node {target_node_id}")
            return False
            
        target_node = self.connected_nodes[target_node_id]
        return self.file_transfer_protocol.send_file(target_node, file_path, chunk_size)
    
    def receive_file(self, source_node_id, file_data, file_name):
        """Receive file from another node"""
        file_path = os.path.join(self.storage_path, file_name)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)
            print(f"Node {self.node_id} received file {file_name} from {source_node_id}")
            return True
        except Exception as e:
            print(f"Error receiving file: {e}")
            return False
    
    def get_storage_info(self):
        """Get storage information"""
        total, used, free = self.file_transfer_protocol.get_storage_usage()
        return {
            'total_gb': self.storage_gb,
            'used_gb': used,
            'free_gb': free,
            'path': self.storage_path
        }
    
    def get_node_info(self):
        """Get node information"""
        return {
            'node_id': self.node_id,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'storage_gb': self.storage_gb,
            'bandwidth_mbps': self.bandwidth_mbps,
            'cpu_cores': self.cpu_cores,
            'connected_nodes': list(self.connected_nodes.keys()),
            'socket_port': self.socket_port
        }