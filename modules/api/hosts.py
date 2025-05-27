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

async def get_all_hosts(start=None, size=None):
    """Получить все хосты через прямой HTTP вызов"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts"
            
            params = {}
            if start is not None:
                params['start'] = start
            if size is not None:
                params['size'] = size
                
            logger.info(f"Making direct API call to: {url} with params: {params}")
            
            response = await client.get(url, headers=_get_headers(), params=params if params else None)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API response type: {type(data)}, content preview: {str(data)[:200]}")
                
                # API может возвращать данные в формате {'response': [...]} или прямо список
                if isinstance(data, dict) and 'response' in data:
                    hosts_list = data['response']
                    if isinstance(hosts_list, dict) and 'hosts' in hosts_list:
                        hosts_list = hosts_list['hosts']
                elif isinstance(data, dict) and 'hosts' in data:
                    hosts_list = data['hosts']
                elif isinstance(data, list):
                    hosts_list = data
                else:
                    logger.error(f"Unexpected API response structure: {type(data)}")
                    return []
                
                logger.info(f"Retrieved {len(hosts_list)} hosts successfully")
                return hosts_list
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting all hosts: {e}")
        return []

async def get_host_by_uuid(host_uuid: str):
    """Получить хост по UUID"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}"
            logger.info(f"Making direct API call to: {url}")
            
            response = await client.get(url, headers=_get_headers())
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved host: {data.get('name', host_uuid) if isinstance(data, dict) else host_uuid}")
                
                # API может возвращать данные в формате {'response': {...}}
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting host {host_uuid}: {e}")
        return None
    
async def create_host(data):
    """Создать новый хост"""
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts"
            logger.info(f"Making direct API call to create host: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                host_data = response.json()
                
                # Парсим ответ API
                if isinstance(host_data, dict) and 'response' in host_data:
                    result = host_data['response']
                else:
                    result = host_data
                    
                logger.info(f"Created host: {result.get('name', 'Unknown') if isinstance(result, dict) else 'Unknown'}")
                return result
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error creating host: {e}")
        return None

async def update_host(host_uuid, data):
    """Обновить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}"
            logger.info(f"Making direct API call to update host: {url}")
            
            response = await client.put(url, headers=_get_headers(), json=data)
            
            if response.status_code == 200:
                host_data = response.json()
                
                # Парсим ответ API
                if isinstance(host_data, dict) and 'response' in host_data:
                    result = host_data['response']
                else:
                    result = host_data
                    
                logger.info(f"Updated host: {result.get('name', host_uuid) if isinstance(result, dict) else host_uuid}")
                return result
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error updating host {host_uuid}: {e}")
        return None

async def delete_host(host_uuid):
    """Удалить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}"
            logger.info(f"Making direct API call to delete host: {url}")
            
            response = await client.delete(url, headers=_get_headers())
            
            if response.status_code in [200, 204]:
                logger.info(f"Deleted host: {host_uuid}")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting host {host_uuid}: {e}")
        return False

