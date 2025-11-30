import grpc
import sys
import os
import threading
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from generated import calculator_pb2
from generated import calculator_pb2_grpc


class AdminMonitor:
    def __init__(self, host='localhost:50051', admin_key='admin123'):
        self.channel = grpc.insecure_channel(host)
        self.admin_stub = calculator_pb2_grpc.AdminServiceStub(self.channel)
        self.admin_key = admin_key
        self.monitoring = False
    
    def format_bytes(self, bytes_value):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def get_system_status(self):
        """Get current system status"""
        try:
            response = self.admin_stub.GetSystemStatus(
                calculator_pb2.SystemStatusRequest(admin_key=self.admin_key)
            )
            return response
        except grpc.RpcError as e:
            print(f"✗ Failed to get system status: [{e.code().name}] {e.details()}")
            return None
    
    def display_system_status(self):
        """Display detailed system status"""
        status = self.get_system_status()
        
        if not status:
            return
        
        print("\n" + "="*70)
        print("SYSTEM STATUS DASHBOARD")
        print("="*70)
        
        print("\n📊 STORAGE OVERVIEW:")
        print(f"  Total Capacity:     {self.format_bytes(status.global_capacity_bytes)}")
        print(f"  Allocated:          {self.format_bytes(status.global_allocated_bytes)} ({status.allocation_percentage:.2f}%)")
        print(f"  Actually Used:      {self.format_bytes(status.global_used_bytes)} ({status.usage_percentage:.2f}%)")
        print(f"  Available:          {self.format_bytes(status.global_available_bytes)}")
        
        # Storage allocation bar
        bar_length = 50
        alloc_filled = int(bar_length * status.allocation_percentage / 100)
        alloc_bar = '█' * alloc_filled + '░' * (bar_length - alloc_filled)
        print(f"\n  Allocation: [{alloc_bar}] {status.allocation_percentage:.2f}%")
        
        # Storage usage bar
        if status.global_allocated_bytes > 0:
            usage_filled = int(bar_length * status.usage_percentage / 100)
            usage_bar = '█' * usage_filled + '░' * (bar_length - usage_filled)
            print(f"  Usage:      [{usage_bar}] {status.usage_percentage:.2f}%")
        
        print("\n👥 USER STATISTICS:")
        print(f"  Active Users:       {status.total_users}")
        print(f"  Maximum Users:      {status.max_users}")
        print(f"  Available Slots:    {status.max_users - status.total_users}")
        
        print("="*70)
    
    def update_storage_capacity(self, new_capacity_gb):
        """Update global storage capacity"""
        try:
            response = self.admin_stub.UpdateGlobalStorage(
                calculator_pb2.UpdateStorageRequest(
                    admin_key=self.admin_key,
                    new_capacity_gb=new_capacity_gb
                )
            )
            
            print(f"\n✓ {response.message}")
            print(f"  Old Capacity: {self.format_bytes(response.old_capacity_bytes)}")
            print(f"  New Capacity: {self.format_bytes(response.new_capacity_bytes)}")
            return True
        except grpc.RpcError as e:
            print(f"✗ Failed to update storage: [{e.code().name}] {e.details()}")
            return False
    
    def start_event_monitoring(self):
        """Start monitoring system events in real-time"""
        self.monitoring = True
        
        def monitor():
            try:
                print("\n" + "="*70)
                print("REAL-TIME EVENT MONITOR")
                print("="*70)
                print("Listening for system events... (Press Ctrl+C to stop)\n")
                
                request = calculator_pb2.SystemEventsRequest(admin_key=self.admin_key)
                
                for event in self.admin_stub.StreamSystemEvents(request):
                    if not self.monitoring:
                        break
                    
                    # Color codes for different event types
                    color = {
                        'USER_ENROLLED': '🟢',
                        'USER_LOGIN': '🔵',
                        'STORAGE_UPDATED': '🟡',
                        'OPERATION_PERFORMED': '⚪'
                    }.get(event.event_type, '⚫')
                    
                    print(f"{color} [{event.timestamp}] {event.event_type}")
                    print(f"   {event.message}")
                    
                    if event.user_email:
                        print(f"   User: {event.user_email}")
                    
                    if event.storage_change != 0:
                        change_str = f"+{self.format_bytes(event.storage_change)}" if event.storage_change > 0 else f"{self.format_bytes(event.storage_change)}"
                        print(f"   Storage: {change_str}")
                    
                    print()
                    
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.CANCELLED:
                    print("\n✓ Monitoring stopped")
                else:
                    print(f"\n✗ Monitoring error: [{e.code().name}] {e.details()}")
            except Exception as e:
                print(f"\n✗ Error: {e}")
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def stop_event_monitoring(self):
        """Stop event monitoring"""
        self.monitoring = False
    
    def close(self):
        """Close the channel"""
        self.channel.close()


def admin_menu():
    """Interactive admin menu"""
    print("="*70)
    print("CloudGrpc Admin Monitor")
    print("="*70)
    
    admin_key = input("Enter admin key (default: admin123): ").strip() or "admin123"
    
    monitor = AdminMonitor(admin_key=admin_key)
    monitor_thread = None
    
    while True:
        print("\n" + "="*70)
        print("ADMIN MENU")
        print("="*70)
        print("1. View System Status")
        print("2. Update Storage Capacity")
        print("3. Start Real-Time Event Monitoring")
        print("4. Stop Event Monitoring")
        print("5. Refresh Display")
        print("6. Exit")
        print("="*70)
        
        choice = input("Select option (1-6): ").strip()
        
        if choice == '1':
            monitor.display_system_status()
        
        elif choice == '2':
            try:
                current_status = monitor.get_system_status()
                if current_status:
                    print(f"\nCurrent Capacity: {monitor.format_bytes(current_status.global_capacity_bytes)}")
                
                new_capacity = int(input("Enter new capacity in GB: ").strip())
                
                if new_capacity <= 0:
                    print("✗ Capacity must be positive!")
                    continue
                
                confirm = input(f"Confirm update to {new_capacity} GB? (yes/no): ").strip().lower()
                
                if confirm == 'yes':
                    monitor.update_storage_capacity(new_capacity)
                else:
                    print("✗ Update cancelled")
            
            except ValueError:
                print("✗ Invalid input! Please enter a number.")
        
        elif choice == '3':
            if monitor_thread and monitor_thread.is_alive():
                print("✗ Monitoring already active!")
            else:
                monitor_thread = monitor.start_event_monitoring()
                input("\nPress Enter to return to menu (monitoring continues in background)...\n")
        
        elif choice == '4':
            monitor.stop_event_monitoring()
            print("✓ Event monitoring stopped")
        
        elif choice == '5':
            monitor.display_system_status()
        
        elif choice == '6':
            print("\n✓ Shutting down admin monitor...")
            monitor.stop_event_monitoring()
            monitor.close()
            break
        
        else:
            print("✗ Invalid choice! Please select 1-6.")


if __name__ == '__main__':
    try:
        admin_menu()
    except KeyboardInterrupt:
        print("\n\n✓ Admin monitor terminated by user.")
        sys.exit(0)