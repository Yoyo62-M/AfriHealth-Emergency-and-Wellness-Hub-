import os
from .node import Node
from utils.address_generator import AddressGenerator

class NodeManager:
    def __init__(self):
        self.nodes = {}
        self.address_generator = AddressGenerator()
        
    def create_node(self, node_id, storage_gb, bandwidth_mbps, cpu_cores, storage_path=None):
        """Create a new node with specified parameters"""
        if node_id in self.nodes:
            print(f"Node {node_id} already exists!")
            return self.nodes[node_id]
            
        # Generate unique addresses
        ip_address = self.address_generator.generate_ip_address()
        mac_address = self.address_generator.generate_mac_address()
        
        # Create node
        node = Node(
            node_id=node_id,
            ip_address=ip_address,
            mac_address=mac_address,
            storage_gb=storage_gb,
            bandwidth_mbps=bandwidth_mbps,
            cpu_cores=cpu_cores,
            storage_path=storage_path
        )
        
        self.nodes[node_id] = node
        print(f"Created node {node_id}: IP={ip_address}, MAC={mac_address}")
        return node
    
    def connect_nodes(self, node1_id, node2_id):
        """Connect two nodes bidirectionally"""
        if node1_id not in self.nodes or node2_id not in self.nodes:
            print("Error: One or both nodes not found!")
            return False
            
        node1 = self.nodes[node1_id]
        node2 = self.nodes[node2_id]
        
        node1.connect_to_node(node2)
        node2.connect_to_node(node1)
        
        print(f"Connected {node1_id} <-> {node2_id}")
        return True
    
    def start_all_nodes(self):
        """Start all nodes"""
        for node in self.nodes.values():
            node.start()
    
    def stop_all_nodes(self):
        """Stop all nodes"""
        for node in self.nodes.values():
            node.stop()
    
    def get_node(self, node_id):
        """Get node by ID"""
        return self.nodes.get(node_id)
    
    def list_nodes(self):
        """List all nodes"""
        return list(self.nodes.keys())
    
    def remove_node(self, node_id):
        """Remove a node"""
        if node_id in self.nodes:
            self.nodes[node_id].stop()
            del self.nodes[node_id]
            print(f"Removed node {node_id}")