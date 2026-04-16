import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MDB_MCP_CONNECTION_STRING", "mongodb://localhost:27017")

print("Connecting to MongoDB...")
client = AsyncIOMotorClient(MONGO_URI)
db = client.solosync_db
