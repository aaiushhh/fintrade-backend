import asyncio
from app.db.database import AsyncSessionLocal
from app.modules.auth.models import User
from app.core.security import hash_password
from sqlalchemy import select, update

async def fix():
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.email=='admin@platform.com').values(hashed_password=hash_password('admin123!')))
        await db.commit()
    print('Fixed')

if __name__ == "__main__":
    asyncio.run(fix())
