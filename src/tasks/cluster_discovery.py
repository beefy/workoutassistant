import socket
import json
import threading
import platform
import os

DISCOVERY_PORT = 9999
DISCOVERY_MESSAGE = "DISCOVER_WORKOUT_CLUSTER"


def start_discovery_listener():

    agent_name = os.getenv("TRACKING_API_USERNAME", "unknown")

    def listener():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", DISCOVERY_PORT))

        while True:
            data, addr = sock.recvfrom(1024)

            if data.decode() == DISCOVERY_MESSAGE:
                response = {
                    "hostname": platform.node(),
                    "agent_name": agent_name,
                    "ip": addr[0]
                }

                sock.sendto(json.dumps(response).encode(), addr)

    thread = threading.Thread(target=listener, daemon=True)
    thread.start()
