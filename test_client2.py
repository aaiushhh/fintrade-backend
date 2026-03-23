import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app, raise_server_exceptions=True)

def run():
    token = create_access_token(data={"sub": "1", "type": "access"})
    h = {"Authorization": f"Bearer {token}"}
    d = {
        "title": "test api fast",
        "description": None,
        "short_description": None
    }
    r2 = client.post("/admin/courses", json=d, headers=h)
    print("Status:", r2.status_code)
    print("Response text:", r2.text)

if __name__ == "__main__":
    run()
