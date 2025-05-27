#!/usr/bin/env python3
try:
    print("Тестирование импортов...")
    
    from modules.handlers import register_all_handlers
    print("✅ register_all_handlers импортирован")
    
    from modules.handlers.start_handler import router
    print("✅ start_handler router импортирован")
    
    from modules.handlers.auth import AuthFilter
    print("✅ AuthFilter импортирован")
    
    from modules.handlers.states import UserStates
    print("✅ UserStates импортированы")
    
    print("🎉 Все основные импорты работают!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
