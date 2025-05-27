from aiogram import Router, types, F
from aiogram.filters import  StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from modules.handlers.auth import AuthFilter
from modules.handlers.states import InboundStates
from modules.api.client import RemnaAPI
from modules.utils.formatters_aiogram import (
    format_bytes, format_datetime, escape_markdown,
    format_inbound_details
)

logger = logging.getLogger(__name__)

router = Router()

# ================ INBOUNDS MENU ================

@router.callback_query(F.data == "inbounds", AuthFilter())
async def handle_inbounds_menu(callback: types.CallbackQuery, state: FSMContext):
    """Handle inbounds menu selection"""
    await callback.answer()
    await state.clear()
    await show_inbounds_menu(callback)

async def show_inbounds_menu(callback: types.CallbackQuery):
    """Show inbounds menu"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📋 Список всех Inbounds", callback_data="list_inbounds"))
    builder.row(types.InlineKeyboardButton(text="📋 Список с деталями", callback_data="list_full_inbounds"))
    builder.row(types.InlineKeyboardButton(text="➕ Создать Inbound", callback_data="create_inbound"))
    builder.row(types.InlineKeyboardButton(text="📊 Статистика Inbounds", callback_data="inbounds_stats"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "🔌 **Управление Inbounds**\n\n"
    
    try:
        # Получаем краткую статистику для превью
        sdk = RemnaAPI.get_sdk()
        inbounds = await sdk.inbounds.get_all_inbounds()
        
        if inbounds:
            total_inbounds = len(inbounds)
            active_inbounds = sum(1 for inbound in inbounds if inbound.is_active)
            
            message += f"**📈 Статистика:**\n"
            message += f"• Всего Inbounds: {total_inbounds}\n"
            message += f"• Активных: {active_inbounds}\n"
            message += f"• Неактивных: {total_inbounds - active_inbounds}\n\n"
        
    except Exception as e:
        logger.error(f"Error getting inbounds stats: {e}")
        message += "**📈 Статистика:** Недоступна\n\n"
    
    message += "Выберите действие:"

    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

# ================ LIST INBOUNDS ================

@router.callback_query(F.data == "list_inbounds", AuthFilter())
async def list_inbounds(callback: types.CallbackQuery, state: FSMContext):
    """List all inbounds"""
    await callback.answer()
    await callback.message.edit_text("🔌 Загрузка списка Inbounds...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        inbounds = await sdk.inbounds.get_all_inbounds()
        
        if not inbounds:
            await callback.message.edit_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
                ]])
            )
            return
        
        # Сохраняем список в состоянии для пагинации
        inbounds_data = [inbound.model_dump() for inbound in inbounds]
        await state.update_data(inbounds=inbounds_data, page=0)
        await state.set_state(InboundStates.selecting_inbound)
        
        await show_inbounds_page(callback.message, inbounds_data, 0, state)
        
    except Exception as e:
        logger.error(f"Error listing inbounds: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке списка Inbounds.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
            ]])
        )

async def show_inbounds_page(message: types.Message, inbounds: list, page: int, state: FSMContext, per_page: int = 8):
    """Show inbounds page with pagination"""
    total_pages = (len(inbounds) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_inbounds = inbounds[start_idx:end_idx]
    
    builder = InlineKeyboardBuilder()
    
    # Список inbound'ов на текущей странице
    for inbound in page_inbounds:
        inbound_name = f"🔌 {inbound.get('tag', 'Unknown')}"
        inbound_info = f" ({inbound.get('type', 'Unknown')}, :{inbound.get('port', 'N/A')})"
        
        if len(inbound_name + inbound_info) > 60:
            display_name = inbound_name[:50] + "..."
        else:
            display_name = inbound_name + inbound_info
        
        builder.row(types.InlineKeyboardButton(
            text=display_name,
            callback_data=f"view_inbound:{inbound.get('uuid', '')}"
        ))
    
    # Пагинация
    if total_pages > 1:
        pagination_buttons = []
        
        if page > 0:
            pagination_buttons.append(types.InlineKeyboardButton(
                text="◀️ Пред",
                callback_data=f"inbounds_page:{page-1}"
            ))
        
        pagination_buttons.append(types.InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="noop"
        ))
        
        if page < total_pages - 1:
            pagination_buttons.append(types.InlineKeyboardButton(
                text="След ▶️",
                callback_data=f"inbounds_page:{page+1}"
            ))
        
        builder.row(*pagination_buttons)
    
    # Кнопки управления
    builder.row(
        types.InlineKeyboardButton(text="🔄 Обновить", callback_data="list_inbounds"),
        types.InlineKeyboardButton(text="📋 С деталями", callback_data="list_full_inbounds")
    )
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds"))
    
    message_text = f"🔌 **Список Inbounds** ({len(inbounds)} всего)\n"
    message_text += f"📄 Страница {page + 1} из {total_pages}\n\n"
    message_text += "Выберите Inbound для просмотра подробной информации:"
    
    try:
        await message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
    except:
        await message.answer(
            text=message_text,
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("inbounds_page:"), AuthFilter())
async def handle_inbounds_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Handle inbounds pagination"""
    await callback.answer()
    
    page = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    inbounds = data.get('inbounds', [])
    
    await state.update_data(page=page)
    await show_inbounds_page(callback.message, inbounds, page, state)

# ================ LIST FULL INBOUNDS ================

@router.callback_query(F.data == "list_full_inbounds", AuthFilter())
async def list_full_inbounds(callback: types.CallbackQuery, state: FSMContext):
    """List all inbounds with full details"""
    await callback.answer()
    await callback.message.edit_text("🔌 Загрузка полного списка Inbounds...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        inbounds = await sdk.inbounds.get_all_inbounds_detailed()
        
        if not inbounds:
            await callback.message.edit_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
                ]])
            )
            return
        
        # Сохраняем список в состоянии для пагинации
        inbounds_data = [inbound.model_dump() if hasattr(inbound, 'model_dump') else inbound for inbound in inbounds]
        await state.update_data(full_inbounds=inbounds_data, page=0)
        await state.set_state(InboundStates.viewing_full_inbounds)
        
        await show_full_inbounds_page(callback.message, inbounds_data, 0, state)
        
    except Exception as e:
        logger.error(f"Error listing full inbounds: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке списка Inbounds.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
            ]])
        )

async def show_full_inbounds_page(message: types.Message, inbounds: list, page: int, state: FSMContext, per_page: int = 6):
    """Show full inbounds page with pagination"""
    total_pages = (len(inbounds) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_inbounds = inbounds[start_idx:end_idx]
    
    builder = InlineKeyboardBuilder()
    
    # Список inbound'ов на текущей странице с деталями
    for inbound in page_inbounds:
        inbound_name = f"🔌 {inbound.get('tag', 'Unknown')}"
        
        # Дополнительная информация для детального просмотра
        details = []
        if inbound.get('type'):
            details.append(f"{inbound['type']}")
        if inbound.get('port'):
            details.append(f":{inbound['port']}")
        
        # Статистика пользователей и нод (если доступна)
        if 'users' in inbound and isinstance(inbound['users'], dict):
            enabled_users = inbound['users'].get('enabled', 0)
            details.append(f"👥{enabled_users}")
        
        if 'nodes' in inbound and isinstance(inbound['nodes'], dict):
            enabled_nodes = inbound['nodes'].get('enabled', 0)
            details.append(f"🖥️{enabled_nodes}")
        
        display_name = inbound_name
        if details:
            detail_str = " (" + " | ".join(details) + ")"
            if len(display_name + detail_str) <= 60:
                display_name += detail_str
        
        builder.row(types.InlineKeyboardButton(
            text=display_name,
            callback_data=f"view_full_inbound:{inbound.get('uuid', '')}"
        ))
    
    # Пагинация
    if total_pages > 1:
        pagination_buttons = []
        
        if page > 0:
            pagination_buttons.append(types.InlineKeyboardButton(
                text="◀️ Пред",
                callback_data=f"full_inbounds_page:{page-1}"
            ))
        
        pagination_buttons.append(types.InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="noop"
        ))
        
        if page < total_pages - 1:
            pagination_buttons.append(types.InlineKeyboardButton(
                text="След ▶️",
                callback_data=f"full_inbounds_page:{page+1}"
            ))
        
        builder.row(*pagination_buttons)
    
    # Кнопки управления
    builder.row(
        types.InlineKeyboardButton(text="🔄 Обновить", callback_data="list_full_inbounds"),
        types.InlineKeyboardButton(text="📋 Простой список", callback_data="list_inbounds")
    )
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds"))
    
    message_text = f"🔌 **Inbounds с подробностями** ({len(inbounds)} всего)\n"
    message_text += f"📄 Страница {page + 1} из {total_pages}\n\n"
    message_text += "Выберите Inbound для просмотра подробной информации:"
    
    try:
        await message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
    except:
        await message.answer(
            text=message_text,
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("full_inbounds_page:"), AuthFilter())
async def handle_full_inbounds_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Handle full inbounds pagination"""
    await callback.answer()
    
    page = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    inbounds = data.get('full_inbounds', [])
    
    await state.update_data(page=page)
    await show_full_inbounds_page(callback.message, inbounds, page, state)

# ================ VIEW INBOUND DETAILS ================

@router.callback_query(F.data.startswith("view_inbound:"), AuthFilter())
async def view_inbound(callback: types.CallbackQuery, state: FSMContext):
    """View inbound details"""
    await callback.answer()
    
    inbound_uuid = callback.data.split(":", 1)[1]
    await show_inbound_details(callback.message, inbound_uuid, state)

@router.callback_query(F.data.startswith("view_full_inbound:"), AuthFilter())
async def view_full_inbound(callback: types.CallbackQuery, state: FSMContext):
    """View full inbound details"""
    await callback.answer()
    
    inbound_uuid = callback.data.split(":", 1)[1]
    await show_inbound_details(callback.message, inbound_uuid, state, is_full=True)

async def show_inbound_details(message: types.Message, uuid: str, state: FSMContext, is_full: bool = False):
    """Show inbound details"""
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем детальную информацию об inbound
        if is_full:
            inbounds = await sdk.inbounds.get_all_inbounds_detailed()
        else:
            inbounds = await sdk.inbounds.get_all_inbounds()
        
        if not inbounds:
            await message.edit_text(
                "❌ Inbound не найден или ошибка при получении данных.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
                ]])
            )
            return
        
        # Ищем inbound по UUID
        inbound = None
        for ib in inbounds:
            ib_data = ib.model_dump() if hasattr(ib, 'model_dump') else ib
            if ib_data.get('uuid') == uuid:
                inbound = ib_data
                break
        
        if not inbound:
            await message.edit_text(
                "❌ Inbound не найден или ошибка при получении данных.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
                ]])
            )
            return
        
        # Сохраняем текущий inbound в состоянии
        await state.update_data(selected_inbound=inbound)
        await state.set_state(InboundStates.viewing_inbound)
        
        # Формируем сообщение с деталями
        message_text = format_inbound_details(inbound)
        
        # Создаем клавиатуру с действиями
        builder = InlineKeyboardBuilder()
        
        # Основные действия
        builder.row(
            types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_inbound:{uuid}"),
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_inbound:{uuid}")
        )
        
        # Управление пользователями
        builder.row(
            types.InlineKeyboardButton(text="👥 + Всем пользователям", callback_data=f"add_to_users:{uuid}"),
            types.InlineKeyboardButton(text="👥 - У всех пользователей", callback_data=f"remove_from_users:{uuid}")
        )
        
        # Управление нодами
        builder.row(
            types.InlineKeyboardButton(text="🖥️ + Всем серверам", callback_data=f"add_to_nodes:{uuid}"),
            types.InlineKeyboardButton(text="🖥️ - У всех серверов", callback_data=f"remove_from_nodes:{uuid}")
        )
        
        # Состояние inbound'а
        if inbound.get('is_active', True):
            builder.row(types.InlineKeyboardButton(text="⏸️ Деактивировать", callback_data=f"deactivate_inbound:{uuid}"))
        else:
            builder.row(types.InlineKeyboardButton(text="▶️ Активировать", callback_data=f"activate_inbound:{uuid}"))
        
        # Опасные действия
        builder.row(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_inbound:{uuid}"))
        
        # Навигация
        back_callback = "list_full_inbounds" if is_full else "list_inbounds"
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data=back_callback))
        
        await message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing inbound details: {e}")
        await message.edit_text(
            "❌ Ошибка при получении данных Inbound.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
            ]])
        )

# ================ INBOUND MANAGEMENT ACTIONS ================

@router.callback_query(F.data.startswith("add_to_users:"), AuthFilter())
async def add_inbound_to_all_users(callback: types.CallbackQuery, state: FSMContext):
    """Add inbound to all users"""
    await callback.answer("➕ Добавляю Inbound всем пользователям...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        result = await sdk.inbounds.add_inbound_to_users(uuid)
        
        await callback.answer(f"✅ Inbound добавлен всем пользователям. Затронуто: {result}", show_alert=True)
        
        # Обновляем информацию об inbound
        await show_inbound_details(callback.message, uuid, state)
        
    except Exception as e:
        logger.error(f"Error adding inbound to users: {e}")
        await callback.answer("❌ Ошибка при добавлении Inbound пользователям", show_alert=True)

@router.callback_query(F.data.startswith("remove_from_users:"), AuthFilter())
async def remove_inbound_from_all_users(callback: types.CallbackQuery, state: FSMContext):
    """Remove inbound from all users"""
    await callback.answer("➖ Удаляю Inbound у всех пользователей...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        result = await sdk.inbounds.remove_inbound_from_users(uuid)
        
        await callback.answer(f"✅ Inbound удален у всех пользователей. Затронуто: {result}", show_alert=True)
        
        # Обновляем информацию об inbound
        await show_inbound_details(callback.message, uuid, state)
        
    except Exception as e:
        logger.error(f"Error removing inbound from users: {e}")
        await callback.answer("❌ Ошибка при удалении Inbound у пользователей", show_alert=True)

@router.callback_query(F.data.startswith("add_to_nodes:"), AuthFilter())
async def add_inbound_to_all_nodes(callback: types.CallbackQuery, state: FSMContext):
    """Add inbound to all nodes"""
    await callback.answer("➕ Добавляю Inbound всем серверам...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        result = await sdk.inbounds.add_inbound_to_nodes(uuid)
        
        await callback.answer(f"✅ Inbound добавлен всем серверам. Затронуто: {result}", show_alert=True)
        
        # Обновляем информацию об inbound
        await show_inbound_details(callback.message, uuid, state)
        
    except Exception as e:
        logger.error(f"Error adding inbound to nodes: {e}")
        await callback.answer("❌ Ошибка при добавлении Inbound серверам", show_alert=True)

@router.callback_query(F.data.startswith("remove_from_nodes:"), AuthFilter())
async def remove_inbound_from_all_nodes(callback: types.CallbackQuery, state: FSMContext):
    """Remove inbound from all nodes"""
    await callback.answer("➖ Удаляю Inbound у всех серверов...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        result = await sdk.inbounds.remove_inbound_from_nodes(uuid)
        
        await callback.answer(f"✅ Inbound удален у всех серверов. Затронуто: {result}", show_alert=True)
        
        # Обновляем информацию об inbound
        await show_inbound_details(callback.message, uuid, state)
        
    except Exception as e:
        logger.error(f"Error removing inbound from nodes: {e}")
        await callback.answer("❌ Ошибка при удалении Inbound у серверов", show_alert=True)

@router.callback_query(F.data.startswith("activate_inbound:"), AuthFilter())
async def activate_inbound(callback: types.CallbackQuery, state: FSMContext):
    """Activate inbound"""
    await callback.answer()
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.inbounds.activate_inbound(uuid)
        
        if success:
            await callback.answer("✅ Inbound активирован", show_alert=True)
            await show_inbound_details(callback.message, uuid, state)
        else:
            await callback.answer("❌ Ошибка при активации", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error activating inbound: {e}")
        await callback.answer("❌ Ошибка при активации Inbound", show_alert=True)

@router.callback_query(F.data.startswith("deactivate_inbound:"), AuthFilter())
async def deactivate_inbound(callback: types.CallbackQuery, state: FSMContext):
    """Deactivate inbound"""
    await callback.answer()
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.inbounds.deactivate_inbound(uuid)
        
        if success:
            await callback.answer("⏸️ Inbound деактивирован", show_alert=True)
            await show_inbound_details(callback.message, uuid, state)
        else:
            await callback.answer("❌ Ошибка при деактивации", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error deactivating inbound: {e}")
        await callback.answer("❌ Ошибка при деактивации Inbound", show_alert=True)

@router.callback_query(F.data.startswith("refresh_inbound:"), AuthFilter())
async def refresh_inbound(callback: types.CallbackQuery, state: FSMContext):
    """Refresh inbound details"""
    await callback.answer("🔄 Обновление данных...")
    
    uuid = callback.data.split(":", 1)[1]
    await show_inbound_details(callback.message, uuid, state)

@router.callback_query(F.data.startswith("delete_inbound:"), AuthFilter())
async def delete_inbound_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm inbound deletion"""
    await callback.answer()
    
    uuid = callback.data.split(":", 1)[1]
    
    data = await state.get_data()
    inbound = data.get('selected_inbound', {})
    inbound_name = inbound.get('tag', 'Unknown')
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🗑️ Да, удалить",
        callback_data=f"confirm_delete_inbound:{uuid}"
    ))
    builder.row(types.InlineKeyboardButton(
        text="❌ Отмена",
        callback_data=f"view_inbound:{uuid}"
    ))
    
    await callback.message.edit_text(
        f"🗑️ **Удаление Inbound**\n\n"
        f"**Название:** {escape_markdown(inbound_name)}\n"
        f"**UUID:** `{uuid}`\n\n"
        f"⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n"
        f"Inbound будет удален у всех пользователей и серверов.\n\n"
        f"Продолжить?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("confirm_delete_inbound:"), AuthFilter())
async def confirm_delete_inbound(callback: types.CallbackQuery, state: FSMContext):
    """Confirm inbound deletion"""
    await callback.answer()
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.inbounds.delete_inbound(uuid)
        
        if success:
            await callback.answer("✅ Inbound удален", show_alert=True)
            await state.clear()
            
            await callback.message.edit_text(
                "✅ **Inbound успешно удален**\n\n"
                "Inbound был удален из системы.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="📋 К списку Inbounds", callback_data="list_inbounds"),
                    types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
                ]])
            )
        else:
            await callback.answer("❌ Ошибка при удалении", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error deleting inbound: {e}")
        await callback.answer("❌ Ошибка при удалении Inbound", show_alert=True)

# ================ INBOUNDS STATISTICS ================

@router.callback_query(F.data == "inbounds_stats", AuthFilter())
async def show_inbounds_statistics(callback: types.CallbackQuery):
    """Show inbounds statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка статистики Inbounds...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        inbounds = await sdk.inbounds.get_all_inbounds_detailed()
        
        if not inbounds:
            await callback.message.edit_text(
                "❌ Не удалось получить статистику Inbounds",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
                ]])
            )
            return
        
        # Анализируем данные
        total_inbounds = len(inbounds)
        active_inbounds = sum(1 for ib in inbounds if ib.get('is_active', True))
        
        # Статистика по типам
        type_stats = {}
        port_usage = {}
        total_users_assigned = 0
        total_nodes_assigned = 0
        
        for inbound in inbounds:
            inbound_data = inbound.model_dump() if hasattr(inbound, 'model_dump') else inbound
            
            # Статистика по типам
            inbound_type = inbound_data.get('type', 'Unknown')
            if inbound_type not in type_stats:
                type_stats[inbound_type] = 0
            type_stats[inbound_type] += 1
            
            # Статистика по портам
            port = inbound_data.get('port')
            if port:
                if port not in port_usage:
                    port_usage[port] = 0
                port_usage[port] += 1
            
            # Статистика пользователей и нод
            if 'users' in inbound_data and isinstance(inbound_data['users'], dict):
                total_users_assigned += inbound_data['users'].get('enabled', 0)
            
            if 'nodes' in inbound_data and isinstance(inbound_data['nodes'], dict):
                total_nodes_assigned += inbound_data['nodes'].get('enabled', 0)
        
        # Формируем сообщение
        message_text = "📊 **Статистика Inbounds**\n\n"
        
        # Общая статистика
        message_text += "**📈 Общая статистика:**\n"
        message_text += f"• Всего Inbounds: {total_inbounds}\n"
        message_text += f"• Активных: {active_inbounds}\n"
        message_text += f"• Неактивных: {total_inbounds - active_inbounds}\n"
        message_text += f"• Назначено пользователям: {total_users_assigned}\n"
        message_text += f"• Назначено серверам: {total_nodes_assigned}\n\n"
        
        # Статистика по типам
        if type_stats:
            message_text += "**🔧 По типам:**\n"
            for inbound_type, count in sorted(type_stats.items()):
                percentage = (count / total_inbounds) * 100
                message_text += f"• {inbound_type}: {count} ({percentage:.1f}%)\n"
            message_text += "\n"
        
        # Наиболее используемые порты
        if port_usage:
            sorted_ports = sorted(port_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            message_text += "**🔢 Популярные порты:**\n"
            for port, count in sorted_ports:
                message_text += f"• Порт {port}: {count} inbound(ов)\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="inbounds_stats"),
            types.InlineKeyboardButton(text="📋 Список", callback_data="list_inbounds")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds"))
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting inbounds statistics: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики Inbounds",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
            ]])
        )

# ================ CREATE INBOUND (PLACEHOLDER) ================

@router.callback_query(F.data == "create_inbound", AuthFilter())
async def create_inbound_placeholder(callback: types.CallbackQuery):
    """Create inbound placeholder"""
    await callback.answer()
    
    await callback.message.edit_text(
        "➕ **Создание Inbound**\n\n"
        "🚧 Функция создания Inbound находится в разработке.\n\n"
        "В текущей версии доступно только управление существующими Inbound'ами:\n"
        "• Просмотр списка\n"
        "• Редактирование параметров\n"
        "• Назначение пользователям и серверам\n"
        "• Активация/деактивация",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="📋 К списку Inbounds", callback_data="list_inbounds"),
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
        ]])
    )

# ================ EDIT INBOUND (PLACEHOLDER) ================

@router.callback_query(F.data.startswith("edit_inbound:"), AuthFilter())
async def edit_inbound_placeholder(callback: types.CallbackQuery, state: FSMContext):
    """Edit inbound placeholder"""
    await callback.answer()
    
    uuid = callback.data.split(":", 1)[1]
    
    await callback.message.edit_text(
        "✏️ **Редактирование Inbound**\n\n"
        "🚧 Функция редактирования Inbound находится в разработке.\n\n"
        "В текущей версии доступны следующие операции:\n"
        "• Активация/деактивация\n"
        "• Назначение пользователям\n"
        "• Назначение серверам\n"
        "• Удаление",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 К Inbound", callback_data=f"view_inbound:{uuid}"),
            types.InlineKeyboardButton(text="📋 К списку", callback_data="list_inbounds")
        ]])
    )

# ================ NO-OP CALLBACK ================

@router.callback_query(F.data == "noop", AuthFilter())
async def noop_callback(callback: types.CallbackQuery):
    """No-operation callback for pagination display"""
    await callback.answer()
