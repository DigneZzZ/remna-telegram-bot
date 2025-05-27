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
