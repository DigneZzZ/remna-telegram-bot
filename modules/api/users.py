import logging
from modules.api.client import RemnaAPI
import re

logger = logging.getLogger(__name__)

class UserAPI:
    """API client for user operations"""
    
    @staticmethod
    async def get_all_users():
        """Get all users with pagination support"""
        all_users = []
        start = 0
        size = 500  # Maximum allowed by API
        
        while True:
            # Get batch of users
            params = {
                'size': size,
                'start': start
            }
            
            try:
                response = await RemnaAPI.get("users", params=params)
                
                if not response:
                    break
                
                # Handle different response structures
                users = []
                if isinstance(response, dict):
                    if 'users' in response:
                        users = response['users']
                    elif 'response' in response and 'users' in response['response']:
                        users = response['response']['users']
                elif isinstance(response, list):
                    users = response
                
                if not users:
                    break
                
                all_users.extend(users)
                
                # If we got less than requested size, we've reached the end
                if len(users) < size:
                    break
                
                start += size
                
            except Exception as e:
                logger.error(f"Error fetching users batch (start={start}, size={size}): {e}")
                break
        
        logger.info(f"Retrieved {len(all_users)} users total")
        return {'users': all_users} if all_users else []
    
    @staticmethod
    async def get_users_count():
        """Get total number of users efficiently"""
        try:
            # Try to get just first page to check total count
            params = {'size': 1, 'start': 0}
            response = await RemnaAPI.get("users", params=params)
            
            if response and isinstance(response, dict):
                # If API returns total count in response
                if 'total' in response:
                    return response['total']
                elif 'count' in response:
                    return response['count']
            
            # Fallback: get all users and count them
            all_users_response = await UserAPI.get_all_users()
            if all_users_response:
                users = []
                if isinstance(all_users_response, dict) and 'users' in all_users_response:
                    users = all_users_response['users']
                elif isinstance(all_users_response, list):
                    users = all_users_response
                return len(users)
            
            return 0
        except Exception as e:
            logger.error(f"Error getting users count: {e}")
            return 0
    
    @staticmethod
    async def get_user_by_uuid(uuid):
        """Get user by UUID"""
        return await RemnaAPI.get(f"users/{uuid}")
    
    @staticmethod
    async def get_user_by_short_uuid(short_uuid):
        """Get user by short UUID"""
        return await RemnaAPI.get(f"users/by-short-uuid/{short_uuid}")
    
    @staticmethod
    async def get_user_by_subscription_uuid(subscription_uuid):
        """Get user by subscription UUID"""
        return await RemnaAPI.get(f"users/by-subscription-uuid/{subscription_uuid}")
    
    @staticmethod
    async def get_user_by_username(username):
        """Get user by username"""
        return await RemnaAPI.get(f"users/by-username/{username}")
    
    @staticmethod
    async def get_user_by_telegram_id(telegram_id):
        """Get user by Telegram ID"""
        result = await RemnaAPI.get(f"users/by-telegram-id/{telegram_id}")
        return result if result else []
    
    @staticmethod
    async def get_user_by_email(email):
        """Get user by email"""
        result = await RemnaAPI.get(f"users/by-email/{email}")
        return result if result else []
    
    @staticmethod
    async def get_user_by_tag(tag):
        """Get user by tag"""
        result = await RemnaAPI.get(f"users/by-tag/{tag}")
        return result if result else []
    
    @staticmethod
    async def create_user(user_data):
        """Create a new user"""
        # Validate required fields
        required_fields = ["username", "trafficLimitStrategy", "expireAt"]
        for field in required_fields:
            if field not in user_data:
                logger.error(f"Missing required field: {field}")
                return None
        
        # Validate username format
        if not re.match(r"^[a-zA-Z0-9_-]{6,34}$", user_data["username"]):
            logger.error(f"Invalid username format: {user_data['username']}")
            return None
            
        # Validate tag format if provided
        if "tag" in user_data and user_data["tag"] and not re.match(r"^[A-Z0-9_]{1,16}$", user_data["tag"]):
            logger.error(f"Invalid tag format: {user_data['tag']}")
            return None
            
        # Если установлен лимит устройств, убедимся что стратегия трафика корректная (NO_RESET)
        if "hwidDeviceLimit" in user_data and user_data.get("hwidDeviceLimit", 0) > 0:
            if user_data.get("trafficLimitStrategy") != "NO_RESET":
                logger.warning(f"Changing trafficLimitStrategy to NO_RESET because hwidDeviceLimit is set to {user_data['hwidDeviceLimit']}")
                user_data["trafficLimitStrategy"] = "NO_RESET"
        
        # Validate traffic limit strategy
        valid_strategies = ["NO_RESET", "DAY", "WEEK", "MONTH"]
        logger.info(f"Traffic limit strategy value: '{user_data.get('trafficLimitStrategy')}'")
        if user_data["trafficLimitStrategy"] not in valid_strategies:
            logger.error(f"Invalid traffic limit strategy: '{user_data['trafficLimitStrategy']}'")
            return None
        
        # Validate numeric fields
        if "trafficLimitBytes" in user_data and user_data["trafficLimitBytes"] < 0:
            logger.error(f"Invalid traffic limit: {user_data['trafficLimitBytes']}")
            return None
            
        if "hwidDeviceLimit" in user_data and user_data["hwidDeviceLimit"] < 0:
            logger.error(f"Invalid HWID device limit: {user_data['hwidDeviceLimit']}")
            return None
        
        # Validate email format if provided
        if "email" in user_data and user_data["email"]:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user_data["email"]):
                logger.error(f"Invalid email format: {user_data['email']}")
                return None
        
        # Log data for debugging
        logger.debug(f"Creating user with data: {user_data}")
        
        # Дополнительная проверка перед отправкой
        if "hwidDeviceLimit" in user_data and user_data.get("hwidDeviceLimit", 0) > 0:
            # Убедимся, что при наличии лимита устройств стратегия всегда NO_RESET
            if user_data.get("trafficLimitStrategy") != "NO_RESET":
                logger.warning(f"Final correction: Setting trafficLimitStrategy=NO_RESET for user with hwidDeviceLimit={user_data['hwidDeviceLimit']}")
                user_data["trafficLimitStrategy"] = "NO_RESET"
        
        # Финальное логирование перед отправкой
        logger.info(f"Final user data before API request: trafficLimitStrategy='{user_data.get('trafficLimitStrategy')}', hwidDeviceLimit={user_data.get('hwidDeviceLimit', 'Not set')}")
        
        return await RemnaAPI.post("users", user_data)
    
    @staticmethod
    async def update_user(uuid, update_data):
        """Update a user"""
        # Добавляем UUID в данные обновления
        update_data["uuid"] = uuid
        
        # Логируем данные для отладки
        logger.debug(f"Updating user {uuid} with data: {update_data}")
        
        return await RemnaAPI.patch("users", update_data)
    
    @staticmethod
    async def delete_user(uuid):
        """Delete a user"""
        return await RemnaAPI.delete(f"users/{uuid}")
    
    @staticmethod
    async def revoke_user_subscription(uuid):
        """Revoke user subscription"""
        return await RemnaAPI.post(f"users/{uuid}/actions/revoke")
    
    @staticmethod
    async def disable_user(uuid):
        """Disable a user"""
        return await RemnaAPI.patch("users", {"uuid": uuid, "status": "DISABLED"})
    
    @staticmethod
    async def enable_user(uuid):
        """Enable a user"""
        return await RemnaAPI.patch("users", {"uuid": uuid, "status": "ACTIVE"})
    
    @staticmethod
    async def reset_user_traffic(uuid):
        """Reset user traffic"""
        return await RemnaAPI.post(f"users/{uuid}/actions/reset-traffic")
    
    @staticmethod
    async def activate_all_inbounds(uuid):
        """Activate all inbounds for a user"""
        return await RemnaAPI.post(f"users/{uuid}/actions/activate-all-inbounds")
    
    @staticmethod
    async def get_user_usage_by_range(uuid, start_date, end_date):
        """Get user usage by date range"""
        params = {
            "start": start_date,
            "end": end_date
        }
        return await RemnaAPI.get(f"users/stats/usage/{uuid}/range", params)
    
    @staticmethod
    async def get_user_hwid_devices(uuid):
        """Get user HWID devices"""
        return await RemnaAPI.get(f"hwid/devices/{uuid}")
    
    @staticmethod
    async def add_user_hwid_device(uuid, hwid, platform=None, os_version=None, device_model=None, user_agent=None):
        """Add a HWID device to a user"""
        data = {
            "userUuid": uuid,
            "hwid": hwid
        }
        
        if platform:
            data["platform"] = platform
        
        if os_version:
            data["osVersion"] = os_version
        
        if device_model:
            data["deviceModel"] = device_model
        
        if user_agent:
            data["userAgent"] = user_agent
        
        return await RemnaAPI.post("hwid/devices", data)
    
    @staticmethod
    async def delete_user_hwid_device(uuid, hwid):
        """Delete a HWID device from a user"""
        data = {
            "userUuid": uuid,
            "hwid": hwid
        }
        
        return await RemnaAPI.post("hwid/devices/delete", data)
    
    @staticmethod
    async def search_users_by_partial_name(partial_name):
        """Search users by partial name match"""
        try:
            response = await UserAPI.get_all_users()
            if not response:
                return []
            
            # Обрабатываем разные структуры ответа
            users = []
            if isinstance(response, dict):
                if 'users' in response:
                    users = response['users']
                elif 'response' in response and 'users' in response['response']:
                    users = response['response']['users']
            elif isinstance(response, list):
                users = response
            
            if not users:
                return []
            
            partial_name_lower = partial_name.lower()
            matching_users = []
            
            for user in users:
                if partial_name_lower in user.get("username", "").lower():
                    matching_users.append(user)
            
            return matching_users
        except Exception as e:
            logger.error(f"Error searching users by partial name: {e}")
            return []
    
    @staticmethod
    async def search_users_by_description(description_keyword):
        """Search users by description keyword"""
        try:
            response = await UserAPI.get_all_users()
            if not response:
                return []
            
            # Обрабатываем разные структуры ответа
            users = []
            if isinstance(response, dict):
                if 'users' in response:
                    users = response['users']
                elif 'response' in response and 'users' in response['response']:
                    users = response['response']['users']
            elif isinstance(response, list):
                users = response
            
            if not users:
                return []
            
            keyword_lower = description_keyword.lower()
            matching_users = []
            
            for user in users:
                user_description = user.get("description", "")
                if user_description and keyword_lower in user_description.lower():
                    matching_users.append(user)
            
            return matching_users
        except Exception as e:
            logger.error(f"Error searching users by description: {e}")
            return []
    
    @staticmethod
    async def get_users_stats():
        """Get user statistics efficiently"""
        try:
            # For now, we need to get all users to calculate stats
            # TODO: Optimize when API provides stats endpoint
            response = await UserAPI.get_all_users()
            
            stats = {'ACTIVE': 0, 'DISABLED': 0, 'LIMITED': 0, 'EXPIRED': 0}
            total_traffic = 0
            
            if response:
                users = []
                if isinstance(response, dict) and 'users' in response:
                    users = response['users']
                elif isinstance(response, list):
                    users = response
                
                for user in users:
                    status = user.get('status', 'UNKNOWN')
                    if status in stats:
                        stats[status] += 1
                    
                    # Calculate traffic
                    traffic_used = user.get('trafficUsed', 0)
                    if isinstance(traffic_used, (int, float)):
                        total_traffic += traffic_used
            
            return {
                'count': len(users) if 'users' in locals() else 0,
                'stats': stats,
                'total_traffic': total_traffic
            }
        except Exception as e:
            logger.error(f"Error getting users stats: {e}")
            return {
                'count': 0,
                'stats': {'ACTIVE': 0, 'DISABLED': 0, 'LIMITED': 0, 'EXPIRED': 0},
                'total_traffic': 0
            }
