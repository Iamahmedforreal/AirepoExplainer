import asyncio
from app.models.users import create_db_and_tables

async def main():
    await create_db_and_tables()
    print("Database tables created/migrated successfully.")

if __name__ == "__main__":
    asyncio.run(main())