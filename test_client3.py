from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user
from app.modules.auth.models import User
from app.db.database import AsyncSessionLocal
from sqlalchemy.orm import selectinload
from sqlalchemy import select

async def mock_get_current_user():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == 1))
        return res.scalar_one()

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app, raise_server_exceptions=True)

def run():
    print("Calling /admin/courses...")
    d = {
        "title": "test api overrides",
        "description": None,
        "duration_minutes": 60
    }
    r2 = client.post("/admin/courses", json=d)
    print("Status:", r2.status_code)
    print("Response text:", r2.text)

if __name__ == "__main__":
    run()
