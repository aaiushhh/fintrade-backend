import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        print("Logging in...")
        rj = await client.post("http://localhost:8000/auth/login", json={"email": "admin@platform.com", "password": "securePass123"})
        token = rj.json().get("access_token")
        if not token:
            print("Login failed!", rj.text)
            return
        
        print("Logged in. Triggering lecture creation...")
        body = {
            "title": "test payload",
            "course_id": 1,
            "scheduled_at": "2026-03-23T05:51:20Z",
            "description": "test",
            "instructor_id": None
        }
        res = await client.post(
            "http://localhost:8000/admin/lectures", 
            json=body,
            headers={"Authorization": f"Bearer {token}"}
        )
        print("STATUS:", res.status_code)
        print("BODY:", res.text)

asyncio.run(main())
