from modules.api.client import RemnaAPI

class BulkAPI:
    """API methods for bulk operations"""
    
    @staticmethod
    async def bulk_delete_users_by_status(status):
        """Bulk delete users by status"""
        data = {"status": status}
        return await RemnaAPI.post("users/bulk/delete-by-status", data)
    
    @staticmethod
    async def bulk_delete_users(uuids):
        """Bulk delete users by UUIDs"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/delete", data)
    
    @staticmethod
    async def bulk_revoke_users_subscription(uuids):
        """Bulk revoke users subscription by UUIDs"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/revoke-subscription", data)
    
    @staticmethod
    async def bulk_reset_user_traffic(uuids):
        """Bulk reset traffic for users by UUIDs"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("users/bulk/reset-traffic", data)
    
    @staticmethod
    async def bulk_update_users(uuids, fields):
        """Bulk update users by UUIDs"""
        data = {
            "uuids": uuids,
            "fields": fields
        }
        return await RemnaAPI.post("users/bulk/update", data)
    
    @staticmethod
    async def bulk_update_users_inbounds(uuids, inbounds):
        """Bulk update users inbounds by UUIDs"""
        data = {
            "uuids": uuids,
            "activeUserInbounds": inbounds
        }
        return await RemnaAPI.post("users/bulk/update-inbounds", data)
    
    @staticmethod
    async def bulk_update_all_users(fields):
        """Bulk update all users"""
        return await RemnaAPI.post("users/bulk/all/update", fields)
    
    @staticmethod
    async def bulk_reset_all_users_traffic():
        """Bulk reset all users traffic"""
        return await RemnaAPI.post("users/bulk/all/reset-traffic")
