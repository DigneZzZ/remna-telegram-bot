#!/usr/bin/env python3
import json

def extract_api_endpoints():
    """Extract and analyze API endpoints from the specification"""
    
    with open('remnawave-api-v162.json', 'r') as f:
        spec = json.load(f)

    paths = spec['paths']
    print('=== REMNAWAVE API v1.6.2 ENDPOINTS ===\n')

    # Группируем эндпоинты по контроллерам/модулям
    controllers = {}
    
    for path, methods in paths.items():
        print(f'Path: {path}')
        for method, details in methods.items():
            operation_id = details.get('operationId', 'N/A')
            summary = details.get('summary', 'N/A')
            tags = details.get('tags', ['Unknown'])
            controller = tags[0] if tags else 'Unknown'
            
            if controller not in controllers:
                controllers[controller] = []
            
            controllers[controller].append({
                'path': path,
                'method': method.upper(),
                'operation_id': operation_id,
                'summary': summary
            })
            
            print(f'  {method.upper()}: {operation_id} - {summary}')
        print()
    
    print("\n=== ENDPOINTS BY CONTROLLER ===\n")
    for controller, endpoints in controllers.items():
        print(f"Controller: {controller}")
        for endpoint in endpoints:
            print(f"  {endpoint['method']} {endpoint['path']} - {endpoint['summary']}")
        print()

if __name__ == "__main__":
    extract_api_endpoints()
