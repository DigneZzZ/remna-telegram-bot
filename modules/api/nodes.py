import logging
import httpx
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

def _get_headers():
    """Получить стандартные заголовки для API запросов"""
    return {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json',
        'X-Forwarded-Proto': 'https',
        'X-Forwarded-For': '127.0.0.1',
        'X-Real-IP': '127.0.0.1'
    }

async def get_all_nodes():
    """Получить все ноды через прямой HTTP вызов"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f'{API_BASE_URL}/nodes'
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response type: {type(data)}, content preview: {str(data)[:200]}")
                
                # API возвращает данные в формате {'response': [...]} для нод
                if isinstance(data, dict) and 'response' in data:
                    response_data = data['response']
                    if isinstance(response_data, list):
                        nodes_list = response_data
                    elif isinstance(response_data, dict) and 'nodes' in response_data:
                        nodes_list = response_data['nodes']
                    else:
                        logger.error(f"Unexpected response structure in 'response' field: {type(response_data)}")
                        return []
                elif isinstance(data, dict) and 'nodes' in data:
                    nodes_list = data['nodes']
                elif isinstance(data, list):
                    nodes_list = data
                else:
                    logger.error(f"Unexpected API response structure: {type(data)}")
                    return []
                
                logger.info(f"Retrieved {len(nodes_list)} nodes via direct API")
                return nodes_list
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting all nodes: {e}")
        return []

async def get_node_by_uuid(node_uuid: str):
    """Получить ноду по UUID"""
    try:
        if not node_uuid:
            logger.error("Node UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved node {node_uuid} successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting node by UUID {node_uuid}: {e}")
        return None

async def restart_node(node_uuid: str):
    """Перезапустить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}/restart"
            logger.info(f"Making direct API call to restart node: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 204]:
                logger.info(f"Node {node_uuid} restart command sent successfully")
                return True
            else:
                logger.error(f"Failed to restart node. Status: {response.status_code}, Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error restarting node {node_uuid}: {e}")
        return False

async def enable_node(node_uuid: str):
    """Включить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}/enable"
            logger.info(f"Making direct API call to enable node: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Node {node_uuid} enabled successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to enable node. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error enabling node {node_uuid}: {e}")
        return None

async def disable_node(node_uuid: str):
    """Отключить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}/disable"
            logger.info(f"Making direct API call to disable node: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Node {node_uuid} disabled successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to disable node. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error disabling node {node_uuid}: {e}")
        return None

