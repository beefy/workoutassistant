import socket
import json
import time

DISCOVERY_PORT = 9999
DISCOVERY_MESSAGE = "DISCOVER_WORKOUT_CLUSTER"
DISCOVERY_TIMEOUT = 2


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
