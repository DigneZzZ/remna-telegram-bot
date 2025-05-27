from aiogram import Router, types, F
from aiogram.filters import Command, Text, StateFilter
from aiogram.fsm.context import FSMContext
import logging

from modules.handlers_aiogram.auth import AuthFilter
from modules.handlers_aiogram.states import (
    UserStates, NodeStates, InboundStates, BulkStates, StatsStates
)

# Import all handlers
from modules.handlers_aiogram.start_handler import router as start_router
from modules.handlers_aiogram.menu_handler import router as menu_router
from modules.handlers_aiogram.user_handlers import router as user_router
from modules.handlers_aiogram.node_handlers import router as node_router
from modules.handlers_aiogram.inbound_handlers import router as inbound_router
from modules.handlers_aiogram.bulk_handlers import router as bulk_router
from modules.handlers_aiogram.stats_handlers import router as stats_router

logger = logging.getLogger(__name__)

# Main router that includes all other routers
main_router = Router()

# Include all sub-routers
main_router.include_router(start_router)
main_router.include_router(menu_router)
main_router.include_router(user_router)
main_router.include_router(node_router)
main_router.include_router(inbound_router)
main_router.include_router(bulk_router)
main_router.include_router(stats_router)

# ================ FALLBACK HANDLERS ================

@main_router.message(Command("start"))
async def fallback_start_unauthorized(message: types.Message, state: FSMContext):
    """Fallback start handler for unauthorized users"""
    await handle_unauthorized_access(message, state)

@main_router.message(F.text)
async def fallback_text_unauthorized(message: types.Message, state: FSMContext):
    """Fallback text handler for unauthorized users"""
    await handle_unauthorized_access(message, state)

@main_router.callback_query()
async def fallback_callback_unauthorized(callback: types.CallbackQuery, state: FSMContext):
    """Fallback callback handler for unauthorized users"""
    await handle_unauthorized_access(callback, state, is_callback=True)

async def handle_unauthorized_access(
    update: types.Message | types.CallbackQuery, 
    state: FSMContext, 
    is_callback: bool = False
):
    """Handle unauthorized access attempts"""
    if is_callback:
        user_id = update.from_user.id
        username = update.from_user.username or "Unknown"
        
        logger.warning(f"Unauthorized callback access attempt from user {user_id} (@{username})")
        
        await update.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
    else:
        user_id = update.from_user.id
        username = update.from_user.username or "Unknown"
        
        logger.warning(f"Unauthorized message access attempt from user {user_id} (@{username})")
        
        await update.answer("⛔ Вы не авторизованы для использования этого бота.")
    
    # Clear any state
    await state.clear()

# ================ CANCEL HANDLER ================

@main_router.message(Command("cancel"), AuthFilter())
async def cancel_handler(message: types.Message, state: FSMContext):
    """Cancel current operation and return to main menu"""
    await state.clear()
    
    from modules.handlers_aiogram.start_handler import show_main_menu
    await show_main_menu(message)

@main_router.callback_query(Text("cancel"), AuthFilter())
async def cancel_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    """Cancel current operation via callback and return to main menu"""
    await callback.answer()
    await state.clear()
    
    from modules.handlers_aiogram.start_handler import show_main_menu
    await show_main_menu(callback.message)

# ================ HELP HANDLER ================

@main_router.message(Command("help"), AuthFilter())
async def help_handler(message: types.Message):
    """Show help information"""
    help_text = """
🤖 **Remnawave Admin Bot - Справка**

**Основные команды:**
• `/start` - Запуск бота и главное меню
• `/cancel` - Отмена текущей операции
• `/help` - Показать эту справку

**Доступные разделы:**
• 👥 **Пользователи** - Управление пользователями VPN
• 🖥️ **Серверы** - Управление нодами и серверами
• 🔌 **Inbounds** - Управление входящими соединениями
• 📊 **Статистика** - Просмотр статистики системы
• 🔄 **Массовые операции** - Операции над множеством объектов

**Навигация:**
• Используйте кнопки для навигации по меню
• Кнопка "🔙 Назад" возвращает к предыдущему экрану
• В любой момент можете написать `/cancel` для возврата в главное меню

**Поддержка:**
• Все операции логируются для отладки
• При ошибках проверьте подключение к API
• Убедитесь, что у вас есть права администратора
"""
    
    await message.answer(help_text)

