import requests
import socket
import ipaddress
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
import time

# Manually configured hosts (fill these in after running network discovery)
BOB_HOST = ""
BOBBY_HOST = ""
ROBERT_HOST = ""

# Auto-discovery cache (refreshed periodically)
_discovered_hosts = {}  # hostname -> ip
_discovered_agents = {}  # agent_name -> {hostname, ip, last_seen}
_last_discovery_time = 0
DISCOVERY_CACHE_DURATION = 300  # 5 minutes


def get_local_ip() -> str:
    """Get the local IP address of this Pi."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def get_network_range() -> Optional[str]:
    """Get the network range (subnet) this Pi is on."""
    try:
        local_ip = get_local_ip()
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        return str(network)
    except Exception:
        return None


def discover_cluster_hosts() -> Dict[str, str]:
    """Discover other Raspberry Pi FastAPI servers on the network (works with dynamic IPs)."""
    global _discovered_hosts, _discovered_agents, _last_discovery_time
    
    # Use cache if recent
    current_time = time.time()
    if current_time - _last_discovery_time < DISCOVERY_CACHE_DURATION and _discovered_hosts:
        return _discovered_hosts
    
    print("Auto-discovering cluster hosts (dynamic IP scan)...")
    network_range = get_network_range()
    if not network_range:
        return {}
    
    network = ipaddress.IPv4Network(network_range)
    found_hosts = {}
    found_agents = {}
    
    def check_host(ip):
        """Check if a host has our FastAPI server running and get agent info."""
        try:
            response = requests.get(f"http://{ip}:8000/health", timeout=1)
            if response.status_code == 200:
                data = response.json()
                hostname = data.get("hostname", str(ip))
                agent_name = data.get("agent_name")
                return hostname, str(ip), agent_name
        except Exception:
            pass
        return None, None, None
    
    # Scan network in parallel (works with any DHCP-assigned IPs)
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_host, network.hosts()))
    
    for hostname, ip, agent_name in results:
        if hostname and ip:
            found_hosts[hostname] = ip
            # Save agent name mapping (bob, bobby, robert)
            if agent_name:
                found_agents[agent_name] = {
                    "hostname": hostname,
                    "ip": ip,
                    "last_seen": current_time
                }
    
    _discovered_hosts = found_hosts
    _discovered_agents = found_agents
    _last_discovery_time = current_time
    
    agent_names = list(found_agents.keys())
    print(f"Discovered {len(found_hosts)} cluster hosts: {list(found_hosts.keys())}")
    if agent_names:
        print(f"Agent names found: {agent_names}")
    
    return found_hosts


def get_agent_by_name(agent_name: str) -> Optional[Dict[str, str]]:
    """Get agent info by name (bob, bobby, robert)."""
    # Trigger auto-discovery if needed
    discover_cluster_hosts()
    global _discovered_agents
    
    return _discovered_agents.get(agent_name.lower())


def get_all_agents() -> Dict[str, Dict[str, str]]:
    """Get all discovered agents with their info."""
    # Trigger auto-discovery if needed
    discover_cluster_hosts()
    global _discovered_agents
    
    return _discovered_agents.copy()


def get_all_cluster_hosts() -> Dict[str, str]:
    """Get all cluster hosts (manual + auto-discovered). Auto-discovery runs automatically."""
    hosts = {}
    
    # Add manually configured hosts (if any)
    manual_hosts = {
        "BOB": BOB_HOST,
        "BOBBY": BOBBY_HOST, 
        "ROBERT": ROBERT_HOST
    }
    
    for name, host in manual_hosts.items():
        if host.strip():
            hosts[name] = host.strip()
    
    # Auto-discovery runs automatically (works with dynamic IPs)
    discovered = discover_cluster_hosts()
    local_hostname = socket.gethostname()
    
    # Add discovered hosts by hostname
    for hostname, ip in discovered.items():
        # Skip self
        if hostname != local_hostname:
            hosts[hostname] = ip
    
    # Also add by agent name if available
    global _discovered_agents
    for agent_name, info in _discovered_agents.items():
        if info["hostname"] != local_hostname:
            # Use agent name as key (bob, bobby, robert)
            hosts[agent_name.upper()] = info["ip"]
    
    return hosts


def health_check(host: str, timeout: int = 5) -> Dict:
    """Check a host for health by sending a GET request to the /health endpoint."""
    try:
        response = requests.get(f"http://{host}:8000/health", timeout=timeout)
        response.raise_for_status()
        result = response.json()
        result["response_time"] = response.elapsed.total_seconds()
        return result
    except requests.Timeout:
        return {"status": "unhealthy", "error": "timeout"}
    except requests.ConnectionError:
        return {"status": "unhealthy", "error": "connection_refused"}
    except requests.RequestException as e:
        return {"status": "unhealthy", "error": str(e)}


def health_check_all_hosts() -> Dict[str, Dict]:
    """Check health of all known cluster hosts."""
    hosts = get_all_cluster_hosts()
    results = {}
    
    def check_single_host(item):
        name, host = item
        return name, health_check(host)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        host_results = list(executor.map(check_single_host, hosts.items()))
    
    for name, result in host_results:
        results[name] = result
    
    return results


def get_healthy_hosts() -> List[str]:
    """Get list of healthy cluster hosts."""
    results = health_check_all_hosts()
    return [host for host, status in results.items() if status.get("status") == "healthy"]


def broadcast_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Dict]:
    """Send a request to an endpoint on all healthy cluster hosts."""
    healthy_hosts = get_healthy_hosts()
    results = {}
    
    def send_request(host_name):
        hosts = get_all_cluster_hosts()
        if host_name not in hosts:
            return host_name, {"status": "error", "error": "host_not_found"}
        
        host_ip = hosts[host_name]
        try:
            if method.upper() == "GET":
                response = requests.get(f"http://{host_ip}:8000{endpoint}", timeout=5)
            elif method.upper() == "POST":
                response = requests.post(f"http://{host_ip}:8000{endpoint}", json=data, timeout=5)
            else:
                return host_name, {"status": "error", "error": "unsupported_method"}
            
            response.raise_for_status()
            return host_name, response.json()
            
        except requests.RequestException as e:
            return host_name, {"status": "error", "error": str(e)}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        host_results = list(executor.map(send_request, healthy_hosts))
    
    for host_name, result in host_results:
        results[host_name] = result
    
    return results
