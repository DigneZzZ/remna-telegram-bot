import logging
from typing import Dict, Any, Optional
from modules.api.client import RemnaAPI

logger = logging.getLogger(__name__)

class SystemAPI:
    """API methods for system management"""
    
    @staticmethod
    async def get_stats() -> Optional[Dict[str, Any]]:
        """Get system statistics
        
        Returns:
            Dict with system stats or None if error
        """
        try:
            logger.info("Getting system statistics...")
            result = await RemnaAPI.get("system/stats")
            if result:
                logger.info("System statistics retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return None
    
    @staticmethod
    async def get_bandwidth_stats() -> Optional[Dict[str, Any]]:
        """Get bandwidth statistics
        
        Returns:
            Dict with bandwidth stats or None if error
        """
        try:
            logger.info("Getting bandwidth statistics...")
            result = await RemnaAPI.get("system/stats/bandwidth")
            if result:
                logger.info("Bandwidth statistics retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Error getting bandwidth stats: {e}")
            return None
    
    @staticmethod
    async def get_nodes_statistics() -> Optional[Dict[str, Any]]:
        """Get nodes statistics
        
        Returns:
            Dict with nodes stats or None if error
        """
        try:
            logger.info("Getting nodes statistics...")
            result = await RemnaAPI.get("system/stats/nodes")
            if result:
                logger.info("Nodes statistics retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Error getting nodes stats: {e}")
            return None
    
    @staticmethod
    async def get_system_info() -> Optional[Dict[str, Any]]:
        """Get general system information
        
        Returns:
            Dict with system info or None if error
        """
        try:
            logger.info("Getting system information...")
            result = await RemnaAPI.get("system/info")
            if result:
                logger.info("System information retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return None
    
    @staticmethod
    async def get_system_health() -> Optional[Dict[str, Any]]:
        """Get system health status
        
        Returns:
            Dict with health status or None if error
        """
        try:
            logger.info("Getting system health status...")
            result = await RemnaAPI.get("system/health")
            if result:
                logger.info("System health status retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return None
    
    @staticmethod
    async def get_xray_config() -> Optional[Dict[str, Any]]:
        """Get XRay configuration
        
        Returns:
            Dict with XRay config or None if error
        """
        try:
            logger.info("Getting XRay configuration...")
            result = await RemnaAPI.get("xray")
            if result:
                logger.info("XRay configuration retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Error getting XRay config: {e}")
            return None
    
    @staticmethod
    async def update_xray_config(config_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update XRay configuration
        
        Args:
            config_data: Configuration data to update
            
        Returns:
            Updated config or None if error
        """
        try:
            if not isinstance(config_data, dict):
                logger.error("Config data must be a dictionary")
                return None
                
            logger.info("Updating XRay configuration...")
            result = await RemnaAPI.patch("xray", config_data)
            if result:
                logger.info("XRay configuration updated successfully")
            return result
        except Exception as e:
            logger.error(f"Error updating XRay config: {e}")
            return None
    
    @staticmethod
    async def restart_xray() -> bool:
        """Restart XRay service
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Restarting XRay service...")
            result = await RemnaAPI.post("xray/restart")
            if result:
                logger.info("XRay service restarted successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error restarting XRay: {e}")
            return False
    
    @staticmethod
    async def get_logs(lines: int = 100, level: str = "info") -> Optional[Dict[str, Any]]:
        """Get system logs
        
        Args:
            lines: Number of log lines to retrieve
            level: Log level filter (debug, info, warn, error)
            
        Returns:
            Dict with logs or None if error
        """
        try:
            logger.info(f"Getting system logs (lines: {lines}, level: {level})")
            params = {"lines": lines, "level": level}
            result = await RemnaAPI.get("system/logs", params=params)
            if result:
                logger.info("System logs retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return None
    
    @staticmethod
    async def get_usage_stats(period: str = "24h") -> Optional[Dict[str, Any]]:
        """Get usage statistics for a period
        
        Args:
            period: Time period (1h, 24h, 7d, 30d)
            
        Returns:
            Dict with usage stats or None if error
        """
        try:
            logger.info(f"Getting usage statistics for period: {period}")
            params = {"period": period}
            result = await RemnaAPI.get("system/stats/usage", params=params)
            if result:
                logger.info("Usage statistics retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return None
    
    @staticmethod
    async def backup_config() -> Optional[Dict[str, Any]]:
        """Create system configuration backup
        
        Returns:
            Backup data or None if error
        """
        try:
            logger.info("Creating system configuration backup...")
            result = await RemnaAPI.post("system/backup")
            if result:
                logger.info("System backup created successfully")
            return result
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    @staticmethod
    async def restore_config(backup_data: Dict[str, Any]) -> bool:
        """Restore system configuration from backup
        
        Args:
            backup_data: Backup data to restore
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not isinstance(backup_data, dict):
                logger.error("Backup data must be a dictionary")
                return False
                
            logger.info("Restoring system configuration from backup...")
            result = await RemnaAPI.post("system/restore", backup_data)
            if result:
                logger.info("System configuration restored successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False

# Convenience functions for common operations
async def get_system_overview() -> Dict[str, Any]:
    """Get comprehensive system overview
    
    Returns:
        Dict with combined system data
    """
    try:
        logger.info("Getting comprehensive system overview...")
        
        # Получаем все основные статистики параллельно
        import asyncio
        
        stats_task = SystemAPI.get_stats()
        bandwidth_task = SystemAPI.get_bandwidth_stats()
        nodes_task = SystemAPI.get_nodes_statistics()
        health_task = SystemAPI.get_system_health()
        
        stats, bandwidth, nodes, health = await asyncio.gather(
            stats_task, bandwidth_task, nodes_task, health_task,
            return_exceptions=True
        )
        
        overview = {
            "timestamp": None,  # Will be set by API
            "stats": stats if not isinstance(stats, Exception) else None,
            "bandwidth": bandwidth if not isinstance(bandwidth, Exception) else None,
            "nodes": nodes if not isinstance(nodes, Exception) else None,
            "health": health if not isinstance(health, Exception) else None,
        }
        
        logger.info("System overview compiled successfully")
        return overview
        
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        return {
            "timestamp": None,
            "stats": None,
            "bandwidth": None,
            "nodes": None,
            "health": None,
            "error": str(e)
        }

async def check_system_status() -> Dict[str, bool]:
    """Quick system status check
    
    Returns:
        Dict with boolean status indicators
    """
    try:
        logger.info("Performing quick system status check...")
        
        # Проверяем основные компоненты
        stats = await SystemAPI.get_stats()
        health = await SystemAPI.get_system_health()
        
        status = {
            "api_accessible": stats is not None,
            "system_healthy": health is not None and health.get("status") == "healthy",
            "xray_running": False,  # Will be determined from stats
            "nodes_connected": False,  # Will be determined from stats
        }
        
        # Дополнительные проверки на основе полученных данных
        if stats:
            # Примерные проверки - адаптируйте под вашу структуру API
            status["xray_running"] = stats.get("xray", {}).get("running", False)
            status["nodes_connected"] = stats.get("nodes", {}).get("connected", 0) > 0
        
        logger.info(f"System status check completed: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Error checking system status: {e}")
        return {
            "api_accessible": False,
            "system_healthy": False,
            "xray_running": False,
            "nodes_connected": False,
            "error": str(e)
        }