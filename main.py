import asyncio
import json
import os
import threading
from nodes.node_manager import NodeManager
from network.network_interface import NetworkInterface
from storage.virtual_storage import StorageManager
from utils.address_generator import AddressGenerator

class CloudSimulation:
    def __init__(self):
        self.node_manager = NodeManager()
        self.network_interface = NetworkInterface()
        self.storage_manager = StorageManager()
        self.address_generator = AddressGenerator()
        self.running = False
        
    def initialize_simulation(self):
        """Initialize the simulation environment"""
        print("Initializing Cloud Simulation...")
        
        # Create base directories
        os.makedirs("storage/virtual_drives", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Initialize network
        self.network_interface.initialize()
        
        print("Simulation initialized successfully!")
        
    def create_node(self, node_id, storage_gb, bandwidth_mbps, cpu_cores, storage_path=None):
        """Manually create a new node"""
        return self.node_manager.create_node(
            node_id=node_id,
            storage_gb=storage_gb,
            bandwidth_mbps=bandwidth_mbps,
            cpu_cores=cpu_cores,
            storage_path=storage_path
        )
    
    def auto_create_nodes(self, count=5):
        """Automatically create minimum required nodes"""
        for i in range(count):
            node_id = f"node_{i+1}"
            self.create_node(
                node_id=node_id,
                storage_gb=10,  # 10GB default
                bandwidth_mbps=100,  # 100Mbps default
                cpu_cores=2  # 2 cores default
            )
    
    def connect_nodes(self, node1_id, node2_id):
        """Connect two nodes"""
        return self.node_manager.connect_nodes(node1_id, node2_id)
    
    def start_simulation(self):
        """Start the simulation"""
        self.running = True
        print("Starting Cloud Simulation...")
        
        # Start network interface
        network_thread = threading.Thread(target=self.network_interface.start)
        network_thread.daemon = True
        network_thread.start()
        
        # Start all nodes
        self.node_manager.start_all_nodes()
        
        print("Simulation started! Press Ctrl+C to stop.")
        
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        self.node_manager.stop_all_nodes()
        self.network_interface.stop()
        print("Simulation stopped.")

def main():
    simulation = CloudSimulation()
    simulation.initialize_simulation()
    
    # Auto-create minimum 5 nodes
    simulation.auto_create_nodes(5)
    
    # Example manual node creation
    simulation.create_node(
        node_id="custom_node_1",
        storage_gb=20,
        bandwidth_mbps=500,
        cpu_cores=4
    )
    
    # Connect some nodes
    simulation.connect_nodes("node_1", "node_2")
    simulation.connect_nodes("node_2", "node_3")
    
    try:
        simulation.start_simulation()
        
        # Keep main thread alive
        while simulation.running:
            asyncio.sleep(1)
            
    except KeyboardInterrupt:
        simulation.stop_simulation()

if __name__ == "__main__":
    main()