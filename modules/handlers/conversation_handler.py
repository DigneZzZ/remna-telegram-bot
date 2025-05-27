from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
import logging

from modules.handlers.auth import AuthFilter
from modules.handlers.states import (
    UserStates, NodeStates, InboundStates, BulkStates, StatsStates
)

# Import all handlers
from modules.handlers.start_handler import router as start_router
from modules.handlers.menu_handler import router as menu_router
from modules.handlers.user_handlers import router as user_router

logger = logging.getLogger(__name__)

# Main router that includes all other routers
main_router = Router()

# Include existing sub-routers
main_router.include_router(start_router)
main_router.include_router(menu_router)
main_router.include_router(user_router)

# Include optional routers only if they exist
try:
    from modules.handlers.node_handlers import router as node_router
    main_router.include_router(node_router)
    logger.info("Node handlers included")
except ImportError:
    logger.warning("Node handlers not found, skipping")

try:
    from modules.handlers.inbound_handlers import router as inbound_router
    main_router.include_router(inbound_router)
    logger.info("Inbound handlers included")
except ImportError:
    logger.warning("Inbound handlers not found, skipping")

try:
    from modules.handlers.bulk_handlers import router as bulk_router
    main_router.include_router(bulk_router)
    logger.info("Bulk handlers included")
except ImportError:
    logger.warning("Bulk handlers not found, skipping")

try:
    from modules.handlers.stats_handlers import router as stats_router
    main_router.include_router(stats_router)
    logger.info("Stats handlers included")
except ImportError:
    logger.warning("Stats handlers not found, skipping")

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
    
    from modules.handlers.menu_handler import show_main_menu
    await show_main_menu(message)

@main_router.callback_query(F.data == "cancel", AuthFilter())
async def cancel_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    """Cancel current operation via callback and return to main menu"""
    await callback.answer()
    await state.clear()
    
    from modules.handlers.menu_handler import show_main_menu
    await show_main_menu(callback)

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
• `/status` - Статус бота и API

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

**API подключение:**
• Бот работает напрямую с Remnawave API
• Проверить статус можно командой `/status`
"""
    
    await message.answer(help_text)

# ================ STATUS HANDLER ================

@main_router.message(Command("status"), AuthFilter())
async def status_handler(message: types.Message, state: FSMContext):
    """Show current bot status using direct API calls"""
    try:
        from modules.api.client import RemnaAPI
        from modules.api.users import get_users_count
        from modules.api.nodes import get_all_nodes
        
        # Получаем текущее состояние
        current_state = await state.get_state()
        state_data = await state.get_data()
        
        # Проверяем подключение к API через прямые HTTP вызовы
        api_status = "❌ Недоступно"
        user_count = "N/A"
        node_count = "N/A"
        
        try:
            # Тестируем API через простой запрос
            test_result = await RemnaAPI.get("users", params={"size": 1})
            if test_result is not None:
                api_status = "✅ Подключено"
                
                # Получаем количество пользователей
                try:
                    user_count = await get_users_count()
                except Exception:
                    user_count = "Ошибка получения"
                
                # Получаем количество нод
                try:
                    nodes = await get_all_nodes()
                    node_count = len(nodes) if nodes else 0
                except Exception:
                    node_count = "Ошибка получения"
            else:
                api_status = "❌ API недоступно"
                
        except Exception as e:
            api_status = f"❌ Ошибка: {str(e)[:50]}..."
        
        status_text = f"""
🔧 **Статус бота**

**API подключение:** {api_status}
**Пользователей в системе:** {user_count}
**Нод в системе:** {node_count}
**Текущее состояние:** {current_state or "Главное меню"}
**Данных в состоянии:** {len(state_data)} элементов

**Информация о пользователе:**
• ID: `{message.from_user.id}`
• Username: @{message.from_user.username or "отсутствует"}
• Имя: {message.from_user.full_name}

**Время запроса:** {message.date.strftime('%d.%m.%Y %H:%M:%S')}

**API endpoints:**
• База: `{RemnaAPI()._get_default_headers().get('Host', 'N/A')}`
• Токен: {'✅ Настроен' if RemnaAPI()._get_default_headers().get('Authorization') else '❌ Отсутствует'}
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
        from modules.config import API_BASE_URL, API_TOKEN
        
        current_state = await state.get_state()
        state_data = await state.get_data()
        
        debug_text = f"""
🐛 **Отладочная информация**

**FSM State:** `{current_state}`
**State Data Items:** {len(state_data)}

**API Configuration:**
• Base URL: `{API_BASE_URL}`
• Token Length: {len(API_TOKEN) if API_TOKEN else 0}
• Token Present: {'✅' if API_TOKEN else '❌'}

**Message Info:**
• Message ID: {message.message_id}
• Chat ID: {message.chat.id}
• User ID: {message.from_user.id}
• Date: {message.date}
• Chat Type: {message.chat.type}

**Handlers Status:**
• Start: ✅ Loaded
• Menu: ✅ Loaded  
• Users: ✅ Loaded
• Nodes: {'✅' if 'node_router' in locals() else '❌'} {'Loaded' if 'node_router' in locals() else 'Not found'}
• Inbounds: {'✅' if 'inbound_router' in locals() else '❌'} {'Loaded' if 'inbound_router' in locals() else 'Not found'}
• Bulk: {'✅' if 'bulk_router' in locals() else '❌'} {'Loaded' if 'bulk_router' in locals() else 'Not found'}
• Stats: {'✅' if 'stats_router' in locals() else '❌'} {'Loaded' if 'stats_router' in locals() else 'Not found'}
"""
        
        await message.answer(debug_text)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка отладки: {e}")

# ================ API TEST HANDLER ================

@main_router.message(Command("apitest"), AuthFilter())
async def api_test_handler(message: types.Message):
    """Test API connectivity and endpoints"""
    try:
        from modules.api.client import RemnaAPI
        
        test_results = []
        
        # Список endpoints для тестирования
        test_endpoints = [
            ("users", {"size": 1}),
            ("nodes", None),
            ("system/stats", None),
            ("hosts", None)
        ]
        
        for endpoint, params in test_endpoints:
            try:
                logger.info(f"Testing endpoint: {endpoint}")
                result = await RemnaAPI.get(endpoint, params)
                
                if result is not None:
                    status = "✅ OK"
                    details = f"Response received ({type(result).__name__})"
                else:
                    status = "❌ FAIL"
                    details = "No response"
                    
            except Exception as e:
                status = "❌ ERROR"
                details = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
            
            test_results.append(f"• `{endpoint}`: {status} - {details}")
        
        test_text = f"""
🧪 **API Test Results**

**Endpoints tested:**
{chr(10).join(test_results)}

**Test completed at:** {message.date.strftime('%H:%M:%S')}
"""
        
        await message.answer(test_text)
        
    except Exception as e:
        logger.error(f"Error in API test handler: {e}")
        await message.answer(f"❌ Ошибка тестирования API: {e}")

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
        "• `/status` - Статус системы\n"
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