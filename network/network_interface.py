import threading
import time
import socket
import json
from .packet import Packet
from .protocol import FileTransferProtocol

class NetworkInterface:
    def __init__(self):
        self.running = False
        self.packet_queue = []
        self.thread = None
        self.sockets = {}
        
    def initialize(self):
        """Initialize network interface"""
        print("Network Interface initialized")
        
    def start(self):
        """Start network interface"""
        self.running = True
        self.thread = threading.Thread(target=self._process_packets)
        self.thread.daemon = True
        self.thread.start()
        print("Network Interface started")
        
    def stop(self):
        """Stop network interface"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Network Interface stopped")
        
    def _process_packets(self):
        """Process packets in the queue"""
        while self.running:
            if self.packet_queue:
                packet = self.packet_queue.pop(0)
                self._deliver_packet(packet)
            time.sleep(0.01)  # Small delay to prevent CPU overuse
            
    def _deliver_packet(self, packet):
        """Deliver packet to destination"""
        # Simulate network latency
        time.sleep(0.001 * packet.size / 1024)  # Simulate transfer time
        
        # In a real implementation, this would use actual sockets
        print(f"Network: Delivered packet from {packet.source_ip} to {packet.destination_ip}")
        
    def send_packet(self, packet):
        """Send a packet through the network"""
        self.packet_queue.append(packet)
        
    def create_socket(self, node_id, port):
        """Create a virtual socket for a node"""
        socket_id = f"{node_id}:{port}"
        self.sockets[socket_id] = {
            'node_id': node_id,
            'port': port,
            'bound': True
        }
        return socket_id