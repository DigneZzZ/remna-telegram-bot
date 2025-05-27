import logging
from modules.api.client import RemnaAPI
import re

logger = logging.getLogger(__name__)

class UserAPI:
    """API client for user operations"""
    
    @staticmethod
    async def get_all_users():
        """Get all users"""
        return await RemnaAPI.get("users")
    
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
