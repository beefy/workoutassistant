#!/usr/bin/env python3
"""
Raspberry Pi Cluster Discovery Troubleshooting Script
Run this on any Pi to debug cluster connectivity and discovery issues.
"""

import json
from clients.raspi_cluster_api import discover_cluster_hosts

if __name__ == "__main__":
    discovered_hosts = discover_cluster_hosts()
    print(f"Discovered Cluster Hosts: {json.dumps(discovered_hosts, indent=2)}")
