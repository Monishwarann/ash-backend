import requests
import json
import time

API_KEY = "AIzaSyCtbDdM4NMpfe67x3pQEAGIynr-RUTaW7M"
SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
BACKEND_URL = "http://127.0.0.1:5000"

def test_auth():
    print("1. Creating test user on Firebase Auth...")
    test_email = f"test_{int(time.time())}@example.com"
    test_password = "password1234"
    
    payload = {
        "email": test_email,
        "password": test_password,
        "returnSecureToken": True
    }
    
    res = requests.post(SIGNUP_URL, json=payload)
    if res.status_code != 200:
        print("Failed to create Firebase user:", res.text)
        return
        
    data = res.json()
    id_token = data['idToken']
    uid = data['localId']
    print(f"Success! Created user UID: {uid}")
    
    print("\n2. Sending token to Flask backend (/api/auth/register)...")
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    backend_payload = {
        "username": f"TestUser_{int(time.time())}",
        "email": test_email
    }
    
    backend_res = requests.post(f"{BACKEND_URL}/api/auth/register", json=backend_payload, headers=headers)
    print(f"Backend Response Code: {backend_res.status_code}")
    print(f"Backend Response Body: {backend_res.text}")
    
    if backend_res.status_code == 201:
        print("\n=> AUTHENTICATION TEST PASSED SUCCESSFULLY!")
    else:
        print("\n=> AUTHENTICATION TEST FAILED!")

if __name__ == "__main__":
    test_auth()
