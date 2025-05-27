import logging
from typing import Dict, Any, List, Optional, Union
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)

class BulkAPI:
    """API methods for bulk operations"""
    
    @staticmethod
    async def bulk_delete_users_by_status(status: str) -> Optional[Dict[str, Any]]:
        """Bulk delete users by status
        
        Args:
            status: User status to filter by (ACTIVE, INACTIVE, etc.)
            
        Returns:
            Result of bulk deletion or None if error
        """
        try:
            if not status:
                logger.error("Status is required for bulk delete by status")
                return None
                
            logger.info(f"Bulk deleting users with status: {status}")
            data = {"status": status.upper()}
            result = await RemnaAPI.post("users/bulk/delete-by-status", json=data)
            
            if result:
                logger.info(f"Bulk delete by status completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk delete users by status: {e}")
            return None
    
    @staticmethod
    async def bulk_delete_users(uuids: List[str]) -> Optional[Dict[str, Any]]:
        """Bulk delete users by UUIDs
        
        Args:
            uuids: List of user UUIDs to delete
            
        Returns:
            Result of bulk deletion or None if error
        """
        try:
            if not uuids or not isinstance(uuids, list):
                logger.error("UUIDs list is required for bulk delete")
                return None
            
            if len(uuids) == 0:
                logger.warning("Empty UUIDs list provided")
                return {"deleted": 0, "message": "No users to delete"}
                
            logger.info(f"Bulk deleting {len(uuids)} users")
            data = {"uuids": uuids}
            result = await RemnaAPI.post("users/bulk/delete", json=data)
            
            if result:
                logger.info(f"Bulk delete completed successfully for {len(uuids)} users")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk delete users: {e}")
            return None
    
    @staticmethod
    async def bulk_revoke_users_subscription(uuids: List[str]) -> Optional[Dict[str, Any]]:
        """Bulk revoke users subscription by UUIDs
        
        Args:
            uuids: List of user UUIDs to revoke subscription
            
        Returns:
            Result of bulk revocation or None if error
        """
        try:
            if not uuids or not isinstance(uuids, list):
                logger.error("UUIDs list is required for bulk revoke subscription")
                return None
            
            if len(uuids) == 0:
                logger.warning("Empty UUIDs list provided")
                return {"revoked": 0, "message": "No users to revoke"}
                
            logger.info(f"Bulk revoking subscription for {len(uuids)} users")
            data = {"uuids": uuids}
            result = await RemnaAPI.post("users/bulk/revoke-subscription", json=data)
            
            if result:
                logger.info(f"Bulk revoke subscription completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk revoke users subscription: {e}")
            return None
    
    @staticmethod
    async def bulk_reset_user_traffic(uuids: List[str]) -> Optional[Dict[str, Any]]:
        """Bulk reset traffic for users by UUIDs
        
        Args:
            uuids: List of user UUIDs to reset traffic
            
        Returns:
            Result of bulk traffic reset or None if error
        """
        try:
            if not uuids or not isinstance(uuids, list):
                logger.error("UUIDs list is required for bulk reset traffic")
                return None
            
            if len(uuids) == 0:
                logger.warning("Empty UUIDs list provided")
                return {"reset": 0, "message": "No users to reset traffic"}
                
            logger.info(f"Bulk resetting traffic for {len(uuids)} users")
            data = {"uuids": uuids}
            result = await RemnaAPI.post("users/bulk/reset-traffic", json=data)
            
            if result:
                logger.info(f"Bulk traffic reset completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk reset user traffic: {e}")
            return None
    
    @staticmethod
    async def bulk_update_users(uuids: List[str], fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Bulk update users by UUIDs
        
        Args:
            uuids: List of user UUIDs to update
            fields: Dictionary of fields to update
            
        Returns:
            Result of bulk update or None if error
        """
        try:
            if not uuids or not isinstance(uuids, list):
                logger.error("UUIDs list is required for bulk update")
                return None
            
            if not fields or not isinstance(fields, dict):
                logger.error("Fields dictionary is required for bulk update")
                return None
            
            if len(uuids) == 0:
                logger.warning("Empty UUIDs list provided")
                return {"updated": 0, "message": "No users to update"}
                
            logger.info(f"Bulk updating {len(uuids)} users with fields: {list(fields.keys())}")
            data = {
                "uuids": uuids,
                "fields": fields
            }
            result = await RemnaAPI.post("users/bulk/update", json=data)
            
            if result:
                logger.info(f"Bulk update completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk update users: {e}")
            return None
    
    @staticmethod
    async def bulk_update_users_inbounds(uuids: List[str], inbounds: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Bulk update users inbounds by UUIDs
        
        Args:
            uuids: List of user UUIDs to update
            inbounds: List of inbound configurations
            
        Returns:
            Result of bulk inbounds update or None if error
        """
        try:
            if not uuids or not isinstance(uuids, list):
                logger.error("UUIDs list is required for bulk inbounds update")
                return None
            
            if not isinstance(inbounds, list):
                logger.error("Inbounds must be a list")
                return None
            
            if len(uuids) == 0:
                logger.warning("Empty UUIDs list provided")
                return {"updated": 0, "message": "No users to update"}
                
            logger.info(f"Bulk updating inbounds for {len(uuids)} users")
            data = {
                "uuids": uuids,
                "activeUserInbounds": inbounds
            }
            result = await RemnaAPI.post("users/bulk/update-inbounds", json=data)
            
            if result:
                logger.info(f"Bulk inbounds update completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk update users inbounds: {e}")
            return None
    
    @staticmethod
    async def bulk_update_all_users(fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Bulk update all users
        
        Args:
            fields: Dictionary of fields to update for all users
            
        Returns:
            Result of bulk update or None if error
        """
        try:
            if not fields or not isinstance(fields, dict):
                logger.error("Fields dictionary is required for bulk update all users")
                return None
                
            logger.info(f"Bulk updating ALL users with fields: {list(fields.keys())}")
            logger.warning("This operation will affect ALL users in the system!")
            
            result = await RemnaAPI.post("users/bulk/all/update", json=fields)
            
            if result:
                logger.info(f"Bulk update all users completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk update all users: {e}")
            return None
    
    @staticmethod
    async def bulk_reset_all_users_traffic() -> Optional[Dict[str, Any]]:
        """Bulk reset all users traffic
        
        Returns:
            Result of bulk traffic reset or None if error
        """
        try:
            logger.info("Bulk resetting traffic for ALL users")
            logger.warning("This operation will reset traffic for ALL users in the system!")
            
            result = await RemnaAPI.post("users/bulk/all/reset-traffic")
            
            if result:
                logger.info("Bulk reset all users traffic completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk reset all users traffic: {e}")
            return None
    
    @staticmethod
    async def bulk_enable_users(uuids: List[str]) -> Optional[Dict[str, Any]]:
        """Bulk enable users by UUIDs
        
        Args:
            uuids: List of user UUIDs to enable
            
        Returns:
            Result of bulk enable or None if error
        """
        try:
            if not uuids or not isinstance(uuids, list):
                logger.error("UUIDs list is required for bulk enable")
                return None
            
            if len(uuids) == 0:
                logger.warning("Empty UUIDs list provided")
                return {"enabled": 0, "message": "No users to enable"}
                
            logger.info(f"Bulk enabling {len(uuids)} users")
            data = {"uuids": uuids}
            result = await RemnaAPI.post("users/bulk/enable", json=data)
            
            if result:
                logger.info(f"Bulk enable completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk enable users: {e}")
            return None
    
    @staticmethod
    async def bulk_disable_users(uuids: List[str]) -> Optional[Dict[str, Any]]:
        """Bulk disable users by UUIDs
        
        Args:
            uuids: List of user UUIDs to disable
            
        Returns:
            Result of bulk disable or None if error
        """
        try:
            if not uuids or not isinstance(uuids, list):
                logger.error("UUIDs list is required for bulk disable")
                return None
            
            if len(uuids) == 0:
                logger.warning("Empty UUIDs list provided")
                return {"disabled": 0, "message": "No users to disable"}
                
            logger.info(f"Bulk disabling {len(uuids)} users")
            data = {"uuids": uuids}
            result = await RemnaAPI.post("users/bulk/disable", json=data)
            
            if result:
                logger.info(f"Bulk disable completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk disable users: {e}")
            return None
    
    @staticmethod
    async def bulk_extend_users_expiry(uuids: List[str], days: int) -> Optional[Dict[str, Any]]:
        """Bulk extend users expiry by specified days
        
        Args:
            uuids: List of user UUIDs to extend
            days: Number of days to extend expiry
            
        Returns:
            Result of bulk extension or None if error
        """
        try:
            if not uuids or not isinstance(uuids, list):
                logger.error("UUIDs list is required for bulk extend expiry")
                return None
            
            if not isinstance(days, int) or days <= 0:
                logger.error("Days must be a positive integer")
                return None
            
            if len(uuids) == 0:
                logger.warning("Empty UUIDs list provided")
                return {"extended": 0, "message": "No users to extend"}
                
            logger.info(f"Bulk extending expiry for {len(uuids)} users by {days} days")
            data = {
                "uuids": uuids,
                "days": days
            }
            result = await RemnaAPI.post("users/bulk/extend-expiry", json=data)
            
            if result:
                logger.info(f"Bulk extend expiry completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk extend users expiry: {e}")
            return None

# Convenience функции для частых операций
async def delete_expired_users() -> Optional[Dict[str, Any]]:
    """Delete all expired users"""
    logger.info("Deleting all expired users")
    return await BulkAPI.bulk_delete_users_by_status("EXPIRED")

async def delete_inactive_users() -> Optional[Dict[str, Any]]:
    """Delete all inactive users"""
    logger.info("Deleting all inactive users")
    return await BulkAPI.bulk_delete_users_by_status("INACTIVE")

async def reset_all_traffic() -> Optional[Dict[str, Any]]:
    """Reset traffic for all users"""
    logger.info("Resetting traffic for all users")
    return await BulkAPI.bulk_reset_all_users_traffic()

async def extend_expiring_users(days: int = 30) -> Optional[Dict[str, Any]]:
    """Extend expiry for users expiring soon"""
    try:
        from modules.api.users import get_all_users
        from datetime import datetime, timedelta
        
        logger.info(f"Finding users expiring in the next {days} days")
        
        # Получаем всех пользователей
        users = await get_all_users()
        if not users:
            return {"extended": 0, "message": "No users found"}
        
        # Находим пользователей, которые истекают в ближайшие дни
        expiring_uuids = []
        now = datetime.now()
        cutoff_date = now + timedelta(days=days)
        
        for user in users:
            expire_at = user.get('expireAt')
            if expire_at:
                try:
                    expire_date = datetime.fromisoformat(expire_at.replace('Z', '').split('.')[0])
                    if now < expire_date < cutoff_date:
                        expiring_uuids.append(user.get('uuid'))
                except Exception:
                    continue
        
        if not expiring_uuids:
            return {"extended": 0, "message": f"No users expiring in the next {days} days"}
        
        logger.info(f"Found {len(expiring_uuids)} users expiring soon")
        return await BulkAPI.bulk_extend_users_expiry(expiring_uuids, days)
        
    except Exception as e:
        logger.error(f"Error extending expiring users: {e}")
        return None