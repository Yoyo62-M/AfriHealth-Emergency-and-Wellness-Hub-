import uuid
from datetime import datetime

class Packet:
    def __init__(self, source_ip, destination_ip, data, packet_type="data"):
        self.packet_id = str(uuid.uuid4())
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.data = data
        self.packet_type = packet_type  # data, ack, control
        self.timestamp = datetime.now()
        self.size = len(str(data))
        
    def to_dict(self):
        return {
            'packet_id': self.packet_id,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'data': self.data,
            'packet_type': self.packet_type,
            'timestamp': self.timestamp.isoformat(),
            'size': self.size
        }