from aiogram import Router, types, F
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
import re

from modules.handlers_aiogram.auth import AuthFilter
from modules.handlers_aiogram.states import UserStates
from modules.api.sdk_client import RemnaSDK
from modules.utils.formatters_aiogram import (
    format_bytes, format_user_details, format_datetime,
    truncate_text, escape_markdown
)
from modules.utils.keyboard_helpers import KeyboardHelper, SelectionHelper, MenuHelper

logger = logging.getLogger(__name__)

router = Router()

# Initialize SDK
sdk = RemnaSDK()

@router.callback_query(Text("users"), AuthFilter())
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
        users_count = await sdk.get_users_count()
        users_stats = await sdk.get_users_stats()
        if users_stats:
            active_count = users_stats.get('active', 0)
            total_traffic = format_bytes(users_stats.get('total_traffic', 0))
            message += f"📊 **Статистика:**\n"
            message += f"• Всего пользователей: {users_count}\n"
            message += f"• Активных: {active_count}\n"
            message += f"• Общий трафик: {total_traffic}\n\n"
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        message += "📊 Статистика недоступна\n\n"
    
    message += "Выберите действие:"

    await callback.answer()
    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

@router.callback_query(Text("list_users"), AuthFilter())
async def list_users(callback: types.CallbackQuery, state: FSMContext):
    """List all users with pagination"""
    await callback.answer()
    
    try:
        # Get all users
        users = await sdk.get_all_users()
        
        if not users:
            await callback.message.edit_text(
                "👥 Пользователи не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
                ]])
            )
            return

        # Store users in state for pagination
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

async def show_users_page(message: types.Message, users: list, page: int, state: FSMContext, per_page: int = 10):
    """Show users page with pagination using keyboard helper"""
    try:
        # Use SelectionHelper for user pagination
        selection_helper = SelectionHelper()
        keyboard = selection_helper.create_users_selection_keyboard(
            users, page, per_page, back_callback="users"
        )
        
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
            
            message_text += f"{status_emoji} **{escape_markdown(user_name)}**\n"
            message_text += f"  💾 Трафик: {traffic_used} / {traffic_limit}\n"
            if user.get('telegram_id'):
                message_text += f"  📱 TG ID: {user.get('telegram_id')}\n"
            message_text += "\n"
        
        await message.edit_text(
            text=message_text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error showing users page: {e}")
        await message.edit_text(
            "❌ Ошибка при отображении списка пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
            ]])
        )

