import os
import hashlib

class FileHandler:
    @staticmethod
    def split_file(file_path, chunk_size=1024):
        """Split file into chunks"""
        chunks = []
        file_name = os.path.basename(file_path)
        
        try:
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    
            return chunks, file_name
        except Exception as e:
            print(f"Error splitting file: {e}")
            return [], file_name
    
    @staticmethod
    def combine_chunks(chunks, output_path):
        """Combine chunks into a file"""
        try:
            with open(output_path, 'wb') as file:
                for chunk in chunks:
                    file.write(chunk)
            return True
        except Exception as e:
            print(f"Error combining chunks: {e}")
            return False
    
    @staticmethod
    def calculate_file_hash(file_path):
        """Calculate MD5 hash of a file"""
        try:
            with open(file_path, 'rb') as file:
                file_hash = hashlib.md5()
                while chunk := file.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return None