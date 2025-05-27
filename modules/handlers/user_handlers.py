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
from modules.api.client import RemnaAPI
from modules.utils.formatters_aiogram import (
    format_bytes, format_user_details, format_datetime,
    truncate_text, escape_markdown
)

logger = logging.getLogger(__name__)

router = Router()

# ================ MAIN USERS MENU ================

@router.callback_query(F.data == "users", AuthFilter())
async def handle_users_menu(callback: types.CallbackQuery, state: FSMContext):
    """Handle users menu selection"""
    await state.clear()
    await show_users_menu(callback)

async def show_users_menu(callback: types.CallbackQuery):
    """Show users menu"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📋 Список всех пользователей", callback_data="list_users"))
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск пользователей", callback_data="search_users_menu"))
    builder.row(types.InlineKeyboardButton(text="➕ Создать пользователя", callback_data="create_user"))
    builder.row(types.InlineKeyboardButton(text="📊 Статистика пользователей", callback_data="users_stats"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "👥 **Управление пользователями**\n\n"
    try:
        # Получаем всех пользователей для подсчета статистики
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        users_count = users_response.total if hasattr(users_response, 'total') else len(users_response.users)
        active_count = sum(1 for user in users_response.users if user.is_active)
        
        total_traffic_used = sum(user.used_traffic or 0 for user in users_response.users)
        total_traffic_limit = sum(user.traffic_limit or 0 for user in users_response.users if user.traffic_limit)
        
        message += f"📊 **Статистика:**\n"
        message += f"• Всего пользователей: {users_count}\n"
        message += f"• Активных: {active_count}\n"
        message += f"• Неактивных: {users_count - active_count}\n"
        message += f"• Использовано трафика: {format_bytes(total_traffic_used)}\n"
        if total_traffic_limit > 0:
            message += f"• Общий лимит: {format_bytes(total_traffic_limit)}\n"
        message += "\n"
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        message += "📊 Статистика недоступна\n\n"
    
    message += "Выберите действие:"

    await callback.answer()
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
        # Get all users using SDK
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response.users:
            await callback.message.edit_text(
                "👥 Пользователи не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
                ]])
            )
            return

        # Convert users to dict format for compatibility and store in state
        users = [user.model_dump() for user in users_response.users]
        await state.update_data(users=users, page=0)
        
        # Show first page
        await show_users_page(callback.message, users, 0, state)
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
    """Show users page with pagination"""
    try:
        total_users = len(users)
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, total_users)
        page_users = users[start_idx:end_idx]
        
        # Build message
        message_text = f"👥 **Список пользователей ({start_idx + 1}-{end_idx} из {total_users})**\n\n"
        
        for i, user in enumerate(page_users):
            user_name = user.get('username', f"User {user.get('uuid', 'Unknown')[:8]}")
            status_emoji = "🟢" if user.get('is_active', False) else "🔴"
            traffic_used = format_bytes(user.get('used_traffic', 0))
            traffic_limit = format_bytes(user.get('traffic_limit', 0)) if user.get('traffic_limit') else "∞"
            
            # Format expiration date
            expire_text = "Не указана"
            if user.get('expire_at'):
                try:
                    expire_date = datetime.fromisoformat(user['expire_at'].replace('Z', '+00:00'))
                    days_left = (expire_date - datetime.now().astimezone()).days
                    expire_text = f"{user['expire_at'][:10]} ({days_left} дн.)"
                except Exception:
                    expire_text = user['expire_at'][:10]
            
            message_text += f"{status_emoji} **{escape_markdown(user_name)}**\n"
            message_text += f"  💾 Трафик: {traffic_used} / {traffic_limit}\n"
            message_text += f"  📅 Истекает: {expire_text}\n"
            if user.get('telegram_id'):
                message_text += f"  📱 TG ID: {user.get('telegram_id')}\n"
            message_text += "\n"
        
        # Create pagination keyboard
        builder = InlineKeyboardBuilder()
        
        # Add user selection buttons
        for i, user in enumerate(page_users):
            user_name = user.get('username', f"User {user.get('uuid', 'Unknown')[:8]}")
            builder.row(types.InlineKeyboardButton(
                text=f"👤 {user_name}",
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
        if user.get('is_active', False):
            builder.row(types.InlineKeyboardButton(text="⏸️ Деактивировать", callback_data=f"deactivate_user:{user.get('uuid')}"))
        else:
            builder.row(types.InlineKeyboardButton(text="▶️ Активировать", callback_data=f"activate_user:{user.get('uuid')}"))
        
        # Traffic management
        builder.row(types.InlineKeyboardButton(text="🔄 Сбросить трафик", callback_data=f"reset_traffic:{user.get('uuid')}"))
        
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
        sdk = RemnaAPI.get_sdk()
        # Get updated user data
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        # Find updated user
        updated_user = None
        for user in users_response.users:
            if user.uuid == user_uuid:
                updated_user = user.model_dump()
                break
        
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
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.enable_user(user_uuid)
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
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.disable_user(user_uuid)
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
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        updated_user = None
        for user in users_response.users:
            if user.uuid == user_uuid:
                updated_user = user.model_dump()
                break
        
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
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.reset_user_traffic(user_uuid)
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
    """Show user subscription info"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        subscription = await sdk.subscriptions.get_user_subscription_url(user_uuid)
        if subscription:
            subscription_text = f"🔗 **Подписка пользователя**\n\n"
            subscription_text += f"**URL:** `{subscription}`\n"
            subscription_text += f"**QR-код:** Доступен в веб-интерфейсе\n"
            
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}"))
            
            await callback.message.edit_text(
                subscription_text,
                reply_markup=builder.as_markup()
            )
        else:
            await callback.answer("❌ Подписка не найдена", show_alert=True)
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        await callback.answer("❌ Ошибка при получении подписки", show_alert=True)

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
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.delete_user(user_uuid)
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
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        filtered_users = [
            user.model_dump() for user in users_response.users
            if search_term.lower() in user.username.lower()
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
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        filtered_users = [
            user.model_dump() for user in users_response.users
            if user.telegram_id == telegram_id
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

@router.callback_query(F.data == "create_user", AuthFilter())
async def start_create_user(callback: types.CallbackQuery, state: FSMContext):
    """Start user creation process"""
    await callback.answer()
    await state.clear()
    await state.set_state(UserStates.enter_username)
    
    await callback.message.edit_text(
        "➕ **Создание нового пользователя**\n\n"
        "**Шаг 1/4:** Введите имя пользователя:\n\n"
        "ℹ️ Имя должно быть уникальным и содержать только латинские буквы, цифры и символы _ -",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
        ]])
    )

