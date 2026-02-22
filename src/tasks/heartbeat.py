from utils.tracking_api import login, system_info_update, heartbeat
import os
import time


def main():
    while True:
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            system_info_update(tracking_token)
            heartbeat(tracking_token)
        
        # Sleep for 5 minutes before sending the next heartbeat
        time.sleep(300)
