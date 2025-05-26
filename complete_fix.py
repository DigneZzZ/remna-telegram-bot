#!/usr/bin/env python3
"""
Complete fix script for Remnawave Admin Bot
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and print results"""
    print(f"\n🔧 {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("Output:")
            print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    """Main fix function"""
    print("🚀 Запуск полного исправления Remnawave Admin Bot")
    print("=" * 60)
    
    # 1. Test current admin config
    print("\n1. Тестирование конфигурации администратора")
    if os.path.exists("test_admin_config.py"):
        run_command("python test_admin_config.py", "Проверка ADMIN_USER_IDS")
    
    # 2. Test API connectivity
    print("\n2. Тестирование API подключения")
    if os.path.exists("test_api.py"):
        run_command("python test_api.py", "Проверка API")
    
    # 3. Stop current containers
    print("\n3. Остановка текущих контейнеров")
    run_command("docker-compose -f docker-compose-prod.yml down", "Остановка контейнеров")
    
    # 4. Rebuild containers
    print("\n4. Пересборка контейнеров")
    run_command("docker-compose -f docker-compose-prod.yml build --no-cache", "Пересборка с очисткой кэша")
    
    # 5. Start containers
    print("\n5. Запуск контейнеров")
    run_command("docker-compose -f docker-compose-prod.yml up -d", "Запуск в фоне")
    
    # 6. Wait and show logs
    print("\n6. Ожидание запуска и показ логов")
    import time
    time.sleep(10)
    run_command("docker-compose -f docker-compose-prod.yml logs --tail=20", "Показ логов")
    
    # 7. Show container status
    print("\n7. Статус контейнеров")
    run_command("docker-compose -f docker-compose-prod.yml ps", "Статус контейнеров")
    
    print("\n✅ Исправление завершено!")
    print("\n📋 Следующие шаги:")
    print("1. Проверьте логи выше на наличие ошибок")
    print("2. Отправьте /start боту для тестирования")
    print("3. Проверьте, что пользователь 127192647 может войти")
    print("4. Если проблемы остаются, проверьте переменные среды в контейнере")

if __name__ == "__main__":
    main()
