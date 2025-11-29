from main import CloudSimulation

def demo_simulation():
    # Initialize simulation
    sim = CloudSimulation()
    sim.initialize_simulation()
    
    # Create nodes
    sim.auto_create_nodes(5)
    
    # Create custom node with specific resources
    sim.create_node(
        node_id="high_perf_node",
        storage_gb=50,
        bandwidth_mbps=1000,
        cpu_cores=8
    )
    
    # Connect nodes
    sim.connect_nodes("node_1", "node_2")
    sim.connect_nodes("node_2", "node_3")
    sim.connect_nodes("high_perf_node", "node_1")
    
    # Start simulation
    sim.start_simulation()
    
    # Example file transfer (you would need to create a test file)
    node1 = sim.node_manager.get_node("node_1")
    node2 = sim.node_manager.get_node("node_2")
    
    if node1 and node2:
        # This would require an actual file to transfer
        print("Simulation ready for file transfers")
    
    return sim

if __name__ == "__main__":
    simulation = demo_simulation()
    
    try:
        # Keep simulation running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        simulation.stop_simulation()