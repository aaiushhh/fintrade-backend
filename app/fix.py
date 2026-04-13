import asyncio
from app.db.database import AsyncSessionLocal
from app.modules.auth.models import User
from app.core.security import hash_password
from app.config import settings
from sqlalchemy import select, update

async def fix():
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(User)
            .where(User.email == settings.ADMIN_EMAIL)
            .values(hashed_password=hash_password(settings.ADMIN_PASSWORD))
        )
        await db.commit()
    print('Fixed')

if __name__ == "__main__":
    asyncio.run(fix())

