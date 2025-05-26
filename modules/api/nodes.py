from modules.api.client import RemnaAPI
import logging

logger = logging.getLogger(__name__)

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
        """Enable a node using direct PATCH endpoint"""
        data = {"uuid": uuid, "isDisabled": False}
        return await RemnaAPI.patch("nodes", data)
    
    @staticmethod
    async def disable_node(uuid):
        """Disable a node using direct PATCH endpoint"""
        data = {"uuid": uuid, "isDisabled": True}
        return await RemnaAPI.patch("nodes", data)
    
    @staticmethod
    async def restart_node(uuid):
        """Restart a node"""
        return await RemnaAPI.post(f"nodes/{uuid}/actions/restart")
    
    @staticmethod
    async def restart_all_nodes():
        """Restart all nodes"""
        return await RemnaAPI.post("nodes/actions/restart")
    
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
        logger.info("Requesting nodes realtime usage from API")
        result = await RemnaAPI.get("nodes/usage/realtime")
        logger.info(f"Nodes realtime usage API response: {result}")
        return result
    
    @staticmethod
    async def get_nodes_usage_by_range(start_date, end_date):
        """Get nodes usage by date range"""
        params = {
            "start": start_date,
            "end": end_date
        }
        return await RemnaAPI.get("nodes/usage/range", params)
    
    @staticmethod
    async def add_inbound_to_all_nodes(inbound_uuid):
        """Add inbound to all nodes"""
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post("inbounds/bulk/add-to-nodes", data)
    
    @staticmethod
    async def remove_inbound_from_all_nodes(inbound_uuid):
        """Remove inbound from all nodes"""
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post("inbounds/bulk/remove-from-nodes", data)
        
    @staticmethod
    async def get_node_certificate():
        """Get panel public key for node certificate"""
        return await RemnaAPI.get("keygen")
        
    @staticmethod
    async def add_inbound_to_node(node_uuid, inbound_uuid):
        """Add inbound to specific node"""
        data = {"inboundUuid": inbound_uuid}
        return await RemnaAPI.post(f"nodes/{node_uuid}/inbounds", data)
    @staticmethod
    async def get_nodes_stats():
        """Get nodes statistics"""
        try:
            logger.info("Requesting nodes stats from API")
            
            # Use existing get_all_nodes method
            nodes = await NodeAPI.get_all_nodes()
            
            if not nodes:
                logger.warning("No nodes data returned")
                return []
                
            # Transform nodes data to stats format
            stats_data = []
            for node in nodes:
                stats_data.append({
                    'name': node.get('name', 'Unknown'),
                    'status': node.get('status', 'disconnected'),
                    'uptime': node.get('uptime', 'N/A'),
                    'id': node.get('id'),
                    'address': node.get('address'),
                    'usage_coefficient': node.get('usageCoefficient', 1.0),
                    'version': node.get('version', 'Unknown'),
                    'last_connected_at': node.get('lastConnectedAt')
                })
                
            logger.info(f"Processed {len(stats_data)} nodes for stats")
            return stats_data
            
        except Exception as e:
            logger.error(f"Error getting nodes stats: {e}", exc_info=True)
            return None