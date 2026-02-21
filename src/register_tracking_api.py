#    curl -X POST "http://localhost:8000/api/v1/auth/register" \
#         -H "Content-Type: application/json" \
#         -d '{"username": "pi-bedroom", "password": "secure-password"}'
import requests
import os

def register_user(username, password):
    url = "https://api.bobtheraspberrypi.com/api/v1/auth/register"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 201 or response.status_code == 200:
        print("User registered successfully!")
    else:
        print(f"Failed to register user. Status code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    username = os.getenv("TRACKING_API_USERNAME")
    password = os.getenv("TRACKING_API_PASSWORD")
    if not username or not password:
        print("Please set the TRACKING_API_USERNAME and TRACKING_API_PASSWORD environment variables.")
    else:
        register_user(username, password)
