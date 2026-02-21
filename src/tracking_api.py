import requests
import os
import base64

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

if __name__ == "__main__":
    username = os.getenv("TRACKING_API_USERNAME")
    password = os.getenv("TRACKING_API_PASSWORD")
    if not username or not password:
        print("Please set the TRACKING_API_USERNAME and TRACKING_API_PASSWORD environment variables.")
    else:
        login(username, password)
