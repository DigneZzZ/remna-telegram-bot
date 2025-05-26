import requests
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
            response = requests.get(f"{API_BASE_URL}/{endpoint}", headers=get_headers(), params=params)
            response.raise_for_status()
            json_response = response.json()
            return json_response.get("response") if isinstance(json_response, dict) else json_response
        except requests.exceptions.RequestException as e:
            logger.error(f"API GET error: {endpoint} - {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GET {endpoint}: {str(e)}")
            return None
    
    @staticmethod
    async def post(endpoint, data=None):
        """Make a POST request to the API"""
        try:
            # Log request data for debugging
            logger.debug(f"POST request to {endpoint} with data: {json.dumps(data, indent=2)}")
            
            response = requests.post(f"{API_BASE_URL}/{endpoint}", headers=get_headers(), json=data)
            
            # Log response status and content for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response content: {response.text[:500]}...")  # Log first 500 chars to avoid huge logs
            
            response.raise_for_status()
            json_response = response.json()
            return json_response.get("response") if isinstance(json_response, dict) else json_response
        except requests.exceptions.RequestException as e:
            logger.error(f"API POST error: {endpoint} - {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.status_code} - {e.response.text}")
                # Try to parse error response if possible
                try:
                    error_json = e.response.json()
                    if "message" in error_json:
                        logger.error(f"API error message: {error_json['message']}")
                except:
                    pass
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
            
            response = requests.patch(f"{API_BASE_URL}/{endpoint}", headers=get_headers(), json=data)
            response.raise_for_status()
            json_response = response.json()
            return json_response.get("response") if isinstance(json_response, dict) else json_response
        except requests.exceptions.RequestException as e:
            logger.error(f"API PATCH error: {endpoint} - {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in PATCH {endpoint}: {str(e)}")
            return None
    
    @staticmethod
    async def delete(endpoint, params=None):
        """Make a DELETE request to the API"""
        try:
            response = requests.delete(f"{API_BASE_URL}/{endpoint}", headers=get_headers(), params=params)
            response.raise_for_status()
            json_response = response.json()
            return json_response.get("response") if isinstance(json_response, dict) else json_response
        except requests.exceptions.RequestException as e:
            logger.error(f"API DELETE error: {endpoint} - {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in DELETE {endpoint}: {str(e)}")
            return None