@router.callback_query(Text(startswith="users_page:"), AuthFilter())
async def handle_users_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Handle users pagination"""
    await callback.answer()
    
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    users = data.get('users', [])
    
    await state.update_data(page=page)
    await show_users_page(callback.message, users, page, state)

@router.callback_query(Text(startswith="select_user:"), AuthFilter())
async def handle_user_selection(callback: types.CallbackQuery, state: FSMContext):
    """Handle user selection"""
    await callback.answer()
    
    user_uuid = callback.data.split(":")[1]
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

@router.callback_query(Text(startswith="refresh_user:"), AuthFilter())
async def refresh_user(callback: types.CallbackQuery, state: FSMContext):
    """Refresh user data"""
    await callback.answer("🔄 Обновление данных...")
    
    user_uuid = callback.data.split(":")[1]
    
    try:
        user = await sdk.get_user(user_uuid)
        if user:
            await state.update_data(selected_user=user)
            await show_user_details(callback.message, user, state)
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

@router.callback_query(Text(startswith="activate_user:"), AuthFilter())
async def activate_user(callback: types.CallbackQuery, state: FSMContext):
    """Activate user"""
    await callback.answer()
    
    user_uuid = callback.data.split(":")[1]
    
    try:
        success = await sdk.update_user(user_uuid, {"is_active": True})
        if success:
            await callback.answer("✅ Пользователь активирован", show_alert=True)
            # Refresh user data
            user = await sdk.get_user(user_uuid)
            if user:
                await state.update_data(selected_user=user)
                await show_user_details(callback.message, user, state)
        else:
            await callback.answer("❌ Ошибка при активации", show_alert=True)
    except Exception as e:
        logger.error(f"Error activating user: {e}")
        await callback.answer("❌ Ошибка при активации", show_alert=True)

@router.callback_query(Text(startswith="deactivate_user:"), AuthFilter())
async def deactivate_user(callback: types.CallbackQuery, state: FSMContext):
    """Deactivate user"""
    await callback.answer()
    
    user_uuid = callback.data.split(":")[1]
    
    try:
        success = await sdk.update_user(user_uuid, {"is_active": False})
        if success:
            await callback.answer("✅ Пользователь деактивирован", show_alert=True)
            # Refresh user data
            user = await sdk.get_user(user_uuid)
            if user:
                await state.update_data(selected_user=user)
                await show_user_details(callback.message, user, state)
        else:
            await callback.answer("❌ Ошибка при деактивации", show_alert=True)
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        await callback.answer("❌ Ошибка при деактивации", show_alert=True)

@router.callback_query(Text(startswith="reset_traffic:"), AuthFilter())
async def reset_user_traffic(callback: types.CallbackQuery, state: FSMContext):
    """Reset user traffic"""
    await callback.answer()
    
    user_uuid = callback.data.split(":")[1]
    
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

@router.callback_query(Text(startswith="confirm_reset_traffic:"), AuthFilter())
async def confirm_reset_traffic(callback: types.CallbackQuery, state: FSMContext):
    """Confirm traffic reset"""
    await callback.answer()
    
    user_uuid = callback.data.split(":")[1]
    
    try:
        success = await sdk.reset_user_traffic(user_uuid)
        if success:
            await callback.answer("✅ Трафик сброшен", show_alert=True)
            # Refresh user data
            user = await sdk.get_user(user_uuid)
            if user:
                await state.update_data(selected_user=user)
                await show_user_details(callback.message, user, state)
        else:
            await callback.answer("❌ Ошибка при сбросе трафика", show_alert=True)
    except Exception as e:
        logger.error(f"Error resetting traffic: {e}")
        await callback.answer("❌ Ошибка при сбросе трафика", show_alert=True)

@router.callback_query(Text(startswith="subscription:"), AuthFilter())
async def show_subscription(callback: types.CallbackQuery, state: FSMContext):
    """Show user subscription info"""
    await callback.answer()
    
    user_uuid = callback.data.split(":")[1]
    
    try:
        subscription = await sdk.get_user_subscription(user_uuid)
        if subscription:
            subscription_text = f"🔗 **Подписка пользователя**\n\n"
            subscription_text += f"**URL:** `{subscription.get('url', 'N/A')}`\n"
            subscription_text += f"**QR-код:** Доступен\n"
            
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="📋 Копировать URL", callback_data=f"copy_subscription:{user_uuid}"))
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

@router.callback_query(Text(startswith="delete_user:"), AuthFilter())
async def delete_user_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm user deletion"""
    await callback.answer()
    
    user_uuid = callback.data.split(":")[1]
    
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

@router.callback_query(Text(startswith="confirm_delete_user:"), AuthFilter())
async def confirm_delete_user(callback: types.CallbackQuery, state: FSMContext):
    """Confirm user deletion"""
    await callback.answer()
    
    user_uuid = callback.data.split(":")[1]
    
    try:
        success = await sdk.delete_user(user_uuid)
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

@router.callback_query(Text("search_users_menu"), AuthFilter())
async def show_search_users_menu(callback: types.CallbackQuery, state: FSMContext):
    """Show search users menu"""
    await callback.answer()
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 По имени", callback_data="search_user_by_name"))
    builder.row(types.InlineKeyboardButton(text="📱 По Telegram ID", callback_data="search_user_by_telegram"))
    builder.row(types.InlineKeyboardButton(text="📝 По описанию", callback_data="search_user_by_description"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="users"))
    
    await callback.message.edit_text(
        "🔍 **Поиск пользователей**\n\n"
        "Выберите тип поиска:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(Text("search_user_by_name"), AuthFilter())
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
        all_users = await sdk.get_all_users()
        filtered_users = [
            user for user in all_users 
            if search_term.lower() in user.get('username', '').lower()
        ]
        
        if not filtered_users:
            await message.answer(
                f"❌ Пользователи с именем содержащим '{search_term}' не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="🔙 Назад", callback_data="search_users_menu")
                    ]
                ])
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
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="search_users_menu")
                ]
            ])
        )

