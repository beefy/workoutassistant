#!/usr/bin/env python3
"""
Raspberry Pi Cluster Discovery Troubleshooting Script
Run this on any Pi to debug cluster connectivity and discovery issues.
"""

import sys
import os
import time
import socket
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor
import subprocess
import json

# Add src directory to path 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_local_network():
    """Test basic network configuration."""
    print("=" * 60)
    print("1. TESTING LOCAL NETWORK CONFIGURATION")
    print("=" * 60)
    
    try:
        # Get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        
        print(f"✅ Local IP: {local_ip}")
        
        # Get hostname
        hostname = socket.gethostname()
        print(f"✅ Hostname: {hostname}")
        
        # Get network range
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        print(f"✅ Network Range: {network}")
        
        return local_ip, str(network)
        
    except Exception as e:
        print(f"❌ Network configuration error: {e}")
        return None, None

def test_local_fastapi():
    """Test if local FastAPI server is running."""
    print("\n" + "=" * 60)
    print("2. TESTING LOCAL FASTAPI SERVER")
    print("=" * 60)
    
    try:
        # Test local health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Local FastAPI server is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Hostname: {data.get('hostname')}")
            print(f"   Agent Name: {data.get('agent_name', 'NOT SET')}")
            print(f"   Service: {data.get('service')}")
            return True, data
        else:
            print(f"❌ Local FastAPI server returned status {response.status_code}")
            return False, None
            
    except requests.ConnectionError:
        print("❌ Local FastAPI server is not running")
        print("   Try: python -m src.tasks.rest_server")
        return False, None
    except Exception as e:
        print(f"❌ Error testing local FastAPI: {e}")
        return False, None

def test_network_connectivity(network_range):
    """Test basic connectivity to other hosts in network."""
    print("\n" + "=" * 60)
    print("3. TESTING NETWORK CONNECTIVITY")
    print("=" * 60)
    
    if not network_range:
        print("❌ No network range available")
        return []
    
    network = ipaddress.IPv4Network(network_range)
    reachable_hosts = []
    
    def ping_host(ip):
        """Test if host responds to ping."""
        try:
            # Use ping command (works on Unix/macOS/Linux)
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1000', str(ip)], 
                capture_output=True, 
                timeout=2
            )
            if result.returncode == 0:
                return str(ip)
        except Exception:
            pass
        return None
    
    print(f"Pinging hosts in {network_range}... (this may take a moment)")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(ping_host, list(network.hosts())[:50]))  # Limit to first 50 IPs
    
    reachable_hosts = [ip for ip in results if ip is not None]
    
    if reachable_hosts:
        print(f"✅ Found {len(reachable_hosts)} reachable hosts:")
        for ip in reachable_hosts:
            print(f"   📡 {ip}")
    else:
        print("❌ No reachable hosts found")
    
    return reachable_hosts

