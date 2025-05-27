#!/usr/bin/env python3
"""
Простейший тест TCP подключения к remnawave
"""
import socket
import time

def test_tcp_connection(host, port, timeout=5):
    """Тест TCP соединения"""
    print(f"Testing TCP connection to {host}:{port}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()
        
        if result == 0:
            print(f"✅ TCP connection successful in {end_time - start_time:.3f}s")
            
            # Попробуем отправить простой HTTP запрос
            try:
                request = b"GET /api HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n"
                sock.send(request)
                
                # Ждем ответ
                sock.settimeout(2)
                response = sock.recv(1024)
                print(f"✅ HTTP response received: {len(response)} bytes")
                print(f"Response preview: {response[:100]}")
                
            except Exception as e:
                print(f"❌ HTTP request failed: {e}")
            
            sock.close()
            return True
        else:
            print(f"❌ TCP connection failed with error code: {result}")
            sock.close()
            return False
            
    except Exception as e:
        print(f"❌ TCP connection exception: {e}")
        return False

def main():
    """Главная функция"""
    print("=== Simple TCP Test ===")
    
    # Тестируем подключение
    success = test_tcp_connection("remnawave", 3003)
    
    if success:
        print("\n✅ TCP connection works!")
    else:
        print("\n❌ TCP connection failed!")
        print("This suggests:")
        print("1. Container 'remnawave' is not running")
        print("2. Port 3003 is not exposed")
        print("3. Network connectivity issues")
        print("4. Firewall blocking connection")

if __name__ == "__main__":
    main()
