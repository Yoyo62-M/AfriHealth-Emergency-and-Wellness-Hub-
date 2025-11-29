import os
import time
from .packet import Packet

class FileTransferProtocol:
    def __init__(self, node):
        self.node = node
        self.chunk_size = 1024  # 1KB chunks
        self.chunks_per_ack = 3  # Send ACK after every 3 chunks
        
    def send_file(self, target_node, file_path, chunk_size=1024):
        """Send file to target node in chunks with acknowledgment"""
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found")
            return False
            
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        print(f"Sending file {file_name} ({file_size} bytes) to {target_node.node_id}")
        
        try:
            with open(file_path, 'rb') as file:
                chunk_count = 0
                total_chunks_sent = 0
                
                while True:
                    chunk_data = b''
                    chunks_for_ack = []
                    
                    # Read chunks for acknowledgment cycle
                    for _ in range(self.chunks_per_ack):
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break
                        chunks_for_ack.append(chunk)
                    
                    if not chunks_for_ack:
                        break  # No more data to send
                    
                    # Send chunks
                    for i, chunk in enumerate(chunks_for_ack):
                        packet_data = {
                            'type': 'file_chunk',
                            'file_name': file_name,
                            'chunk_index': chunk_count + i,
                            'total_chunks': (file_size + chunk_size - 1) // chunk_size,
                            'data': chunk.hex()  # Convert to hex for simulation
                        }
                        
                        packet = Packet(
                            source_ip=self.node.ip_address,
                            destination_ip=target_node.ip_address,
                            data=packet_data
                        )
                        
                        # Simulate sending through network
                        self.node.network_interface.send_packet(packet)
                        total_chunks_sent += 1
                    
                    # Wait for acknowledgment
                    ack_received = self._wait_for_acknowledgment(target_node, file_name, chunk_count)
                    
                    if not ack_received:
                        print(f"Error: No acknowledgment received for chunks {chunk_count}-{chunk_count+len(chunks_for_ack)-1}")
                        return False
                    
                    chunk_count += len(chunks_for_ack)
                    print(f"Sent chunks {chunk_count-len(chunks_for_ack)}-{chunk_count-1}, waiting for ACK...")
                
                print(f"File transfer completed: {total_chunks_sent} chunks sent")
                return True
                
        except Exception as e:
            print(f"Error during file transfer: {e}")
            return False
    
    def _wait_for_acknowledgment(self, target_node, file_name, chunk_count):
        """Wait for acknowledgment from target node"""
        # Simulate network delay
        time.sleep(0.1)
        
        # In a real implementation, this would wait for an actual ACK packet
        # For simulation, we'll assume ACK is always received
        ack_packet = Packet(
            source_ip=target_node.ip_address,
            destination_ip=self.node.ip_address,
            data={
                'type': 'ack',
                'file_name': file_name,
                'chunk_count': chunk_count,
                'message': 'ACK received'
            },
            packet_type='ack'
        )
        
        print(f"Received ACK from {target_node.node_id} for chunks up to {chunk_count}")
        return True
    
    def get_storage_usage(self):
        """Get storage usage information"""
        try:
            total = self.node.storage_gb * 1024 * 1024 * 1024  # Convert to bytes
            used = 0
            
            if os.path.exists(self.node.storage_path):
                for dirpath, dirnames, filenames in os.walk(self.node.storage_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        used += os.path.getsize(filepath)
            
            free = total - used
            return total, used, free
            
        except Exception as e:
            print(f"Error getting storage usage: {e}")
            return 0, 0, 0