async def enable_host(host_uuid):
    """Включить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}/enable"
            logger.info(f"Making direct API call to enable host: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                host_data = response.json()
                
                # Парсим ответ API
                if isinstance(host_data, dict) and 'response' in host_data:
                    result = host_data['response']
                else:
                    result = host_data
                    
                logger.info(f"Enabled host: {result.get('name', host_uuid) if isinstance(result, dict) else host_uuid}")
                return result
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error enabling host {host_uuid}: {e}")
        return None

async def disable_host(host_uuid):
    """Отключить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}/disable"
            logger.info(f"Making direct API call to disable host: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                host_data = response.json()
                
                # Парсим ответ API
                if isinstance(host_data, dict) and 'response' in host_data:
                    result = host_data['response']
                else:
                    result = host_data
                    
                logger.info(f"Disabled host: {result.get('name', host_uuid) if isinstance(result, dict) else host_uuid}")
                return result
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error disabling host {host_uuid}: {e}")
        return None

async def restart_host(host_uuid):
    """Перезапустить хост"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}/restart"
            logger.info(f"Making direct API call to restart host: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                host_data = response.json()
                
                # Парсим ответ API
                if isinstance(host_data, dict) and 'response' in host_data:
                    result = host_data['response']
                else:
                    result = host_data
                    
                logger.info(f"Restarted host: {result.get('name', host_uuid) if isinstance(result, dict) else host_uuid}")
                return result
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error restarting host {host_uuid}: {e}")
        return None
    
async def bulk_enable_hosts(uuids):
    """Массово включить хосты по UUID"""
    try:
        if not uuids or not isinstance(uuids, list) or len(uuids) == 0:
            logger.error("Host UUIDs list is empty or invalid")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/bulk/enable"
            data = {"uuids": uuids}
            logger.info(f"Making direct API call to bulk enable hosts: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Bulk enabled {len(uuids)} hosts")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error bulk enabling hosts: {e}")
        return False

async def bulk_disable_hosts(uuids):
    """Массово отключить хосты по UUID"""
    try:
        if not uuids or not isinstance(uuids, list) or len(uuids) == 0:
            logger.error("Host UUIDs list is empty or invalid")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/bulk/disable"
            data = {"uuids": uuids}
            logger.info(f"Making direct API call to bulk disable hosts: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Bulk disabled {len(uuids)} hosts")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error bulk disabling hosts: {e}")
        return False

async def bulk_restart_hosts(uuids):
    """Массово перезапустить хосты по UUID"""
    try:
        if not uuids or not isinstance(uuids, list) or len(uuids) == 0:
            logger.error("Host UUIDs list is empty or invalid")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/bulk/restart"
            data = {"uuids": uuids}
            logger.info(f"Making direct API call to bulk restart hosts: {url}")
            
            response = await client.post(url, headers=_get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Bulk restarted {len(uuids)} hosts")
                return True
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error bulk restarting hosts: {e}")
        return False

async def get_host_usage(host_uuid: str, start_date: str = None, end_date: str = None):
    """Получить статистику использования хоста"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return None
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}/usage"
            
            params = {}
            if start_date:
                params['start'] = start_date
            if end_date:
                params['end'] = end_date
                
            logger.info(f"Making direct API call to get host usage: {url}")
            
            response = await client.get(url, headers=_get_headers(), params=params if params else None)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved usage for host {host_uuid} successfully")
                
                # Парсим ответ API
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to get host usage. Status: {response.status_code}, Response: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting host usage {host_uuid}: {e}")
        return None

async def test_host_connection(host_uuid: str):
    """Тестировать соединение с хостом"""
    try:
        if not host_uuid:
            logger.error("Host UUID is empty or None")
            return False
            
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            url = f"{API_BASE_URL}/hosts/{host_uuid}/test"
            logger.info(f"Making direct API call to test host connection: {url}")
            
            response = await client.post(url, headers=_get_headers())
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Host {host_uuid} connection test completed")
                
                # Парсим ответ API
                if isinstance(data, dict) and 'response' in data:
                    return data['response']
                else:
                    return data
            else:
                logger.error(f"Failed to test host connection. Status: {response.status_code}, Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error testing host connection {host_uuid}: {e}")
        return False

async def get_hosts_count():
    """Получить количество хостов"""
    try:
        # Попробуем сначала получить статистику
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            stats_endpoints = [
                f"{API_BASE_URL}/hosts/count",
                f"{API_BASE_URL}/hosts/stats",
                f"{API_BASE_URL}/stats/hosts"
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
                                             response_data.get('totalHosts'))
                            else:
                                count_value = (data.get('count') or 
                                             data.get('total') or 
                                             data.get('totalHosts'))
                        elif isinstance(data, (int, float)):
                            count_value = int(data)
                        
                        if count_value is not None:
                            logger.info(f"Got hosts count from {endpoint}: {count_value}")
                            return int(count_value)
                except Exception as e:
                    logger.debug(f"Stats endpoint {endpoint} failed: {e}")
            
            # Если статистические endpoints не работают, получаем все хосты
            hosts = await get_all_hosts()
            count = len(hosts) if hosts else 0
            logger.info(f"Got hosts count by fetching all hosts: {count}")
            return count
            
    except Exception as e:
        logger.error(f"Error getting hosts count: {e}")
        return 0

