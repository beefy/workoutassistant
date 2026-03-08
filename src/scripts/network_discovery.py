#!/usr/bin/env python3
"""
Network discovery script for Raspberry Pi cluster.
Run this on each Pi to get network information and discover other Pis.
"""

import socket
import subprocess
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import ipaddress


def get_local_ip():
    """Get the local IP address of this Pi."""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def get_hostname():
    """Get the hostname of this Pi."""
    return socket.gethostname()


def get_network_range():
    """Get the network range (subnet) this Pi is on."""
    try:
        local_ip = get_local_ip()
        # Assume /24 subnet (most common for home networks)
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        return str(network)
    except Exception:
        return None


def scan_for_apis(network_range=None):
    """Scan the network for other FastAPI health endpoints."""
    if not network_range:
        network_range = get_network_range()
    
    if not network_range:
        print("Could not determine network range")
        return []
    
    print(f"Scanning network {network_range} for FastAPI servers...")
    
    network = ipaddress.IPv4Network(network_range)
    found_apis = []
    
    def check_host(ip):
        """Check if a host has our FastAPI server running."""
        try:
            response = requests.get(f"http://{ip}:8000/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return {
                    "ip": str(ip),
                    "hostname": data.get("hostname", "unknown"),
                    "status": data.get("status", "unknown"),
                    "service": data.get("service", "unknown")
                }
        except Exception:
            pass
        return None
    
    # Scan network in parallel (much faster)
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(check_host, network.hosts()))
    
    found_apis = [result for result in results if result is not None]
    return found_apis


def print_network_info():
    """Print comprehensive network information."""
    local_ip = get_local_ip()
    hostname = get_hostname()
    network_range = get_network_range()
    
    print("=" * 50)
    print("RASPBERRY PI NETWORK INFORMATION")
    print("=" * 50)
    print(f"Hostname: {hostname}")
    print(f"Local IP: {local_ip}")
    print(f"Network Range: {network_range}")
    print()
    
    # Find other APIs on the network
    print("Scanning for other FastAPI servers...")
    found_apis = scan_for_apis(network_range)
    
    if found_apis:
        print(f"\nFound {len(found_apis)} FastAPI server(s):")
        for api in found_apis:
            print(f"  - {api['hostname']} ({api['ip']}) - {api['status']}")
        
        # Generate code snippet
        print("\n" + "=" * 50)
        print("COPY THIS TO YOUR raspi_cluster_api.py:")
        print("=" * 50)
        for i, api in enumerate(found_apis):
            var_name = api['hostname'].upper().replace('-', '_').replace('.', '_')
            print(f"{var_name}_HOST = \"{api['ip']}\"")
    else:
        print("No other FastAPI servers found on the network.")
        print("\nMake sure:")
        print("1. Other Pis are running the FastAPI server")
        print("2. Port 8000 is open (see firewall commands below)")
    
    print("\n" + "=" * 50)
    print("NETWORK SETUP COMMANDS")
    print("=" * 50)
    print("Run these commands on each Pi:")
    print()
    print("1. Check current IP:")
    print("   hostname -I")
    print()
    print("2. Set static IP (optional but recommended):")
    print("   sudo nano /etc/dhcpcd.conf")
    print("   # Add these lines:")
    print(f"   # interface eth0")
    print(f"   # static ip_address={local_ip}/24")
    print(f"   # static routers={'.'.join(local_ip.split('.')[:-1])}.1")
    print(f"   # static domain_name_servers=8.8.8.8")
    print()
    print("3. Open firewall for FastAPI:")
    print("   sudo ufw allow 8000")
    print("   sudo ufw enable")
    print()
    print("4. Test connectivity between Pis:")
    print(f"   ping {local_ip}")
    print(f"   curl http://{local_ip}:8000/health")


if __name__ == "__main__":
    print_network_info()