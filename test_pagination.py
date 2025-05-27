#!/usr/bin/env python3
"""
Test script for pagination functionality
"""
import sys
import os
import asyncio
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.api.users import UserAPI
from modules.config import API_BASE_URL

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pagination():
    """Test user pagination functionality"""
    print(f"Testing pagination with API: {API_BASE_URL}")
    
    try:
        # Test new paginated get_all_users
        print("\n=== Testing get_all_users() with pagination ===")
        users_response = await UserAPI.get_all_users()
        
        if users_response:
            users = []
            if isinstance(users_response, dict) and 'users' in users_response:
                users = users_response['users']
            elif isinstance(users_response, list):
                users = users_response
            
            print(f"Total users retrieved: {len(users)}")
            
            if users:
                print(f"First user: {users[0].get('username', 'Unknown')}")
                print(f"Last user: {users[-1].get('username', 'Unknown')}")
        else:
            print("No users found")
        
        # Test users count
        print("\n=== Testing get_users_count() ===")
        count = await UserAPI.get_users_count()
        print(f"Users count: {count}")
        
        # Test users stats
        print("\n=== Testing get_users_stats() ===")
        stats = await UserAPI.get_users_stats()
        print(f"Users stats: {stats}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pagination())
