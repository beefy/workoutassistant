import requests
import os
import base64
import datetime
import psutil

def login(username, password):
    # curl -X POST "https://api.bobtheraspberrypi.com/api/v1/auth/login" \
    #     -u "username:password" \
    #     -H "Content-Type: application/json"
    url = "https://api.bobtheraspberrypi.com/api/v1/auth/login"
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        print("Login successful!")
        token = response.json().get("access_token")
        print(f"Received token: {token}")
        return token
    else:
        print(f"Failed to login. Status code: {response.status_code}, Response: {response.text}")
        return None

def status_update(token, status):
    agent_name = os.getenv("TRACKING_API_USERNAME")
    if not agent_name:
        print("TRACKING_API_USERNAME environment variable not set.")
        return

    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    url = "https://api.bobtheraspberrypi.com/api/v1/status-updates/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    # {
    # "agent_name": "string",
    # "update_text": "string",
    # "timestamp": "2026-02-21T19:36:44.907Z"
    # }

    payload = {
        "agent_name": agent_name,
        "update_text": status,
        "timestamp": timestamp
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200 or response.status_code == 201:
        print("Status update sent successfully!")
    else:
        print(f"Failed to send status update. Status code: {response.status_code}, Response: {response.text}")

def system_info_update(token):
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().used
    disk = psutil.disk_usage('/').used
    # {
    #     "agent_name": "string",
    #     "cpu": 0,
    #     "memory": 0,
    #     "disk": 0,
    #     "ts": "2026-02-21T20:09:06.641Z"
    # }
    agent_name = os.getenv("TRACKING_API_USERNAME")
    if not agent_name:
        print("TRACKING_API_USERNAME environment variable not set.")
        return

    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    url = "https://api.bobtheraspberrypi.com/api/v1/system-info/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "agent_name": agent_name,
        "cpu": cpu_percent,
        "memory": memory,
        "disk": disk,
        "ts": timestamp
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200 or response.status_code == 201:
        print("System info sent successfully!")
    else:
        print(f"Failed to send system info. Status code: {response.status_code}, Response: {response.text}")

def response_time_update(token, received_time, response_time):
    agent_name = os.getenv("TRACKING_API_USERNAME")
    if not agent_name:
        print("TRACKING_API_USERNAME environment variable not set.")
        return

    url = "https://api.bobtheraspberrypi.com/api/v1/response-times/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    # {
    #     "agent_name": "string",
    #     "received_time": "2026-02-21T20:09:06.641Z",
    #     "response_time": 0
    # }

    payload = {
        "agent_name": agent_name,
        "received_ts": received_time,
        "sent_ts": response_time
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200 or response.status_code == 201:
        print("Response time info sent successfully!")
    else:
        print(f"Failed to send response time info. Status code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    username = os.getenv("TRACKING_API_USERNAME")
    password = os.getenv("TRACKING_API_PASSWORD")
    if not username or not password:
        print("Please set the TRACKING_API_USERNAME and TRACKING_API_PASSWORD environment variables.")
    else:
        token = login(username, password)
        if token:
            status_update(token, "Testing Status Update API")
            system_info_update(token)
            response_time_update(token, datetime.datetime.now(datetime.UTC).isoformat(), datetime.datetime.now(datetime.UTC).isoformat())
