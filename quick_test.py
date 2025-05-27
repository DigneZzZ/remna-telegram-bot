#!/usr/bin/env python3
try:
    print("Тестирование импортов...")
    
    from modules.handlers_aiogram import register_all_handlers
    print("✅ register_all_handlers импортирован")
    
    from modules.handlers_aiogram.start_handler import router
    print("✅ start_handler router импортирован")
    
    from modules.handlers_aiogram.auth import AuthFilter
    print("✅ AuthFilter импортирован")
    
    from modules.handlers_aiogram.states import UserStates
    print("✅ UserStates импортированы")
    
    print("🎉 Все основные импорты работают!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
