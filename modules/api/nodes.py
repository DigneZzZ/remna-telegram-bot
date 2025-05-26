from modules.api.client import RemnaAPI

class NodeAPI:
    """API methods for node management"""
    
    @staticmethod
    async def get_all_nodes():
        """Get all nodes"""
        return await RemnaAPI.get("nodes")
    
    @staticmethod
    async def get_node_by_uuid(uuid):
        """Get node by UUID"""
        return await RemnaAPI.get(f"nodes/{uuid}")
    
    @staticmethod
    async def create_node(data):
        """Create a new node"""
        return await RemnaAPI.post("nodes", data)
    
    @staticmethod
    async def update_node(uuid, data):
        """Update a node"""
        data["uuid"] = uuid
        return await RemnaAPI.patch("nodes", data)
    
    @staticmethod
    async def delete_node(uuid):
        """Delete a node"""
        return await RemnaAPI.delete(f"nodes/{uuid}")
    
    @staticmethod
    async def enable_node(uuid):
        """Enable a node"""
        return await RemnaAPI.post(f"nodes/{uuid}/actions/enable")
    
    @staticmethod
    async def disable_node(uuid):
        """Disable a node"""
        return await RemnaAPI.post(f"nodes/{uuid}/actions/disable")
    
    @staticmethod
    async def restart_node(uuid):
        """Restart a node"""
        return await RemnaAPI.post(f"nodes/{uuid}/actions/restart")
    
    @staticmethod
    async def restart_all_nodes():
        """Restart all nodes"""
        return await RemnaAPI.post("nodes/actions/restart-all")
    
    @staticmethod
    async def reorder_nodes(nodes_data):
        """Reorder nodes"""
        return await RemnaAPI.post("nodes/actions/reorder", {"nodes": nodes_data})
    
    @staticmethod
    async def get_node_usage_by_range(uuid, start_date, end_date):
        """Get node usage by date range"""
        params = {
            "start": start_date,
            "end": end_date
        }
        return await RemnaAPI.get(f"nodes/usage/{uuid}/users/range", params)
    
    @staticmethod
    async def get_nodes_realtime_usage():
        """Get nodes realtime usage"""
        return await RemnaAPI.get("nodes/usage/realtime")
    
    @staticmethod
    async def get_nodes_usage_by_range(start_date, end_date):
        """Get nodes usage by date range"""
        params = {
            "start": start_date,
            "end": end_date
        }
        return await RemnaAPI.get("nodes/usage/range", params)
