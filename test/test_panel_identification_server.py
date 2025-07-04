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
from panel_communication_service import PanelCommunicationService

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
    
    # Initialize panel communication service
    panel_service = PanelCommunicationService()
    
    print(f"\n🚀 Sending identification messages to {len(panels)} panels...")
    print("-" * 50)
    
    success_count = 0
    failed_panels = []
    
    for panel in panels:
        panel_ip = panel['ip_address']
        panel_name = panel['name']
        
        print(f"\n📺 Testing panel: {panel_name} ({panel_ip})")
        
        # Send identification message
        identification_text = f"PANEL: {panel_ip}"
        try:
            result = panel_service.send_custom_text(
                panel_ip=panel_ip,
                text=identification_text,
                color=2,  # Verde
                font_size=2,  # 16px
                effect=2  # Fijo
            )
            
            if result.get('success'):
                print(f"  ✅ Successfully sent: '{identification_text}'")
                success_count += 1
                
                # Also send a timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                time_result = panel_service.send_custom_text(
                    panel_ip=panel_ip,
                    text=f"TEST: {timestamp}",
                    color=1,  # Rojo
                    font_size=1,  # 12px
                    effect=2  # Fijo
                )
                if time_result.get('success'):
                    print(f"  ✅ Sent timestamp: {timestamp}")
                else:
                    print(f"  ⚠️  Failed to send timestamp")
                    
            else:
                print(f"  ❌ Failed to send identification message: {result.get('message')}")
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
    
    return success_count > 0

def test_specific_panel(panel_ip):
    """Test a specific panel by IP"""
    print(f"🔍 Testing specific panel: {panel_ip}")
    
    panel_service = PanelCommunicationService()
    
    # Send test message
    test_message = f"TEST: {panel_ip}"
    result = panel_service.send_custom_text(
        panel_ip=panel_ip,
        text=test_message,
        color=2,  # Verde
        font_size=2,  # 16px
        effect=2  # Fijo
    )
    
    if result.get('success'):
        print(f"  ✅ Sent test message: '{test_message}'")
        
        # Send timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        time_result = panel_service.send_custom_text(
            panel_ip=panel_ip,
            text=f"TIME: {timestamp}",
            color=1,  # Rojo
            font_size=1,  # 12px
            effect=2  # Fijo
        )
        if time_result.get('success'):
            print(f"  ✅ Sent timestamp: {timestamp}")
        
        return True
    else:
        print(f"  ❌ Failed to send test message: {result.get('message')}")
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