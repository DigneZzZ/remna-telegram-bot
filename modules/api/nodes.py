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
