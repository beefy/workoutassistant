import requests
import os
import base64
import datetime
import psutil
import logging
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

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
        logger.info("Login successful!")
        token = response.json().get("access_token")
        return token
    else:
        logger.error(f"Failed to login. Status code: {response.status_code}, Response: {response.text}")
        return None

def status_update(token, status):
    agent_name = os.getenv("TRACKING_API_USERNAME")
    if not agent_name:
        logger.error("TRACKING_API_USERNAME environment variable not set.")
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
        logger.info("Status update sent successfully!")
    else:
        logger.error(f"Failed to send status update. Status code: {response.status_code}, Response: {response.text}")

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
        logger.error("TRACKING_API_USERNAME environment variable not set.")
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
        logger.info("System info sent successfully!")
    else:
        logger.error(f"Failed to send system info. Status code: {response.status_code}, Response: {response.text}")

def response_time_update(token, received_time, response_time):
    agent_name = os.getenv("TRACKING_API_USERNAME")
    if not agent_name:
        logger.error("TRACKING_API_USERNAME environment variable not set.")
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
        logger.info("Response time info sent successfully!")
    else:
        logger.error(f"Failed to send response time info. Status code: {response.status_code}, Response: {response.text}")

def heartbeat(token):
    agent_name = os.getenv("TRACKING_API_USERNAME")
    if not agent_name:
        logger.error("TRACKING_API_USERNAME environment variable not set.")
        return

    url = "https://api.bobtheraspberrypi.com/api/v1/heartbeat/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    # {
    #     "agent_name": "string",
    #     "last_heartbeat_ts": "2026-02-21T20:09:06.641Z"
    # }

    payload = {
        "agent_name": agent_name,
        "last_heartbeat_ts": datetime.datetime.now(datetime.UTC).isoformat()
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200 or response.status_code == 201:
        logger.info("Heartbeat sent successfully!")
    else:
        logger.error(f"Failed to send heartbeat. Status code: {response.status_code}, Response: {response.text}")


def unsubscribe_user(email):
    url = f"https://api.bobtheraspberrypi.com/api/v1/newsletter/unsubscribe?email={email}"
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logger.info(f"Successfully unsubscribed {email} from newsletter.")
    else:
        logger.error(f"Failed to unsubscribe {email}. Status code: {response.status_code}, Response: {response.text}")


def refresh_indicators(token):
    # POST /api/v1/indicators/indicators/refresh
    url = "https://api.bobtheraspberrypi.com/api/v1/indicators/indicators/refresh"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200 or response.status_code == 201:
        logger.info("Indicator refresh triggered successfully!")
    else:
        logger.error(f"Failed to trigger indicator refresh. Status code: {response.status_code}, Response: {response.text}")


def get_indicators(token):
    # GET /api/v1/indicators/indicators/
    url = "https://api.bobtheraspberrypi.com/api/v1/indicators/indicators"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logger.info("Indicators fetched successfully!")
        return response.json()
    else:
        logger.error(f"Failed to fetch indicators. Status code: {response.status_code}, Response: {response.text}")
        return None


def get_indicator_cache_stats(token):
    # GET /api/v1/indicators/indicators/cache-stats/
    url = "https://api.bobtheraspberrypi.com/api/v1/indicators/indicators/cache-stats"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logger.info("Cache stats fetched successfully!")
        return response.json()
    else:
        logger.error(f"Failed to fetch cache stats. Status code: {response.status_code}, Response: {response.text}")
        return None


def upload_balances(token, balances):
    # POST /api/v1/balances/upload
    # {
    #     "agent_name": "string",
    #     "balances": [
    #         {
    #         "token_name": "string",
    #         "token_amount_in_wallet": 0,
    #         "token_value_usd": 0
    #         }
    #     ],
    #     "timestamp": "2026-03-04T21:48:37.462Z"
    # }
    url = "https://api.bobtheraspberrypi.com/api/v1/balances/upload"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    balances_cleaned = []
    for balance in balances:
        balances_cleaned.append({
            "token_name": balance,
            "token_amount_in_wallet": balances[balance]['balance'],
            "token_value_usd": balances[balance]['usd_price']
        })

    payload = {
        "agent_name": os.getenv("TRACKING_API_USERNAME"),
        "balances": balances_cleaned,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200 or response.status_code == 201:
        logger.info("Balances uploaded successfully!")
    else:
        logger.error(f"Failed to upload balances. Status code: {response.status_code}, Response: {response.text}")


if __name__ == "__main__":
    username = os.getenv("TRACKING_API_USERNAME")
    password = os.getenv("TRACKING_API_PASSWORD")
    if not username or not password:
        logger.error("Please set the TRACKING_API_USERNAME and TRACKING_API_PASSWORD environment variables.")
    else:
        token = login(username, password)
        if token:
            status_update(token, "Testing Status Update API")
            system_info_update(token)
            response_time_update(token, datetime.datetime.now(datetime.UTC).isoformat(), datetime.datetime.now(datetime.UTC).isoformat())
            heartbeat(token)