@router.callback_query(Text("search_user_by_telegram"), AuthFilter())
async def search_user_by_telegram(callback: types.CallbackQuery, state: FSMContext):
    """Start search by Telegram ID"""
    await callback.answer()
    await state.set_state(UserStates.search_telegram_id)
    
    await callback.message.edit_text(
        "📱 **Поиск по Telegram ID**\n\n"
        "Введите Telegram ID пользователя:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="search_users_menu")
            ]
        ])
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
        all_users = await sdk.get_all_users()
        filtered_users = [
            user for user in all_users 
            if user.get('telegram_id') == telegram_id
        ]
        
        if not filtered_users:
            await message.answer(
                f"❌ Пользователь с Telegram ID {telegram_id} не найден",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="🔙 Назад", callback_data="search_users_menu")
                    ]
                ])
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
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="search_users_menu")
                ]
            ])
        )

# ================ CREATE USER FUNCTIONALITY ================

@router.callback_query(Text("create_user"), AuthFilter())
async def start_create_user(callback: types.CallbackQuery, state: FSMContext):
    """Start user creation process"""
    await callback.answer()
    await state.clear()
    await state.set_state(UserStates.enter_username)
    
    await callback.message.edit_text(
        "➕ **Создание нового пользователя**\n\n"
        "**Шаг 1/4:** Введите имя пользователя:\n\n"
        "ℹ️ Имя должно быть уникальным и содержать только латинские буквы, цифры и символы _ -",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
            ]
        ])
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
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_telegram_id"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
            ]
        ])
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
    await state.set_state(UserStates.enter_description)
    
    await message.answer(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** {telegram_id if telegram_id > 0 else 'Не указан'}\n\n"
        "**Шаг 3/4:** Введите описание пользователя:\n\n"
        "ℹ️ Краткое описание или назначение аккаунта",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
            ]
        ])
    )

@router.callback_query(Text("skip_telegram_id"), AuthFilter())
async def skip_telegram_id(callback: types.CallbackQuery, state: FSMContext):
    """Skip Telegram ID input"""
    await callback.answer()
    
    data = await state.get_data()
    username = data.get('username')
    
    await state.update_data(telegram_id=None)
    await state.set_state(UserStates.enter_description)
    
    await callback.message.edit_text(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** Не указан\n\n"
        "**Шаг 3/4:** Введите описание пользователя:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
            ]
        ])
    )

@router.message(StateFilter(UserStates.enter_description), AuthFilter())
async def handle_description_input(message: types.Message, state: FSMContext):
    """Handle description input"""
    description = message.text.strip()
    
    if len(description) > 200:
        await message.answer("❌ Описание слишком длинное (максимум 200 символов)")
        return
    
    data = await state.get_data()
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    
    await state.update_data(description=description)
    await state.set_state(UserStates.enter_traffic_limit)
    
    await message.answer(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** {telegram_id or 'Не указан'}\n"
        f"✅ **Описание:** {description}\n\n"
        "**Шаг 4/4:** Введите лимит трафика:\n\n"
        "Примеры:\n"
        "• `10GB` - 10 гигабайт\n"
        "• `500MB` - 500 мегабайт\n"
        "• `1TB` - 1 терабайт\n"
        "• `0` - без ограничений",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="∞ Без ограничений", callback_data="unlimited_traffic"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
            ]
        ])
    )

@router.callback_query(Text("skip_description"), AuthFilter())
async def skip_description(callback: types.CallbackQuery, state: FSMContext):
    """Skip description input"""
    await callback.answer()
    
    data = await state.get_data()
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    
    await state.update_data(description="")
    await state.set_state(UserStates.enter_traffic_limit)
    
    await callback.message.edit_text(
        "➕ **Создание нового пользователя**\n\n"
        f"✅ **Имя:** {username}\n"
        f"✅ **Telegram ID:** {telegram_id or 'Не указан'}\n"
        f"✅ **Описание:** Не указано\n\n"
        "**Шаг 4/4:** Введите лимит трафика:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="∞ Без ограничений", callback_data="unlimited_traffic"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="users")
            ]
        ])
    )

