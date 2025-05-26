import aiohttp
import logging
import json
from modules.config import API_BASE_URL, API_TOKEN

logger = logging.getLogger(__name__)

def get_headers():
    """Get headers for API requests"""
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

class RemnaAPI:
    """API client for Remnawave API"""
    
    @staticmethod
    async def get(endpoint, params=None):
        """Make a GET request to the API"""
        try:
            url = f"{API_BASE_URL}/{endpoint}"
            logger.debug(f"Making GET request to: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=get_headers(), params=params) as response:
                    response_text = await response.text()
                    logger.debug(f"Response status: {response.status}")
                    logger.debug(f"Response content-type: {response.headers.get('content-type', 'unknown')}")
                    logger.debug(f"Response content (first 200 chars): {response_text[:200]}")
                    
                    response.raise_for_status()
                    
                    # Check if response is JSON
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' not in content_type:
                        logger.error(f"Expected JSON but got {content_type}. Response: {response_text[:500]}")
                        return None
                    
                    json_response = await response.json()
                    return json_response.get("response") if isinstance(json_response, dict) else json_response
        except aiohttp.ClientError as e:
            logger.error(f"API GET error: {endpoint} - {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for GET {endpoint}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GET {endpoint}: {str(e)}")
            return None
    
    @staticmethod
    async def post(endpoint, data=None):
        """Make a POST request to the API"""
        try:
            url = f"{API_BASE_URL}/{endpoint}"
            logger.debug(f"Making POST request to: {url}")
            logger.debug(f"POST data: {json.dumps(data, indent=2) if data else 'None'}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=get_headers(), json=data) as response:
                    response_text = await response.text()
                    logger.debug(f"Response status: {response.status}")
                    logger.debug(f"Response content-type: {response.headers.get('content-type', 'unknown')}")
                    logger.debug(f"Response content (first 200 chars): {response_text[:200]}")
                    
                    response.raise_for_status()
                    
                    # Check if response is JSON
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' not in content_type:
                        logger.error(f"Expected JSON but got {content_type}. Response: {response_text[:500]}")
                        return None
                    
                    json_response = await response.json()
                    return json_response.get("response") if isinstance(json_response, dict) else json_response
        except aiohttp.ClientError as e:
            logger.error(f"API POST error: {endpoint} - {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for POST {endpoint}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in POST {endpoint}: {str(e)}")
            return None
    
    @staticmethod
    async def patch(endpoint, data=None):
        """Make a PATCH request to the API"""
        try:
            # Логируем данные запроса для отладки
            logger.debug(f"PATCH request to {endpoint} with data: {json.dumps(data, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(f"{API_BASE_URL}/{endpoint}", headers=get_headers(), json=data) as response:
                    response.raise_for_status()
                    json_response = await response.json()
                    return json_response.get("response") if isinstance(json_response, dict) else json_response
        except aiohttp.ClientError as e:
            logger.error(f"API PATCH error: {endpoint} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in PATCH {endpoint}: {str(e)}")
            return None
    
    @staticmethod
    async def delete(endpoint, params=None):
        """Make a DELETE request to the API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{API_BASE_URL}/{endpoint}", headers=get_headers(), params=params) as response:
                    response.raise_for_status()
                    json_response = await response.json()
                    return json_response.get("response") if isinstance(json_response, dict) else json_response
        except aiohttp.ClientError as e:
            logger.error(f"API DELETE error: {endpoint} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in DELETE {endpoint}: {str(e)}")
            return None