@router.message(StateFilter(UserStates.enter_username), AuthFilter())
async def handle_username_input(message: types.Message, state: FSMContext):
    """Handle username input"""
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
    
    await message.answer(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n\n"
        "**Шаг 2/4:** Введите Telegram ID пользователя:\n\n"
        "ℹ️ Введите 0 или пропустите, если Telegram ID неизвестен",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_telegram_id"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
        ]])
    )

@router.message(StateFilter(UserStates.enter_telegram_id), AuthFilter())
async def handle_telegram_id_input(message: types.Message, state: FSMContext):
    """Handle Telegram ID input"""
    try:
        telegram_id = int(message.text.strip())
        if telegram_id < 0:
            raise ValueError("Negative ID")
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID (положительное число) или 0")
        return
    
    data = await state.get_data()
    username = data.get('username')
    
    await state.update_data(telegram_id=telegram_id if telegram_id > 0 else None)
    await state.set_state(UserStates.enter_traffic_limit)
    
    await message.answer(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** {telegram_id if telegram_id > 0 else 'Не указан'}\n\n"
        "**Шаг 3/4:** Введите лимит трафика:\n\n"
        "Примеры:\n"
        "• `10GB` - 10 гигабайт\n"
        "• `500MB` - 500 мегабайт\n"
        "• `1TB` - 1 терабайт\n"
        "• `0` - без ограничений",
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
    
    await state.update_data(telegram_id=None)
    await state.set_state(UserStates.enter_traffic_limit)
    
    await callback.message.edit_text(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** Не указан\n\n"
        "**Шаг 3/4:** Введите лимит трафика:",
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
            "• `10GB` или `10G`\n"
            "• `500MB` или `500M`\n"
            "• `1TB` или `1T`\n"
            "• `0` - без ограничений"
        )
        return
    
    data = await state.get_data()
    await state.update_data(traffic_limit=traffic_limit)
    await state.set_state(UserStates.enter_description)
    
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    traffic_text = format_bytes(traffic_limit) if traffic_limit > 0 else "Без ограничений"
    
    await message.answer(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** {telegram_id or 'Не указан'}\n"
        f"✅ **Лимит трафика:** {traffic_text}\n\n"
        "**Шаг 4/4:** Введите описание пользователя (опционально):",
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
    await state.update_data(traffic_limit=0)
    await state.set_state(UserStates.enter_description)
    
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    
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
    telegram_id = data.get('telegram_id')
    traffic_limit = data.get('traffic_limit', 0)
    description = data.get('description')
    
    traffic_text = format_bytes(traffic_limit) if traffic_limit > 0 else "Без ограничений"
    
    confirmation_text = (
        "➕ **Создание пользователя - Подтверждение**\n\n"
        f"**Имя:** {username}\n"
        f"**Telegram ID:** {telegram_id or 'Не указан'}\n"
        f"**Лимит трафика:** {traffic_text}\n"
        f"**Описание:** {description or 'Не указано'}\n\n"
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
        # Prepare user data for SDK
        user_data = {
            "username": data.get('username'),
            "traffic_limit": data.get('traffic_limit', 0),
        }
        
        if data.get('telegram_id'):
            user_data["telegram_id"] = data.get('telegram_id')
        
        if data.get('description'):
            user_data["description"] = data.get('description')
        
        # Create user using SDK
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.create_user(**user_data)
        
        if success:
            await callback.answer("✅ Пользователь создан", show_alert=True)
            await state.clear()
            await callback.message.edit_text(
                f"✅ **Пользователь создан успешно!**\n\n"
                f"Имя: **{user_data['username']}**\n"
                f"Статус: Активен\n\n"
                f"Пользователь готов к использованию.",
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
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if users_response.users:
            total_users = users_response.total if hasattr(users_response, 'total') else len(users_response.users)
            active_users = sum(1 for user in users_response.users if user.is_active)
            inactive_users = total_users - active_users
            
            total_traffic_used = sum(user.used_traffic or 0 for user in users_response.users)
            total_traffic_limit = sum(user.traffic_limit or 0 for user in users_response.users if user.traffic_limit)
            
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
    
    # Format current values
    username = user.get('username', 'Unknown')
    telegram_id = user.get('telegram_id', 'Не указан')
    traffic_limit = format_bytes(user.get('traffic_limit', 0)) if user.get('traffic_limit') else "Без ограничений"
    description = user.get('description', 'Не указано')
    
    message = f"📝 **Редактирование пользователя**\n\n"
    message += f"👤 Имя: {escape_markdown(username)}\n\n"
    message += f"**Текущие значения:**\n"
    message += f"📱 Telegram ID: {telegram_id}\n"
    message += f"📈 Лимит трафика: {traffic_limit}\n"
    message += f"📝 Описание: {escape_markdown(str(description))}\n\n"
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
            "📱 **Изменение Telegram ID**\n\n"
            "Введите новый Telegram ID (или 0 для удаления):",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")
            ]])
        )
    elif field == "traffic_limit":
        await state.set_state(UserStates.enter_edit_traffic_limit)
        await callback.message.edit_text(
            "📈 **Изменение лимита трафика**\n\n"
            "Введите новый лимит трафика:\n\n"
            "Примеры: `10GB`, `500MB`, `1TB`, `0` (без ограничений)",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="∞ Без ограничений", callback_data="set_unlimited"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")
            ]])
        )
    elif field == "description":
        await state.set_state(UserStates.enter_edit_description)
        await callback.message.edit_text(
            "📝 **Изменение описания**\n\n"
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
        # Update user using SDK
        sdk = RemnaAPI.get_sdk()
        update_data = {"telegram_id": telegram_id if telegram_id > 0 else None}
        success = await sdk.users.update_user(user['uuid'], update_data)
        
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
        # Update user using SDK
        sdk = RemnaAPI.get_sdk()
        update_data = {"traffic_limit": traffic_limit}
        success = await sdk.users.update_user(user['uuid'], update_data)
        
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
        # Update user using SDK
        sdk = RemnaAPI.get_sdk()
        update_data = {"description": description}
        success = await sdk.users.update_user(user['uuid'], update_data)
        
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
        # Update user using SDK
        sdk = RemnaAPI.get_sdk()
        update_data = {"traffic_limit": 0}
        success = await sdk.users.update_user(user['uuid'], update_data)
        
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
        # Update user using SDK
        sdk = RemnaAPI.get_sdk()
        update_data = {"description": ""}
        success = await sdk.users.update_user(user['uuid'], update_data)
        
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



# Добавляем в конец файла недостающий функционал

# ================ HWID DEVICES FUNCTIONALITY ================

@router.callback_query(F.data.startswith("user_devices:"), AuthFilter())
async def show_user_devices(callback: types.CallbackQuery, state: FSMContext):
    """Show user HWID devices"""
    await callback.answer()
    
    user_uuid = callback.data.split(":", 1)[1]
    
    try:
        sdk = RemnaAPI.get_sdk()
        # Получаем устройства пользователя
        devices = await sdk.users.get_user_devices(user_uuid)
        
        if not devices:
            await callback.message.edit_text(
                "📱 **HWID устройства пользователя**\n\n"
                "❌ Устройства не найдены или не поддерживаются",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}")
                ]])
            )
            return
        
        # Получаем данные пользователя
        data = await state.get_data()
        user = data.get('selected_user', {})
        username = user.get('username', 'Unknown')
        
        message_text = f"📱 **HWID устройства пользователя {escape_markdown(username)}**\n\n"
        
        builder = InlineKeyboardBuilder()
        
        for i, device in enumerate(devices):
            device_info = f"**Устройство {i+1}:**\n"
            device_info += f"• ID: `{device.get('hwid', 'Unknown')[:16]}...`\n"
            device_info += f"• Платформа: {device.get('platform', 'Unknown')}\n"
            device_info += f"• Первое подключение: {format_datetime(device.get('first_seen', ''))}\n"
            device_info += f"• Последнее подключение: {format_datetime(device.get('last_seen', ''))}\n"
            device_info += f"• Активно: {'✅' if device.get('is_active', False) else '❌'}\n\n"
            
            message_text += device_info
            
            # Добавляем кнопки управления устройством
            builder.row(types.InlineKeyboardButton(
                text=f"📱 Устройство {i+1}",
                callback_data=f"device_manage:{user_uuid}:{device.get('hwid', '')}"
            ))
        
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"user_devices:{user_uuid}"))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}"))
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting user devices: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении списка устройств",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"refresh_user:{user_uuid}")
            ]])
        )