def parse_traffic_limit(traffic_str: str) -> int:
    """Parse traffic limit string to bytes"""
    traffic_str = traffic_str.upper().strip()
    
    if traffic_str == "0":
        return 0
        
    # Extract number and unit
    import re
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
    
    # Show confirmation
    await show_create_user_confirmation(message, state, data)

@router.callback_query(Text("unlimited_traffic"), AuthFilter())
async def set_unlimited_traffic(callback: types.CallbackQuery, state: FSMContext):
    """Set unlimited traffic"""
    await callback.answer()
    
    data = await state.get_data()
    await state.update_data(traffic_limit=0)
    
    # Show confirmation
    await show_create_user_confirmation(callback.message, state, data)

async def show_create_user_confirmation(message: types.Message, state: FSMContext, data: dict):
    """Show user creation confirmation"""
    username = data.get('username')
    telegram_id = data.get('telegram_id')
    description = data.get('description', '')
    traffic_limit = data.get('traffic_limit', 0)
    
    traffic_text = format_bytes(traffic_limit) if traffic_limit > 0 else "Без ограничений"
    
    confirmation_text = (
        "➕ **Создание пользователя - Подтверждение**\n\n"
        f"**Имя:** {username}\n"
        f"**Telegram ID:** {telegram_id or 'Не указан'}\n"
        f"**Описание:** {description or 'Не указано'}\n"
        f"**Лимит трафика:** {traffic_text}\n\n"
        "Создать пользователя с указанными параметрами?"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Создать", callback_data="confirm_create_user"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="users"))
    
    await message.edit_text(
        confirmation_text,
        reply_markup=builder.as_markup()
    )

@router.callback_query(Text("confirm_create_user"), AuthFilter())
async def confirm_create_user(callback: types.CallbackQuery, state: FSMContext):
    """Confirm user creation"""
    await callback.answer()
    
    data = await state.get_data()
    
    try:
        user_data = {
            "username": data.get('username'),
            "telegram_id": data.get('telegram_id'),
            "description": data.get('description', ''),
            "traffic_limit": data.get('traffic_limit', 0),
            "is_active": True
        }
        
        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        success = await sdk.create_user(user_data)
        
        if success:
            await callback.answer("✅ Пользователь создан", show_alert=True)
            await state.clear()
            await callback.message.edit_text(
                f"✅ **Пользователь создан успешно!**\n\n"
                f"Имя: **{user_data['username']}**\n"
                f"Статус: Активен\n\n"
                f"Пользователь готов к использованию.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="👥 К списку пользователей", callback_data="list_users"),
                        types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
                    ]
                ])
            )
        else:
            await callback.answer("❌ Ошибка при создании", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await callback.answer("❌ Ошибка при создании пользователя", show_alert=True)

# ================ STATISTICS ================

@router.callback_query(Text("users_stats"), AuthFilter())
async def show_users_statistics(callback: types.CallbackQuery):
    """Show users statistics"""
    await callback.answer()
    
    try:
        stats = await sdk.get_users_stats()
        
        if stats:
            stats_text = "📊 **Статистика пользователей**\n\n"
            stats_text += f"👥 **Общее количество:** {stats.get('total', 0)}\n"
            stats_text += f"🟢 **Активных:** {stats.get('active', 0)}\n"
            stats_text += f"🔴 **Неактивных:** {stats.get('inactive', 0)}\n"
            stats_text += f"📊 **Общий трафик:** {format_bytes(stats.get('total_traffic', 0))}\n"
            stats_text += f"⬇️ **Использовано:** {format_bytes(stats.get('used_traffic', 0))}\n"
            stats_text += f"⬆️ **Доступно:** {format_bytes(stats.get('available_traffic', 0))}\n"
        else:
            stats_text = "📊 **Статистика недоступна**"
            
        await callback.message.edit_text(
            stats_text,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="🔄 Обновить", callback_data="users_stats"),
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
                ]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="users")
                ]
            ])
        )