async def get_node_usage(node_uuid: str, start_date: str = None, end_date: str = None):
    """Получить статистику использования ноды"""
    try:
        if not node_uuid:
            logger.error("Node UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}/usage"
            
            params = {}
            if start_date:
                params['start'] = start_date
            if end_date:
                params['end'] = end_date
                
            logger.info(f"Making direct API call to get node usage: {url}")
            
            response = await client.get(url, headers=_get_headers(), params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved usage for node {node_uuid} successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to get node usage. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting node usage {node_uuid}: {e}")
        return None

async def create_node(node_data: dict):
    """Создать новую ноду"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes"
            logger.info(f"Making direct API call to create node: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=node_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Node created successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to create node. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error creating node: {e}")
        return None

async def update_node(node_uuid: str, node_data: dict):
    """Обновить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is required")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}"
            logger.info(f"Making direct API call to update node: {url}")
            
            response = await client.put(url, headers=_get_headers(), json=node_data)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Node {node_uuid} updated successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to update node. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error updating node {node_uuid}: {e}")
        return None

async def delete_node(node_uuid: str):
    """Удалить ноду"""
    try:
        if not node_uuid:
            logger.error("Node UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}"
            logger.info(f"Making direct API call to delete node: {url}")
            
            response = await client.delete(url, headers=_get_headers())
            
            if response.status_code in [200, 204]:
                logger.info(f"Node {node_uuid} deleted successfully")
                return True
            else:
                logger.error(f"Failed to delete node. Status: {response.status_code}, Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting node {node_uuid}: {e}")
        return False

async def get_nodes_usage_realtime():
    """Получить статистику использования нод в реальном времени"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/usage/realtime"
            logger.info(f"Making direct API call to get realtime nodes usage: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved realtime nodes usage successfully")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to get realtime nodes usage. Status: {response.status_code}, Response: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting realtime nodes usage: {e}")
        return []

async def get_nodes_count():
    """Получить количество нод"""
    try:
        # Попробуем сначала получить статистику
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            stats_endpoints = [
                f"{API_BASE_URL}/nodes/count",
                f"{API_BASE_URL}/nodes/stats",
                f"{API_BASE_URL}/stats/nodes"
            ]
            
            for endpoint in stats_endpoints:
                try:
                    response = await client.get(endpoint, headers=_get_headers())
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Ищем счетчик в различных форматах ответа
                        count_value = None
                        if isinstance(data, dict):
                            if 'response' in data:
                                response_data = data['response']
                                count_value = (response_data.get('count') or 
                                             response_data.get('total') or 
                                             response_data.get('totalNodes'))
                            else:
                                count_value = (data.get('count') or 
                                             data.get('total') or 
                                             data.get('totalNodes'))
                        elif isinstance(data, (int, float)):
                            count_value = int(data)
                        
                        if count_value is not None:
                            logger.info(f"Got nodes count from {endpoint}: {count_value}")
                            return int(count_value)
                except Exception as e:
                    logger.debug(f"Stats endpoint {endpoint} failed: {e}")
            
            # Если статистические endpoints не работают, получаем все ноды
            nodes = await get_all_nodes()
            count = len(nodes) if nodes else 0
            logger.info(f"Got nodes count by fetching all nodes: {count}")
            return count
            
    except Exception as e:
        logger.error(f"Error getting nodes count: {e}")
        return 0

async def get_nodes_stats():
    """Получить статистику нод"""
    try:
        # Попробуем получить статистику напрямую
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            stats_endpoints = [
                f"{API_BASE_URL}/nodes/stats",
                f"{API_BASE_URL}/stats/nodes",
                f"{API_BASE_URL}/dashboard/stats"
            ]
            
            for endpoint in stats_endpoints:
                try:
                    response = await client.get(endpoint, headers=_get_headers())
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Парсим статистику из ответа
                        if isinstance(data, dict):
                            stats_data = data.get('response', data)
                            if 'nodes' in stats_data or 'totalNodes' in stats_data:
                                logger.info(f"Got nodes stats from {endpoint}")
                                return stats_data
                except Exception as e:
                    logger.debug(f"Stats endpoint {endpoint} failed: {e}")
        
        # Если прямые endpoints не работают, вычисляем статистику из всех нод
        nodes = await get_all_nodes()
        if not nodes:
            return None
            
        total_nodes = len(nodes)
        connected_nodes = 0
        active_nodes = 0
        disabled_nodes = 0
        
        for node in nodes:
            if isinstance(node, dict):
                # Проверяем подключение
                if (node.get('isConnected') or 
                    node.get('is_connected') or 
                    node.get('connected')):
                    connected_nodes += 1
                
                # Проверяем активность
                if (node.get('isActive') or 
                    node.get('is_active') or 
                    node.get('active') or
                    node.get('status') == 'active'):
                    active_nodes += 1
                
                # Проверяем отключенные
                if (node.get('isDisabled') or 
                    node.get('is_disabled') or 
                    node.get('disabled') or
                    node.get('status') == 'disabled'):
                    disabled_nodes += 1
        
        stats = {
            'total': total_nodes,
            'connected': connected_nodes,
            'active': active_nodes,
            'disabled': disabled_nodes
        }
        
        logger.info(f"Calculated nodes stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting nodes stats: {e}")
        return None

async def test_node_connection(node_uuid: str):
    """Тестировать соединение с нодой"""
    try:
        if not node_uuid:
            logger.error("Node UUID is required")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/nodes/{node_uuid}/test"
            logger.info(f"Making direct API call to test node connection: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Node {node_uuid} connection test completed")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to test node connection. Status: {response.status_code}, Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error testing node connection {node_uuid}: {e}")
        return False

# Псевдонимы для обратной совместимости
get_nodes = get_all_nodes

# Для обратной совместимости с классом
class NodesAPI:
    """API methods for nodes management - Legacy compatibility class"""
    
    @staticmethod
    async def get_all_nodes():
        return await get_all_nodes()
    
    @staticmethod
    async def get_node_by_uuid(node_uuid: str):
        return await get_node_by_uuid(node_uuid)
    
    @staticmethod
    async def restart_node(node_uuid: str):
        return await restart_node(node_uuid)
    
    @staticmethod
    async def enable_node(node_uuid: str):
        return await enable_node(node_uuid)
    
    @staticmethod
    async def disable_node(node_uuid: str):
        return await disable_node(node_uuid)
    
    @staticmethod
    async def create_node(node_data: dict):
        return await create_node(node_data)
    
    @staticmethod
    async def update_node(node_uuid: str, node_data: dict):
        return await update_node(node_uuid, node_data)
    
    @staticmethod
    async def delete_node(node_uuid: str):
        return await delete_node(node_uuid)
    
    @staticmethod
    async def get_node_usage(node_uuid: str, start_date: str = None, end_date: str = None):
        return await get_node_usage(node_uuid, start_date, end_date)
    
    @staticmethod
    async def test_node_connection(node_uuid: str):
        return await test_node_connection(node_uuid)
    
    @staticmethod
    async def get_nodes_usage_realtime():
        return await get_nodes_usage_realtime()
    
    @staticmethod
    async def get_nodes_count():
        return await get_nodes_count