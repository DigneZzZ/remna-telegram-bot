from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from modules.handlers.auth import AuthFilter
from modules.api.users import get_users_count, get_users_stats
from modules.api.nodes import get_all_nodes

logger = logging.getLogger(__name__)

router = Router()

async def show_main_menu(message_or_callback: types.Message | types.CallbackQuery, text: str = None):
    """Show main menu with system statistics"""
    # Build keyboard
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👥 Управление пользователями", callback_data="users"))
    builder.row(types.InlineKeyboardButton(text="🖥️ Управление серверами", callback_data="nodes"))
    builder.row(types.InlineKeyboardButton(text="📊 Статистика системы", callback_data="stats"))
    builder.row(types.InlineKeyboardButton(text="🌐 Управление хостами", callback_data="hosts"))
    builder.row(types.InlineKeyboardButton(text="🔌 Управление Inbounds", callback_data="inbounds"))
    builder.row(types.InlineKeyboardButton(text="🔄 Массовые операции", callback_data="bulk"))
    
    # Get system stats
    stats_text = await get_system_stats()
    
    message_text = text or "🎛️ **Главное меню Remnawave Admin**\n\n"
    message_text += stats_text + "\n"
    message_text += "Выберите раздел для управления:"

    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.answer()
        await message_or_callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
    else:
        await message_or_callback.answer(
            text=message_text,
            reply_markup=builder.as_markup()
        )

async def get_system_stats():
    """Get system statistics for dashboard"""
    try:
        # Get user statistics
        try:
            logger.info("Getting user statistics...")
            user_stats = await get_users_stats()
            logger.info(f"User stats response: {user_stats}")
            if user_stats:
                total_users = user_stats.get('total', 0)
                active_users = user_stats.get('active', 0)
                logger.info(f"User stats parsed - total: {total_users}, active: {active_users}")
            else:
                # Fallback to count method
                logger.info("No user stats, falling back to count method...")
                total_users = await get_users_count()
                active_users = "N/A"
                logger.info(f"User count fallback: {total_users}")
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            total_users = "Error"
            active_users = "Error"
            
        # Get node statistics
        try:
            logger.info("Getting node statistics...")
            nodes = await get_all_nodes()
            logger.info(f"Nodes response: {len(nodes) if nodes else 0} nodes")
            if nodes:
                total_nodes = len(nodes)
                online_nodes = sum(1 for node in nodes if node.get('isConnected') == True)
                logger.info(f"Node stats - total: {total_nodes}, online: {online_nodes}")
                # Debug node statuses
                for i, node in enumerate(nodes[:3]):  # Log first 3 nodes for debugging
                    logger.info(f"Node {i}: isConnected={node.get('isConnected')}, name={node.get('name', 'Unknown')}")
            else:
                total_nodes = 0
                online_nodes = 0
        except Exception as e:
            logger.error(f"Error getting node stats: {e}")
            total_nodes = "Error"
            online_nodes = "Error"

        # Format statistics
        stats = "📊 **Статистика системы:**\n"
        stats += f"👥 Пользователи: {total_users} (активных: {active_users})\n"
        stats += f"🖥️ Серверы: {online_nodes}/{total_nodes} онлайн"
        
        logger.info(f"Final stats: {stats.replace('*', '').replace('📊', '').replace('👥', '').replace('🖥️', '').strip()}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return "📊 **Статистика системы:** Ошибка загрузки"

@router.callback_query(F.data == "main_menu", AuthFilter())
async def handle_main_menu(callback: types.CallbackQuery):
    """Handle main menu callback"""
    await show_main_menu(callback)

@router.callback_query(F.data == "back", AuthFilter())
async def handle_back(callback: types.CallbackQuery):
    """Handle back button"""
    await show_main_menu(callback)

# Удаляем этот обработчик, поскольку специфичные обработчики для каждого типа callback уже есть в соответствующих файлах
# Этот обработчик мешал правильной маршрутизации callback'ов из подменю

# @router.callback_query(
#     F.data.in_(["users", "nodes", "stats", "hosts", "inbounds", "bulk"]), 
#     AuthFilter()
# )
# async def handle_main_menu_callbacks(callback: types.CallbackQuery):
#     """Handle main menu callbacks"""
#     callback_data = callback.data
#     logger.info(f"Handling main menu callback: {callback_data}")
#     
#     # Import handlers here to avoid circular imports
#     if callback_data == "users":
#         from modules.handlers.user_handlers import show_users_menu
#         await show_users_menu(callback)
#     elif callback_data == "nodes":
#         from modules.handlers.node_handlers import show_nodes_menu
#         await show_nodes_menu(callback)
#     elif callback_data == "stats":
#         from modules.handlers.stats_handlers import show_stats_menu
#         await show_stats_menu(callback)
#     elif callback_data == "hosts":
#         from modules.handlers.host_handlers import show_hosts_menu
#         await show_hosts_menu(callback)
#     elif callback_data == "inbounds":
#         from modules.handlers.inbound_handlers import show_inbounds_menu
#         await show_inbounds_menu(callback)
#     elif callback_data == "bulk":
#         from modules.handlers.bulk_handlers import show_bulk_menu
#         await show_bulk_menu(callback)
#     else:
#         logger.warning(f"Unknown main menu callback data: {callback_data}")
#         await callback.answer("🔧 Раздел в разработке", show_alert=True)

def register_menu_handlers(dp):
    """Register menu handlers"""
    dp.include_router(router)
