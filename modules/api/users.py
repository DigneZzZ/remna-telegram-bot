import logging
from modules.api.client import RemnaAPI
from remnawave_api.models import UserResponseDto, UsersResponseDto

logger = logging.getLogger(__name__)

async def get_all_users():
    """Получить всех пользователей"""
    try:
        sdk = RemnaAPI.get_sdk()        # Используем правильный метод согласно OpenAPI схеме
        response: UsersResponseDto = await sdk.users.get_all_users_v2(start=0, size=1000)
        logger.info(f"Retrieved {response.total} users total")
        return response.users
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

async def get_user_by_uuid(user_uuid: str):
    """Получить пользователя по UUID"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        user: UserResponseDto = await sdk.users.get_user_by_uuid(uuid=user_uuid)
        logger.info(f"Retrieved user: {user.username}")
        return user
    except Exception as e:
        logger.error(f"Error getting user {user_uuid}: {e}")
        return None

async def enable_user(user_uuid: str):
    """Включить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        user: UserResponseDto = await sdk.users.enable_user(uuid=user_uuid)
        logger.info(f"Enabled user: {user.username}")
        return user
    except Exception as e:
        logger.error(f"Error enabling user {user_uuid}: {e}")
        return None

async def disable_user(user_uuid: str):
    """Отключить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        user: UserResponseDto = await sdk.users.disable_user(uuid=user_uuid)
        logger.info(f"Disabled user: {user.username}")
        return user
    except Exception as e:
        logger.error(f"Error disabling user {user_uuid}: {e}")
        return None

async def delete_user(user_uuid: str):
    """Удалить пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return False
            
        sdk = RemnaAPI.get_sdk()
        await sdk.users.delete_user(uuid=user_uuid)
        logger.info(f"Deleted user: {user_uuid}")
        return True
    except Exception as e:
        logger.error(f"Error deleting user {user_uuid}: {e}")
        return False

async def reset_user_traffic(user_uuid: str):
    """Сбросить трафик пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        user: UserResponseDto = await sdk.users.reset_user_traffic(uuid=user_uuid)
        logger.info(f"Reset traffic for user: {user.username}")
        return user
    except Exception as e:
        logger.error(f"Error resetting traffic for user {user_uuid}: {e}")
        return None

async def revoke_user_subscription(user_uuid: str):
    """Отозвать подписку пользователя"""
    try:
        if not user_uuid:
            logger.error("User UUID is empty or None")
            return None
            
        sdk = RemnaAPI.get_sdk()
        user: UserResponseDto = await sdk.users.revoke_user_subscription(uuid=user_uuid)
        logger.info(f"Revoked subscription for user: {user.username}")
        return user
    except Exception as e:
        logger.error(f"Error revoking subscription for user {user_uuid}: {e}")
        return None

async def get_users_count():
    """Получить количество пользователей"""
    try:
        sdk = RemnaAPI.get_sdk()
        response: UsersResponseDto = await sdk.users.get_all_users_v2(start=0, size=1)
        return response.total
    except Exception as e:
        logger.error(f"Error getting users count: {e}")
        return 0

async def get_users_stats():
    """Получить статистику пользователей"""
    try:
        sdk = RemnaAPI.get_sdk()
        response: UsersResponseDto = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        total_users = response.total
        active_users = 0
        
        # Подсчитываем активных пользователей
        for user in response.users:
            if hasattr(user, 'is_active') and user.is_active:
                active_users += 1
            elif hasattr(user, 'status') and user.status == 'active':
                active_users += 1
        
        return {
            'total': total_users,
            'active': active_users
        }
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        return None
