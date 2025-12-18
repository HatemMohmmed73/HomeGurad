import json
import time
import subprocess
import re
from pathlib import Path

# Configuration
OUTPUT_FILE = "data/active_devices.json"
WIFI_INTERFACE = "wlx3c6ad20d17fa"  # Your Wi-Fi adapter name

def get_arp_table():
    """Run ip neigh show and parse output"""
    devices = {}
    try:
        # Run ip neigh show
        result = subprocess.run(['ip', 'neigh', 'show'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 5:
                ip = parts[0]
                dev = parts[2]
                mac = parts[4]
                state = parts[-1]
                
                # Filter only devices on your Wi-Fi hotspot
                if dev == WIFI_INTERFACE and state in ['REACHABLE', 'STALE', 'DELAY', 'PROBE']:
                    devices[mac] = {
                        "ip": ip,
                        "mac": mac,
                        "status": "active" if state == 'REACHABLE' else "idle",
                        "interface": dev,
                        "last_seen": time.time()
                    }
                    print(f"Found: {ip} ({mac}) - {state}")
                    
    except Exception as e:
        print(f"Error running ip neigh: {e}")
        
    return devices

def main():
    print(f"Starting Network Monitor on interface: {WIFI_INTERFACE}")
    print(f"Saving to: {OUTPUT_FILE}")
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    while True:
        try:
            active_devices = get_arp_table()
            
            # Save to JSON file
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(active_devices, f, indent=2)
                
            # Wait 10 seconds
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