def test_fastapi_discovery(reachable_hosts):
    """Test FastAPI server discovery on reachable hosts."""
    print("\n" + "=" * 60)
    print("4. TESTING FASTAPI SERVER DISCOVERY")
    print("=" * 60)
    
    if not reachable_hosts:
        print("❌ No reachable hosts to test")
        return []
    
    fastapi_servers = []
    
    def check_fastapi_server(ip):
        """Check if host has FastAPI server running."""
        try:
            response = requests.get(f"http://{ip}:8000/health", timeout=3)
            if response.status_code == 200:
                data = response.json()
                return {
                    'ip': ip,
                    'hostname': data.get('hostname', 'unknown'),
                    'agent_name': data.get('agent_name'),
                    'status': data.get('status'),
                    'service': data.get('service'),
                    'response_time': response.elapsed.total_seconds()
                }
        except Exception as e:
            # Only show errors for debugging if needed
            return None
        return None
    
    print(f"Checking {len(reachable_hosts)} hosts for FastAPI servers...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_fastapi_server, reachable_hosts))
    
    fastapi_servers = [result for result in results if result is not None]
    
    if fastapi_servers:
        print(f"✅ Found {len(fastapi_servers)} FastAPI server(s):")
        for server in fastapi_servers:
            agent_name = server['agent_name'] or 'NO AGENT NAME'
            print(f"   🚀 {server['ip']} - {server['hostname']} - {agent_name} - {server['response_time']:.3f}s")
    else:
        print("❌ No FastAPI servers found")
        print("   Make sure other Pis are running: python -m src.tasks.rest_server")
    
    return fastapi_servers

def test_cluster_api_functions():
    """Test the cluster API functions directly."""
    print("\n" + "=" * 60)
    print("5. TESTING CLUSTER API FUNCTIONS")
    print("=" * 60)
    
    try:
        from clients.raspi_cluster_api import (
            discover_cluster_hosts,
            get_all_agents,
            health_check_all_hosts,
            get_healthy_hosts
        )
        
        # Test discovery
        print("Testing discover_cluster_hosts()...")
        discovered_hosts = discover_cluster_hosts()
        print(f"   Discovered hosts: {discovered_hosts}")
        
        # Test agents
        print("Testing get_all_agents()...")
        agents = get_all_agents()
        print(f"   Agents: {agents}")
        
        # Test health checks
        print("Testing health_check_all_hosts()...")
        health_results = health_check_all_hosts()
        print(f"   Health results: {health_results}")
        
        # Test healthy hosts
        print("Testing get_healthy_hosts()...")
        healthy_hosts = get_healthy_hosts()
        print(f"   Healthy hosts: {healthy_hosts}")
        
        return {
            'discovered_hosts': discovered_hosts,
            'agents': agents,
            'health_results': health_results,
            'healthy_hosts': healthy_hosts
        }
        
    except Exception as e:
        print(f"❌ Error testing cluster API functions: {e}")
        return None

def test_environment_variables():
    """Test required environment variables."""
    print("\n" + "=" * 60)
    print("6. TESTING ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    # Check TRACKING_API_USERNAME
    agent_name = os.getenv('TRACKING_API_USERNAME')
    if agent_name:
        print(f"✅ TRACKING_API_USERNAME: {agent_name}")
        if agent_name.lower() in ['bob', 'bobby', 'robert']:
            print("✅ Agent name is valid")
        else:
            print("⚠️  Agent name should be 'bob', 'bobby', or 'robert'")
    else:
        print("❌ TRACKING_API_USERNAME not set")
        print("   Set it with: export TRACKING_API_USERNAME='bob'")
    
    # Check optional API settings
    api_host = os.getenv('API_HOST', '0.0.0.0')
    api_port = os.getenv('API_PORT', '8000')
    print(f"ℹ️  API_HOST: {api_host}")
    print(f"ℹ️  API_PORT: {api_port}")

def provide_troubleshooting_tips(results):
    """Provide troubleshooting tips based on test results."""
    print("\n" + "=" * 60)
    print("7. TROUBLESHOOTING TIPS")
    print("=" * 60)
    
    local_fastapi_ok = results.get('local_fastapi_ok', False)
    reachable_hosts = results.get('reachable_hosts', [])
    fastapi_servers = results.get('fastapi_servers', [])
    cluster_api_results = results.get('cluster_api_results')
    
    if not local_fastapi_ok:
        print("🔧 LOCAL FASTAPI SERVER ISSUES:")
        print("   1. Start the server: python -m src.tasks.rest_server")
        print("   2. Check if port 8000 is available: lsof -i :8000")
        print("   3. Check firewall: sudo ufw status")
        print()
    
    if not reachable_hosts:
        print("🔧 NETWORK CONNECTIVITY ISSUES:")
        print("   1. Check if Pis are on same network")
        print("   2. Check WiFi/Ethernet connection")
        print("   3. Try manual ping: ping <other-pi-ip>")
        print()
    
    if reachable_hosts and not fastapi_servers:
        print("🔧 REMOTE FASTAPI SERVER ISSUES:")
        print("   1. Start servers on other Pis: python -m src.tasks.rest_server")
        print("   2. Check firewall on other Pis: sudo ufw allow 8000")
        print("   3. Test manually: curl http://<other-pi-ip>:8000/health")
        print()
    
    if fastapi_servers and not cluster_api_results:
        print("🔧 CLUSTER API ISSUES:")
        print("   1. Check Python import path")
        print("   2. Verify requirements.txt dependencies installed")
        print("   3. Check for Python errors in logs")
        print()
    
    agent_name = os.getenv('TRACKING_API_USERNAME')
    if not agent_name:
        print("🔧 ENVIRONMENT VARIABLE ISSUES:")
        print("   1. Set agent name: export TRACKING_API_USERNAME='bob'")
        print("   2. Add to ~/.bashrc for persistence")
        print("   3. Restart FastAPI server after setting")
        print()
    
    if len(fastapi_servers) > 0:
        print("✅ SUCCESS TIPS:")
        print("   - Cluster discovery working!")
        print("   - Make sure all Pis have unique agent names")
        print("   - Test Discord !status command now")

def main():
    """Run all cluster discovery tests."""
    print("RASPBERRY PI CLUSTER DISCOVERY TROUBLESHOOTING")
    print("=" * 60)
    print("This script will help debug cluster connectivity issues")
    print()
    
    results = {}
    
    # Test 1: Local network
    local_ip, network_range = test_local_network()
    results['local_ip'] = local_ip
    results['network_range'] = network_range
    
    # Test 2: Local FastAPI
    local_fastapi_ok, local_data = test_local_fastapi()
    results['local_fastapi_ok'] = local_fastapi_ok
    results['local_data'] = local_data
    
    # Test 3: Network connectivity
    reachable_hosts = test_network_connectivity(network_range)
    results['reachable_hosts'] = reachable_hosts
    
    # Test 4: FastAPI discovery
    fastapi_servers = test_fastapi_discovery(reachable_hosts)
    results['fastapi_servers'] = fastapi_servers
    
    # Test 5: Cluster API functions
    cluster_api_results = test_cluster_api_functions()
    results['cluster_api_results'] = cluster_api_results
    
    # Test 6: Environment variables
    test_environment_variables()
    
    # Test 7: Troubleshooting tips
    provide_troubleshooting_tips(results)
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)
    
    if fastapi_servers:
        print(f"🎉 Found {len(fastapi_servers)} working FastAPI servers!")
    else:
        print("❌ No working FastAPI servers found. Check troubleshooting tips above.")

if __name__ == "__main__":
    main()