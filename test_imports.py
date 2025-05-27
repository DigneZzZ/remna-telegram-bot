#!/usr/bin/env python3

print("Проверка импортов...")

try:
    import modules.handlers_aiogram.start_handler
    print('✅ start_handler: OK')
except Exception as e:
    print(f'❌ start_handler: {e}')

try:
    import modules.handlers_aiogram.menu_handler
    print('✅ menu_handler: OK')
except Exception as e:
    print(f'❌ menu_handler: {e}')

try:
    import modules.handlers_aiogram.auth
    print('✅ auth: OK')
except Exception as e:
    print(f'❌ auth: {e}')

try:
    import modules.handlers_aiogram.user_handlers
    print('✅ user_handlers: OK')
except Exception as e:
    print(f'❌ user_handlers: {e}')

try:
    import modules.handlers_aiogram.node_handlers
    print('✅ node_handlers: OK')
except Exception as e:
    print(f'❌ node_handlers: {e}')

print("Проверка завершена.")
