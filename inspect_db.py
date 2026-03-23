import asyncio
from sqlalchemy import inspect
from app.db.database import AsyncSessionLocal

async def print_schema():
    async with AsyncSessionLocal() as session:
        def do_inspect(conn):
            inspector = inspect(conn)
            return {
                "courses": [c["name"] for c in inspector.get_columns("courses")],
                "entrance_exams": [c["name"] for c in inspector.get_columns("entrance_exams")],
                "lectures": [c["name"] for c in inspector.get_columns("lectures")]
            }
        
        async with session.bind.connect() as conn:
            cols = await conn.run_sync(do_inspect)
        import json
        with open("schema_out.json", "w") as f:
            json.dump(cols, f, indent=2)

if __name__ == "__main__":
    asyncio.run(print_schema())