# ================ STATUS HANDLER ================

@main_router.message(Command("status"), AuthFilter())
async def status_handler(message: types.Message, state: FSMContext):
    """Show current bot status"""
    try:
        from modules.api.client import RemnaAPI
        
        # Получаем текущее состояние
        current_state = await state.get_state()
        state_data = await state.get_data()
        
        # Проверяем подключение к API
        try:
            sdk = RemnaAPI.get_sdk()
            users_response = await sdk.users.get_all_users_v2()
            api_status = "✅ Подключено"
            user_count = len(users_response.users) if users_response and users_response.users else 0
        except Exception as e:
            api_status = f"❌ Ошибка: {str(e)[:50]}..."
            user_count = "N/A"
        
        status_text = f"""
🔧 **Статус бота**

**API подключение:** {api_status}
**Пользователей в системе:** {user_count}
**Текущее состояние:** {current_state or "Главное меню"}
**Данных в состоянии:** {len(state_data)} элементов

**Информация о пользователе:**
• ID: `{message.from_user.id}`
• Username: @{message.from_user.username or "отсутствует"}
• Имя: {message.from_user.full_name}

**Время запроса:** {message.date.strftime('%d.%m.%Y %H:%M:%S')}
"""
        
        await message.answer(status_text)
        
    except Exception as e:
        logger.error(f"Error in status handler: {e}")
        await message.answer(f"❌ Ошибка при получении статуса: {e}")

# ================ DEBUGGING HANDLERS ================

@main_router.message(Command("debug"), AuthFilter())
async def debug_handler(message: types.Message, state: FSMContext):
    """Debug information for administrators"""
    try:
        current_state = await state.get_state()
        state_data = await state.get_data()
        
        debug_text = f"""
🐛 **Отладочная информация**

**FSM State:** `{current_state}`
**State Data:** 
```json
{state_data}
```

**Message Info:**
• Message ID: {message.message_id}
• Chat ID: {message.chat.id}
• User ID: {message.from_user.id}
• Date: {message.date}

**Chat Type:** {message.chat.type}
"""
        
        await message.answer(debug_text)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка отладки: {e}")

# ================ ERROR HANDLERS ================

@main_router.message()
async def unknown_message_handler(message: types.Message, state: FSMContext):
    """Handle unknown messages from authorized users"""
    logger.info(f"Unknown message from authorized user {message.from_user.id}: {message.text}")
    
    await message.answer(
        "❓ Неизвестная команда.\n\n"
        "Используйте:\n"
        "• `/start` - Главное меню\n"
        "• `/help` - Справка\n"
        "• `/cancel` - Отмена операции"
    )

@main_router.callback_query()
async def unknown_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handle unknown callbacks from authorized users"""
    logger.info(f"Unknown callback from authorized user {callback.from_user.id}: {callback.data}")
    
    await callback.answer(
        "❓ Неизвестное действие. Попробуйте вернуться в главное меню.",
        show_alert=True
    )

# ================ UTILITY FUNCTIONS ================

def get_main_router() -> Router:
    """Get the main router with all handlers"""
    return main_router

def register_handlers(dp):
    """Register all handlers with the dispatcher"""
    dp.include_router(main_router)
    logger.info("All handlers registered successfully")

# ================ MIDDLEWARE SETUP ================

async def setup_middlewares(dp):
    """Setup middlewares for the dispatcher"""
    # Здесь можно добавить middleware для логирования, аналитики и т.д.
    logger.info("Middlewares setup completed")

# ================ ROUTER CONFIGURATION ================

# Configure router settings
main_router.message.filter(F.chat.type == "private")  # Only private chats
main_router.callback_query.filter(F.message.chat.type == "private")  # Only private chats

logger.info("Main router configured and ready")