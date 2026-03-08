import socket
import json
import time
import requests

DISCOVERY_PORT = 9999
DISCOVERY_MESSAGE = "DISCOVER_WORKOUT_CLUSTER"
DISCOVERY_TIMEOUT = 2
HEALTH_TIMEOUT = 3


def discover_cluster_hosts():

    discovered = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(DISCOVERY_TIMEOUT)

    # enable broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # send discovery packet
    sock.sendto(DISCOVERY_MESSAGE.encode(), ("255.255.255.255", DISCOVERY_PORT))

    start = time.time()

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            info = json.loads(data.decode())

            hostname = info["hostname"]
            discovered[hostname] = addr[0]

        except socket.timeout:
            break

        if time.time() - start > DISCOVERY_TIMEOUT:
            break

    sock.close()

    return discovered


def health_check_all_hosts():
    """Discover cluster hosts and check their health status."""
    discovered_hosts = discover_cluster_hosts()
    health_results = {}
    
    for hostname, ip in discovered_hosts.items():
        try:
            start_time = time.time()
            response = requests.get(f"http://{ip}:8000/health", timeout=HEALTH_TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                health_data['response_time'] = response_time
                health_data['ip'] = ip
                health_results[hostname] = health_data
            else:
                health_results[hostname] = {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'ip': ip
                }
        except Exception as e:
            health_results[hostname] = {
                'status': 'unhealthy', 
                'error': str(e),
                'ip': ip
            }
    
    return health_results


def get_all_agents():
    """Get all discovered agents with their information."""
    health_status = health_check_all_hosts()
    agents = {}
    
    for hostname, health_data in health_status.items():
        agent_name = health_data.get('agent_name', hostname)
        if agent_name:
            agents[agent_name] = {
                'hostname': hostname,
                'ip': health_data.get('ip'),
                'status': health_data.get('status'),
                'agent_name': agent_name
            }
    
    return agents


def get_healthy_hosts():
    """Get list of healthy hosts."""
    health_status = health_check_all_hosts()
    healthy = []
    
    for hostname, health_data in health_status.items():
        if health_data.get('status') == 'healthy':
            healthy.append({
                'hostname': hostname,
                'ip': health_data.get('ip'),
                'agent_name': health_data.get('agent_name')
            })
    
    return healthy


def get_agent_by_name(agent_name):
    """Get agent info by name (bob, bobby, robert, etc)."""
    agents = get_all_agents()
    return agents.get(agent_name.lower())
