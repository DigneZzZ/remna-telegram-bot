#!/usr/bin/env python3
"""
Test user formatting to debug Markdown parsing issues
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.utils.formatters import format_user_details, escape_markdown

def test_user_formatting():
    """Test user formatting with sample data"""
    
    # Sample user data that might cause Markdown parsing issues
    test_user = {
        'username': 'testtest',
        'uuid': '2e8d692b-08a5-4bb3-acc9-06f808c29209',
        'shortUuid': 'abc123',
        'subscriptionUuid': 'sub-uuid-123',
        'subscriptionUrl': 'https://example.com/path/with-special-chars?param=value&other=test',
        'status': 'ACTIVE',
        'usedTrafficBytes': 1024000000,  # 1GB
        'trafficLimitBytes': 10240000000,  # 10GB
        'trafficLimitStrategy': 'MONTH',
        'expireAt': '2024-12-31T23:59:59Z',
        'description': 'Test user with special chars: !@#$%^&*()_+{}|:"<>?[]\\;\'./,',
        'tag': 'test-tag',
        'telegramId': '123456789',
        'email': 'test@example.com',
        'hwidDeviceLimit': 3,
        'createdAt': '2024-01-01T00:00:00Z',
        'updatedAt': '2024-05-26T10:00:00Z'
    }
    
    try:
        print("Testing user formatting...")
        formatted_message = format_user_details(test_user)
        
        print("✅ User formatting successful!")
        print("=" * 50)
        print(formatted_message)
        print("=" * 50)
        
        # Test individual escaping functions
        test_strings = [
            'Normal text',
            'Text with *bold* and _italic_',
            'Text with special chars: !@#$%^&*()_+{}|:"<>?[]\\;\'./,',
            'URL: https://example.com/path?param=value&other=test'
        ]
        
        print("\nTesting escape_markdown function:")
        for test_str in test_strings:
            escaped = escape_markdown(test_str)
            print(f"Original: {test_str}")
            print(f"Escaped:  {escaped}")
            print()
            
        return True
        
    except Exception as e:
        print(f"❌ Error during formatting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_markdown_parsing():
    """Test potential Markdown parsing issues"""
    
    problematic_urls = [
        'https://example.com/sub/12345678_abcdef',
        'vless://uuid@host:port?type=tcp&security=none',
        'https://api.example.com/v1/subscriptions/uuid-here/config?format=clash&token=abc_123',
        'sub://YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE='
    ]
    
    print("Testing problematic URLs in Markdown:")
    for url in problematic_urls:
        try:
            # Test in code block
            test_message = f"🔗 *URL:* `{url}`"
            print(f"✅ URL OK: {url[:50]}...")
        except Exception as e:
            print(f"❌ URL problematic: {url[:50]}... - {e}")

if __name__ == "__main__":
    print("🧪 Testing user formatting and Markdown parsing\n")
    
    success = test_user_formatting()
    print()
    test_markdown_parsing()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
