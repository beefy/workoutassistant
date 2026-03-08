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
            
            # Also test via 0.0.0.0 to confirm binding
            try:
                test_response = requests.get("http://0.0.0.0:8000/health", timeout=3)
                if test_response.status_code == 200:
                    print("✅ Server accessible on 0.0.0.0:8000")
                else:
                    print(f"⚠️  Server responds differently on 0.0.0.0: {test_response.status_code}")
            except Exception:
                print("⚠️  Server not accessible via 0.0.0.0 (but localhost works)")
            
            return True, data
        else:
            print(f"❌ Local FastAPI server returned status {response.status_code}")
            return False, None
            
    except requests.ConnectionError:
        print("❌ Local FastAPI server is not running")
        print("   Try: python -m src.tasks.rest_server")
        print("   Check what's using port 8000: sudo lsof -i :8000")
        print("   Check if TRACKING_API_USERNAME is set: echo $TRACKING_API_USERNAME")
        return False, None
    except Exception as e:
        print(f"❌ Error testing local FastAPI: {e}")
        return False, None

def test_hostname_connectivity():
    """Test connectivity to known cluster hostnames."""
    print("\n" + "=" * 60)
    print("3. TESTING HOSTNAME CONNECTIVITY")
    print("=" * 60)
    
    cluster_hostnames = ["bob.local", "bobby.local", "robert.local"]
    reachable_hostnames = []
    
    def ping_hostname(hostname):
        """Test if hostname responds to ping."""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1000', hostname], 
                capture_output=True, 
                timeout=3
            )
            if result.returncode == 0:
                return hostname
        except Exception:
            pass
        return None
    
    print(f"Testing connectivity to cluster hostnames: {cluster_hostnames}")
    
    for hostname in cluster_hostnames:
        result = ping_hostname(hostname)
        if result:
            print(f"✅ {hostname} - reachable")
            reachable_hostnames.append(hostname)
        else:
            print(f"❌ {hostname} - unreachable")
    
    if reachable_hostnames:
        print(f"\n✅ {len(reachable_hostnames)} hostname(s) reachable")
    else:
        print("\n❌ No cluster hostnames reachable")
        print("   Make sure .local addresses work: ping bob.local")
        print("   Check mDNS/Bonjour is working")
    
    return reachable_hostnames

def test_fastapi_hostname_discovery(reachable_hostnames):
    """Test FastAPI server discovery on reachable hostnames."""
    print("\n" + "=" * 60)
    print("4. TESTING FASTAPI HOSTNAME DISCOVERY")
    print("=" * 60)
    
    if not reachable_hostnames:
        print("❌ No reachable hostnames to test")
        return []
    
    fastapi_servers = []
    
    def check_port_connectivity(hostname):
        """Check if port 8000 is open on hostname."""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((hostname, 8000))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def check_fastapi_hostname(hostname):
        """Check if hostname has FastAPI server running."""
        # First check if port 8000 is open
        port_open = check_port_connectivity(hostname)
        if not port_open:
            print(f"   ❌ {hostname}: Port 8000 not open/accessible")
            return None
            
        try:
            response = requests.get(f"http://{hostname}:8000/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'hostname': hostname,
                    'actual_hostname': data.get('hostname', 'unknown'),
                    'agent_name': data.get('agent_name'),
                    'status': data.get('status'),
                    'service': data.get('service'),
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                print(f"   ❌ {hostname}: HTTP {response.status_code} - {response.text[:50]}")
                return None
        except requests.Timeout:
            print(f"   ❌ {hostname}: Request timeout")
        except requests.ConnectionError as e:
            print(f"   ❌ {hostname}: Connection error - {str(e)[:80]}")
        except Exception as e:
            print(f"   ❌ {hostname}: {str(e)[:50]}")
        return None
    
    print(f"Checking {len(reachable_hostnames)} hostnames for FastAPI servers...")
    
    for hostname in reachable_hostnames:
        result = check_fastapi_hostname(hostname)
        if result:
            fastapi_servers.append(result)
    
    if fastapi_servers:
        print(f"\n✅ Found {len(fastapi_servers)} FastAPI server(s):")
        for server in fastapi_servers:
            agent_name = server['agent_name'] or 'NO AGENT NAME'
            print(f"   🚀 {server['hostname']} - {server['actual_hostname']} - {agent_name} - {server['response_time']:.3f}s")
    else:
        print("\n❌ No FastAPI servers found")
        print("\n🔍 DEBUGGING STEPS:")
        print("   1. Check if servers are running: python -m src.tasks.rest_server")
        print("   2. Test local connection: curl http://localhost:8000/health")
        print("   3. Check what's listening on port 8000: sudo lsof -i :8000")
        print("   4. Check firewall: sudo ufw status")
        print("   5. Test manual connection: curl http://bob.local:8000/health")
        print("   6. Check server logs for errors")
    
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
    reachable_hostnames = results.get('reachable_hostnames', [])
    fastapi_servers = results.get('fastapi_servers', [])
    cluster_api_results = results.get('cluster_api_results')
    
    if not local_fastapi_ok:
        print("🔧 LOCAL FASTAPI SERVER ISSUES:")
        print("   1. Start the server: python -m src.tasks.rest_server")
        print("   2. Check if port 8000 is available: lsof -i :8000")
        print("   3. Set agent name: export TRACKING_API_USERNAME='bob'")
        print()
    
    if not reachable_hostnames:
        print("🔧 HOSTNAME CONNECTIVITY ISSUES:")
        print("   1. Check .local domain resolution: ping bob.local")
        print("   2. Ensure mDNS/Bonjour is running: sudo systemctl status avahi-daemon")
        print("   3. Check if hostnames are correct on each Pi: hostname")
        print("   4. Test manual resolution: nslookup bob.local")
        print()
    
    if reachable_hostnames and not fastapi_servers:
        print("🔧 REMOTE FASTAPI SERVER ISSUES:")
        print("   1. Start servers on other Pis: python -m src.tasks.rest_server")
        print("   2. Set agent names: export TRACKING_API_USERNAME='bobby'")
        print("   3. Test manually: curl http://bobby.local:8000/health")
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
        print("   - Hostname-based cluster discovery working!")
        print("   - Make sure all Pis have unique agent names")
        print("   - Test Discord !status command now")
        print("   - Much faster than IP scanning!")

def main():
    """Run all cluster discovery tests."""
    print("RASPBERRY PI CLUSTER DISCOVERY TROUBLESHOOTING")
    print("=" * 60)
    print("This script will help debug hostname-based cluster connectivity")
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
    
    # Test 3: Hostname connectivity
    reachable_hostnames = test_hostname_connectivity()
    results['reachable_hostnames'] = reachable_hostnames
    
    # Test 4: FastAPI hostname discovery
    fastapi_servers = test_fastapi_hostname_discovery(reachable_hostnames)
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
        print(f"🎉 Found {len(fastapi_servers)} working FastAPI servers via hostnames!")
        print("Hostname-based discovery is much faster than IP scanning!")
    else:
        print("❌ No working FastAPI servers found. Check troubleshooting tips above.")

if __name__ == "__main__":
    main()