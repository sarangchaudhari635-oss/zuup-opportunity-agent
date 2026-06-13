import requests

base = "http://127.0.0.1:8000"
email = "simple_test_user_2@zuup.dev"
password = "TestPassword@123"

# Register
reg_resp = requests.post(f"{base}/auth/register", json={
    "email": email,
    "password": password,
    "full_name": "Simple Tester"
})
print("Register status:", reg_resp.status_code)
if reg_resp.status_code in (200, 201):
    print("Register response:", reg_resp.json())
else:
    print("Register failed:", reg_resp.text)

# Login
login_resp = requests.post(f"{base}/auth/login", json={
    "email": email,
    "password": password
})
print("Login status:", login_resp.status_code)
if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    print("Token length:", len(token))
    
    # Get opportunities
    headers = {"Authorization": f"Bearer {token}"}
    opps_resp = requests.get(f"{base}/opportunities?page=1&page_size=3", headers=headers)
    print("Opps status:", opps_resp.status_code)
    if opps_resp.status_code == 200:
        items = opps_resp.json().get("items", [])
        for i, item in enumerate(items):
            print(f"Item {i}: type={item.get('type')}, title={item.get('title')}")
else:
    print("Login failed:", login_resp.text)
