"""
Улучшенный API клиент для Aiogram с полной поддержкой SDK
"""
import logging
from remnawave_api import RemnawaveSDK
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

class RemnaSDK:
    """Современный API клиент с полной поддержкой SDK"""
    
    _sdk = None
    
    @classmethod
    def get_sdk(cls):
        """Получить или создать экземпляр SDK"""
        if cls._sdk is None:
            if not API_TOKEN or not API_BASE_URL:
                raise ValueError("API_TOKEN и API_BASE_URL должны быть настроены")
            
            cls._sdk = RemnawaveSDK(base_url=API_BASE_URL, token=API_TOKEN)
            logger.info(f"Инициализирован RemnawaveSDK: {API_BASE_URL}")
        return cls._sdk
    
    # =============================================================================
    # USERS API
    # =============================================================================
    
    @classmethod
    async def get_all_users(cls, **kwargs):
        """Получить всех пользователей"""
        sdk = cls.get_sdk()
        response = await sdk.users.get_all_users_v2(**kwargs)
        return {
            'total': response.total,
            'users': [user.model_dump() for user in response.users]
        }
    
    @classmethod
    async def get_user_by_uuid(cls, uuid: str):
        """Получить пользователя по UUID"""
        sdk = cls.get_sdk()
        user = await sdk.users.get_user_by_uuid(uuid)
        return user.model_dump() if user else None
    
    @classmethod
    async def create_user(cls, user_data: dict):
        """Создать пользователя"""
        sdk = cls.get_sdk()
        user = await sdk.users.create_user(**user_data)
        return user.model_dump()
    
    @classmethod
    async def update_user(cls, uuid: str, update_data: dict):
        """Обновить пользователя"""
        sdk = cls.get_sdk()
        user = await sdk.users.update_user(uuid, **update_data)
        return user.model_dump()
    
    @classmethod
    async def delete_user(cls, uuid: str):
        """Удалить пользователя"""
        sdk = cls.get_sdk()
        result = await sdk.users.delete_user(uuid)
        return result
    
    @classmethod
    async def reset_user_traffic(cls, uuid: str):
        """Сбросить трафик пользователя"""
        sdk = cls.get_sdk()
        result = await sdk.users.reset_user_traffic(uuid)
        return result
    
    @classmethod
    async def revoke_user_subscription(cls, uuid: str):
        """Отозвать подписку пользователя"""
        sdk = cls.get_sdk()
        result = await sdk.users.revoke_user_subscription(uuid)
        return result
    
    # =============================================================================
    # NODES API
    # =============================================================================
    
    @classmethod
    async def get_all_nodes(cls):
        """Получить все ноды"""
        sdk = cls.get_sdk()
        nodes = await sdk.nodes.get_all_nodes()
        return [node.model_dump() for node in nodes]
    
    @classmethod
    async def get_node_by_uuid(cls, uuid: str):
        """Получить ноду по UUID"""
        sdk = cls.get_sdk()
        node = await sdk.nodes.get_node_by_uuid(uuid)
        return node.model_dump() if node else None
    
    @classmethod
    async def create_node(cls, node_data: dict):
        """Создать ноду"""
        sdk = cls.get_sdk()
        node = await sdk.nodes.create_node(**node_data)
        return node.model_dump()
    
    @classmethod
    async def update_node(cls, uuid: str, update_data: dict):
        """Обновить ноду"""
        sdk = cls.get_sdk()
        node = await sdk.nodes.update_node(uuid, **update_data)
        return node.model_dump()
    
    @classmethod
    async def delete_node(cls, uuid: str):
        """Удалить ноду"""
        sdk = cls.get_sdk()
        result = await sdk.nodes.delete_node(uuid)
        return result
    
    @classmethod
    async def enable_node(cls, uuid: str):
        """Включить ноду"""
        sdk = cls.get_sdk()
        node = await sdk.nodes.enable_node(uuid)
        return node.model_dump()
    
    @classmethod
    async def disable_node(cls, uuid: str):
        """Отключить ноду"""
        sdk = cls.get_sdk()
        node = await sdk.nodes.disable_node(uuid)
        return node.model_dump()
    
    @classmethod
    async def restart_node(cls, uuid: str):
        """Перезапустить ноду"""
        sdk = cls.get_sdk()
        result = await sdk.nodes.restart_node(uuid)
        return result
    
    @classmethod
    async def get_nodes_usage(cls):
        """Получить статистику использования нод"""
        sdk = cls.get_sdk()
        usage = await sdk.nodes.get_nodes_usage()
        return [u.model_dump() for u in usage]
    
    @classmethod
    async def get_node_certificate(cls, uuid: str = None):
        """Получить сертификат ноды"""
        sdk = cls.get_sdk()
        if uuid:
            cert = await sdk.nodes.get_node_certificate(uuid)
        else:
            # Получить общий сертификат панели
            cert = await sdk.nodes.get_panel_certificate()
        return cert.model_dump()
    
    # =============================================================================
    # INBOUNDS API
    # =============================================================================
    
    @classmethod
    async def get_all_inbounds(cls):
        """Получить все inbound'ы"""
        sdk = cls.get_sdk()
        inbounds = await sdk.inbounds.get_all_inbounds()
        return [inbound.model_dump() for inbound in inbounds]
    
    @classmethod
    async def get_inbound_by_uuid(cls, uuid: str):
        """Получить inbound по UUID"""
        sdk = cls.get_sdk()
        inbound = await sdk.inbounds.get_inbound_by_uuid(uuid)
        return inbound.model_dump() if inbound else None
    
    @classmethod
    async def create_inbound(cls, inbound_data: dict):
        """Создать inbound"""
        sdk = cls.get_sdk()
        inbound = await sdk.inbounds.create_inbound(**inbound_data)
        return inbound.model_dump()
    
    @classmethod
    async def update_inbound(cls, uuid: str, update_data: dict):
        """Обновить inbound"""
        sdk = cls.get_sdk()
        inbound = await sdk.inbounds.update_inbound(uuid, **update_data)
        return inbound.model_dump()
    
    @classmethod
    async def delete_inbound(cls, uuid: str):
        """Удалить inbound"""
        sdk = cls.get_sdk()
        result = await sdk.inbounds.delete_inbound(uuid)
        return result
    
    # =============================================================================
    # HOSTS API
    # =============================================================================
    
    @classmethod
    async def get_all_hosts(cls):
        """Получить все хосты"""
        sdk = cls.get_sdk()
        hosts = await sdk.hosts.get_all_hosts()
        return [host.model_dump() for host in hosts]
    
    @classmethod
    async def get_host_by_uuid(cls, uuid: str):
        """Получить хост по UUID"""
        sdk = cls.get_sdk()
        host = await sdk.hosts.get_host_by_uuid(uuid)
        return host.model_dump() if host else None
    
    @classmethod
    async def create_host(cls, host_data: dict):
        """Создать хост"""
        sdk = cls.get_sdk()
        host = await sdk.hosts.create_host(**host_data)
        return host.model_dump()
    
    @classmethod
    async def update_host(cls, uuid: str, update_data: dict):
        """Обновить хост"""
        sdk = cls.get_sdk()
        host = await sdk.hosts.update_host(uuid, **update_data)
        return host.model_dump()
    
    @classmethod
    async def delete_host(cls, uuid: str):
        """Удалить хост"""
        sdk = cls.get_sdk()
        result = await sdk.hosts.delete_host(uuid)
        return result
    
    @classmethod
    async def enable_host(cls, uuid: str):
        """Включить хост"""
        sdk = cls.get_sdk()
        host = await sdk.hosts.enable_host(uuid)
        return host.model_dump()
    
    @classmethod
    async def disable_host(cls, uuid: str):
        """Отключить хост"""
        sdk = cls.get_sdk()
        host = await sdk.hosts.disable_host(uuid)
        return host.model_dump()
    
    # =============================================================================
    # SYSTEM API
    # =============================================================================
    
    @classmethod
    async def get_system_stats(cls):
        """Получить системную статистику"""
        sdk = cls.get_sdk()
        stats = await sdk.system.get_system_stats()
        return stats.model_dump()
    
    @classmethod
    async def get_system_health(cls):
        """Получить состояние системы"""
        sdk = cls.get_sdk()
        health = await sdk.system.get_system_health()
        return health.model_dump()
    
    # =============================================================================
    # BULK API
    # =============================================================================
    
    @classmethod
    async def bulk_reset_traffic(cls, user_uuids: list = None):
        """Массовый сброс трафика"""
        sdk = cls.get_sdk()
        if user_uuids:
            # Сброс для конкретных пользователей
            result = await sdk.users.bulk_reset_traffic(user_uuids)
        else:
            # Сброс для всех пользователей
            result = await sdk.users.bulk_reset_all_traffic()
        return result
    
    @classmethod
    async def bulk_delete_users(cls, user_uuids: list):
        """Массовое удаление пользователей"""
        sdk = cls.get_sdk()
        result = await sdk.users.bulk_delete_users(user_uuids)
        return result
    
    @classmethod
    async def bulk_delete_inactive_users(cls):
        """Удалить всех неактивных пользователей"""
        sdk = cls.get_sdk()
        result = await sdk.users.bulk_delete_inactive_users()
        return result
    
    @classmethod
    async def bulk_delete_expired_users(cls):
        """Удалить всех пользователей с истекшим сроком"""
        sdk = cls.get_sdk()
        result = await sdk.users.bulk_delete_expired_users()
        return result
