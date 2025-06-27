"""
Test script to identify panels by sending their IP address to each panel
This will help verify that the panel communication is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import requests
import time
from datetime import datetime
from panel_communication import PanelManager, PanelConfig, init_panels_from_config

# Configuration
API_BASE_URL = "http://localhost:6001"

def get_panels_from_api():
    """Get all panels from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/panels", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error getting panels: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return []

def test_panel_identification():
    """Test panel identification by sending IP address to each panel"""
    print("🔍 PANEL IDENTIFICATION TEST")
    print("=" * 50)
    
    # Get panels from API
    panels = get_panels_from_api()
    if not panels:
        print("❌ No panels found or API not accessible")
        return False
    
    print(f"📺 Found {len(panels)} panels:")
    for panel in panels:
        print(f"  - {panel['name']} ({panel['ip_address']}) - {panel['status']}")
    
    # Initialize panel manager with panel configurations
    panel_configs = []
    for panel in panels:
        config = {
            'ip': panel['ip_address'],
            'port': 5000,  # Default CP5200 port
            'panel_id': panel['id'],
            'timeout': 5.0,
            'retry_attempts': 3,
            'retry_delay': 1.0
        }
        panel_configs.append(config)
    
    # Initialize panel manager
    manager = init_panels_from_config(panel_configs)
    
    print(f"\n🚀 Sending identification messages to {len(panels)} panels...")
    print("-" * 50)
    
    success_count = 0
    failed_panels = []
    
    for panel in panels:
        panel_ip = panel['ip_address']
        panel_name = panel['name']
        
        print(f"\n📺 Testing panel: {panel_name} ({panel_ip})")
        
        # Get panel connection
        panel_conn = manager.get_panel(panel_ip)
        if not panel_conn:
            print(f"  ❌ Panel connection not found")
            failed_panels.append(panel_ip)
            continue
        
        # Send identification message
        identification_text = f"PANEL: {panel_ip}"
        try:
            success = panel_conn.send_text(identification_text, line=1, position=0)
            if success:
                print(f"  ✅ Successfully sent: '{identification_text}'")
                success_count += 1
                
                # Also send a timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                time_success = panel_conn.send_clock(f"TEST: {timestamp}")
                if time_success:
                    print(f"  ✅ Sent timestamp: {timestamp}")
                else:
                    print(f"  ⚠️  Failed to send timestamp")
                    
            else:
                print(f"  ❌ Failed to send identification message")
                failed_panels.append(panel_ip)
                
        except Exception as e:
            print(f"  ❌ Error sending message: {e}")
            failed_panels.append(panel_ip)
        
        # Small delay between panels
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total panels: {len(panels)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_panels)}")
    
    if failed_panels:
        print(f"\n❌ Failed panels:")
        for ip in failed_panels:
            print(f"  - {ip}")
    
    if success_count > 0:
        print(f"\n✅ {success_count} panels responded correctly!")
        print("Check the panels to see the IP addresses displayed.")
    
    # Get panel status
    print(f"\n📺 Current panel status:")
    all_status = manager.get_all_status()
    for status in all_status:
        online_status = "🟢 ONLINE" if status['online'] else "🔴 OFFLINE"
        print(f"  - {status['ip']}: {online_status}")
    
    return success_count > 0

def test_specific_panel(panel_ip):
    """Test a specific panel by IP"""
    print(f"🔍 Testing specific panel: {panel_ip}")
    
    config = PanelConfig(
        ip=panel_ip,
        port=5000,
        panel_id=1,
        timeout=5.0,
        retry_attempts=3,
        retry_delay=1.0
    )
    
    from panel_communication import PanelConnection
    panel = PanelConnection(config)
    
    # Try to connect
    if panel.connect():
        print(f"  ✅ Connected to panel {panel_ip}")
        
        # Send test message
        test_message = f"TEST: {panel_ip}"
        if panel.send_text(test_message, line=1, position=0):
            print(f"  ✅ Sent test message: '{test_message}'")
            
            # Send timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            if panel.send_clock(f"TIME: {timestamp}"):
                print(f"  ✅ Sent timestamp: {timestamp}")
            
            return True
        else:
            print(f"  ❌ Failed to send test message")
            return False
    else:
        print(f"  ❌ Failed to connect to panel {panel_ip}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test panel identification")
    parser.add_argument("--panel-ip", help="Test specific panel by IP")
    
    args = parser.parse_args()
    
    if args.panel_ip:
        # Test specific panel
        test_specific_panel(args.panel_ip)
    else:
        # Test all panels
        test_panel_identification() 