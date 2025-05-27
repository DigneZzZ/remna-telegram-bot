from modules.api.client import RemnaAPI

class HostAPI:
    """API methods for host management"""
    
    @staticmethod
    async def get_all_hosts():
        """Get all hosts"""
        return await RemnaAPI.get("hosts")
    
    @staticmethod
    async def get_host_by_uuid(uuid):
        """Get host by UUID"""
        return await RemnaAPI.get(f"hosts/{uuid}")
    
    @staticmethod
    async def create_host(data):
        """Create a new host"""
        return await RemnaAPI.post("hosts", data)
    
    @staticmethod
    async def update_host(uuid, data):
        """Update a host"""
        data["uuid"] = uuid
        return await RemnaAPI.patch("hosts", data)
    
    @staticmethod
    async def delete_host(uuid):
        """Delete a host"""
        return await RemnaAPI.delete(f"hosts/{uuid}")
    
    @staticmethod
    async def enable_host(uuid):
        """Enable a host using direct PATCH endpoint"""
        data = {"uuid": uuid, "isDisabled": False}
        return await RemnaAPI.patch("hosts", data)
    
    @staticmethod
    async def disable_host(uuid):
        """Disable a host using direct PATCH endpoint"""
        data = {"uuid": uuid, "isDisabled": True}
        return await RemnaAPI.patch("hosts", data)
    
    @staticmethod
    async def bulk_enable_hosts(uuids):
        """Bulk enable hosts by UUIDs"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/enable", data)
    
    @staticmethod
    async def bulk_disable_hosts(uuids):
        """Bulk disable hosts by UUIDs"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/disable", data)
    
    @staticmethod
    async def reorder_hosts(hosts_data):
        """Reorder hosts"""
        return await RemnaAPI.post("hosts/actions/reorder", {"hosts": hosts_data})
    
    @staticmethod
    async def bulk_delete_hosts(uuids):
        """Bulk delete hosts by UUIDs"""
        data = {"uuids": uuids}
        return await RemnaAPI.post("hosts/bulk/delete", data)
    
    @staticmethod
    async def bulk_set_inbound_to_hosts(uuids, inbound_uuid):
        """Set inbound to hosts by UUIDs"""
        data = {
            "uuids": uuids,
            "inboundUuid": inbound_uuid
        }
        return await RemnaAPI.post("hosts/bulk/set-inbound", data)
    
    @staticmethod
    async def bulk_set_port_to_hosts(uuids, port):
        """Set port to hosts by UUIDs"""
        data = {
            "uuids": uuids,
            "port": port
        }
        return await RemnaAPI.post("hosts/bulk/set-port", data)
