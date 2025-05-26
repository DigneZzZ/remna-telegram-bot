from modules.api.client import RemnaAPI

class InboundAPI:
    """API methods for inbound management"""
    
    @staticmethod
    async def get_inbounds():
        """Get all inbounds"""
        return await RemnaAPI.get("inbounds")
    
    @staticmethod
    async def get_full_inbounds():
        """Get inbounds with full details"""
        return await RemnaAPI.get("inbounds/full")
    
    @staticmethod
    async def add_inbound_to_users(inbound_uuid):
        """Add inbound to all users"""
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post("inbounds/bulk/add-to-users", data)
    
    @staticmethod
    async def remove_inbound_from_users(inbound_uuid):
        """Remove inbound from all users"""
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post("inbounds/bulk/remove-from-users", data)
    
    @staticmethod
    async def add_inbound_to_nodes(inbound_uuid):
        """Add inbound to all nodes"""
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post("inbounds/bulk/add-to-nodes", data)
    
    @staticmethod
    async def remove_inbound_from_nodes(inbound_uuid):
        """Remove inbound from all nodes"""
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post("inbounds/bulk/remove-from-nodes", data)
