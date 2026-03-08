#!/usr/bin/env python3
"""
Test script for Raspberry Pi cluster communication.
Run this on each Pi to test cluster connectivity.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from clients.raspi_cluster_api import (
    health_check_all_hosts, 
    get_all_cluster_hosts,
    get_healthy_hosts,
    discover_cluster_hosts,
    broadcast_request
)
import json


def test_cluster_discovery():
    """Test auto-discovery of cluster hosts."""
    print("=" * 50)
    print("TESTING CLUSTER DISCOVERY")
    print("=" * 50)
    
    discovered = discover_cluster_hosts()
    print(f"Auto-discovered hosts: {discovered}")
    
    all_hosts = get_all_cluster_hosts()
    print(f"All configured hosts: {all_hosts}")
    
    return len(all_hosts) > 0


def test_health_checks():
    """Test health checks for all cluster hosts."""
    print("\n" + "=" * 50)
    print("TESTING HEALTH CHECKS")
    print("=" * 50)
    
    results = health_check_all_hosts()
    
    for host_name, health_data in results.items():
        status = health_data.get("status", "unknown")
        if status == "healthy":
            hostname = health_data.get("hostname", "unknown")
            response_time = health_data.get("response_time", 0)
            print(f"✅ {host_name} ({hostname}): {status} - {response_time:.3f}s")
        else:
            error = health_data.get("error", "unknown error")
            print(f"❌ {host_name}: {status} - {error}")
    
    healthy_hosts = get_healthy_hosts()
    print(f"\nHealthy hosts: {healthy_hosts}")
    return len(healthy_hosts) > 0


def test_broadcast():
    """Test broadcasting requests to all healthy hosts."""
    print("\n" + "=" * 50)
    print("TESTING BROADCAST REQUESTS")
    print("=" * 50)
    
    # Test broadcasting health checks
    results = broadcast_request("/health")
    
    print("Broadcast health check results:")
    for host_name, result in results.items():
        if result.get("status") == "healthy":
            hostname = result.get("hostname", "unknown")
            print(f"✅ {host_name} ({hostname}): responded successfully")
        else:
            error = result.get("error", "unknown error")
            print(f"❌ {host_name}: {error}")
    
    return len(results) > 0


def main():
    """Run all cluster tests."""
    print("RASPBERRY PI CLUSTER CONNECTIVITY TEST")
    print("=" * 50)
    
    # Test 1: Discovery
    discovery_success = test_cluster_discovery()
    
    if not discovery_success:
        print("\n❌ NO CLUSTER HOSTS FOUND!")
        print("\nTroubleshooting steps:")
        print("1. Make sure other Pis are running the FastAPI server:")
        print("   python -m src.tasks.rest_server")
        print("2. Run network discovery script:")
        print("   python src/scripts/network_discovery.py")
        print("3. Check firewall settings:")
        print("   sudo ufw status")
        print("   sudo ufw allow 8000")
        return
    
    # Test 2: Health checks
    health_success = test_health_checks()
    
    # Test 3: Broadcast
    if health_success:
        broadcast_success = test_broadcast()
        
        if broadcast_success:
            print("\n🎉 CLUSTER COMMUNICATION SUCCESSFUL!")
        else:
            print("\n⚠️  Cluster discovered but broadcast failed")
    else:
        print("\n⚠️  Cluster hosts found but none are healthy")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()