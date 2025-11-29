import random
import uuid

class AddressGenerator:
    def __init__(self):
        self.used_ips = set()
        self.used_macs = set()
        
    def generate_ip_address(self):
        """Generate a unique IP address"""
        while True:
            ip = f"192.168.{random.randint(1, 254)}.{random.randint(2, 254)}"
            if ip not in self.used_ips:
                self.used_ips.add(ip)
                return ip
                
    def generate_mac_address(self):
        """Generate a unique MAC address"""
        while True:
            mac = "02:00:00:%02x:%02x:%02x" % (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
            if mac not in self.used_macs:
                self.used_macs.add(mac)
                return mac
                
    def generate_socket_address(self, node_id):
        """Generate a socket address"""
        return f"{node_id}:{random.randint(8000, 9000)}"