async def get_hosts_stats():
    """Получить статистику хостов"""
    try:
        # Попробуем получить статистику напрямую
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            stats_endpoints = [
                f"{API_BASE_URL}/hosts/stats",
                f"{API_BASE_URL}/stats/hosts",
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
                            if 'hosts' in stats_data or 'totalHosts' in stats_data:
                                logger.info(f"Got hosts stats from {endpoint}")
                                return stats_data
                except Exception as e:
                    logger.debug(f"Stats endpoint {endpoint} failed: {e}")
        
        # Если прямые endpoints не работают, вычисляем статистику из всех хостов
        hosts = await get_all_hosts()
        if not hosts:
            return None
            
        total_hosts = len(hosts)
        active_hosts = 0
        disabled_hosts = 0
        connected_hosts = 0
        
        for host in hosts:
            if isinstance(host, dict):
                # Проверяем активность
                if (host.get('isActive') or 
                    host.get('is_active') or 
                    host.get('active') or
                    host.get('status') == 'active'):
                    active_hosts += 1
                
                # Проверяем отключенные
                if (host.get('isDisabled') or 
                    host.get('is_disabled') or 
                    host.get('disabled') or
                    host.get('status') == 'disabled'):
                    disabled_hosts += 1
                
                # Проверяем подключение
                if (host.get('isConnected') or 
                    host.get('is_connected') or 
                    host.get('connected')):
                    connected_hosts += 1
        
        stats = {
            'total': total_hosts,
            'active': active_hosts,
            'disabled': disabled_hosts,
            'connected': connected_hosts
        }
        
        logger.info(f"Calculated hosts stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting hosts stats: {e}")
        return None

# Псевдонимы для обратной совместимости
get_hosts = get_all_hosts

# Для обратной совместимости с классом
class HostsAPI:
    """API methods for hosts management - Legacy compatibility class"""
    
    @staticmethod
    async def get_all_hosts(start=None, size=None):
        return await get_all_hosts(start, size)
    
    @staticmethod
    async def get_host_by_uuid(host_uuid: str):
        return await get_host_by_uuid(host_uuid)
    
    @staticmethod
    async def create_host(data):
        return await create_host(data)
    
    @staticmethod
    async def update_host(host_uuid, data):
        return await update_host(host_uuid, data)
    
    @staticmethod
    async def delete_host(host_uuid):
        return await delete_host(host_uuid)
    
    @staticmethod
    async def enable_host(host_uuid):
        return await enable_host(host_uuid)
    
    @staticmethod
    async def disable_host(host_uuid):
        return await disable_host(host_uuid)
    
    @staticmethod
    async def restart_host(host_uuid):
        return await restart_host(host_uuid)
    
    @staticmethod
    async def bulk_enable_hosts(uuids):
        return await bulk_enable_hosts(uuids)
    
    @staticmethod
    async def bulk_disable_hosts(uuids):
        return await bulk_disable_hosts(uuids)
    
    @staticmethod
    async def bulk_restart_hosts(uuids):
        return await bulk_restart_hosts(uuids)
    
    @staticmethod
    async def get_host_usage(host_uuid: str, start_date: str = None, end_date: str = None):
        return await get_host_usage(host_uuid, start_date, end_date)
    
    @staticmethod
    async def test_host_connection(host_uuid: str):
        return await test_host_connection(host_uuid)