@router.callback_query(F.data.startswith("device_manage:"), AuthFilter())
async def manage_device(callback: types.CallbackQuery, state: FSMContext):
    """Manage specific device"""
    await callback.answer()
    
    parts = callback.data.split(":", 2)
    user_uuid = parts[1]
    device_hwid = parts[2]
    
    try:
        sdk = RemnaAPI.get_sdk()
        # Получаем информацию об устройстве
        devices = await sdk.users.get_user_devices(user_uuid)
        device = None
        
        for d in devices:
            if d.get('hwid') == device_hwid:
                device = d
                break
        
        if not device:
            await callback.message.edit_text(
                "❌ Устройство не найдено",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"user_devices:{user_uuid}")
                ]])
            )
            return
        
        device_info = f"📱 **Управление устройством**\n\n"
        device_info += f"**ID:** `{device.get('hwid', 'Unknown')}`\n"
        device_info += f"**Платформа:** {device.get('platform', 'Unknown')}\n"
        device_info += f"**Первое подключение:** {format_datetime(device.get('first_seen', ''))}\n"
        device_info += f"**Последнее подключение:** {format_datetime(device.get('last_seen', ''))}\n"
        device_info += f"**Статус:** {'🟢 Активно' if device.get('is_active', False) else '🔴 Неактивно'}\n"
        
        builder = InlineKeyboardBuilder()
        
        if device.get('is_active', False):
            builder.row(types.InlineKeyboardButton(
                text="🚫 Заблокировать устройство",
                callback_data=f"device_block:{user_uuid}:{device_hwid}"
            ))
        else:
            builder.row(types.InlineKeyboardButton(
                text="✅ Разблокировать устройство",
                callback_data=f"device_unblock:{user_uuid}:{device_hwid}"
            ))
        
        builder.row(types.InlineKeyboardButton(
            text="🗑️ Удалить устройство",
            callback_data=f"device_delete:{user_uuid}:{device_hwid}"
        ))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к устройствам", callback_data=f"user_devices:{user_uuid}"))
        
        await callback.message.edit_text(
            text=device_info,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error managing device: {e}")
        await callback.answer("❌ Ошибка при управлении устройством", show_alert=True)

@router.callback_query(F.data.startswith("device_block:"), AuthFilter())
async def block_device(callback: types.CallbackQuery, state: FSMContext):
    """Block user device"""
    await callback.answer()
    
    parts = callback.data.split(":", 2)
    user_uuid = parts[1]
    device_hwid = parts[2]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.block_user_device(user_uuid, device_hwid)
        
        if success:
            await callback.answer("🚫 Устройство заблокировано", show_alert=True)
            # Обновляем информацию об устройстве
            await manage_device(callback, state)
        else:
            await callback.answer("❌ Ошибка при блокировке устройства", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error blocking device: {e}")
        await callback.answer("❌ Ошибка при блокировке устройства", show_alert=True)

@router.callback_query(F.data.startswith("device_unblock:"), AuthFilter())
async def unblock_device(callback: types.CallbackQuery, state: FSMContext):
    """Unblock user device"""
    await callback.answer()
    
    parts = callback.data.split(":", 2)
    user_uuid = parts[1]
    device_hwid = parts[2]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.unblock_user_device(user_uuid, device_hwid)
        
        if success:
            await callback.answer("✅ Устройство разблокировано", show_alert=True)
            # Обновляем информацию об устройстве
            await manage_device(callback, state)
        else:
            await callback.answer("❌ Ошибка при разблокировке устройства", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error unblocking device: {e}")
        await callback.answer("❌ Ошибка при разблокировке устройства", show_alert=True)

@router.callback_query(F.data.startswith("device_delete:"), AuthFilter())
async def delete_device_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm device deletion"""
    await callback.answer()
    
    parts = callback.data.split(":", 2)
    user_uuid = parts[1]
    device_hwid = parts[2]
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🗑️ Да, удалить",
        callback_data=f"device_delete_confirm:{user_uuid}:{device_hwid}"
    ))
    builder.row(types.InlineKeyboardButton(
        text="❌ Отмена",
        callback_data=f"device_manage:{user_uuid}:{device_hwid}"
    ))
    
    await callback.message.edit_text(
        "🗑️ **Удаление устройства**\n\n"
        f"**HWID:** `{device_hwid[:16]}...`\n\n"
        "⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n"
        "Устройство будет полностью удалено из системы.\n\n"
        "Продолжить?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("device_delete_confirm:"), AuthFilter())
async def confirm_device_deletion(callback: types.CallbackQuery, state: FSMContext):
    """Confirm device deletion"""
    await callback.answer()
    
    parts = callback.data.split(":", 2)
    user_uuid = parts[1]
    device_hwid = parts[2]
    
    try:
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.delete_user_device(user_uuid, device_hwid)
        
        if success:
            await callback.answer("✅ Устройство удалено", show_alert=True)
            # Возвращаемся к списку устройств
            await show_user_devices(callback, state)
        else:
            await callback.answer("❌ Ошибка при удалении устройства", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        await callback.answer("❌ Ошибка при удалении устройства", show_alert=True)

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

@router.message(StateFilter(UserStates.enter_username), AuthFilter())
async def handle_template_username_input(message: types.Message, state: FSMContext):
    """Handle username input for template creation"""
    data = await state.get_data()
    template_id = data.get('selected_template')
    
    # Если это создание по шаблону
    if template_id:
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
    else:
        # Обычное создание пользователя - используем существующий обработчик
        await handle_username_input(message, state)

@router.callback_query(F.data == "skip_telegram_id_template", AuthFilter())
async def skip_telegram_id_template(callback: types.CallbackQuery, state: FSMContext):
    """Skip Telegram ID for template creation"""
    await callback.answer()
    
    data = await state.get_data()
    template_id = data.get('selected_template')
    template = USER_TEMPLATES[template_id]
    username = data.get('username')
    
    await state.update_data(telegram_id=None)
    
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

@router.message(StateFilter(UserStates.enter_telegram_id), AuthFilter())
async def handle_template_telegram_id_input(message: types.Message, state: FSMContext):
    """Handle Telegram ID input for template creation"""
    data = await state.get_data()
    template_id = data.get('selected_template')
    
    # Если это создание по шаблону
    if template_id:
        try:
            telegram_id = int(message.text.strip())
            if telegram_id < 0:
                raise ValueError("Negative ID")
        except ValueError:
            await message.answer("❌ Введите корректный Telegram ID (положительное число) или 0")
            return
        
        template = USER_TEMPLATES[template_id]
        username = data.get('username')
        
        await state.update_data(telegram_id=telegram_id if telegram_id > 0 else None)
        
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
    else:
        # Обычное создание пользователя
        await handle_telegram_id_input(message, state)

@router.callback_query(F.data == "skip_description_template", AuthFilter())
async def skip_description_template(callback: types.CallbackQuery, state: FSMContext):
    """Skip description for template creation"""
    await callback.answer()
    await state.update_data(description=None)
    await show_template_confirmation(callback.message, state)

@router.message(StateFilter(UserStates.enter_description), AuthFilter())
async def handle_template_description_input(message: types.Message, state: FSMContext):
    """Handle description input for template creation"""
    data = await state.get_data()
    template_id = data.get('selected_template')
    
    if template_id:
        description = message.text.strip()
        await state.update_data(description=description)
        await show_template_confirmation(message, state)
    else:
        # Обычное создание пользователя
        await handle_description_input(message, state)

async def show_template_confirmation(message: types.Message, state: FSMContext):
    """Show template user creation confirmation"""
    data = await state.get_data()
    template_id = data.get('selected_template')
    template = USER_TEMPLATES[template_id]
    
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    description = data.get('description')
    
    traffic_text = format_bytes(template['traffic_limit']) if template['traffic_limit'] > 0 else "Безлимитный"
    
    # Вычисляем дату истечения
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
        # Вычисляем дату истечения
        expire_date = datetime.now() + timedelta(days=template['expire_days'])
        
        # Prepare user data for SDK
        user_data = {
            "username": data.get('username'),
            "traffic_limit": template['traffic_limit'],
            "expire_at": expire_date.isoformat(),
            "description": data.get('description') or template['description']
        }
        
        if data.get('telegram_id'):
            user_data["telegram_id"] = data.get('telegram_id')
        
        # Create user using SDK
        sdk = RemnaAPI.get_sdk()
        success = await sdk.users.create_user(**user_data)
        
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
        sdk = RemnaAPI.get_sdk()
        
        # Получаем всех пользователей
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        users = users_response.users
        
        # Получаем информацию о нодах
        nodes = await sdk.nodes.get_all_nodes()
        
        # Базовая статистика
        total_users = len(users)
        active_users = sum(1 for user in users if user.is_active)
        inactive_users = total_users - active_users
        
        total_traffic_used = sum(user.used_traffic or 0 for user in users)
        total_traffic_limit = sum(user.traffic_limit or 0 for user in users if user.traffic_limit)
        
        # Статистика по нодам
        node_stats = {}
        for node in nodes:
            node_uuid = node.uuid
            node_users = [user for user in users if user.node_uuid == node_uuid]
            
            node_stats[node_uuid] = {
                'name': node.name,
                'total_users': len(node_users),
                'active_users': sum(1 for user in node_users if user.is_active),
                'traffic_used': sum(user.used_traffic or 0 for user in node_users),
                'traffic_limit': sum(user.traffic_limit or 0 for user in node_users if user.traffic_limit),
                'status': 'online' if node.is_connected else 'offline'
            }
        
        # Статистика по периодам
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        new_users_week = sum(
            1 for user in users 
            if user.created_at and datetime.fromisoformat(user.created_at.replace('Z', '+00:00')) > week_ago
        )
        new_users_month = sum(
            1 for user in users 
            if user.created_at and datetime.fromisoformat(user.created_at.replace('Z', '+00:00')) > month_ago
        )
        
        # Статистика по истечению
        expired_users = sum(
            1 for user in users 
            if user.expire_at and datetime.fromisoformat(user.expire_at.replace('Z', '+00:00')) < now
        )
        
        expiring_soon = sum(
            1 for user in users 
            if user.expire_at and now < datetime.fromisoformat(user.expire_at.replace('Z', '+00:00')) < now + timedelta(days=7)
        )
        
        # Формируем сообщение
        stats_text = "📊 **Расширенная статистика пользователей**\n\n"
        
        # Общая статистика
        stats_text += "**📈 Общая статистика:**\n"
        stats_text += f"• Всего пользователей: {total_users}\n"
        stats_text += f"• Активных: {active_users} ({(active_users/total_users*100):.1f}%)\n"
        stats_text += f"• Неактивных: {inactive_users} ({(inactive_users/total_users*100):.1f}%)\n"
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

@router.callback_query(F.data == "expiring_users", AuthFilter())
async def show_expiring_users(callback: types.CallbackQuery, state: FSMContext):
    """Show users expiring soon"""
    await callback.answer()
    
    try:
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        now = datetime.now()
        week_later = now + timedelta(days=7)
        
        expiring_users = [
            user for user in users_response.users
            if user.expire_at and now < datetime.fromisoformat(user.expire_at.replace('Z', '+00:00')) < week_later
        ]
        
        if not expiring_users:
            await callback.message.edit_text(
                "⏰ **Истекающие пользователи**\n\n"
                "✅ Нет пользователей, истекающих в ближайшую неделю",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users_extended_stats")
                ]])
            )
            return
        
        # Convert to dict format and store
        users_dict = [user.model_dump() for user in expiring_users]
        await state.update_data(users=users_dict, page=0)
        await state.set_state(UserStates.selecting_user)
        
        message_text = f"⏰ **Пользователи, истекающие в течение недели ({len(expiring_users)})**\n\n"
        
        for user in expiring_users[:10]:  # Показываем первые 10
            expire_date = datetime.fromisoformat(user.expire_at.replace('Z', '+00:00'))
            days_left = (expire_date - now).days
            
            status_emoji = "🟢" if user.is_active else "🔴"
            urgency_emoji = "🔥" if days_left <= 3 else "⚠️" if days_left <= 5 else "⏰"
            
            message_text += f"{status_emoji}{urgency_emoji} **{escape_markdown(user.username)}**\n"
            message_text += f"  📅 Истекает через {days_left} дн. ({expire_date.strftime('%Y-%m-%d')})\n"
            message_text += f"  💾 Использовано: {format_bytes(user.used_traffic or 0)}\n\n"
        
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

# Обновляем функцию show_user_details, чтобы добавить кнопку устройств
async def show_user_details(message: types.Message, user: dict, state: FSMContext):
    """Show user details with action buttons (updated version)"""
    try:
        user_details = format_user_details(user)
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_user:{user.get('uuid')}"))
        builder.row(types.InlineKeyboardButton(text="🔄 Обновить данные", callback_data=f"refresh_user:{user.get('uuid')}"))
        
        # Status control buttons
        if user.get('is_active', False):
            builder.row(types.InlineKeyboardButton(text="⏸️ Деактивировать", callback_data=f"deactivate_user:{user.get('uuid')}"))
        else:
            builder.row(types.InlineKeyboardButton(text="▶️ Активировать", callback_data=f"activate_user:{user.get('uuid')}"))
        
        # Traffic management
        builder.row(types.InlineKeyboardButton(text="🔄 Сбросить трафик", callback_data=f"reset_traffic:{user.get('uuid')}"))
        
        # Device management
        builder.row(types.InlineKeyboardButton(text="📱 Устройства", callback_data=f"user_devices:{user.get('uuid')}"))
        
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

# Обновляем основное меню пользователей
async def show_users_menu(callback: types.CallbackQuery):
    """Show users menu (updated version)"""
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
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "👥 **Управление пользователями**\n\n"
    try:
        # Получаем всех пользователей для подсчета статистики
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        users_count = users_response.total if hasattr(users_response, 'total') else len(users_response.users)
        active_count = sum(1 for user in users_response.users if user.is_active)
        
        total_traffic_used = sum(user.used_traffic or 0 for user in users_response.users)
        total_traffic_limit = sum(user.traffic_limit or 0 for user in users_response.users if user.traffic_limit)
        
        # Статистика по истечению
        now = datetime.now()
        expiring_soon = sum(
            1 for user in users_response.users 
            if user.expire_at and now < datetime.fromisoformat(user.expire_at.replace('Z', '+00:00')) < now + timedelta(days=7)
        )
        
        message += f"📊 **Статистика:**\n"
        message += f"• Всего пользователей: {users_count}\n"
        message += f"• Активных: {active_count}\n"
        message += f"• Неактивных: {users_count - active_count}\n"
        message += f"• Истекают скоро: {expiring_soon}\n"
        message += f"• Использовано трафика: {format_bytes(total_traffic_used)}\n"
        if total_traffic_limit > 0:
            message += f"• Общий лимит: {format_bytes(total_traffic_limit)}\n"
        message += "\n"
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        message += "📊 Статистика недоступна\n\n"
    
    message += "Выберите действие:"

    await callback.answer()
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )
