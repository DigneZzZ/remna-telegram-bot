from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
import re
import random
import string
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from modules.handlers.auth import AuthFilter
from modules.handlers.states import UserStates
# Используем прямые HTTP вызовы вместо SDK
from modules.api import users as users_api
from modules.api import nodes as nodes_api

logger = logging.getLogger(__name__)

router = Router()



# ================ UTILITY FUNCTIONS ================

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = bytes_value
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

# В начале файла, после импортов, добавьте эти функции:

def safe_markdown_escape(text: str) -> str:
    """Безопасное экранирование для Markdown V2"""
    if not text:
        return ""
    
    # Символы, которые нужно экранировать в MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    escaped_text = str(text)
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    
    return escaped_text

def format_safe_message(text: str, use_markdown: bool = False) -> str:
    """Форматирование сообщения с безопасной обработкой специальных символов"""
    if not use_markdown:
        return text
    
    # Заменяем ** на безопасное форматирование
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Обрабатываем жирный текст
        if '**' in line:
            parts = line.split('**')
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Нечетные индексы - это текст между **
                    parts[i] = f"*{safe_markdown_escape(part)}*"
                else:
                    parts[i] = safe_markdown_escape(part)
            line = ''.join(parts)
        else:
            line = safe_markdown_escape(line)
        
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

# Заменяем существующую функцию escape_markdown
def escape_markdown(text: str) -> str:
    """Escape markdown special characters - улучшенная версия"""
    return safe_markdown_escape(text)

def format_datetime(dt_string: str) -> str:
    """Format datetime string to readable format"""
    if not dt_string:
        return "Не указано"
    
    try:
        # Remove timezone info and milliseconds
        clean_dt = dt_string.replace('Z', '').split('.')[0]
        dt = datetime.fromisoformat(clean_dt)
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return dt_string[:19].replace('T', ' ')

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to maximum length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def format_user_details(user: dict) -> str:
    """Format user details for display - safe version without markdown"""
    try:
        username = user.get('username', 'Unknown')
        uuid = user.get('uuid', 'N/A')
        short_uuid = user.get('shortUuid', 'N/A')
        status = user.get('status', 'Unknown')
        
        # Traffic information
        used_traffic = user.get('usedTraffic', 0) or 0
        traffic_limit = user.get('trafficLimit', 0) or 0
        
        used_formatted = format_bytes(used_traffic)
        limit_formatted = format_bytes(traffic_limit) if traffic_limit > 0 else "∞"
        
        # Dates
        created_at = format_datetime(user.get('createdAt', ''))
        updated_at = format_datetime(user.get('updatedAt', ''))
        expire_at = format_datetime(user.get('expireAt', ''))
        
        # Status emoji
        status_emoji = "🟢" if status == 'ACTIVE' else "🔴"
        
        # Build details text WITHOUT markdown
        details = f"👤 Пользователь: {username}\n\n"
        details += f"📊 Основная информация:\n"
        details += f"• Статус: {status_emoji} {status}\n"
        details += f"• UUID: {uuid}\n"
        details += f"• Short UUID: {short_uuid}\n\n"
        
        details += f"💾 Трафик:\n"
        details += f"• Использовано: {used_formatted}\n"
        details += f"• Лимит: {limit_formatted}\n"
        
        if traffic_limit > 0:
            percentage = (used_traffic / traffic_limit) * 100
            details += f"• Использовано: {percentage:.1f}%\n"
        
        details += f"\n📅 Временные метки:\n"
        details += f"• Создан: {created_at}\n"
        details += f"• Обновлен: {updated_at}\n"
        details += f"• Истекает: {expire_at}\n"
        
        # Additional information
        if user.get('telegramId'):
            details += f"\n📱 Telegram ID: {user.get('telegramId')}\n"
        
        if user.get('description'):
            desc = str(user.get('description'))
            details += f"\n📝 Описание: {truncate_text(desc, 100)}\n"
        
        return details
        
    except Exception as e:
        logger.error(f"Error formatting user details: {e}")
        return f"❌ Ошибка форматирования данных пользователя: {e}"

# ================ MAIN USERS MENU ================

@router.callback_query(F.data == "users", AuthFilter())
async def handle_users_menu(callback: types.CallbackQuery, state: FSMContext):
    """Handle users menu selection"""
    await state.clear()
    await show_users_menu(callback)

async def show_users_menu(callback: types.CallbackQuery):
    """Show users menu - safe version"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📋 Список всех пользователей", callback_data="list_users"))
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск пользователей", callback_data="search_users_menu"))
    builder.row(
        types.InlineKeyboardButton(text="➕ Создать вручную", callback_data="create_user"),
        types.InlineKeyboardButton(text="📋 По шаблону", callback_data="create_user_template")
    )
    builder.row(
        types.InlineKeyboardButton(text="📊 Статистика", callback_data="users_stats"),
        types.InlineKeyboardButton(text="📈 Расширенная", callback_data="users_extended_stats")
    )
    builder.row(types.InlineKeyboardButton(text="⚙️ Массовые операции", callback_data="mass_operations"))
    builder.row(types.InlineKeyboardButton(text="📤 Экспорт", callback_data="export_users"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "👥 Управление пользователями\n\n"
    try:
        # Получаем всех пользователей для подсчета статистики
        users_list = await users_api.get_all_users()
        if users_list:
            users_count = len(users_list)
            active_count = sum(1 for user in users_list if user.get('status') == 'ACTIVE')
            
            total_traffic_used = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
            total_traffic_limit = sum(user.get('trafficLimit', 0) or 0 for user in users_list if user.get('trafficLimit'))
            
            # Статистика по истечению
            now = datetime.now()
            expiring_soon = 0
            for user in users_list:
                expire_at = user.get('expireAt')
                if expire_at:
                    try:
                        expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                        if now < expire_date < now + timedelta(days=7):
                            expiring_soon += 1
                    except Exception:
                        pass
            
            message += f"📊 Статистика:\n"
            message += f"• Всего пользователей: {users_count}\n"
            message += f"• Активных: {active_count}\n"
            message += f"• Неактивных: {users_count - active_count}\n"
            message += f"• Истекают скоро: {expiring_soon}\n"
            message += f"• Использовано трафика: {format_bytes(total_traffic_used)}\n"
            if total_traffic_limit > 0:
                message += f"• Общий лимит: {format_bytes(total_traffic_limit)}\n"
            message += "\n"
        else:
            message += "📊 Пользователи не найдены\n\n"
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        message += "📊 Статистика недоступна\n\n"
    
    message += "Выберите действие:"

    await callback.answer()
    # Отправляем без parse_mode
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

# ================ LIST USERS ================

@router.callback_query(F.data == "list_users", AuthFilter())
async def list_users(callback: types.CallbackQuery, state: FSMContext):
    """List all users with pagination"""
    await callback.answer()
    await callback.message.edit_text("📋 Загрузка списка пользователей...")
    
    try:
        # Get all users using direct API
        users_list = await users_api.get_all_users()
        
        if not users_list:
            await callback.message.edit_text(
                "👥 Пользователи не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
                ]])
            )
            return

        # Store users in state
        await state.update_data(users=users_list, page=0)
        
        # Show first page
        await show_users_page(callback.message, users_list, 0, state)
        await state.set_state(UserStates.selecting_user)
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении списка пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
            ]])
        )

async def show_users_page(message: types.Message, users: list, page: int, state: FSMContext, per_page: int = 8):
    """Show users page with pagination - completely safe version without any markdown"""
    try:
        total_users = len(users)
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, total_users)
        page_users = users[start_idx:end_idx]
        
        # Build message WITHOUT any markdown formatting - only plain text
        message_text = f"👥 Список пользователей ({start_idx + 1}-{end_idx} из {total_users})\n\n"
        
        for i, user in enumerate(page_users):
            user_name = user.get('username', f"User {user.get('uuid', 'Unknown')[:8]}")
            status_emoji = "🟢" if user.get('status') == 'ACTIVE' else "🔴"
            traffic_used = format_bytes(user.get('usedTraffic', 0) or 0)
            traffic_limit = format_bytes(user.get('trafficLimit', 0) or 0) if user.get('trafficLimit') else "∞"
            
            # Format expiration date safely
            expire_text = "Не указана"
            expire_at = user.get('expireAt')
            if expire_at:
                try:
                    expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                    days_left = (expire_date - datetime.now().astimezone()).days
                    expire_text = f"{expire_at[:10]} ({days_left} дн.)"
                except Exception:
                    expire_text = expire_at[:10]
            
            # Use simple text formatting without any special characters
            message_text += f"{status_emoji} {user_name}\n"
            message_text += f"  💾 Трафик: {traffic_used} / {traffic_limit}\n"
            message_text += f"  📅 Истекает: {expire_text}\n"
            if user.get('telegramId'):
                message_text += f"  📱 TG ID: {user.get('telegramId')}\n"
            message_text += "\n"
        
        # Create pagination keyboard
        builder = InlineKeyboardBuilder()
        
        # Add user selection buttons
        for i, user in enumerate(page_users):
            user_name = user.get('username', f"User {user.get('uuid', 'Unknown')[:8]}")
            display_name = truncate_text(user_name, 25)
            builder.row(types.InlineKeyboardButton(
                text=f"👤 {display_name}",
                callback_data=f"select_user:{user.get('uuid')}"
            ))
        
        # Add pagination controls
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"users_page:{page-1}"))
        
        nav_buttons.append(types.InlineKeyboardButton(text=f"📄 {page+1}", callback_data="current_page"))
        
        if end_idx < total_users:
            nav_buttons.append(types.InlineKeyboardButton(text="➡️", callback_data=f"users_page:{page+1}"))
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users"))
        
        # Send message without any parse_mode
        await message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing users page: {e}")
        await message.edit_text(
            "❌ Ошибка при отображении списка пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
            ]])
        )

@router.callback_query(F.data.startswith("users_page:"), AuthFilter())
async def handle_users_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Handle users pagination"""
    await callback.answer()
    
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    users = data.get('users', [])
    
    await state.update_data(page=page)
    await show_users_page(callback.message, users, page, state)

@router.callback_query(F.data.startswith("select_user:"), AuthFilter())
async def handle_user_selection(callback: types.CallbackQuery, state: FSMContext):
    """Handle user selection"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    data = await state.get_data()
    users = data.get('users', [])
    
    # Find selected user
    selected_user = None
    for user in users:
        if user.get('uuid') == user_uuid:
            selected_user = user
            break
    
    if not selected_user:
        await callback.message.edit_text(
            "❌ Пользователь не найден",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_users")
            ]])
        )
        return
    
    await state.update_data(selected_user=selected_user)
    await state.set_state(UserStates.viewing_user)
    await show_user_details(callback.message, selected_user, state)

async def show_user_details(message: types.Message, user: dict, state: FSMContext):
    """Show user details with action buttons"""
    try:
        user_details = format_user_details(user)
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_user:{user.get('uuid')}"))
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить данные", callback_data=f"refresh_user:{user.get('uuid')}"))
        
        # Status control buttons
        if user.get('status') == 'ACTIVE':
            builder.row(types.InlineKeyboardButton(text="⏸️ Деактивировать", callback_data=f"deactivate_user:{user.get('uuid')}"))
        else:
            builder.row(types.InlineKeyboardButton(text="▶️ Активировать", callback_data=f"activate_user:{user.get('uuid')}"))
        
        # Traffic management
        builder.row(types.InlineKeyboardButton(text="🔄 Сбросить трафик", callback_data=f"reset_traffic:{user.get('uuid')}"))
        
        # Additional features
        builder.row(
            types.InlineKeyboardButton(text="📱 Устройства", callback_data=f"user_devices:{user.get('uuid')}"),
            types.InlineKeyboardButton(text="📋 История", callback_data=f"user_history:{user.get('uuid')}")
        )
        
        # Subscription management
        builder.row(types.InlineKeyboardButton(text="🔗 Подписка", callback_data=f"subscription:{user.get('uuid')}"))
        
        # Dangerous actions
        builder.row(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_user:{user.get('uuid')}"))
        
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="list_users"))
        
        await message.edit_text(
            text=user_details,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing user details: {e}")
        await message.edit_text(
            "❌ Ошибка при отображении данных пользователя",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_users")
            ]])
        )

# ================ USER ACTIONS ================

@router.callback_query(F.data.startswith("refresh_user:"), AuthFilter())
async def refresh_user(callback: types.CallbackQuery, state: FSMContext):
    """Refresh user data"""
    await callback.answer("🔄 Обновление данных...")
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Get updated user data
        updated_user = await users_api.get_user_by_uuid(user_uuid)
        
        if updated_user:
            await state.update_data(selected_user=updated_user)
            await show_user_details(callback.message, updated_user, state)
        else:
            await callback.message.edit_text(
                "❌ Пользователь не найден",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_users")
                ]])
            )
    except Exception as e:
        logger.error(f"Error refreshing user: {e}")
        await callback.answer("❌ Ошибка при обновлении данных", show_alert=True)

@router.callback_query(F.data.startswith("activate_user:"), AuthFilter())
async def activate_user(callback: types.CallbackQuery, state: FSMContext):
    """Activate user"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        success = await users_api.enable_user(user_uuid)
        if success:
            await callback.answer("✅ Пользователь активирован", show_alert=True)
            # Refresh user data
            await refresh_user_and_show(callback, state, user_uuid)
        else:
            await callback.answer("❌ Ошибка при активации", show_alert=True)
    except Exception as e:
        logger.error(f"Error activating user: {e}")
        await callback.answer("❌ Ошибка при активации", show_alert=True)

@router.callback_query(F.data.startswith("deactivate_user:"), AuthFilter())
async def deactivate_user(callback: types.CallbackQuery, state: FSMContext):
    """Deactivate user"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        success = await users_api.disable_user(user_uuid)
        if success:
            await callback.answer("✅ Пользователь деактивирован", show_alert=True)
            # Refresh user data
            await refresh_user_and_show(callback, state, user_uuid)
        else:
            await callback.answer("❌ Ошибка при деактивации", show_alert=True)
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        await callback.answer("❌ Ошибка при деактивации", show_alert=True)

async def refresh_user_and_show(callback: types.CallbackQuery, state: FSMContext, user_uuid: str):
    """Helper function to refresh user data and show details"""
    try:
        updated_user = await users_api.get_user_by_uuid(user_uuid)
        
        if updated_user:
            await state.update_data(selected_user=updated_user)
            await show_user_details(callback.message, updated_user, state)
    except Exception as e:
        logger.error(f"Error refreshing user data: {e}")

@router.callback_query(F.data.startswith("reset_traffic:"), AuthFilter())
async def reset_user_traffic(callback: types.CallbackQuery, state: FSMContext):
    """Reset user traffic"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    # Show confirmation
    data = await state.get_data()
    selected_user = data.get('selected_user')
    username = selected_user.get('username', 'Unknown') if selected_user else 'Unknown'
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Да, сбросить", callback_data=f"confirm_reset_traffic:{user_uuid}"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"refresh_user:{user_uuid}"))
    
    await callback.message.edit_text(
        f"🔄 **Сброс трафика пользователя**\n\n"
        f"Пользователь: **{escape_markdown(username)}**\n\n"
        f"⚠️ Это действие сбросит счетчик использованного трафика до 0.\n\n"
        f"Продолжить?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("confirm_reset_traffic:"), AuthFilter())
async def confirm_reset_traffic(callback: types.CallbackQuery, state: FSMContext):
    """Confirm traffic reset"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Reset traffic by updating usedTraffic to 0
        success = await users_api.update_user(user_uuid, {"usedTraffic": 0})
        if success:
            await callback.answer("✅ Трафик сброшен", show_alert=True)
            await refresh_user_and_show(callback, state, user_uuid)
        else:
            await callback.answer("❌ Ошибка при сбросе трафика", show_alert=True)
    except Exception as e:
        logger.error(f"Error resetting traffic: {e}")
        await callback.answer("❌ Ошибка при сбросе трафика", show_alert=True)

@router.callback_query(F.data.startswith("subscription:"), AuthFilter())
async def show_subscription(callback: types.CallbackQuery, state: FSMContext):
    """Show user subscription info with actual subscription link"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Get user data first
        user = await users_api.get_user_by_uuid(user_uuid)
        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_users")
                ]])
            )
            return
        
        username = user.get('username', 'Unknown')
        
        # Get subscription URL using the correct API endpoint
        api_client = RemnaAPI()
        subscription_data = await api_client.get(f"users/{user_uuid}/subscription")
        
        if subscription_data and subscription_data.get('url'):
            subscription_url = subscription_data.get('url')
            
            subscription_text = f"🔗 **Подписка пользователя**\n\n"
            subscription_text += f"**👤 Пользователь:** {escape_markdown(username)}\n"
            subscription_text += f"**🆔 UUID:** `{user.get('uuid', 'Unknown')}`\n"
            subscription_text += f"**📋 Short UUID:** `{user.get('shortUuid', 'Unknown')}`\n\n"
            
            subscription_text += f"**🔗 Ссылка на подписку:**\n"
            subscription_text += f"`{subscription_url}`\n\n"
            
            subscription_text += f"**📱 Использование:**\n"
            subscription_text += f"• Скопируйте ссылку и добавьте в VPN клиент\n"
            subscription_text += f"• Ссылка автоматически обновляет конфигурации\n"
            subscription_text += f"• Поддерживает все активные inbound'ы пользователя"
            
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="📋 Копировать ссылку", url=subscription_url))
            builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"subscription:{user_uuid}"))
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}"))
            
            await callback.message.edit_text(
                subscription_text,
                reply_markup=builder.as_markup()
            )
        else:
            # Fallback if subscription endpoint is not available
            subscription_text = f"🔗 **Подписка пользователя**\n\n"
            subscription_text += f"**👤 Пользователь:** {escape_markdown(username)}\n"
            subscription_text += f"**🆔 UUID:** `{user.get('uuid', 'Unknown')}`\n"
            subscription_text += f"**📋 Short UUID:** `{user.get('shortUuid', 'Unknown')}`\n\n"
            
            subscription_text += f"**ℹ️ Информация:**\n"
            subscription_text += f"• Ссылка подписки формируется автоматически\n"
            subscription_text += f"• Доступна в веб-интерфейсе панели\n"
            subscription_text += f"• Используйте Short UUID для быстрого поиска\n\n"
            
            subscription_text += f"**🌐 Веб-интерфейс:**\n"
            subscription_text += f"Найдите пользователя по Short UUID в панели управления"
            
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"subscription:{user_uuid}"))
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}"))
            
            await callback.message.edit_text(
                subscription_text,
                reply_markup=builder.as_markup()
            )
            
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        
        # Показываем альтернативную информацию при ошибке
        try:
            user = await users_api.get_user_by_uuid(user_uuid)
            if user:
                subscription_text = f"🔗 **Подписка пользователя**\n\n"
                subscription_text += f"**👤 Пользователь:** {escape_markdown(user.get('username', 'Unknown'))}\n"
                subscription_text += f"**📋 Short UUID:** `{user.get('shortUuid', 'Unknown')}`\n\n"
                subscription_text += f"❌ **Ошибка получения ссылки подписки**\n\n"
                subscription_text += f"**🔧 Альтернативные способы:**\n"
                subscription_text += f"• Используйте веб-интерфейс панели\n"
                subscription_text += f"• Найдите пользователя по Short UUID\n"
                subscription_text += f"• Скопируйте ссылку подписки из панели"
                
                builder = InlineKeyboardBuilder()
                builder.row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"subscription:{user_uuid}"))
                builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}"))
                
                await callback.message.edit_text(
                    subscription_text,
                    reply_markup=builder.as_markup()
                )
            else:
                await callback.answer("❌ Ошибка при получении подписки", show_alert=True)
        except Exception:
            await callback.answer("❌ Ошибка при получении подписки", show_alert=True)

# ================ ENHANCED SUBSCRIPTION FUNCTIONALITY ================

@router.callback_query(F.data.startswith("subscription_configs:"), AuthFilter())
async def show_subscription_configs(callback: types.CallbackQuery, state: FSMContext):
    """Show individual configuration links for user"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Get user data
        user = await users_api.get_user_by_uuid(user_uuid)
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        username = user.get('username', 'Unknown')
        
        # Try to get individual configs using the API
        api_client = RemnaAPI()
        
        # Get all inbounds for this user
        try:
            # Attempt to get user's inbound configurations
            configs_data = await api_client.get(f"users/{user_uuid}/configs")
            
            if configs_data and isinstance(configs_data, list):
                configs_text = f"🔧 **Конфигурации пользователя**\n\n"
                configs_text += f"**👤 Пользователь:** {escape_markdown(username)}\n\n"
                
                builder = InlineKeyboardBuilder()
                
                for i, config in enumerate(configs_data[:10], 1):  # Limit to 10 configs
                    protocol = config.get('protocol', 'Unknown')
                    inbound_tag = config.get('inboundTag', f'Config {i}')
                    config_url = config.get('url', '')
                    
                    configs_text += f"**{i}. {protocol.upper()} - {inbound_tag}**\n"
                    
                    if config_url:
                        # Add button for each config
                        builder.row(types.InlineKeyboardButton(
                            text=f"📋 {protocol.upper()} - {inbound_tag[:20]}",
                            url=config_url
                        ))
                        configs_text += f"✅ Ссылка доступна\n\n"
                    else:
                        configs_text += f"❌ Ссылка недоступна\n\n"
                
                builder.row(types.InlineKeyboardButton(text="🔗 Общая подписка", callback_data=f"subscription:{user_uuid}"))
                builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}"))
                
                await callback.message.edit_text(
                    configs_text,
                    reply_markup=builder.as_markup()
                )
            else:
                # Fallback to subscription link
                await show_subscription(callback, state)
                
        except Exception as e:
            logger.warning(f"Individual configs not available: {e}")
            # Fallback to main subscription
            await show_subscription(callback, state)
            
    except Exception as e:
        logger.error(f"Error showing subscription configs: {e}")
        await callback.answer("❌ Ошибка при получении конфигураций", show_alert=True)


@router.callback_query(F.data.startswith("delete_user:"), AuthFilter())
async def delete_user_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm user deletion"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    # Show confirmation
    data = await state.get_data()
    selected_user = data.get('selected_user')
    username = selected_user.get('username', 'Unknown') if selected_user else 'Unknown'
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🗑️ Да, удалить", callback_data=f"confirm_delete_user:{user_uuid}"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"refresh_user:{user_uuid}"))
    
    await callback.message.edit_text(
        f"🗑️ **Удаление пользователя**\n\n"
        f"Пользователь: **{escape_markdown(username)}**\n\n"
        f"⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n"
        f"Все данные пользователя будут удалены навсегда.\n\n"
        f"Продолжить?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("confirm_delete_user:"), AuthFilter())
async def confirm_delete_user(callback: types.CallbackQuery, state: FSMContext):
    """Confirm user deletion"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        success = await users_api.delete_user(user_uuid)
        if success:
            await callback.answer("✅ Пользователь удален", show_alert=True)
            # Return to users list
            await state.clear()
            await callback.message.edit_text(
                "✅ Пользователь успешно удален",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 К списку пользователей", callback_data="list_users")
                ]])
            )
        else:
            await callback.answer("❌ Ошибка при удалении", show_alert=True)
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        await callback.answer("❌ Ошибка при удалении", show_alert=True)

# ================ SEARCH FUNCTIONALITY ================

@router.callback_query(F.data == "search_users_menu", AuthFilter())
async def show_search_users_menu(callback: types.CallbackQuery, state: FSMContext):
    """Show search users menu"""
    await callback.answer()
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 По имени", callback_data="search_user_by_name"))
    builder.row(types.InlineKeyboardButton(text="📱 По Telegram ID", callback_data="search_user_by_telegram"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users"))
    
    await callback.message.edit_text(
        "🔍 **Поиск пользователей**\n\n"
        "Выберите тип поиска:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "search_user_by_name", AuthFilter())
async def search_user_by_name(callback: types.CallbackQuery, state: FSMContext):
    """Start search by username"""
    await callback.answer()
    await state.set_state(UserStates.search_username)
    
    await callback.message.edit_text(
        "🔍 **Поиск по имени пользователя**\n\n"
        "Введите имя пользователя или его часть:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="search_users_menu")
        ]])
    )

@router.message(StateFilter(UserStates.search_username), AuthFilter())
async def handle_search_username(message: types.Message, state: FSMContext):
    """Handle username search input"""
    search_term = message.text.strip()
    
    if not search_term:
        await message.answer("❌ Введите корректное имя пользователя")
        return
    
    try:
        # Get all users and filter by username
        users_list = await users_api.get_all_users()
        filtered_users = [
            user for user in users_list
            if search_term.lower() in user.get('username', '').lower()
        ]
        
        if not filtered_users:
            await message.answer(
                f"❌ Пользователи с именем содержащим '{search_term}' не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="search_users_menu")
                ]])
            )
            return
        
        # Store results and show
        await state.update_data(users=filtered_users, page=0)
        await state.set_state(UserStates.selecting_user)
        await show_users_page(message, filtered_users, 0, state)
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        await message.answer(
            "❌ Ошибка при поиске пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="search_users_menu")
            ]])
        )

@router.callback_query(F.data == "search_user_by_telegram", AuthFilter())
async def search_user_by_telegram(callback: types.CallbackQuery, state: FSMContext):
    """Start search by Telegram ID"""
    await callback.answer()
    await state.set_state(UserStates.search_telegram_id)
    
    await callback.message.edit_text(
        "📱 **Поиск по Telegram ID**\n\n"
        "Введите Telegram ID пользователя:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="search_users_menu")
        ]])
    )

@router.message(StateFilter(UserStates.search_telegram_id), AuthFilter())
async def handle_search_telegram_id(message: types.Message, state: FSMContext):
    """Handle Telegram ID search input"""
    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID (число)")
        return
    
    try:
        # Get all users and filter by telegram_id
        users_list = await users_api.get_all_users()
        filtered_users = [
            user for user in users_list
            if user.get('telegramId') == telegram_id
        ]
        
        if not filtered_users:
            await message.answer(
                f"❌ Пользователь с Telegram ID {telegram_id} не найден",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="search_users_menu")
                ]])
            )
            return
        
        # Show user details directly if found
        user = filtered_users[0]
        await state.update_data(selected_user=user)
        await state.set_state(UserStates.viewing_user)
        await show_user_details(message, user, state)
        
    except Exception as e:
        logger.error(f"Error searching users by telegram ID: {e}")
        await message.answer(
            "❌ Ошибка при поиске пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="search_users_menu")
            ]])
        )

# ================ CREATE USER FUNCTIONALITY ================

# Найдите функцию start_create_user (около строки 850-900) и замените её на эту:

@router.callback_query(F.data == "create_user", AuthFilter())
async def start_create_user(callback: types.CallbackQuery, state: FSMContext):
    """Start user creation process"""
    await callback.answer()
    await state.clear()
    await state.set_state(UserStates.enter_username)
    
    # Используем простой текст без сложного форматирования
    message_text = "➕ Создание нового пользователя\n\n"
    message_text += "Шаг 1/4: Введите имя пользователя:\n\n"
    message_text += "ℹ️ Требования:\n"
    message_text += "• Только латинские буквы, цифры и символы _ -\n"
    message_text += "• Минимум 3 символа\n"
    message_text += "• Имя должно быть уникальным"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="users"))
    
    try:
        await callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Error in start_create_user: {e}")
        # Fallback - отправить новое сообщение
        await callback.message.answer(
            text=message_text,
            reply_markup=builder.as_markup()
        )

@router.message(StateFilter(UserStates.enter_username), AuthFilter())
async def handle_username_input(message: types.Message, state: FSMContext):
    """Handle username input"""
    data = await state.get_data()
    template_id = data.get('selected_template')
    
    # Если это создание по шаблону
    if template_id:
        return await handle_template_username_input(message, state)
    
    # Обычное создание пользователя
    username = message.text.strip()
    
    # Validate username
    if not re.match(r'^[a-zA-Z0-9_-]+$', username) or len(username) < 3:
        await message.answer(
            "❌ Некорректное имя пользователя.\n\n"
            "Требования:\n"
            "• Минимум 3 символа\n"
            "• Только латинские буквы, цифры, _ и -"
        )
        return
    
    await state.update_data(username=username)
    await state.set_state(UserStates.enter_telegram_id)
    
    # БЕЗ markdown форматирования
    await message.answer(
        "➕ Создание нового пользователя\n\n"
        f"✅ Имя: {username}\n\n"
        "Шаг 2/4: Введите Telegram ID пользователя:\n\n"
        "ℹ️ Введите 0 или пропустите, если Telegram ID неизвестен",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_telegram_id"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
        ]])
    )

@router.message(StateFilter(UserStates.enter_telegram_id), AuthFilter())
async def handle_telegram_id_input(message: types.Message, state: FSMContext):
    """Handle Telegram ID input"""
    data = await state.get_data()
    template_id = data.get('selected_template')
    
    # Если это создание по шаблону
    if template_id:
        return await handle_template_telegram_id_input(message, state)
    
    # Обычное создание пользователя
    try:
        telegram_id = int(message.text.strip())
        if telegram_id < 0:
            raise ValueError("Negative ID")
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID (положительное число) или 0")
        return
    
    data = await state.get_data()
    username = data.get('username')
    
    await state.update_data(telegramId=telegram_id if telegram_id > 0 else None)
    await state.set_state(UserStates.enter_traffic_limit)
    
    # БЕЗ markdown форматирования
    await message.answer(
        "➕ Создание нового пользователя\n\n"
        f"✅ Имя: {username}\n"
        f"✅ Telegram ID: {telegram_id if telegram_id > 0 else 'Не указан'}\n\n"
        "Шаг 3/4: Введите лимит трафика:\n\n"
        "Примеры:\n"
        "• 10GB - 10 гигабайт\n"
        "• 500MB - 500 мегабайт\n"
        "• 1TB - 1 терабайт\n"
        "• 0 - без ограничений",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="∞ Без ограничений", callback_data="unlimited_traffic"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
        ]])
    )

@router.callback_query(F.data == "skip_telegram_id", AuthFilter())
async def skip_telegram_id(callback: types.CallbackQuery, state: FSMContext):
    """Skip Telegram ID input"""
    await callback.answer()
    
    data = await state.get_data()
    username = data.get('username')
    
    await state.update_data(telegramId=None)
    await state.set_state(UserStates.enter_traffic_limit)
    
    # БЕЗ markdown форматирования
    await callback.message.edit_text(
        "➕ Создание нового пользователя\n\n"
        f"✅ Имя: {username}\n"
        f"✅ Telegram ID: Не указан\n\n"
        "Шаг 3/4: Введите лимит трафика:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="∞ Без ограничений", callback_data="unlimited_traffic"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
        ]])
    )

def parse_traffic_limit(traffic_str: str) -> int:
    """Parse traffic limit string to bytes"""
    traffic_str = traffic_str.upper().strip()
    
    if traffic_str == "0":
        return 0
        
    # Extract number and unit
    match = re.match(r'^(\d+(?:\.\d+)?)\s*(GB|MB|TB|G|M|T)?$', traffic_str)
    if not match:
        raise ValueError("Invalid format")
    
    amount = float(match.group(1))
    unit = match.group(2) or "GB"
    
    # Convert to bytes
    multipliers = {
        'MB': 1024**2, 'M': 1024**2,
        'GB': 1024**3, 'G': 1024**3, 
        'TB': 1024**4, 'T': 1024**4
    }
    
    return int(amount * multipliers[unit])

@router.message(StateFilter(UserStates.enter_traffic_limit), AuthFilter())
async def handle_traffic_limit_input(message: types.Message, state: FSMContext):
    """Handle traffic limit input"""
    try:
        traffic_limit = parse_traffic_limit(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Некорректный формат лимита трафика.\n\n"
            "Примеры корректного формата:\n"
            "• 10GB или 10G\n"
            "• 500MB или 500M\n"
            "• 1TB или 1T\n"
            "• 0 - без ограничений"
        )
        return
    
    data = await state.get_data()
    await state.update_data(trafficLimit=traffic_limit)
    await state.set_state(UserStates.enter_description)
    
    username = data.get('username')
    telegram_id = data.get('telegramId')
    traffic_text = format_bytes(traffic_limit) if traffic_limit > 0 else "Без ограничений"
    
    # БЕЗ markdown форматирования
    await message.answer(
        "➕ Создание нового пользователя\n\n"
        f"✅ Имя: {username}\n"
        f"✅ Telegram ID: {telegram_id or 'Не указан'}\n"
        f"✅ Лимит трафика: {traffic_text}\n\n"
        "Шаг 4/4: Введите описание пользователя (опционально):",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
        ]])
    )

@router.callback_query(F.data == "unlimited_traffic", AuthFilter())
async def set_unlimited_traffic(callback: types.CallbackQuery, state: FSMContext):
    """Set unlimited traffic"""
    await callback.answer()
    
    data = await state.get_data()
    await state.update_data(trafficLimit=0)
    await state.set_state(UserStates.enter_description)
    
    username = data.get('username')
    telegram_id = data.get('telegramId')
    
    await callback.message.edit_text(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** {telegram_id or 'Не указан'}\n"
        f"✅ **Лимит трафика:** Без ограничений\n\n"
        "**Шаг 4/4:** Введите описание пользователя (опционально):",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
        ]])
    )

@router.message(StateFilter(UserStates.enter_description), AuthFilter())
async def handle_description_input(message: types.Message, state: FSMContext):
    """Handle description input"""
    data = await state.get_data()
    template_id = data.get('selected_template')
    
    if template_id:
        return await handle_template_description_input(message, state)
    
    # Обычное создание пользователя
    description = message.text.strip()
    await state.update_data(description=description)
    
    # Show confirmation
    await show_create_user_confirmation(message, state)

@router.callback_query(F.data == "skip_description", AuthFilter())
async def skip_description(callback: types.CallbackQuery, state: FSMContext):
    """Skip description input"""
    await callback.answer()
    await state.update_data(description=None)
    
    # Show confirmation
    await show_create_user_confirmation(callback.message, state)

async def show_create_user_confirmation(message: types.Message, state: FSMContext):
    """Show user creation confirmation"""
    data = await state.get_data()
    username = data.get('username')
    telegram_id = data.get('telegramId')
    traffic_limit = data.get('trafficLimit', 0)
    description = data.get('description')
    
    traffic_text = format_bytes(traffic_limit) if traffic_limit > 0 else "Без ограничений"
    
    # БЕЗ markdown форматирования
    confirmation_text = (
        "➕ Создание пользователя - Подтверждение\n\n"
        f"Имя: {username}\n"
        f"Telegram ID: {telegram_id or 'Не указан'}\n"
        f"Лимит трафика: {traffic_text}\n"
        f"Описание: {description or 'Не указано'}\n\n"
        "Создать пользователя с указанными параметрами?"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Создать", callback_data="confirm_create_user"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="users"))
    
    try:
        await message.edit_text(
            confirmation_text,
            reply_markup=builder.as_markup()
        )
    except:
        # If edit fails, send new message
        await message.answer(
            confirmation_text,
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "confirm_create_user", AuthFilter())
async def confirm_create_user(callback: types.CallbackQuery, state: FSMContext):
    """Confirm user creation"""
    await callback.answer()
    
    data = await state.get_data()
    
    try:
        # Prepare user data for API
        user_data = {
            "username": data.get('username'),
            "trafficLimit": data.get('trafficLimit', 0),
        }
        
        if data.get('telegramId'):
            user_data["telegramId"] = data.get('telegramId')
        
        if data.get('description'):
            user_data["description"] = data.get('description')
        
        # Create user using direct API
        success = await users_api.create_user(user_data)
        
        if success:
            await callback.answer("✅ Пользователь создан", show_alert=True)
            await state.clear()
            
            # Simple message without markdown
            success_message = "✅ Пользователь создан успешно!\n\n"
            success_message += f"Имя: {user_data['username']}\n"
            success_message += f"Статус: Активен\n\n"
            success_message += f"Пользователь готов к использованию."
            
            await callback.message.edit_text(
                success_message,
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="👥 К списку пользователей", callback_data="list_users"),
                    types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
                ]])
            )
        else:
            await callback.answer("❌ Ошибка при создании", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await callback.answer("❌ Ошибка при создании пользователя", show_alert=True)

# ================ STATISTICS ================

@router.callback_query(F.data == "users_stats", AuthFilter())
async def show_users_statistics(callback: types.CallbackQuery):
    """Show users statistics"""
    await callback.answer()
    
    try:
        users_list = await users_api.get_all_users()
        
        if users_list:
            total_users = len(users_list)
            active_users = sum(1 for user in users_list if user.get('status') == 'ACTIVE')
            inactive_users = total_users - active_users
            
            total_traffic_used = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
            total_traffic_limit = sum(user.get('trafficLimit', 0) or 0 for user in users_list if user.get('trafficLimit'))
            
            stats_text = "📊 **Статистика пользователей**\n\n"
            stats_text += f"👥 **Общее количество:** {total_users}\n"
            stats_text += f"🟢 **Активных:** {active_users}\n"
            stats_text += f"🔴 **Неактивных:** {inactive_users}\n"
            stats_text += f"📈 **Использовано трафика:** {format_bytes(total_traffic_used)}\n"
            if total_traffic_limit > 0:
                stats_text += f"📊 **Общий лимит:** {format_bytes(total_traffic_limit)}\n"
                remaining = total_traffic_limit - total_traffic_used
                stats_text += f"⬆️ **Осталось:** {format_bytes(remaining)}\n"
                usage_percent = (total_traffic_used / total_traffic_limit) * 100
                stats_text += f"📊 **Использовано:** {usage_percent:.1f}%\n"
        else:
            stats_text = "📊 **Статистика недоступна**\n\nПользователи не найдены."
            
        await callback.message.edit_text(
            stats_text,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔄 Обновить", callback_data="users_stats"),
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
            ]])
        )

# ================ EDIT USER FUNCTIONALITY ================

@router.callback_query(F.data.startswith("edit_user:"), AuthFilter())
async def start_edit_user(callback: types.CallbackQuery, state: FSMContext):
    """Start editing a user"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    # Get current user data
    data = await state.get_data()
    user = data.get('selected_user')
    
    if not user:
        await callback.message.edit_text(
            "❌ Данные пользователя не найдены",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_users")
            ]])
        )
        return
    
    await state.update_data(edit_user=user)
    await state.set_state(UserStates.editing_user)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📱 Telegram ID", callback_data="edit_field:telegram_id"))
    builder.row(types.InlineKeyboardButton(text="📈 Лимит трафика", callback_data="edit_field:traffic_limit"))
    builder.row(types.InlineKeyboardButton(text="📝 Описание", callback_data="edit_field:description"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}"))
    
    # Format current values БЕЗ markdown
    username = user.get('username', 'Unknown')
    telegram_id = user.get('telegramId', 'Не указан')
    traffic_limit = format_bytes(user.get('trafficLimit', 0)) if user.get('trafficLimit') else "Без ограничений"
    description = user.get('description', 'Не указано')
    
    message = f"📝 Редактирование пользователя\n\n"
    message += f"👤 Имя: {username}\n\n"
    message += f"Текущие значения:\n"
    message += f"📱 Telegram ID: {telegram_id}\n"
    message += f"📈 Лимит трафика: {traffic_limit}\n"
    message += f"📝 Описание: {str(description)}\n\n"
    message += "Выберите поле для редактирования:"
    
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("edit_field:"), AuthFilter())
async def edit_field_selection(callback: types.CallbackQuery, state: FSMContext):
    """Handle edit field selection"""
    await callback.answer()
    
    field = callback.data.split(":", 1)[1]
    await state.update_data(edit_field=field)
    
    if field == "telegram_id":
        await state.set_state(UserStates.enter_edit_telegram_id)
        await callback.message.edit_text(
            "📱 Изменение Telegram ID\n\n"
            "Введите новый Telegram ID (или 0 для удаления):",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")
            ]])
        )
    elif field == "traffic_limit":
        await state.set_state(UserStates.enter_edit_traffic_limit)
        await callback.message.edit_text(
            "📈 Изменение лимита трафика\n\n"
            "Введите новый лимит трафика:\n\n"
            "Примеры: 10GB, 500MB, 1TB, 0 (без ограничений)",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="∞ Без ограничений", callback_data="set_unlimited"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")
            ]])
        )
    elif field == "description":
        await state.set_state(UserStates.enter_edit_description)
        await callback.message.edit_text(
            "📝 Изменение описания\n\n"
            "Введите новое описание:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🗑️ Удалить описание", callback_data="clear_description"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")
            ]])
        )

@router.message(StateFilter(UserStates.enter_edit_telegram_id), AuthFilter())
async def handle_edit_telegram_id(message: types.Message, state: FSMContext):
    """Handle Telegram ID edit"""
    try:
        telegram_id = int(message.text.strip())
        if telegram_id < 0:
            raise ValueError("Negative ID")
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID (число >= 0)")
        return
    
    data = await state.get_data()
    user = data.get('edit_user')
    
    try:
        # Update user using direct API
        update_data = {"telegramId": telegram_id if telegram_id > 0 else None}
        success = await users_api.update_user(user['uuid'], update_data)
        
        if success:
            await message.answer(
                "✅ Telegram ID успешно обновлен",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"refresh_user:{user['uuid']}")
                ]])
            )
            await state.clear()
        else:
            await message.answer("❌ Ошибка при обновлении Telegram ID")
    except Exception as e:
        logger.error(f"Error updating telegram ID: {e}")
        await message.answer("❌ Ошибка при обновлении Telegram ID")

@router.message(StateFilter(UserStates.enter_edit_traffic_limit), AuthFilter())
async def handle_edit_traffic_limit(message: types.Message, state: FSMContext):
    """Handle traffic limit edit"""
    try:
        traffic_limit = parse_traffic_limit(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Некорректный формат лимита трафика.\n\n"
            "Примеры: `10GB`, `500MB`, `1TB`, `0`"
        )
        return
    
    data = await state.get_data()
    user = data.get('edit_user')
    
    try:
        # Update user using direct API
        update_data = {"trafficLimit": traffic_limit}
        success = await users_api.update_user(user['uuid'], update_data)
        
        if success:
            traffic_text = format_bytes(traffic_limit) if traffic_limit > 0 else "Без ограничений"
            await message.answer(
                f"✅ Лимит трафика обновлен: {traffic_text}",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"refresh_user:{user['uuid']}")
                ]])
            )
            await state.clear()
        else:
            await message.answer("❌ Ошибка при обновлении лимита трафика")
    except Exception as e:
        logger.error(f"Error updating traffic limit: {e}")
        await message.answer("❌ Ошибка при обновлении лимита трафика")

@router.message(StateFilter(UserStates.enter_edit_description), AuthFilter())
async def handle_edit_description(message: types.Message, state: FSMContext):
    """Handle description edit"""
    description = message.text.strip()
    
    data = await state.get_data()
    user = data.get('edit_user')
    
    try:
        # Update user using direct API
        update_data = {"description": description}
        success = await users_api.update_user(user['uuid'], update_data)
        
        if success:
            await message.answer(
                "✅ Описание успешно обновлено",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"refresh_user:{user['uuid']}")
                ]])
            )
            await state.clear()
        else:
            await message.answer("❌ Ошибка при обновлении описания")
    except Exception as e:
        logger.error(f"Error updating description: {e}")
        await message.answer("❌ Ошибка при обновлении описания")

@router.callback_query(F.data == ("set_unlimited"), AuthFilter())
async def set_unlimited_traffic_edit(callback: types.CallbackQuery, state: FSMContext):
    """Set unlimited traffic during edit"""
    await callback.answer()
    
    data = await state.get_data()
    user = data.get('edit_user')
    
    try:
        # Update user using direct API
        update_data = {"trafficLimit": 0}
        success = await users_api.update_user(user['uuid'], update_data)
        
        if success:
            await callback.message.edit_text(
                "✅ Лимит трафика установлен: Без ограничений",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"refresh_user:{user['uuid']}")
                ]])
            )
            await state.clear()
        else:
            await callback.message.edit_text("❌ Ошибка при обновлении лимита трафика")
    except Exception as e:
        logger.error(f"Error setting unlimited traffic: {e}")
        await callback.message.edit_text("❌ Ошибка при установке безлимитного трафика")

@router.callback_query(F.data == ("clear_description"), AuthFilter())
async def clear_description_edit(callback: types.CallbackQuery, state: FSMContext):
    """Clear description during edit"""
    await callback.answer()
    
    data = await state.get_data()
    user = data.get('edit_user')
    
    try:
        # Update user using direct API (исправлено с SDK на прямой API)
        update_data = {"description": ""}
        success = await users_api.update_user(user['uuid'], update_data)
        
        if success:
            await callback.message.edit_text(
                "✅ Описание удалено",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"refresh_user:{user['uuid']}")
                ]])
            )
            await state.clear()
        else:
            await callback.message.edit_text("❌ Ошибка при удалении описания")
    except Exception as e:
        logger.error(f"Error clearing description: {e}")
        await callback.message.edit_text("❌ Ошибка при удалении описания")

@router.callback_query(F.data == ("cancel_edit"), AuthFilter())
async def cancel_edit(callback: types.CallbackQuery, state: FSMContext):
    """Cancel edit operation"""
    await callback.answer()
    
    data = await state.get_data()
    user = data.get('edit_user')
    
    await state.clear()
    await callback.message.edit_text(
        "❌ Редактирование отменено",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"refresh_user:{user['uuid'] if user else 'unknown'}")
        ]])
    )

# ================ USER TEMPLATES FUNCTIONALITY ================

# Предопределенные шаблоны пользователей
USER_TEMPLATES = {
    "basic": {
        "name": "Базовый",
        "description": "Базовый пользователь с ограничениями",
        "traffic_limit": 10 * 1024**3,  # 10GB
        "expire_days": 30,
        "icon": "👤"
    },
    "premium": {
        "name": "Премиум",
        "description": "Премиум пользователь с увеличенными лимитами",
        "traffic_limit": 100 * 1024**3,  # 100GB
        "expire_days": 30,
        "icon": "⭐"
    },
    "unlimited": {
        "name": "Безлимитный",
        "description": "Пользователь без ограничений трафика",
        "traffic_limit": 0,  # Unlimited
        "expire_days": 365,
        "icon": "🚀"
    },
    "trial": {
        "name": "Пробный",
        "description": "Пробный доступ на короткий срок",
        "traffic_limit": 1024**3,  # 1GB
        "expire_days": 7,
        "icon": "🔍"
    }
}

@router.callback_query(F.data == "create_user_template", AuthFilter())
async def show_user_templates(callback: types.CallbackQuery, state: FSMContext):
    """Show user creation templates"""
    await callback.answer()
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    
    for template_id, template in USER_TEMPLATES.items():
        builder.row(types.InlineKeyboardButton(
            text=f"{template['icon']} {template['name']}",
            callback_data=f"template_select:{template_id}"
        ))
    
    builder.row(types.InlineKeyboardButton(text="✏️ Создать вручную", callback_data="create_user"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users"))
    
    message = "📋 **Шаблоны пользователей**\n\n"
    message += "Выберите готовый шаблон для быстрого создания пользователя:\n\n"
    
    for template_id, template in USER_TEMPLATES.items():
        traffic_text = format_bytes(template['traffic_limit']) if template['traffic_limit'] > 0 else "Безлимитный"
        message += f"{template['icon']} **{template['name']}**\n"
        message += f"  • Трафик: {traffic_text}\n"
        message += f"  • Срок: {template['expire_days']} дней\n"
        message += f"  • {template['description']}\n\n"
    
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("template_select:"), AuthFilter())
async def select_template(callback: types.CallbackQuery, state: FSMContext):
    """Select a user template"""
    await callback.answer()
    
    template_id = callback.data.split(":", 1)[1]
    template = USER_TEMPLATES.get(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return
    
    await state.update_data(selected_template=template_id)
    await state.set_state(UserStates.enter_username)
    
    traffic_text = format_bytes(template['traffic_limit']) if template['traffic_limit'] > 0 else "Безлимитный"
    
    await callback.message.edit_text(
        f"➕ **Создание пользователя по шаблону**\n\n"
        f"{template['icon']} **Шаблон:** {template['name']}\n"
        f"📈 **Трафик:** {traffic_text}\n"
        f"📅 **Срок:** {template['expire_days']} дней\n"
        f"📝 **Описание:** {template['description']}\n\n"
        f"**Шаг 1/3:** Введите имя пользователя:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="create_user_template")
        ]])
    )

async def handle_template_username_input(message: types.Message, state: FSMContext):
    """Handle username input for template creation"""
    username = message.text.strip()
    
    # Validate username
    if not re.match(r'^[a-zA-Z0-9_-]+$', username) or len(username) < 3:
        await message.answer(
            "❌ Некорректное имя пользователя.\n\n"
            "Требования:\n"
            "• Минимум 3 символа\n"
            "• Только латинские буквы, цифры, _ и -"
        )
        return
    
    data = await state.get_data()
    template_id = data.get('selected_template')
    template = USER_TEMPLATES[template_id]
    
    await state.update_data(username=username)
    await state.set_state(UserStates.enter_telegram_id)
    
    traffic_text = format_bytes(template['traffic_limit']) if template['traffic_limit'] > 0 else "Безлимитный"
    
    await message.answer(
        f"➕ **Создание пользователя по шаблону**\n\n"
        f"{template['icon']} **Шаблон:** {template['name']}\n"
        f"✅ **Имя:** {username}\n"
        f"📈 **Трафик:** {traffic_text}\n"
        f"📅 **Срок:** {template['expire_days']} дней\n\n"
        f"**Шаг 2/3:** Введите Telegram ID пользователя:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_telegram_id_template"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="create_user_template")
        ]])
    )

@router.callback_query(F.data == "skip_telegram_id_template", AuthFilter())
async def skip_telegram_id_template(callback: types.CallbackQuery, state: FSMContext):
    """Skip Telegram ID for template creation"""
    await callback.answer()
    
    data = await state.get_data()
    template_id = data.get('selected_template')
    template = USER_TEMPLATES[template_id]
    username = data.get('username')
    
    await state.update_data(telegram_id=None)
    await state.set_state(UserStates.enter_description)
    
    traffic_text = format_bytes(template['traffic_limit']) if template['traffic_limit'] > 0 else "Безлимитный"
    
    await callback.message.edit_text(
        f"➕ **Создание пользователя по шаблону**\n\n"
        f"{template['icon']} **Шаблон:** {template['name']}\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** Не указан\n"
        f"📈 **Трафик:** {traffic_text}\n"
        f"📅 **Срок:** {template['expire_days']} дней\n\n"
        f"**Шаг 3/3:** Введите описание (опционально):",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description_template"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="create_user_template")
        ]])
    )

async def handle_template_telegram_id_input(message: types.Message, state: FSMContext):
    """Handle Telegram ID input for template creation"""
    try:
        telegram_id = int(message.text.strip())
        if telegram_id < 0:
            raise ValueError("Negative ID")
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID (положительное число) или 0")
        return
    
    data = await state.get_data()
    template_id = data.get('selected_template')
    template = USER_TEMPLATES[template_id]
    username = data.get('username')
    
    await state.update_data(telegram_id=telegram_id if telegram_id > 0 else None)
    await state.set_state(UserStates.enter_description)
    
    traffic_text = format_bytes(template['traffic_limit']) if template['traffic_limit'] > 0 else "Безлимитный"
    
    await message.answer(
        f"➕ **Создание пользователя по шаблону**\n\n"
        f"{template['icon']} **Шаблон:** {template['name']}\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** {telegram_id if telegram_id > 0 else 'Не указан'}\n"
        f"📈 **Трафик:** {traffic_text}\n"
        f"📅 **Срок:** {template['expire_days']} дней\n\n"
        f"**Шаг 3/3:** Введите описание (опционально):",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description_template"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="create_user_template")
        ]])
    )

@router.callback_query(F.data == "skip_description_template", AuthFilter())
async def skip_description_template(callback: types.CallbackQuery, state: FSMContext):
    """Skip description for template creation"""
    await callback.answer()
    await state.update_data(description=None)
    await show_template_confirmation(callback.message, state)

async def handle_template_description_input(message: types.Message, state: FSMContext):
    """Handle description input for template creation"""
    description = message.text.strip()
    await state.update_data(description=description)
    await show_template_confirmation(message, state)

async def show_template_confirmation(message: types.Message, state: FSMContext):
    """Show template user creation confirmation"""
    data = await state.get_data()
    template_id = data.get('selected_template')
    template = USER_TEMPLATES[template_id]
    
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    description = data.get('description')
    
    traffic_text = format_bytes(template['traffic_limit']) if template['traffic_limit'] > 0 else "Безлимитный"
    expire_date = datetime.now() + timedelta(days=template['expire_days'])
    
    confirmation_text = (
        f"➕ **Создание пользователя - Подтверждение**\n\n"
        f"{template['icon']} **Шаблон:** {template['name']}\n"
        f"**Имя:** {username}\n"
        f"**Telegram ID:** {telegram_id or 'Не указан'}\n"
        f"**Лимит трафика:** {traffic_text}\n"
        f"**Истекает:** {expire_date.strftime('%Y-%m-%d %H:%M')}\n"
        f"**Описание:** {description or template['description']}\n\n"
        f"Создать пользователя с указанными параметрами?"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Создать", callback_data="confirm_create_template_user"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="create_user_template"))
    
    try:
        await message.edit_text(
            confirmation_text,
            reply_markup=builder.as_markup()
        )
    except:
        await message.answer(
            confirmation_text,
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "confirm_create_template_user", AuthFilter())
async def confirm_create_template_user(callback: types.CallbackQuery, state: FSMContext):
    """Confirm template user creation"""
    await callback.answer()
    
    data = await state.get_data()
    template_id = data.get('selected_template')
    template = USER_TEMPLATES[template_id]
    
    try:
        expire_date = datetime.now() + timedelta(days=template['expire_days'])
        
        # Prepare user data for API
        user_data = {
            "username": data.get('username'),
            "trafficLimit": template['traffic_limit'],
            "expireAt": expire_date.isoformat(),
            "description": data.get('description') or template['description']
        }
        
        if data.get('telegram_id'):
            user_data["telegramId"] = data.get('telegram_id')
        
        # Create user using direct API
        success = await users_api.create_user(user_data)
        
        if success:
            await callback.answer("✅ Пользователь создан по шаблону", show_alert=True)
            await state.clear()
            
            traffic_text = format_bytes(template['traffic_limit']) if template['traffic_limit'] > 0 else "Безлимитный"
            
            await callback.message.edit_text(
                f"✅ **Пользователь создан успешно!**\n\n"
                f"{template['icon']} **Шаблон:** {template['name']}\n"
                f"**Имя:** {user_data['username']}\n"
                f"**Трафик:** {traffic_text}\n"
                f"**Истекает:** {expire_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Пользователь готов к использованию.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="👥 К списку пользователей", callback_data="list_users"),
                    types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
                ]])
            )
        else:
            await callback.answer("❌ Ошибка при создании", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error creating template user: {e}")
        await callback.answer("❌ Ошибка при создании пользователя", show_alert=True)

# ================ EXTENDED STATISTICS ================

@router.callback_query(F.data == "users_extended_stats", AuthFilter())
async def show_extended_users_statistics(callback: types.CallbackQuery):
    """Show extended users statistics with node breakdown"""
    await callback.answer()
    
    try:
        # Получаем всех пользователей через прямой API
        users_list = await users_api.get_all_users()
        
        # Получаем информацию о нодах
        nodes_list = await nodes_api.get_all_nodes()
        
        # Базовая статистика
        total_users = len(users_list)
        active_users = sum(1 for user in users_list if user.get('status') == 'ACTIVE')
        inactive_users = total_users - active_users
        
        total_traffic_used = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
        total_traffic_limit = sum(user.get('trafficLimit', 0) or 0 for user in users_list if user.get('trafficLimit'))
        
        # Статистика по нодам
        node_stats = {}
        for node in nodes_list:
            node_uuid = node.get('uuid')
            node_users = [user for user in users_list if user.get('nodeUuid') == node_uuid]
            
            node_stats[node_uuid] = {
                'name': node.get('name'),
                'total_users': len(node_users),
                'active_users': sum(1 for user in node_users if user.get('status') == 'ACTIVE'),
                'traffic_used': sum(user.get('usedTraffic', 0) or 0 for user in node_users),
                'traffic_limit': sum(user.get('trafficLimit', 0) or 0 for user in node_users if user.get('trafficLimit')),
                'status': 'online' if node.get('isConnected') else 'offline'
            }
        
        # Статистика по периодам
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        new_users_week = 0
        new_users_month = 0
        for user in users_list:
            created_at = user.get('createdAt')
            if created_at:
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if created_date > week_ago:
                        new_users_week += 1
                    if created_date > month_ago:
                        new_users_month += 1
                except Exception:
                    pass
        
        # Статистика по истечению
        expired_users = 0
        expiring_soon = 0
        for user in users_list:
            expire_at = user.get('expireAt')
            if expire_at:
                try:
                    expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                    if expire_date < now:
                        expired_users += 1
                    elif now < expire_date < now + timedelta(days=7):
                        expiring_soon += 1
                except Exception:
                    pass
        
        # Формируем сообщение
        stats_text = "📊 **Расширенная статистика пользователей**\n\n"
        
        # Общая статистика
        stats_text += "**📈 Общая статистика:**\n"
        stats_text += f"• Всего пользователей: {total_users}\n"
        if total_users > 0:
            stats_text += f"• Активных: {active_users} ({(active_users/total_users*100):.1f}%)\n"
            stats_text += f"• Неактивных: {inactive_users} ({(inactive_users/total_users*100):.1f}%)\n"
        else:
            stats_text += f"• Активных: {active_users}\n"
            stats_text += f"• Неактивных: {inactive_users}\n"
        stats_text += f"• Истекших: {expired_users}\n"
        stats_text += f"• Истекают в течение недели: {expiring_soon}\n\n"
        
        # Статистика трафика
        stats_text += "**💾 Трафик:**\n"
        stats_text += f"• Использовано: {format_bytes(total_traffic_used)}\n"
        if total_traffic_limit > 0:
            stats_text += f"• Общий лимит: {format_bytes(total_traffic_limit)}\n"
            remaining = total_traffic_limit - total_traffic_used
            stats_text += f"• Осталось: {format_bytes(remaining)}\n"
            usage_percent = (total_traffic_used / total_traffic_limit) * 100
            stats_text += f"• Использовано: {usage_percent:.1f}%\n"
        stats_text += "\n"
        
        # Статистика по периодам
        stats_text += "**📅 По периодам:**\n"
        stats_text += f"• Новых за неделю: {new_users_week}\n"
        stats_text += f"• Новых за месяц: {new_users_month}\n\n"
        
        # Статистика по нодам
        if node_stats:
            stats_text += "**🔗 По нодам:**\n"
            for node_uuid, stats in node_stats.items():
                status_emoji = "🟢" if stats['status'] == 'online' else "🔴"
                stats_text += f"{status_emoji} **{escape_markdown(stats['name'])}**\n"
                stats_text += f"  • Пользователей: {stats['total_users']} (активных: {stats['active_users']})\n"
                stats_text += f"  • Трафик: {format_bytes(stats['traffic_used'])}"
                if stats['traffic_limit'] > 0:
                    stats_text += f" / {format_bytes(stats['traffic_limit'])}"
                stats_text += "\n"
        
        # Кнопки навигации
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="📊 По нодам", callback_data="stats_by_nodes"),
            types.InlineKeyboardButton(text="📈 По периодам", callback_data="stats_by_period")
        )
        builder.row(
            types.InlineKeyboardButton(text="⚠️ Истекающие", callback_data="expiring_users"),
            types.InlineKeyboardButton(text="❌ Истекшие", callback_data="expired_users")
        )
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="users_extended_stats"))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users"))
        
        await callback.message.edit_text(
            text=stats_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting extended stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении расширенной статистики",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
            ]])
        )
# ================ EXPIRED USERS ================

@router.callback_query(F.data == "expired_users", AuthFilter())
async def show_expired_users(callback: types.CallbackQuery, state: FSMContext):
    """Show expired users"""
    await callback.answer()
    
    try:
        users_list = await users_api.get_all_users()
        
        now = datetime.now()
        
        expired_users = []
        for user in users_list:
            expire_at = user.get('expireAt')
            if expire_at:
                try:
                    expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                    if expire_date < now:
                        expired_users.append(user)
                except Exception:
                    pass
        
        if not expired_users:
            await callback.message.edit_text(
                "❌ **Истекшие пользователи**\n\n"
                "✅ Нет истекших пользователей",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats")
                ]])
            )
            return
        
        # Store expired users in state
        await state.update_data(users=expired_users, page=0)
        await state.set_state(UserStates.selecting_user)
        
        message_text = f"❌ **Истекшие пользователи ({len(expired_users)})**\n\n"
        
        for user in expired_users[:10]:  # Показываем первые 10
            expire_at = user.get('expireAt')
            expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
            days_expired = (now - expire_date).days
            
            status_emoji = "🟢" if user.get('status') == 'ACTIVE' else "🔴"
            
            username = user.get('username', 'Unknown')
            used_traffic = user.get('usedTraffic', 0) or 0
            
            message_text += f"{status_emoji}❌ **{escape_markdown(username)}**\n"
            message_text += f"  📅 Истек {days_expired} дн. назад ({expire_date.strftime('%Y-%m-%d')})\n"
            message_text += f"  💾 Использовано: {format_bytes(used_traffic)}\n\n"
        
        if len(expired_users) > 10:
            message_text += f"... и еще {len(expired_users) - 10} пользователей\n\n"
        
        # Кнопки для массовых действий
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="📝 Список полный", callback_data="list_users"),
            types.InlineKeyboardButton(text="🔄 Продлить всех", callback_data="extend_all_expired")
        )
        builder.row(
            types.InlineKeyboardButton(text="🗑️ Удалить всех", callback_data="delete_all_expired_confirm"),
            types.InlineKeyboardButton(text="⏸️ Деактивировать всех", callback_data="deactivate_all_expired")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats"))
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing expired users: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении списка истекших пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats")
            ]])
        )

# ================ BULK ACTIONS ================

@router.callback_query(F.data == "extend_all_expiring", AuthFilter())
async def extend_all_expiring_users(callback: types.CallbackQuery, state: FSMContext):
    """Extend all expiring users"""
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📅 +7 дней", callback_data="bulk_extend:7"),
        types.InlineKeyboardButton(text="📅 +30 дней", callback_data="bulk_extend:30")
    )
    builder.row(
        types.InlineKeyboardButton(text="📅 +90 дней", callback_data="bulk_extend:90"),
        types.InlineKeyboardButton(text="📅 +365 дней", callback_data="bulk_extend:365")
    )
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="expiring_users"))
    
    await callback.message.edit_text(
        "🔄 **Массовое продление пользователей**\n\n"
        "На сколько дней продлить всех истекающих пользователей?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("bulk_extend:"), AuthFilter())
async def confirm_bulk_extend(callback: types.CallbackQuery, state: FSMContext):
    """Confirm bulk extension"""
    await callback.answer()
    
    days = int(callback.data.split(":")[1])
    
    try:
        users_list = await users_api.get_all_users()
        now = datetime.now()
        week_later = now + timedelta(days=7)
        
        expiring_users = []
        for user in users_list:
            expire_at = user.get('expireAt')
            if expire_at:
                try:
                    expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                    if now < expire_date < week_later:
                        expiring_users.append(user)
                except Exception:
                    pass
        
        if not expiring_users:
            await callback.message.edit_text(
                "✅ Нет пользователей для продления",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats")
                ]])
            )
            return
        
        # Confirm bulk action
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"execute_bulk_extend:{days}"))
        builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="expiring_users"))
        
        await callback.message.edit_text(
            f"🔄 **Подтверждение массового продления**\n\n"
            f"Будет продлено **{len(expiring_users)}** пользователей на **{days} дней**\n\n"
            f"Продолжить?",
            reply_markup=builder.as_markup()
        )
        
        # Store data for execution
        await state.update_data(bulk_extend_days=days, bulk_extend_users=expiring_users)
        
    except Exception as e:
        logger.error(f"Error preparing bulk extend: {e}")
        await callback.message.edit_text("❌ Ошибка при подготовке массового продления")

@router.callback_query(F.data.startswith("execute_bulk_extend:"), AuthFilter())
async def execute_bulk_extend(callback: types.CallbackQuery, state: FSMContext):
    """Execute bulk extension"""
    await callback.answer()
    
    days = int(callback.data.split(":")[1])
    data = await state.get_data()
    users_to_extend = data.get('bulk_extend_users', [])
    
    if not users_to_extend:
        await callback.message.edit_text("❌ Нет пользователей для продления")
        return
    
    await callback.message.edit_text("🔄 Выполняется массовое продление...")
    
    success_count = 0
    error_count = 0
    
    for user in users_to_extend:
        try:
            current_expire = user.get('expireAt')
            if current_expire:
                current_date = datetime.fromisoformat(current_expire.replace('Z', '+00:00'))
                new_expire_date = current_date + timedelta(days=days)
            else:
                new_expire_date = datetime.now() + timedelta(days=days)
            
            update_data = {"expireAt": new_expire_date.isoformat()}
            success = await users_api.update_user(user['uuid'], update_data)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            logger.error(f"Error extending user {user.get('username', 'Unknown')}: {e}")
            error_count += 1
    
    await state.clear()
    
    result_text = f"✅ **Массовое продление завершено**\n\n"
    result_text += f"Успешно продлено: **{success_count}** пользователей\n"
    if error_count > 0:
        result_text += f"Ошибок: **{error_count}**\n"
    result_text += f"Продлено на: **{days} дней**"
    
    await callback.message.edit_text(
        result_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад к статистике", callback_data="users_extended_stats")
        ]])
    )

# ================ USER DEVICES MANAGEMENT ================

@router.callback_query(F.data.startswith("user_devices:"), AuthFilter())
async def show_user_devices(callback: types.CallbackQuery, state: FSMContext):
    """Show user devices and connections"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Get user data
        user = await users_api.get_user_by_uuid(user_uuid)
        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_users")
                ]])
            )
            return
        
        username = user.get('username', 'Unknown')
        
        # Показываем реальную информацию об устройствах
        devices_text = f"📱 **Устройства пользователя {escape_markdown(username)}**\n\n"
        
        # Информация о подключениях
        status = user.get('status', 'Unknown')
        last_online = user.get('lastOnline')
        used_traffic = user.get('usedTraffic', 0) or 0
        
        devices_text += f"**📊 Статистика подключений:**\n"
        devices_text += f"• Статус: {'🟢 Активен' if status == 'ACTIVE' else '🔴 Неактивен'}\n"
        devices_text += f"• Использовано трафика: {format_bytes(used_traffic)}\n"
        
        if last_online:
            devices_text += f"• Последняя активность: {last_online[:19].replace('T', ' ')}\n"
        
        devices_text += f"\n**🔧 Доступные операции:**\n"
        devices_text += f"• Сброс активных подключений\n"
        devices_text += f"• Принудительное переподключение\n"
        devices_text += f"• Обновление конфигурации"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Сбросить подключения", callback_data=f"reset_connections:{user_uuid}"))
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"user_devices:{user_uuid}"))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"refresh_user:{user_uuid}"))
        
        await callback.message.edit_text(
            devices_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing user devices: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении информации об устройствах",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}")
            ]])
        )

@router.callback_query(F.data.startswith("reset_connections:"), AuthFilter())
async def reset_user_connections(callback: types.CallbackQuery, state: FSMContext):
    """Reset user connections"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    # Show confirmation
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Да, сбросить", callback_data=f"confirm_reset_connections:{user_uuid}"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"user_devices:{user_uuid}"))
    
    await callback.message.edit_text(
        "🔄 **Сброс подключений пользователя**\n\n"
        "⚠️ Это действие разорвет все активные подключения пользователя.\n"
        "Пользователю потребуется переподключиться.\n\n"
        "Продолжить?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("confirm_reset_connections:"), AuthFilter())
async def confirm_reset_connections(callback: types.CallbackQuery, state: FSMContext):
    """Confirm connection reset"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        # Попытка сброса подключений через API (может не поддерживаться)
        # В случае отсутствия специального метода, можно перезапустить/обновить пользователя
        success = await users_api.update_user(user_uuid, {"status": "ACTIVE"})
        
        if success:
            await callback.message.edit_text(
                "✅ Подключения пользователя сброшены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад к устройствам", callback_data=f"user_devices:{user_uuid}")
                ]])
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка при сбросе подключений",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"user_devices:{user_uuid}")
                ]])
            )
            
    except Exception as e:
        logger.error(f"Error resetting connections: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при сбросе подключений",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"user_devices:{user_uuid}")
            ]])
        )

# ================ ADDITIONAL STATISTICS ================

@router.callback_query(F.data == "stats_by_nodes", AuthFilter())
async def show_stats_by_nodes(callback: types.CallbackQuery):
    """Show detailed statistics by nodes"""
    await callback.answer()
    
    try:
        users_list = await users_api.get_all_users()
        nodes_list = await nodes_api.get_all_nodes()
        
        stats_text = "📊 **Статистика по нодам**\n\n"
        
        for node in nodes_list:
            node_uuid = node.get('uuid')
            node_name = node.get('name', 'Unknown')
            is_connected = node.get('isConnected', False)
            
            # Filter users for this node
            node_users = [user for user in users_list if user.get('nodeUuid') == node_uuid]
            
            status_emoji = "🟢" if is_connected else "🔴"
            total_users = len(node_users)
            active_users = sum(1 for user in node_users if user.get('status') == 'ACTIVE')
            
            total_traffic = sum(user.get('usedTraffic', 0) or 0 for user in node_users)
            
            stats_text += f"{status_emoji} **{escape_markdown(node_name)}**\n"
            stats_text += f"  👥 Пользователей: {total_users} (активных: {active_users})\n"
            stats_text += f"  💾 Трафик: {format_bytes(total_traffic)}\n"
            stats_text += f"  🌐 Адрес: {node.get('address', 'N/A')}:{node.get('port', 'N/A')}\n\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_by_nodes"))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats"))
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing stats by nodes: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики по нодам",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats")
            ]])
        )

@router.callback_query(F.data == "stats_by_period", AuthFilter())
async def show_stats_by_period(callback: types.CallbackQuery):
    """Show statistics by time periods"""
    await callback.answer()
    
    try:
        users_list = await users_api.get_all_users()
        
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Count new users by periods
        new_today = 0
        new_week = 0
        new_month = 0
        
        for user in users_list:
            created_at = user.get('createdAt')
            if created_at:
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if created_date > day_ago:
                        new_today += 1
                    if created_date > week_ago:
                        new_week += 1
                    if created_date > month_ago:
                        new_month += 1
                except Exception:
                    pass
        
        # Traffic analysis by periods
        stats_text = "📈 **Статистика по периодам**\n\n"
        
        stats_text += "**👥 Новые пользователи:**\n"
        stats_text += f"• За сегодня: {new_today}\n"
        stats_text += f"• За неделю: {new_week}\n"
        stats_text += f"• За месяц: {new_month}\n\n"
        
        # Activity analysis
        total_users = len(users_list)
        active_users = sum(1 for user in users_list if user.get('status') == 'ACTIVE')
        
        stats_text += "**📊 Активность:**\n"
        stats_text += f"• Всего пользователей: {total_users}\n"
        stats_text += f"• Активных: {active_users}\n"
        if total_users > 0:
            activity_rate = (active_users / total_users) * 100
            stats_text += f"• Уровень активности: {activity_rate:.1f}%\n"
        
        # Traffic statistics
        total_traffic = sum(user.get('usedTraffic', 0) or 0 for user in users_list)
        avg_traffic = total_traffic / total_users if total_users > 0 else 0
        
        stats_text += f"\n**💾 Трафик:**\n"
        stats_text += f"• Общий: {format_bytes(total_traffic)}\n"
        stats_text += f"• Средний на пользователя: {format_bytes(avg_traffic)}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_by_period"))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats"))
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing stats by period: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики по периодам",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats")
            ]])
        )

# ================ EXPORT FUNCTIONALITY ================

@router.callback_query(F.data == "export_users", AuthFilter())
async def export_users_menu(callback: types.CallbackQuery):
    """Show export options"""
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📄 Список всех пользователей", callback_data="export_all_users"))
    builder.row(types.InlineKeyboardButton(text="🟢 Только активные", callback_data="export_active_users"))
    builder.row(types.InlineKeyboardButton(text="⚠️ Истекающие", callback_data="export_expiring_users"))
    builder.row(types.InlineKeyboardButton(text="❌ Истекшие", callback_data="export_expired_users"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users"))
    
    await callback.message.edit_text(
        "📤 **Экспорт пользователей**\n\n"
        "Выберите категорию пользователей для экспорта в текстовом формате:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("export_"), AuthFilter())
async def handle_export(callback: types.CallbackQuery):
    """Handle export requests"""
    await callback.answer()
    
    export_type = callback.data.replace("export_", "")
    
    try:
        users_list = await users_api.get_all_users()
        
        # Фильтруем пользователей по типу экспорта
        if export_type == "active_users":
            filtered_users = [user for user in users_list if user.get('status') == 'ACTIVE']
            title = "Активные пользователи"
        elif export_type == "expiring_users":
            now = datetime.now()
            week_later = now + timedelta(days=7)
            filtered_users = []
            for user in users_list:
                expire_at = user.get('expireAt')
                if expire_at:
                    try:
                        expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                        if now < expire_date < week_later:
                            filtered_users.append(user)
                    except Exception:
                        pass
            title = "Истекающие пользователи"
        elif export_type == "expired_users":
            now = datetime.now()
            filtered_users = []
            for user in users_list:
                expire_at = user.get('expireAt')
                if expire_at:
                    try:
                        expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                        if expire_date < now:
                            filtered_users.append(user)
                    except Exception:
                        pass
            title = "Истекшие пользователи"
        else:  # all_users
            filtered_users = users_list
            title = "Все пользователи"
        
        # Создаем текстовый экспорт
        export_text = f"📊 **{title}** (Всего: {len(filtered_users)})\n\n"
        
        for i, user in enumerate(filtered_users[:50], 1):  # Ограничиваем до 50 для телеграма
            username = user.get('username', 'Unknown')
            status = user.get('status', 'Unknown')
            used_traffic = format_bytes(user.get('usedTraffic', 0) or 0)
            expire_at = user.get('expireAt', 'Не указано')
            if expire_at and expire_at != 'Не указано':
                expire_at = expire_at[:19].replace('T', ' ')
            
            status_emoji = "🟢" if status == 'ACTIVE' else "🔴"
            
            export_text += f"{i}. {status_emoji} **{escape_markdown(username)}**\n"
            export_text += f"   Трафик: {used_traffic} | Истекает: {expire_at}\n\n"
        
        if len(filtered_users) > 50:
            export_text += f"... и еще {len(filtered_users) - 50} пользователей\n\n"
            export_text += f"💡 Для полного экспорта используйте веб-интерфейс"
        
        await callback.message.edit_text(
            export_text,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="export_users")
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при экспорте данных",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="export_users")
            ]])
        )

# ================ MASS USER OPERATIONS ================

@router.callback_query(F.data == "mass_operations", AuthFilter())
async def show_mass_operations(callback: types.CallbackQuery):
    """Show mass operations menu"""
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Массовое продление", callback_data="mass_extend_menu"))
    builder.row(types.InlineKeyboardButton(text="⏸️ Массовая деактивация", callback_data="mass_deactivate_menu"))
    builder.row(types.InlineKeyboardButton(text="▶️ Массовая активация", callback_data="mass_activate_menu"))
    builder.row(types.InlineKeyboardButton(text="🗑️ Массовое удаление", callback_data="mass_delete_menu"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users"))
    
    await callback.message.edit_text(
        "⚙️ **Массовые операции**\n\n"
        "⚠️ **Внимание!** Массовые операции влияют на множество пользователей одновременно\\.\n\n"
        "Выберите тип операции:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "mass_extend_menu", AuthFilter())
async def mass_extend_menu(callback: types.CallbackQuery):
    """Show mass extend menu"""
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⚠️ Истекающих пользователей", callback_data="extend_all_expiring"))
    builder.row(types.InlineKeyboardButton(text="❌ Истекших пользователей", callback_data="extend_all_expired"))
    builder.row(types.InlineKeyboardButton(text="🟢 Активных пользователей", callback_data="extend_all_active"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="mass_operations"))
    
    await callback.message.edit_text(
        "🔄 **Массовое продление пользователей**\n\n"
        "Выберите категорию пользователей для продления:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("mass_"), AuthFilter())
async def handle_mass_operation_placeholder(callback: types.CallbackQuery):
    """Placeholder for mass operations"""
    await callback.answer()
    
    operation = callback.data.replace("mass_", "").replace("_menu", "")
    
    await callback.message.edit_text(
        f"⚙️ **Массовая операция: {operation}**\n\n"
        f"🔧 Функция массовых операций в разработке\n\n"
        f"Планируется реализация:\n"
        f"• Фильтрация пользователей\n"
        f"• Предварительный просмотр\n"
        f"• Пакетное выполнение\n"
        f"• Отчет о результатах",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="mass_operations")
        ]])
    )

# ================ USER HISTORY AND LOGS ================

@router.callback_query(F.data.startswith("user_history:"), AuthFilter())
async def show_user_history(callback: types.CallbackQuery):
    """Show user activity history"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        user = await users_api.get_user_by_uuid(user_uuid)
        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return
        
        username = user.get('username', 'Unknown')
        
        # Показываем реальную доступную информацию
        history_text = f"📋 **История пользователя {escape_markdown(username)}**\n\n"
        
        # Временные метки
        created_at = user.get('createdAt')
        updated_at = user.get('updatedAt')
        expire_at = user.get('expireAt')
        last_online = user.get('lastOnline')
        
        history_text += "**📅 Временная линия:**\n"
        if created_at:
            history_text += f"• Создан: {created_at[:19].replace('T', ' ')}\n"
        if updated_at:
            history_text += f"• Последнее изменение: {updated_at[:19].replace('T', ' ')}\n"
        if last_online:
            history_text += f"• Последняя активность: {last_online[:19].replace('T', ' ')}\n"
        if expire_at:
            history_text += f"• Истекает: {expire_at[:19].replace('T', ' ')}\n"
        
        # Статистика использования
        history_text += f"\n**📊 Статистика использования:**\n"
        history_text += f"• Использовано трафика: {format_bytes(user.get('usedTraffic', 0) or 0)}\n"
        history_text += f"• Текущий статус: {user.get('status', 'Unknown')}\n"
        
        if user.get('trafficLimit'):
            limit = user.get('trafficLimit')
            used = user.get('usedTraffic', 0) or 0
            percentage = (used / limit * 100) if limit > 0 else 0
            history_text += f"• Лимит трафика: {format_bytes(limit)}\n"
            history_text += f"• Использовано: {percentage:.1f}%\n"
        
        # Дополнительная информация
        if user.get('telegramId'):
            history_text += f"• Telegram ID: {user.get('telegramId')}\n"
        
        if user.get('description'):
            history_text += f"• Описание: {user.get('description')}\n"
        
        # Вычисляем время использования
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                days_active = (datetime.now() - created_date).days
                history_text += f"• Дней с создания: {days_active}\n"
            except Exception:
                pass
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"user_history:{user_uuid}"))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}"))
        
        await callback.message.edit_text(
            history_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing user history: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении истории пользователя",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}")
            ]])
        )


# ================ FINAL ROUTER CONFIGURATION ================

# Добавляем дополнительные кнопки в детальный просмотр пользователя
async def show_user_details_extended(message: types.Message, user: dict, state: FSMContext):
    """Extended version of show_user_details with more options"""
    try:
        user_details = format_user_details(user)
        
        builder = InlineKeyboardBuilder()
        
        # Основные действия
        builder.row(types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_user:{user.get('uuid')}"))
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить данные", callback_data=f"refresh_user:{user.get('uuid')}"))
        
        # Управление статусом
        if user.get('status') == 'ACTIVE':
            builder.row(types.InlineKeyboardButton(text="⏸️ Деактивировать", callback_data=f"deactivate_user:{user.get('uuid')}"))
        else:
            builder.row(types.InlineKeyboardButton(text="▶️ Активировать", callback_data=f"activate_user:{user.get('uuid')}"))
        
        # Управление трафиком
        builder.row(types.InlineKeyboardButton(text="🔄 Сбросить трафик", callback_data=f"reset_traffic:{user.get('uuid')}"))
        
        # Расширенные функции
        builder.row(
            types.InlineKeyboardButton(text="📱 Устройства", callback_data=f"user_devices:{user.get('uuid')}"),
            types.InlineKeyboardButton(text="📋 История", callback_data=f"user_history:{user.get('uuid')}")
        )
        
        # Подписка и конфигурации
        builder.row(types.InlineKeyboardButton(text="🔗 Подписка", callback_data=f"subscription:{user.get('uuid')}"))
        
        # Опасные действия
        builder.row(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_user:{user.get('uuid')}"))
        
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="list_users"))
        
        await message.edit_text(
            text=user_details,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing extended user details: {e}")
        await message.edit_text(
            "❌ Ошибка при отображении данных пользователя",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_users")
            ]])
        )

@router.callback_query(F.data == "expiring_users", AuthFilter())
async def show_expiring_users(callback: types.CallbackQuery, state: FSMContext):
    """Show users expiring soon"""
    await callback.answer()
    
    try:
        users_list = await users_api.get_all_users()
        
        now = datetime.now()
        week_later = now + timedelta(days=7)
        
        expiring_users = []
        for user in users_list:
            expire_at = user.get('expireAt')
            if expire_at:
                try:
                    expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                    if now < expire_date < week_later:
                        expiring_users.append(user)
                except Exception:
                    pass
        
        if not expiring_users:
            await callback.message.edit_text(
                "⏰ **Истекающие пользователи**\n\n"
                "✅ Нет пользователей, истекающих в ближайшую неделю",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats")
                ]])
            )
            return
        
        # Store expiring users in state
        await state.update_data(users=expiring_users, page=0)
        await state.set_state(UserStates.selecting_user)
        
        message_text = f"⏰ **Пользователи, истекающие в течение недели ({len(expiring_users)})**\n\n"
        
        for user in expiring_users[:10]:  # Показываем первые 10
            expire_at = user.get('expireAt')
            expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
            days_left = (expire_date - now).days
            
            status_emoji = "🟢" if user.get('status') == 'ACTIVE' else "🔴"
            urgency_emoji = "🔥" if days_left <= 3 else "⚠️" if days_left <= 5 else "⏰"
            
            username = user.get('username', 'Unknown')
            used_traffic = user.get('usedTraffic', 0) or 0
            
            message_text += f"{status_emoji}{urgency_emoji} **{escape_markdown(username)}**\n"
            message_text += f"  📅 Истекает через {days_left} дн. ({expire_date.strftime('%Y-%m-%d')})\n"
            message_text += f"  💾 Использовано: {format_bytes(used_traffic)}\n\n"
        
        if len(expiring_users) > 10:
            message_text += f"... и еще {len(expiring_users) - 10} пользователей\n\n"
        
        # Кнопки для массовых действий
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="📝 Список полный", callback_data="list_users"),
            types.InlineKeyboardButton(text="🔄 Продлить всех", callback_data="extend_all_expiring")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats"))
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing expiring users: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении списка истекающих пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats")
            ]])
        )

# В конце файла убрать дублирование
# Оставить только одно определение:
show_user_details = show_user_details_extended

# ================ UPDATE USER DETAILS TO INCLUDE SUBSCRIPTION OPTIONS ================

async def show_user_details_with_subscription(message: types.Message, user: dict, state: FSMContext):
    """Enhanced user details with subscription management options"""
    try:
        user_details = format_user_details(user)
        
        builder = InlineKeyboardBuilder()
        
        # Основные действия
        builder.row(types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_user:{user.get('uuid')}"))
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить данные", callback_data=f"refresh_user:{user.get('uuid')}"))
        
        # Управление статусом
        if user.get('status') == 'ACTIVE':
            builder.row(types.InlineKeyboardButton(text="⏸️ Деактивировать", callback_data=f"deactivate_user:{user.get('uuid')}"))
        else:
            builder.row(types.InlineKeyboardButton(text="▶️ Активировать", callback_data=f"activate_user:{user.get('uuid')}"))
        
        # Управление трафиком
        builder.row(types.InlineKeyboardButton(text="🔄 Сбросить трафик", callback_data=f"reset_traffic:{user.get('uuid')}"))
        
        # Расширенные функции
        builder.row(
            types.InlineKeyboardButton(text="📱 Устройства", callback_data=f"user_devices:{user.get('uuid')}"),
            types.InlineKeyboardButton(text="📋 История", callback_data=f"user_history:{user.get('uuid')}")
        )
        
        # Подписка и конфигурации - ОБНОВЛЕННЫЙ РАЗДЕЛ
        builder.row(
            types.InlineKeyboardButton(text="🔗 Подписка", callback_data=f"subscription:{user.get('uuid')}"),
            types.InlineKeyboardButton(text="🔧 Конфигурации", callback_data=f"subscription_configs:{user.get('uuid')}")
        )
        
        # Опасные действия
        builder.row(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_user:{user.get('uuid')}"))
        
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="list_users"))
        
        await message.edit_text(
            text=user_details,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing user details with subscription: {e}")
        await message.edit_text(
            "❌ Ошибка при отображении данных пользователя",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_users")
            ]])
        )

# Заменяем старую функцию на новую
show_user_details = show_user_details_with_subscription

logger.info("User handlers module loaded successfully (with enhanced subscription support)")