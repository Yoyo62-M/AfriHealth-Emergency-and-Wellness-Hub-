import os
import shutil

class StorageManager:
    def __init__(self):
        self.virtual_drives = {}
        
    def create_virtual_drive(self, drive_id, size_gb, path=None):
        """Create a virtual storage drive"""
        drive_path = path or f"storage/virtual_drives/{drive_id}"
        
        try:
            os.makedirs(drive_path, exist_ok=True)
            self.virtual_drives[drive_id] = {
                'path': drive_path,
                'size_gb': size_gb,
                'used_gb': 0,
                'free_gb': size_gb
            }
            print(f"Created virtual drive {drive_id} at {drive_path} ({size_gb}GB)")
            return True
        except Exception as e:
            print(f"Error creating virtual drive: {e}")
            return False
    
    def get_drive_info(self, drive_id):
        """Get information about a virtual drive"""
        if drive_id not in self.virtual_drives:
            return None
            
        drive_info = self.virtual_drives[drive_id]
        drive_path = drive_info['path']
        
        # Calculate actual usage
        total_size = drive_info['size_gb'] * 1024 * 1024 * 1024
        used_size = 0
        
        if os.path.exists(drive_path):
            for dirpath, dirnames, filenames in os.walk(drive_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    used_size += os.path.getsize(filepath)
        
        used_gb = used_size / (1024 * 1024 * 1024)
        free_gb = drive_info['size_gb'] - used_gb
        
        return {
            'drive_id': drive_id,
            'path': drive_path,
            'total_gb': drive_info['size_gb'],
            'used_gb': round(used_gb, 2),
            'free_gb': round(free_gb, 2)
        }
    
    def cleanup(self):
        """Clean up all virtual drives"""
        for drive_id, drive_info in self.virtual_drives.items():
            try:
                if os.path.exists(drive_info['path']):
                    shutil.rmtree(drive_info['path'])
                    print(f"Cleaned up virtual drive {drive_id}")
            except Exception as e:
                print(f"Error cleaning up drive {drive_id}: {e}")