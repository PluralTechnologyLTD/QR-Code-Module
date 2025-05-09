from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client["QRCode"]


def get_database():
    return db


async def insert_dummy_data(db):
    existing = await db["projects"].count_documents({})
    if existing == 0:
        dummy_projects = [
            {
                "project_name": "Project A",
                "fov": 90,
                "models_used": ["Model A", "Model B"],
                "timestamp": None,
            },
            {
                "project_name": "Project B",
                "fov": 60,
                "models_used": ["Model C", "Model D"],
                "timestamp": None,
            },
            {
                "project_name": "Project C",
                "fov": 120,
                "models_used": ["Model E", "Model F"],
                "timestamp": None,
            },
        ]
        await db["projects"].insert_many(dummy_projects)
