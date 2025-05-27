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
                inactive_users = user_stats.get('inactive', 0)
                logger.info(f"User stats parsed - total: {total_users}, active: {active_users}, inactive: {inactive_users}")
            else:
                # Fallback to count method
                logger.info("No user stats, falling back to count method...")
                total_users = await get_users_count()
                active_users = "N/A"
                inactive_users = "N/A"
                logger.info(f"User count fallback: {total_users}")
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            total_users = "Error"
            active_users = "Error"
            inactive_users = "Error"
            
        # Get node statistics
        try:
            logger.info("Getting node statistics...")
            nodes = await get_all_nodes()
            logger.info(f"Nodes response: {len(nodes) if nodes else 0} nodes")
            if nodes:
                total_nodes = len(nodes)
                online_nodes = sum(1 for node in nodes if node.get('isConnected') == True)
                offline_nodes = total_nodes - online_nodes
                logger.info(f"Node stats - total: {total_nodes}, online: {online_nodes}, offline: {offline_nodes}")
                # Debug node statuses
                for i, node in enumerate(nodes[:3]):  # Log first 3 nodes for debugging
                    logger.info(f"Node {i}: isConnected={node.get('isConnected')}, name={node.get('name', 'Unknown')}")
            else:
                total_nodes = 0
                online_nodes = 0
                offline_nodes = 0
        except Exception as e:
            logger.error(f"Error getting node stats: {e}")
            total_nodes = "Error"
            online_nodes = "Error"
            offline_nodes = "Error"

        # Format statistics
        stats = "📈 **Системная статистика**\n\n"
        
        if isinstance(total_users, int) and isinstance(active_users, int) and isinstance(inactive_users, int):
            stats += f"👥 **Пользователи ({total_users} всего):**\n"
            stats += f"  • ✅ Активных: {active_users}\n"
            stats += f"  • ❌ Неактивных: {inactive_users}\n\n"
        else:
            stats += f"👥 **Пользователи:** {total_users} всего\n\n"
            
        if isinstance(total_nodes, int) and isinstance(online_nodes, int) and isinstance(offline_nodes, int):
            node_status = "✅" if offline_nodes == 0 else "❌"
            stats += f"🖥️ **Серверы:** {online_nodes}/{total_nodes} онлайн ({node_status} {offline_nodes} офлайн)\n\n"
            stats += f"🔌 **Подключения:** 0 активных\n\n"  # TODO: Implement connections count
        else:
            stats += f"🖥️ **Серверы:** {total_nodes} всего\n\n"
        
        logger.info(f"Final stats: {stats.replace('*', '').replace('📈', '').replace('👥', '').replace('🖥️', '').strip()}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return "📈 **Системная статистика**\n\n❌ Ошибка загрузки данных"

@router.callback_query(F.data == "main_menu", AuthFilter())
async def handle_main_menu(callback: types.CallbackQuery):
    """Handle main menu callback"""
    await show_main_menu(callback)

@router.callback_query(F.data == "back", AuthFilter())
async def handle_back(callback: types.CallbackQuery):
    """Handle back button"""
    await show_main_menu(callback)

# Восстанавливаем основной обработчик меню, но делаем его более гибким
@router.callback_query(
    F.data.in_(["users", "nodes", "stats", "hosts", "inbounds", "bulk"]), 
    AuthFilter()
)
async def handle_main_menu_callbacks(callback: types.CallbackQuery):
    """Handle main menu callbacks"""
    callback_data = callback.data
    logger.info(f"Handling main menu callback: {callback_data}")
    
    try:
        # Import handlers here to avoid circular imports
        if callback_data == "users":
            from modules.handlers.user_handlers import show_users_menu
            await show_users_menu(callback)
        elif callback_data == "nodes":
            try:
                from modules.handlers.node_handlers import show_nodes_menu
                await show_nodes_menu(callback)
            except ImportError:
                logger.warning("Node handlers not implemented yet")
                await callback.answer("🔧 Управление серверами в разработке", show_alert=True)
        elif callback_data == "stats":
            try:
                from modules.handlers.stats_handlers import show_stats_menu
                await show_stats_menu(callback)
            except ImportError:
                logger.warning("Stats handlers not implemented yet")
                await callback.answer("🔧 Статистика в разработке", show_alert=True)
        elif callback_data == "hosts":
            try:
                from modules.handlers.host_handlers import show_hosts_menu
                await show_hosts_menu(callback)
            except ImportError:
                logger.warning("Host handlers not implemented yet")
                await callback.answer("🔧 Управление хостами в разработке", show_alert=True)
        elif callback_data == "inbounds":
            try:
                from modules.handlers.inbound_handlers import show_inbounds_menu
                await show_inbounds_menu(callback)
            except ImportError:
                logger.warning("Inbound handlers not implemented yet")
                await callback.answer("🔧 Управление Inbounds в разработке", show_alert=True)
        elif callback_data == "bulk":
            try:
                from modules.handlers.bulk_handlers import show_bulk_menu
                await show_bulk_menu(callback)
            except ImportError:
                logger.warning("Bulk handlers not implemented yet")
                # Показываем базовое меню массовых операций из user_handlers
                try:
                    from modules.handlers.user_handlers import show_mass_operations
                    await show_mass_operations(callback)
                except ImportError:
                    await callback.answer("🔧 Массовые операции в разработке", show_alert=True)
        else:
            logger.warning(f"Unknown main menu callback data: {callback_data}")
            await callback.answer("🔧 Раздел в разработке", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error handling callback {callback_data}: {e}")
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)

def register_menu_handlers(dp):
    """Register menu handlers"""
    dp.include_router(router)