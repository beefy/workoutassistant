import requests
import os

def login(username, password):
    url = "https://api.bobtheraspberrypi.com/api/v1/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("Login successful!")
        token = response.json().get("access_token")
        print(f"Received token: {token}")
        return token
    else:
        print(f"Failed to login. Status code: {response.status_code}, Response: {response.text}")
        return None

if __name__ == "__main__":
    username = os.getenv("TRACKING_API_USERNAME")
    password = os.getenv("TRACKING_API_PASSWORD")
    if not username or not password:
        print("Please set the TRACKING_API_USERNAME and TRACKING_API_PASSWORD environment variables.")
    else:
        login(username, password)
