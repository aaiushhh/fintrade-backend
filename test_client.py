from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=True)

def run():
    print("Logging in...")
    r = client.post("/auth/login", json={"email": "admin@platform.com", "password": "admin123"})
    if r.status_code != 200:
        print("Login failed:", r.status_code, r.text)
        return
    token = r.json()["access_token"]
    
    print("Calling /admin/courses...")
    h = {"Authorization": f"Bearer {token}"}
    d = {
        "title": "test via API",
        "description": None,
        "duration_minutes": 60
    }
    r2 = client.post("/admin/courses", json=d, headers=h)
    print("Status:", r2.status_code)
    print("Response text:", r2.text)

if __name__ == "__main__":
    run()
