"""
Test script to identify panels by sending their IP address to each panel
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
            print(f"Error getting panels: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return []

def test_panel_identification():
    """Test panel identification by sending IP address to each panel"""
    print("PANEL IDENTIFICATION TEST")
    print("=" * 50)
    
    # Get panels from API
    panels = get_panels_from_api()
    if not panels:
        print("No panels found or API not accessible")
        return False
    
    print(f"Found {len(panels)} panels:")
    for panel in panels:
        print(f"  - {panel['name']} ({panel['ip_address']}) - {panel['status']}")
    
    # Initialize panel communication service
    panel_service = PanelCommunicationService()
    
    print(f"\nSending identification messages to {len(panels)} panels...")
    print("-" * 50)
    
    success_count = 0
    failed_panels = []
    
    for panel in panels:
        panel_ip = panel['ip_address']
        panel_name = panel['name']
        
        print(f"\nTesting panel: {panel_name} ({panel_ip})")
        
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
                print(f"  Successfully sent: '{identification_text}'")
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
                    print(f"  Sent timestamp: {timestamp}")
                else:
                    print(f"  Failed to send timestamp")
                    
            else:
                print(f"  Failed to send identification message: {result.get('message')}")
                failed_panels.append(panel_ip)
                
        except Exception as e:
            print(f"  Error sending message: {e}")
            failed_panels.append(panel_ip)
        
        # Small delay between panels
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Total panels: {len(panels)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_panels)}")
    
    if failed_panels:
        print(f"\nFailed panels:")
        for ip in failed_panels:
            print(f"  - {ip}")
    
    if success_count > 0:
        print(f"\n{success_count} panels responded correctly!")
        print("Check the panels to see the IP addresses displayed.")
    
    return success_count > 0

if __name__ == "__main__":
    test_panel_identification() 