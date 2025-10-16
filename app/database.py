from app.zenstack_client import zenstack_client
from app.config import settings
import asyncio

# ZenStack client instance (already initialized in zenstack_client.py)
async def get_zenstack_client():
    """Get ZenStack client instance"""
    return zenstack_client

async def init_database():
    """Initialize database connection"""
    # ZenStack client is already initialized
    # Just verify connection by making a test request
    try:
        # Test connection by getting users (this will fail gracefully if ZenStack service is down)
        await zenstack_client.get_users(skip=0, take=1)
        print("✅ ZenStack service connection verified")
    except Exception as e:
        print(f"⚠️ ZenStack service not available: {e}")
        print("Make sure ZenStack service is running on port 3001")

async def cleanup_database():
    """Cleanup database connection"""
    await zenstack_client.close()
