from datetime import datetime, timedelta
import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import re

from modules.config import (
    MAIN_MENU, USER_MENU, SELECTING_USER, WAITING_FOR_INPUT, CONFIRM_ACTION,
    EDIT_USER, EDIT_FIELD, EDIT_VALUE, CREATE_USER, CREATE_USER_FIELD, USER_FIELDS
)
from modules.api.users import UserAPI
from modules.utils.formatters import format_bytes, format_user_details, format_user_details_safe, escape_markdown, safe_edit_message
from modules.utils.selection_helpers import SelectionHelper
from modules.utils.auth import check_admin, check_authorization
from modules.handlers.start_handler import show_main_menu

logger = logging.getLogger(__name__)

async def show_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show users menu"""
    keyboard = [
        [InlineKeyboardButton("📋 Список всех пользователей", callback_data="list_users")],
        [InlineKeyboardButton("🔍 Поиск по имени (частичный)", callback_data="search_user")],
        [InlineKeyboardButton("🔍 Поиск по Telegram ID", callback_data="search_user_telegram")],
        [InlineKeyboardButton("🔍 Поиск по описанию", callback_data="search_user_description")],
        [InlineKeyboardButton("➕ Создать пользователя", callback_data="create_user")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "👥 *Управление пользователями*\n\n"
    message += "🔍 *Доступные варианты поиска:*\n"
    message += "• По имени - поиск части имени пользователя\n"
    message += "• По Telegram ID - точный поиск по ID\n"
    message += "• По описанию - поиск в описании пользователя\n\n"
    message += "Выберите действие:"

    await safe_edit_message(
        update.callback_query,
        message,
        reply_markup,
        "Markdown"
    )

async def handle_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle users menu selection"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "list_users":
        await list_users(update, context)
        return SELECTING_USER

    elif data == "search_user":
        await safe_edit_message(
            query,
            "🔍 Введите часть имени пользователя для поиска:\n\n"
            "💡 *Подсказка:* Можно вводить любую часть имени, "
            "будут найдены все пользователи, содержащие указанный текст.",
            parse_mode="Markdown"
        )
        context.user_data["search_type"] = "username"
        return WAITING_FOR_INPUT

    elif data == "search_user_uuid":
        await safe_edit_message(
            query,
            "🔍 Введите UUID пользователя для поиска:",
            parse_mode="Markdown"
        )
        context.user_data["search_type"] = "uuid"
        return WAITING_FOR_INPUT
        
    elif data == "search_user_telegram":
        await safe_edit_message(
            query,
            "🔍 Введите Telegram ID пользователя для поиска:",
            parse_mode="Markdown"
        )
        context.user_data["search_type"] = "telegram_id"
        return WAITING_FOR_INPUT
        
    elif data == "search_user_description":
        await safe_edit_message(
            query,
            "🔍 Введите ключевое слово для поиска в описании пользователей:",
            parse_mode="Markdown"
        )
        context.user_data["search_type"] = "description"
        return WAITING_FOR_INPUT
        
    elif data == "search_user_email":
        await query.edit_message_text(
            "🔍 Введите Email пользователя для поиска:",
            parse_mode="Markdown"
        )
        context.user_data["search_type"] = "email"
        return WAITING_FOR_INPUT
        
    elif data == "search_user_tag":
        await query.edit_message_text(
            "🔍 Введите тег пользователя для поиска:",
            parse_mode="Markdown"
        )
        context.user_data["search_type"] = "tag"
        return WAITING_FOR_INPUT
    
    elif data == "create_user" or data == "menu_create_user":
        await start_create_user(update, context)
        return CREATE_USER_FIELD

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU

    return USER_MENU

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users with improved selection interface"""
    await update.callback_query.edit_message_text("📋 Загрузка списка пользователей...")

    try:
        # Use SelectionHelper for user-friendly interface
        keyboard, users_data = await SelectionHelper.get_users_selection_keyboard(
            callback_prefix="select_user",
            include_back=True,
            max_per_row=1
        )
        
        if not users_data:
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Пользователи не найдены.",
                reply_markup=reply_markup
            )
            return USER_MENU

        # Store users data for later use
        context.user_data["users_data"] = users_data
        
        message = f"👥 *Список пользователей* ({len(users_data)} шт.)\n\n"
        message += "Выберите пользователя для просмотра подробной информации:"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error in list_users: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке списка пользователей: {str(e)}",
            reply_markup=reply_markup
        )
        return USER_MENU

    if not users or not users.get("users"):
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Пользователи не найдены или ошибка при получении списка.",
            reply_markup=reply_markup
        )
        return USER_MENU

    # Create a paginated list of users
    users_per_page = 5
    context.user_data["users"] = users["users"]
    context.user_data["current_page"] = 0
    context.user_data["users_per_page"] = users_per_page

    await send_users_page(update, context)
    return SELECTING_USER

async def send_users_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a page of users"""
    users = context.user_data["users"]
    current_page = context.user_data["current_page"]
    users_per_page = context.user_data["users_per_page"]

    start_idx = current_page * users_per_page
    end_idx = min(start_idx + users_per_page, len(users))

    message = f"👥 *Пользователи* (Страница {current_page + 1}/{(len(users) + users_per_page - 1) // users_per_page}):\n\n"

    for i in range(start_idx, end_idx):
        user = users[i]
        status_emoji = "✅" if user["status"] == "ACTIVE" else "❌"
        
        # Format expiration date
        try:
            expire_date = datetime.fromisoformat(user['expireAt'].replace('Z', '+00:00'))
            days_left = (expire_date - datetime.now().astimezone()).days
            expire_status = "🟢" if days_left > 7 else "🟡" if days_left > 0 else "🔴"
            expire_text = f"{user['expireAt'][:10]} ({days_left} дней)"
        except Exception:
            expire_status = "📅"
            expire_text = user['expireAt'][:10]
        
        message += f"{i+1}. {status_emoji} *{escape_markdown(user['username'])}*\n"
        message += f"   🔑 ID: `{user['shortUuid']}`\n"
        message += f"   📈 Трафик: {format_bytes(user['usedTrafficBytes'])}/{format_bytes(user['trafficLimitBytes'])}\n"
        message += f"   {expire_status} Истекает: {expire_text}\n\n"

    # Create navigation buttons
    keyboard = []
    nav_row = []

    if current_page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data="prev_page"))

    if end_idx < len(users):
        nav_row.append(InlineKeyboardButton("Вперед ▶️", callback_data="next_page"))

    if nav_row:
        keyboard.append(nav_row)

    # Add action buttons for each user
    for i in range(start_idx, end_idx):
        user = users[i]
        user_row = [
            InlineKeyboardButton(f"👤 {user['username']}", callback_data=f"view_{user['uuid']}")
        ]
        keyboard.append(user_row)

    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user selection with improved UI"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()

    data = query.data

    # Handle new SelectionHelper callbacks
    if data.startswith("select_user_"):
        user_uuid = data.split("_", 2)[2]
        await show_user_details(update, context, user_uuid)
        return SELECTING_USER

    # Handle back button from SelectionHelper
    elif data == "back":
        await show_users_menu(update, context)
        return USER_MENU

    # Handle pagination from SelectionHelper
    elif data.startswith("users_page_"):
        page = int(data.split("_")[2])
        try:
            keyboard, users_data = await SelectionHelper.get_users_selection_keyboard(
                callback_prefix="select_user",
                include_back=True,
                max_per_row=1,
                page=page
            )
            
            context.user_data["users_data"] = users_data
            
            message = f"👥 *Список пользователей* ({len(users_data)} шт.) - страница {page + 1}\n\n"
            message += "Выберите пользователя для просмотра подробной информации:"

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in pagination: {e}")
            await show_users_menu(update, context)
            return USER_MENU

    # Legacy support for old callback patterns
    elif data == "prev_page":
        context.user_data["current_page"] -= 1
        await send_users_page(update, context)

    elif data == "next_page":
        context.user_data["current_page"] += 1
        await send_users_page(update, context)

    elif data == "back_to_users":
        await show_users_menu(update, context)
        return USER_MENU

    elif data == "back_to_list":
        await list_users(update, context)
        return SELECTING_USER

    elif data.startswith("view_"):
        uuid = data.split("_")[1]
        await show_user_details(update, context, uuid)
        
    elif data.startswith("add_hwid_"):
        uuid = data.split("_")[2]
        await start_add_hwid(update, context, uuid)
        return WAITING_FOR_INPUT
        
    elif data.startswith("del_hwid_"):
        parts = data.split("_")
        uuid = parts[2]
        hwid = parts[3]
        await delete_hwid_device(update, context, uuid, hwid)

    return SELECTING_USER

async def show_user_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show user details"""
    user = await UserAPI.get_user_by_uuid(uuid)
    if not user:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Пользователь не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return USER_MENU

    try:
        message = format_user_details(user)
    except Exception as e:
        logger.error(f"Error formatting user details: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при форматировании данных пользователя: {str(e)}",
            reply_markup=reply_markup
        )
        return USER_MENU

    # Create action buttons using SelectionHelper for better UX
    keyboard = SelectionHelper.create_user_info_keyboard(uuid, action_prefix="user_action")

    # Сначала пробуем отправить с Markdown форматированием
    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "can't parse entities" in error_msg or "markdown" in error_msg:
            logger.error(f"Markdown parsing error: {e}")
            logger.error("Failed to send user details with Markdown, trying safe formatting")
            
            # Используем безопасное форматирование без Markdown
            try:
                safe_message = format_user_details_safe(user)
                await update.callback_query.edit_message_text(
                    text=safe_message,
                    reply_markup=keyboard
                )
            except Exception as e2:
                logger.error(f"Error with safe formatting: {e2}")
                # Последний fallback - минимальное сообщение
                fallback_message = f"👤 Пользователь: {user['username']}\n🆔 UUID: {user['uuid']}\n📊 Статус: {user['status']}"
                
                try:
                    await update.callback_query.edit_message_text(
                        text=fallback_message,
                        reply_markup=keyboard
                    )
                except Exception as e3:
                    logger.error(f"Critical error in user details display: {e3}")
                    await update.callback_query.answer("❌ Ошибка при отображении данных")
        else:
            # Другая ошибка (не связанная с парсингом)
            logger.error(f"Non-parsing error in show_user_details: {e}")
            await update.callback_query.answer("❌ Ошибка при обновлении сообщения")

    context.user_data["current_user"] = user
    return SELECTING_USER

async def handle_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user action with improved SelectionHelper support"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()

    data = query.data

    # Handle new SelectionHelper callback patterns
    if data.startswith("user_action_"):
        action_parts = data.split("_")
        if len(action_parts) >= 4:
            action = action_parts[2]
            uuid = "_".join(action_parts[3:])  # Handle UUIDs with underscores
            
            if action == "edit":
                return await start_edit_user(update, context, uuid)
            elif action == "refresh":
                await show_user_details(update, context, uuid)
                return SELECTING_USER
            elif action == "disable":
                context.user_data["action"] = "disable"
                context.user_data["uuid"] = uuid
                
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Да, отключить", callback_data="confirm_action"),
                        InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"⚠️ Вы уверены, что хотите отключить пользователя?\n\nUUID: `{uuid}`",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return CONFIRM_ACTION
            elif action == "enable":
                context.user_data["action"] = "enable"
                context.user_data["uuid"] = uuid
                
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Да, включить", callback_data="confirm_action"),
                        InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"⚠️ Вы уверены, что хотите включить пользователя?\n\nUUID: `{uuid}`",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return CONFIRM_ACTION
            elif action == "reset" and len(action_parts) >= 5 and action_parts[3] == "traffic":
                context.user_data["action"] = "reset"
                context.user_data["uuid"] = "_".join(action_parts[4:])
                
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Да, сбросить", callback_data="confirm_action"),
                        InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"⚠️ Вы уверены, что хотите сбросить трафик пользователя?\n\nUUID: `{uuid}`",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return CONFIRM_ACTION
            elif action == "revoke":
                context.user_data["action"] = "revoke"
                context.user_data["uuid"] = uuid
                
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Да, отозвать", callback_data="confirm_action"),
                        InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"⚠️ Вы уверены, что хотите отозвать подписку пользователя?\n\nUUID: `{uuid}`",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return CONFIRM_ACTION
            elif action == "delete":
                # Confirm user deletion with extra protection
                await confirm_delete_user(update, context, uuid)
                return CONFIRM_ACTION

    # Legacy support for back navigation
    if data == "back_to_list":
        await list_users(update, context)
        return SELECTING_USER

    elif data == "back_to_users":
        await show_users_menu(update, context)
        return USER_MENU

    elif data.startswith("disable_"):
        uuid = data.split("_")[1]
        context.user_data["action"] = "disable"
        context.user_data["uuid"] = uuid
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, отключить", callback_data="confirm_action"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ Вы уверены, что хотите отключить пользователя?\n\nUUID: `{uuid}`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return CONFIRM_ACTION

    elif data.startswith("enable_"):
        uuid = data.split("_")[1]
        context.user_data["action"] = "enable"
        context.user_data["uuid"] = uuid
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, включить", callback_data="confirm_action"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ Вы уверены, что хотите включить пользователя?\n\nUUID: `{uuid}`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return CONFIRM_ACTION

    elif data.startswith("reset_"):
        uuid = data.split("_")[1]
        context.user_data["action"] = "reset"
        context.user_data["uuid"] = uuid
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, сбросить", callback_data="confirm_action"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ Вы уверены, что хотите сбросить трафик пользователя?\n\nUUID: `{uuid}`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return CONFIRM_ACTION

    elif data.startswith("revoke_"):
        uuid = data.split("_")[1]
        context.user_data["action"] = "revoke"
        context.user_data["uuid"] = uuid
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, отозвать", callback_data="confirm_action"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ Вы уверены, что хотите отозвать подписку пользователя?\n\nUUID: `{uuid}`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return CONFIRM_ACTION

    elif data.startswith("edit_"):
        uuid = data.split("_")[1]
        return await start_edit_user(update, context, uuid)
        
    elif data.startswith("hwid_"):
        uuid = data.split("_")[1]
        return await show_user_hwid_devices(update, context, uuid)
        
    elif data.startswith("stats_"):
        uuid = data.split("_")[1]
        return await show_user_stats(update, context, uuid)
        
    elif data.startswith("confirm_del_hwid_"):
        parts = data.split("_")
        uuid = parts[3]
        hwid = parts[4]
        return await confirm_delete_hwid_device(update, context, uuid, hwid)

    return SELECTING_USER

async def handle_action_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle action confirmation"""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Handle final delete confirmation
    if data == "final_delete_user":
        return await execute_user_deletion(update, context)

    if data == "confirm_action":
        action = context.user_data.get("action")
        uuid = context.user_data.get("uuid")
        
        if not action or not uuid:
            await query.edit_message_text("❌ Ошибка: действие или UUID не найдены.")
            return SELECTING_USER
        
        result = None
        action_text = ""
        
        if action == "disable":
            result = await UserAPI.disable_user(uuid)
            action_text = "отключен"
        elif action == "enable":
            result = await UserAPI.enable_user(uuid)
            action_text = "включен"
        elif action == "reset":
            result = await UserAPI.reset_user_traffic(uuid)
            action_text = "сброшен трафик"
        elif action == "revoke":
            result = await UserAPI.revoke_user_subscription(uuid)
            action_text = "отозвана подписка"
        
        if result:
            keyboard = [
                [InlineKeyboardButton("👁️ Просмотр пользователя", callback_data=f"view_{uuid}")],
                [InlineKeyboardButton("🔙 Назад к списку", callback_data="back_to_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ Пользователь успешно {action_text}.\n\nUUID: `{uuid}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data=f"view_{uuid}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ Не удалось выполнить действие: {action}.\n\nUUID: `{uuid}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    else:
        uuid = context.user_data.get("uuid")
        if uuid:
            await show_user_details(update, context, uuid)
        else:
            await show_users_menu(update, context)
            return USER_MENU

    return SELECTING_USER

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input"""
    # Check if we're waiting for HWID input
    if context.user_data.get("waiting_for") == "hwid":
        return await handle_hwid_input(update, context)
    
    # Check if we're waiting for delete confirmation
    if context.user_data.get("waiting_for") == "delete_confirmation":
        return await handle_delete_confirmation(update, context)

    # Check if we're searching for a user
    search_type = context.user_data.get("search_type")

    if not search_type:
        # Check if we're in user creation mode
        if "create_user_fields" in context.user_data and "current_field_index" in context.user_data:
            return await handle_create_user_input(update, context)
    
        # If we're not in any special mode, show an error
        await update.message.reply_text("❌ Ошибка: тип поиска не найден.")
        await show_users_menu(update, context)
        return USER_MENU

    search_value = update.message.text.strip()

    if search_type == "username":
        # Изменяем на поиск по частичному совпадению
        users = await UserAPI.search_users_by_partial_name(search_value)
        if users:
            if len(users) > 1:
                message = f"🔍 Найдено {len(users)} пользователей с именем, содержащим '{search_value}':\n\n"
                keyboard = []
                
                for i, user in enumerate(users):
                    message += f"{i+1}. {user['username']} - {user['status']}\n"
                    keyboard.append([InlineKeyboardButton(f"👤 {user['username']}", callback_data=f"view_{user['uuid']}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    await update.message.reply_text(
                        text=message,
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logger.error(f"Error sending username search results: {e}")
                    # Fallback без форматирования
                    await update.message.reply_text(
                        text=f"Найдено {len(users)} пользователей. Используйте кнопки для выбора:",
                        reply_markup=reply_markup
                    )
                return SELECTING_USER
            else:
                # Single user found
                user = users[0]
                try:
                    message = format_user_details(user)
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("🔄 Сбросить трафик", callback_data=f"reset_{user['uuid']}"),
                            InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_{user['uuid']}")
                        ]
                    ]
                    
                    if user["status"] == "ACTIVE":
                        keyboard.append([
                            InlineKeyboardButton("🔴 Отключить", callback_data=f"disable_{user['uuid']}"),
                            InlineKeyboardButton("🔄 Отозвать подписку", callback_data=f"revoke_{user['uuid']}")
                        ])
                    else:
                        keyboard.append([
                            InlineKeyboardButton("🟢 Включить", callback_data=f"enable_{user['uuid']}"),
                            InlineKeyboardButton("🔄 Отозвать подписку", callback_data=f"revoke_{user['uuid']}")
                        ])
                    
                    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Попытка отправить с Markdown
                    try:
                        await update.message.reply_text(
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Error sending formatted message with Markdown: {e}")
                        # Fallback без Markdown
                        await update.message.reply_text(
                            text=message,
                            reply_markup=reply_markup
                        )
                    
                    context.user_data["current_user"] = user
                    return SELECTING_USER
                except Exception as e:
                    logger.error(f"Error formatting user details in username search: {e}")
                    # Fallback сообщение
                    keyboard = [[InlineKeyboardButton(f"👤 {user['username']}", callback_data=f"view_{user['uuid']}")]]
                    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        text=f"Найден пользователь: {user['username']}",
                        reply_markup=reply_markup
                    )
                    return SELECTING_USER
        else:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Пользователи с именем, содержащим '{search_value}', не найдены.",
                reply_markup=reply_markup
            )
            return USER_MENU


            
    elif search_type == "telegram_id":
        users = await UserAPI.get_user_by_telegram_id(search_value)
        if users:
            # Handle multiple users with the same Telegram ID
            if len(users) > 1:
                message = f"🔍 Найдено {len(users)} пользователей с Telegram ID {search_value}:\n\n"
                keyboard = []
                
                for i, user in enumerate(users):
                    message += f"{i+1}. {user['username']} - {user['status']}\n"
                    keyboard.append([InlineKeyboardButton(f"👤 {user['username']}", callback_data=f"view_{user['uuid']}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    await update.message.reply_text(
                        text=message,
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logger.error(f"Error sending telegram_id search results: {e}")
                    # Fallback без форматирования
                    await update.message.reply_text(
                        text=f"Найдено {len(users)} пользователей. Используйте кнопки для выбора:",
                        reply_markup=reply_markup
                    )
                return SELECTING_USER
            else:
                # Single user found
                user = users[0]
                try:
                    message = format_user_details(user)
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("🔄 Сбросить трафик", callback_data=f"reset_{user['uuid']}"),
                            InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_{user['uuid']}")
                        ]
                    ]
                    
                    if user["status"] == "ACTIVE":
                        keyboard.append([
                            InlineKeyboardButton("🔴 Отключить", callback_data=f"disable_{user['uuid']}"),
                            InlineKeyboardButton("🔄 Отозвать подписку", callback_data=f"revoke_{user['uuid']}")
                        ])
                    else:
                        keyboard.append([
                            InlineKeyboardButton("🟢 Включить", callback_data=f"enable_{user['uuid']}"),
                            InlineKeyboardButton("🔄 Отозвать подписку", callback_data=f"revoke_{user['uuid']}")
                        ])
                    
                    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Попытка отправить с Markdown
                    try:
                        await update.message.reply_text(
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Error sending formatted message with Markdown: {e}")
                        # Fallback без Markdown
                        await update.message.reply_text(
                            text=message,
                            reply_markup=reply_markup
                        )
                    
                    context.user_data["current_user"] = user
                    return SELECTING_USER
                except Exception as e:
                    logger.error(f"Error formatting user details in telegram_id search: {e}")
                    # Fallback сообщение
                    keyboard = [[InlineKeyboardButton(f"👤 {user['username']}", callback_data=f"view_{user['uuid']}")]]
                    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        text=f"Найден пользователь: {user['username']}",
                        reply_markup=reply_markup
                    )
                    return SELECTING_USER
                
                context.user_data["current_user"] = user
                return SELECTING_USER
        else:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Пользователь с Telegram ID '{search_value}' не найден.",
                reply_markup=reply_markup
            )
            return USER_MENU
            
    elif search_type == "description":
        try:
            users = await UserAPI.search_users_by_description(search_value)
            if users:
                # Handle multiple users with matching descriptions
                if len(users) > 1:
                    message = f"🔍 Найдено {len(users)} пользователей с описанием, содержащим '{search_value}':\n\n"
                    keyboard = []
                    
                    for i, user in enumerate(users):
                        description_preview = user.get('description', '')[:30] + "..." if len(user.get('description', '')) > 30 else user.get('description', '')
                        # Избегаем использования escape_markdown в списке результатов
                        message += f"{i+1}. {user['username']} - {user['status']}\n"
                        message += f"   📝 {description_preview}\n\n"
                        keyboard.append([InlineKeyboardButton(f"👤 {user['username']}", callback_data=f"view_{user['uuid']}")])
                    
                    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    try:
                        await update.message.reply_text(
                            text=message,
                            reply_markup=reply_markup
                        )
                    except Exception as e:
                        logger.error(f"Error sending description search results: {e}")
                        # Fallback без форматирования
                        await update.message.reply_text(
                            text=f"Найдено {len(users)} пользователей. Используйте кнопки для выбора:",
                            reply_markup=reply_markup
                        )
                    return SELECTING_USER
                else:
                    # Single user found
                    user = users[0]
                    try:
                        message = format_user_details(user)
                        
                        keyboard = [
                            [
                                InlineKeyboardButton("🔄 Сбросить трафик", callback_data=f"reset_{user['uuid']}"),
                                InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_{user['uuid']}")
                            ]
                        ]
                        
                        if user["status"] == "ACTIVE":
                            keyboard.append([
                                InlineKeyboardButton("🔴 Отключить", callback_data=f"disable_{user['uuid']}"),
                                InlineKeyboardButton("🔄 Отозвать подписку", callback_data=f"revoke_{user['uuid']}")
                            ])
                        else:
                            keyboard.append([
                                InlineKeyboardButton("🟢 Включить", callback_data=f"enable_{user['uuid']}"),
                                InlineKeyboardButton("🔄 Отозвать подписку", callback_data=f"revoke_{user['uuid']}")
                            ])
                        
                        keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await update.message.reply_text(
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode="Markdown"
                        )
                        
                        context.user_data["current_user"] = user
                        return SELECTING_USER
                    except Exception as e:
                        logger.error(f"Error formatting user details in description search: {e}")
                        # Fallback сообщение
                        keyboard = [[InlineKeyboardButton(f"👤 {user['username']}", callback_data=f"view_{user['uuid']}")]]
                        keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await update.message.reply_text(
                            text=f"Найден пользователь: {user['username']}",
                            reply_markup=reply_markup
                        )
                        return SELECTING_USER
            else:
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"❌ Пользователи с описанием, содержащим '{search_value}', не найдены.",
                    reply_markup=reply_markup
                )
                return USER_MENU
        except Exception as e:
            logger.error(f"Error in description search: {e}")
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Произошла ошибка при поиске по описанию.",
                reply_markup=reply_markup
            )
            return USER_MENU

    # If we reach here, unknown search type
    await update.message.reply_text("❌ Неизвестный тип поиска.")
    await show_users_menu(update, context)
    return USER_MENU


async def start_edit_user(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Start editing a user"""
    user = await UserAPI.get_user_by_uuid(uuid)
    if not user:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Пользователь не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return USER_MENU

    context.user_data["edit_user"] = user

    keyboard = [
        [InlineKeyboardButton("📅 Дата истечения", callback_data="edit_expireAt")],
        [InlineKeyboardButton("📈 Лимит трафика", callback_data="edit_trafficLimitBytes")],
        [InlineKeyboardButton("🔄 Стратегия сброса трафика", callback_data="edit_trafficLimitStrategy")],
        [InlineKeyboardButton("📝 Описание", callback_data="edit_description")],
        [InlineKeyboardButton("📱 Telegram ID", callback_data="edit_telegramId")],
        [InlineKeyboardButton("📧 Email", callback_data="edit_email")],
        [InlineKeyboardButton("🏷️ Тег", callback_data="edit_tag")],
        [InlineKeyboardButton("📱 Лимит устройств", callback_data="edit_hwidDeviceLimit")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"view_{uuid}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Форматируем дату истечения
    expire_date = "Не указана"
    if user.get('expireAt'):
        try:
            expire_date = user['expireAt'][:10]  # Берём только YYYY-MM-DD часть
        except Exception:
            expire_date = str(user['expireAt'])

    # Форматируем лимит трафика 
    traffic_limit = format_bytes(user.get('trafficLimitBytes', 0))
    
    # Получаем стратегию сброса трафика
    traffic_strategy = user.get('trafficLimitStrategy', 'Не указана')
    
    # Форматируем другие поля
    description = user.get('description', 'Не указано')
    telegram_id = user.get('telegramId', 'Не указан')
    email = user.get('email', 'Не указан')
    tag = user.get('tag', 'Не указан')
    hwid_limit = str(user.get('hwidDeviceLimit', 'Не указан'))
    
    message = f"📝 *Редактирование пользователя*\n\n"
    message += f"👤 Имя: {escape_markdown(user['username'])}\n"
    message += f"🆔 UUID: `{user['uuid']}`\n\n"
    message += f"*Текущие значения:*\n"
    message += f"📅 Дата истечения: {escape_markdown(expire_date)}\n"
    message += f"📈 Лимит трафика: {traffic_limit}\n"
    message += f"🔄 Стратегия сброса: {escape_markdown(str(traffic_strategy))}\n"
    message += f"📝 Описание: {escape_markdown(str(description))}\n"
    message += f"📱 Telegram ID: {escape_markdown(str(telegram_id))}\n"
    message += f"📧 Email: {escape_markdown(str(email))}\n"
    message += f"🏷️ Тег: {escape_markdown(str(tag))}\n"
    message += f"📱 Лимит устройств: {escape_markdown(str(hwid_limit))}\n\n"
    message += "Выберите поле для редактирования:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return EDIT_USER

async def handle_edit_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit field selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("edit_"):
        field = data.split("_")[1]
        context.user_data["edit_field"] = field
        
        user = context.user_data["edit_user"]
        current_value = user.get(field, "")
        
        if field == "expireAt":
            current_value = current_value[:10] if current_value else "Не указана"
            message = f"📅 *Изменение даты истечения*\n\n"
            message += f"Текущее значение: `{current_value}`\n\n"
            message += f"Введите новую дату истечения в формате YYYY-MM-DD:"
        
        elif field == "trafficLimitBytes":
            current_value = format_bytes(current_value)
            message = f"📈 *Изменение лимита трафика*\n\n"
            message += f"Текущее значение: `{current_value}`\n\n"
            message += f"Введите новый лимит трафика в байтах (0 для безлимитного):"
        
        elif field == "trafficLimitStrategy":
            strategy_names = {
                "NO_RESET": "Без сброса",
                "DAY": "Ежедневно",
                "WEEK": "Еженедельно",
                "MONTH": "Ежемесячно"
            }
            readable_value = strategy_names.get(current_value, current_value) if current_value else "Не указана"
            message = f"🔄 *Изменение стратегии сброса трафика*\n\n"
            message += f"Текущее значение: `{current_value}` ({readable_value})\n\n"
            message += f"Выберите новую стратегию сброса трафика:"
            
            keyboard = [
                [InlineKeyboardButton("NO_RESET - Без сброса", callback_data="set_NO_RESET")],
                [InlineKeyboardButton("DAY - Ежедневно", callback_data="set_DAY")],
                [InlineKeyboardButton("WEEK - Еженедельно", callback_data="set_WEEK")],
                [InlineKeyboardButton("MONTH - Ежемесячно", callback_data="set_MONTH")],
                [InlineKeyboardButton("🔙 Назад", callback_data=f"edit_{user['uuid']}")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return EDIT_FIELD
        
        elif field == "description":
            message = f"📝 *Изменение описания*\n\n"
            message += f"Текущее значение: `{escape_markdown(current_value) if current_value else 'Не указано'}`\n\n"
            message += f"Введите новое описание:"
        
        elif field == "telegramId":
            message = f"📱 *Изменение Telegram ID*\n\n"
            message += f"Текущее значение: `{current_value if current_value else 'Не указан'}`\n\n"
            message += f"Введите новый Telegram ID:"
        
        elif field == "email":
            message = f"📧 *Изменение Email*\n\n"
            message += f"Текущее значение: `{escape_markdown(current_value) if current_value else 'Не указан'}`\n\n"
            message += f"Введите новый Email:"
            
        elif field == "tag":
            message = f"🏷️ *Изменение тега*\n\n"
            message += f"Текущее значение: `{escape_markdown(current_value) if current_value else 'Не указан'}`\n\n"
            message += f"Введите новый тег (только ЗАГЛАВНЫЕ буквы, цифры и подчеркивания):"
            
        elif field == "hwidDeviceLimit":
            message = f"📱 *Изменение лимита устройств*\n\n"
            message += f"Текущее значение: `{current_value if current_value else 'Не указано'}`\n\n" 
            message += f"Введите новый лимит устройств (0 для отключения):"
        
        else:
            message = f"*Изменение {field}*\n\n"
            message += f"Текущее значение: `{escape_markdown(str(current_value)) if current_value else 'Не указано'}`\n\n"
            message += f"Введите новое значение:"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"edit_{user['uuid']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_VALUE

    elif data.startswith("view_"):
        uuid = data.split("_")[1]
        await show_user_details(update, context, uuid)
        return SELECTING_USER

    return EDIT_USER

async def handle_edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit field value"""
    query = update.callback_query

    if query:
        await query.answer()
        data = query.data
        
        if data.startswith("set_"):
            value = data.split("_")[1]
            field = context.user_data["edit_field"]
            user = context.user_data["edit_user"]
            
            # Update the user with the new value
            update_data = {field: value}
            result = await UserAPI.update_user(user["uuid"], update_data)
            
            if result:
                keyboard = [
                    [InlineKeyboardButton("👁️ Просмотр пользователя", callback_data=f"view_{user['uuid']}")],
                    [InlineKeyboardButton("📝 Продолжить редактирование", callback_data=f"edit_{user['uuid']}")],
                    [InlineKeyboardButton("🔙 Назад к списку", callback_data="back_to_list")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ Поле {field} успешно обновлено на {value}.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"edit_{user['uuid']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"❌ Не удалось обновить поле {field}.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            
            return EDIT_USER
        
        elif data.startswith("edit_"):
            uuid = data.split("_")[1]
            return await start_edit_user(update, context, uuid)

    else:  # Text input
        field = context.user_data["edit_field"]
        user = context.user_data["edit_user"]
        value = update.message.text.strip()
        
        # Process the value based on the field
        if field == "expireAt":
            try:
                # Validate date format
                date_obj = datetime.strptime(value, "%Y-%m-%d")
                value = date_obj.strftime("%Y-%m-%dT00:00:00.000Z")
            except ValueError:
                keyboard = [
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"edit_{user['uuid']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ Неверный формат даты. Используйте YYYY-MM-DD.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return EDIT_USER
        
        elif field == "trafficLimitBytes":
            try:
                value = int(value)
                if value < 0:
                    raise ValueError("Traffic limit cannot be negative")
            except ValueError:
                keyboard = [
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"edit_{user['uuid']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ Неверный формат числа. Введите целое число >= 0.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return EDIT_USER
        
        elif field == "telegramId":
            try:
                value = int(value)
            except ValueError:
                keyboard = [
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"edit_{user['uuid']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ Неверный формат Telegram ID. Введите целое число.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return EDIT_USER
                
        elif field == "hwidDeviceLimit":
            try:
                value = int(value)
                if value < 0:
                    raise ValueError("Device limit cannot be negative")
                
                # Если устанавливается лимит устройств > 0, добавляем в обновляемые данные trafficLimitStrategy=NO_RESET
                if value > 0:
                    update_data["trafficLimitStrategy"] = "NO_RESET"
                    logger.info(f"Auto-setting trafficLimitStrategy=NO_RESET when setting hwidDeviceLimit to {value} for user {user['uuid']}")
            except ValueError:
                keyboard = [
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"edit_{user['uuid']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ Неверный формат числа. Введите целое число >= 0.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return EDIT_USER
        
        # Update the user with the new value
        update_data = {field: value}
        result = await UserAPI.update_user(user["uuid"], update_data)
        
        if result:
            keyboard = [
                [InlineKeyboardButton("👁️ Просмотр пользователя", callback_data=f"view_{user['uuid']}")],
                [InlineKeyboardButton("📝 Продолжить редактирование", callback_data=f"edit_{user['uuid']}")],
                [InlineKeyboardButton("🔙 Назад к списку", callback_data="back_to_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Поле {field} успешно обновлено.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data=f"edit_{user['uuid']}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Не удалось обновить поле {field}.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return EDIT_USER

async def start_create_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start creating a new user - first show template selection"""
    # Clear any previous user creation data
    context.user_data.pop("create_user", None)
    context.user_data.pop("create_user_fields", None)
    context.user_data.pop("current_field_index", None)
    context.user_data.pop("search_type", None)  # Clear search type to avoid confusion
    context.user_data.pop("using_template", None)
    
    # Initialize user creation data
    context.user_data["create_user"] = {}
    
    # Show template selection
    await show_template_selection(update, context)
    return CREATE_USER_FIELD

async def show_template_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show template selection menu"""
    from modules.utils.presets import get_template_names
    
    message = "🎯 *Создание пользователя*\n\n"
    message += "Выберите готовый шаблон или создайте пользователя вручную:\n\n"
    message += "📋 *Готовые шаблоны* содержат все необходимые настройки\n"
    message += "⚙️ *Ручное создание* позволяет настроить каждое поле отдельно"
    
    # Создаем кнопки для шаблонов
    keyboard = []
    templates = get_template_names()
    
    # Добавляем кнопки шаблонов по 2 в ряду
    for i in range(0, len(templates), 2):
        row = []
        for j in range(2):
            if i + j < len(templates):
                template_name = templates[i + j]
                row.append(InlineKeyboardButton(
                    template_name, 
                    callback_data=f"template_{template_name}"
                ))
        keyboard.append(row)
    
    # Добавляем кнопки управления
    keyboard.extend([
        [InlineKeyboardButton("⚙️ Создать вручную", callback_data="create_manual")],
        [InlineKeyboardButton("❌ Отмена", callback_data="back_to_users")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def handle_template_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, template_name: str):
    """Handle template selection and show confirmation"""
    from modules.utils.presets import get_template_by_name, format_template_info
    
    template = get_template_by_name(template_name)
    if not template:
        await update.callback_query.edit_message_text(
            "❌ Шаблон не найден. Попробуйте еще раз.",
            parse_mode="Markdown"
        )
        return CREATE_USER_FIELD
    
    # Сохраняем выбранный шаблон
    context.user_data["selected_template"] = template_name
    context.user_data["using_template"] = True
    
    # Показываем информацию о шаблоне
    message = "📋 *Предпросмотр шаблона*\n\n"
    message += format_template_info(template_name)
    message += "\n\n💡 *Что дальше?*\n"
    message += "• Вы можете использовать шаблон как есть, только указав имя пользователя\n"
    message += "• Или настроить дополнительные поля (email, Telegram ID, тег и т.д.)"
    
    keyboard = [
        [InlineKeyboardButton("✅ Использовать шаблон", callback_data=f"use_template_{template_name}")],
        [InlineKeyboardButton("⚙️ Настроить дополнительно", callback_data=f"customize_template_{template_name}")],
        [InlineKeyboardButton("🔙 Выбрать другой шаблон", callback_data="back_to_templates")],
        [InlineKeyboardButton("❌ Отмена", callback_data="back_to_users")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def start_template_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, template_name: str, customize: bool = False):
    """Start user creation with selected template"""
    from modules.utils.presets import apply_template_to_user_data
    
    # Применяем шаблон
    context.user_data["create_user"] = apply_template_to_user_data({}, template_name)
    context.user_data["using_template"] = True
    context.user_data["template_name"] = template_name
    
    if customize:
        # Полная настройка - проходим все поля
        context.user_data["create_user_fields"] = list(USER_FIELDS.keys())
        context.user_data["current_field_index"] = 0
    else:
        # Только имя пользователя и опциональные поля
        context.user_data["create_user_fields"] = ["username"]
        context.user_data["current_field_index"] = 0
    
    # Начинаем с первого поля
    await ask_for_field(update, context)
    return CREATE_USER_FIELD

async def ask_for_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for a field value when creating a user"""
    fields = context.user_data["create_user_fields"]
    index = context.user_data["current_field_index"]

    if index >= len(fields):
        # All fields collected, create the user
        return await finish_create_user(update, context)

    field = fields[index]
    field_name = USER_FIELDS[field]
    
    # Проверяем, используется ли шаблон
    using_template = context.user_data.get("using_template", False)
    current_value = context.user_data["create_user"].get(field)
    
    # Если используется шаблон и поле уже заполнено, показываем текущее значение
    template_info = ""
    if using_template and current_value is not None:
        if field == "trafficLimitBytes":
            from modules.utils.formatters import format_bytes
            display_value = "Безлимитный" if current_value == 0 else format_bytes(current_value)
            template_info = f"\n🎯 *Значение из шаблона:* {display_value}"
        elif field == "hwidDeviceLimit":
            if current_value == 0:
                display_value = "Без лимита"
            elif current_value == 1:
                display_value = "1 устройство"
            elif current_value in [2, 3, 4]:
                display_value = f"{current_value} устройства"
            else:
                display_value = f"{current_value} устройств"
            template_info = f"\n🎯 *Значение из шаблона:* {display_value}"
        elif field == "trafficLimitStrategy":
            strategy_map = {
                "NO_RESET": "Без сброса",
                "DAY": "Ежедневно",
                "WEEK": "Еженедельно",
                "MONTH": "Ежемесячно"
            }
            display_value = strategy_map.get(current_value, current_value)
            template_info = f"\n🎯 *Значение из шаблона:* {display_value}"
        else:
            template_info = f"\n🎯 *Значение из шаблона:* {current_value}"

    # Special handling for username when using template
    if field == "username":
        template_name = context.user_data.get("template_name", "")
        message = f"👤 *Введите имя пользователя*\n\n"
        if using_template:
            message += f"Выбранный шаблон: {template_name}\n"
            message += "Введите уникальное имя пользователя (6-34 символа, только буквы, цифры, дефисы и подчеркивания):"
        else:
            message += "Введите имя пользователя:"
        
        # После ввода имени предлагаем дополнительные поля
        if using_template and len(fields) == 1:  # Только username в списке полей
            keyboard = [
                [InlineKeyboardButton("✅ Создать пользователя", callback_data="finish_template_user")],
                [InlineKeyboardButton("⚙️ Добавить дополнительные поля", callback_data="add_optional_fields")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)

    # Special handling for expireAt
    elif field == "expireAt":
        # Default to 30 days from now
        default_value = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        message = f"📅 *Выберите или введите дату истечения*{template_info}\n\n"
        message += "Введите дату в формате YYYY-MM-DD или выберите один из пресетов ниже:"
        
        # Создаем пресеты дат с разными периодами
        today = datetime.now()
        keyboard = [
            [
                InlineKeyboardButton("1 день", callback_data=f"create_date_{(today + timedelta(days=1)).strftime('%Y-%m-%d')}"),
                InlineKeyboardButton("3 дня", callback_data=f"create_date_{(today + timedelta(days=3)).strftime('%Y-%m-%d')}"),
                InlineKeyboardButton("7 дней", callback_data=f"create_date_{(today + timedelta(days=7)).strftime('%Y-%m-%d')}")
            ],
            [
                InlineKeyboardButton("30 дней", callback_data=f"create_date_{(today + timedelta(days=30)).strftime('%Y-%m-%d')}"),
                InlineKeyboardButton("60 дней", callback_data=f"create_date_{(today + timedelta(days=60)).strftime('%Y-%m-%d')}"),
                InlineKeyboardButton("90 дней", callback_data=f"create_date_{(today + timedelta(days=90)).strftime('%Y-%m-%d')}")
            ],
            [
                InlineKeyboardButton("180 дней", callback_data=f"create_date_{(today + timedelta(days=180)).strftime('%Y-%m-%d')}"),
                InlineKeyboardButton("365 дней", callback_data=f"create_date_{(today + timedelta(days=365)).strftime('%Y-%m-%d')}")
            ],
            [InlineKeyboardButton("80 лет 👑", callback_data=f"create_date_{(today + timedelta(days=365*80)).strftime('%Y-%m-%d')}")],
            [InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return CREATE_USER_FIELD
    
    # Special handling for trafficLimitBytes
    elif field == "trafficLimitBytes":
        message = f"📈 *Выберите лимит трафика*\n\nВыберите один из пресетов или введите своё значение в байтах:"
        
        # Создаём пресеты трафика с шагом по 200 ГБ до 1 ТБ (и другие популярные)
        # Конвертация в байты: умножаем на 1024^3
        GB = 1024 * 1024 * 1024
        keyboard = [
            [
                InlineKeyboardButton("50 ГБ", callback_data=f"create_traffic_{50 * GB}"),
                InlineKeyboardButton("100 ГБ", callback_data=f"create_traffic_{100 * GB}"),
                InlineKeyboardButton("200 ГБ", callback_data=f"create_traffic_{200 * GB}")
            ],
            [
                InlineKeyboardButton("400 ГБ", callback_data=f"create_traffic_{400 * GB}"),
                InlineKeyboardButton("600 ГБ", callback_data=f"create_traffic_{600 * GB}"),
                InlineKeyboardButton("800 ГБ", callback_data=f"create_traffic_{800 * GB}")
            ],
            [
                InlineKeyboardButton("1 ТБ", callback_data=f"create_traffic_{1024 * GB}"),
                InlineKeyboardButton("2 ТБ", callback_data=f"create_traffic_{2048 * GB}"),
                InlineKeyboardButton("5 ТБ", callback_data=f"create_traffic_{5120 * GB}")
            ],
            [
                InlineKeyboardButton("Безлимитный", callback_data="create_traffic_0")
            ],
            [InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create")]
        ]
        
        # Логирование для отладки
        logger.debug(f"Setting up traffic limit buttons with callback data: create_traffic_0 for unlimited")
        logger.debug(f"First button callback: {keyboard[0][0].callback_data}")
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return CREATE_USER_FIELD

    # Special handling for description
    elif field == "description":
        message = f"📝 *Введите описание пользователя*\n\nВыберите один из шаблонов или введите своё описание:"
        
        # Создаём шаблоны для часто используемых описаний
        keyboard = [
            [InlineKeyboardButton("Стандартный пользователь", callback_data="create_desc_Стандартный пользователь")],
            [InlineKeyboardButton("VIP-клиент", callback_data="create_desc_VIP-клиент")],
            [InlineKeyboardButton("Тестовый аккаунт", callback_data="create_desc_Тестовый аккаунт")],
            [InlineKeyboardButton("Корпоративный клиент", callback_data="create_desc_Корпоративный клиент")],
            [InlineKeyboardButton("Демо-аккаунт", callback_data="create_desc_Демо-аккаунт")],
            [InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return CREATE_USER_FIELD
    
    # Special handling for hwidDeviceLimit
    elif field == "hwidDeviceLimit":
        message = f"📱 *Выберите лимит устройств*\n\nВыберите один из пресетов или введите своё значение:"
        
        # Создаём пресеты для лимита устройств
        keyboard = [
            [
                InlineKeyboardButton("1 устройство", callback_data="create_device_1"),
                InlineKeyboardButton("2 устройства", callback_data="create_device_2"),
                InlineKeyboardButton("3 устройства", callback_data="create_device_3")
            ],
            [
                InlineKeyboardButton("4 устройства", callback_data="create_device_4"),
                InlineKeyboardButton("5 устройств", callback_data="create_device_5"),
                InlineKeyboardButton("10 устройств", callback_data="create_device_10")
            ],
            [
                InlineKeyboardButton("Без лимита (0)", callback_data="create_device_0")
            ],
            [InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return CREATE_USER_FIELD
        
    # Special handling for trafficLimitStrategy
    elif field == "trafficLimitStrategy":
        keyboard = [
            [InlineKeyboardButton("NO_RESET - Без сброса", callback_data="create_field_NO_RESET")],
            [InlineKeyboardButton("DAY - Ежедневно", callback_data="create_field_DAY")],
            [InlineKeyboardButton("WEEK - Еженедельно", callback_data="create_field_WEEK")],
            [InlineKeyboardButton("MONTH - Ежемесячно", callback_data="create_field_MONTH")],
            [InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"🔄 Выберите стратегию сброса трафика:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return CREATE_USER_FIELD

    else:
        message = f"Введите {field_name}:{template_info}"

    keyboard = [[InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]]

    # Для шаблонов добавляем кнопку "использовать значение из шаблона"
    if using_template and current_value is not None and field not in ["username"]:
        if field == "trafficLimitBytes":
            display_value = "Безлимитный" if current_value == 0 else format_bytes(current_value)
            keyboard.insert(0, [InlineKeyboardButton(f"✅ Оставить: {display_value}", callback_data=f"use_template_value_{field}")])
        elif field == "hwidDeviceLimit":
            if current_value == 0:
                display_value = "Без лимита"
            elif current_value == 1:
                display_value = "1 устройство"
            elif current_value in [2, 3, 4]:
                display_value = f"{current_value} устройства"
            else:
                display_value = f"{current_value} устройств"
            keyboard.insert(0, [InlineKeyboardButton(f"✅ Оставить: {display_value}", callback_data=f"use_template_value_{field}")])
        elif field == "trafficLimitStrategy":
            strategy_map = {
                "NO_RESET": "Без сброса",
                "DAY": "Ежедневно", 
                "WEEK": "Еженедельно",
                "MONTH": "Ежемесячно"
            }
            display_value = strategy_map.get(current_value, current_value)
            keyboard.insert(0, [InlineKeyboardButton(f"✅ Оставить: {display_value}", callback_data=f"use_template_value_{field}")])
        else:
            keyboard.insert(0, [InlineKeyboardButton(f"✅ Оставить: {current_value}", callback_data=f"use_template_value_{field}")])

    # Add cancel button
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_create")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    return CREATE_USER_FIELD

async def handle_create_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input when creating a user"""
    query = update.callback_query

    if query:
        await query.answer()
        data = query.data
        
        if data == "skip_field":
            # Skip this field
            context.user_data["current_field_index"] += 1
            await ask_for_field(update, context)
            return CREATE_USER_FIELD
        
        elif data == "cancel_create":
            # Cancel user creation
            await show_users_menu(update, context)
            return USER_MENU
        
        elif data == "back_to_main":
            # Return to main menu
            await show_main_menu(update, context)
            return MAIN_MENU
        
        # Обработка выбора шаблона
        elif data.startswith("template_"):
            template_name = data[9:]  # убираем "template_"
            await handle_template_selection(update, context, template_name)
            return CREATE_USER_FIELD
        
        elif data == "create_manual":
            # Создание вручную - используем весь список полей
            context.user_data["create_user_fields"] = list(USER_FIELDS.keys())
            context.user_data["current_field_index"] = 0
            context.user_data["using_template"] = False
            await ask_for_field(update, context)
            return CREATE_USER_FIELD
        
        elif data == "back_to_templates":
            await show_template_selection(update, context)
            return CREATE_USER_FIELD
        
        elif data.startswith("use_template_"):
            template_name = data[13:]  # убираем "use_template_"
            await start_template_creation(update, context, template_name, customize=False)
            return CREATE_USER_FIELD
        
        elif data.startswith("customize_template_"):
            template_name = data[19:]  # убираем "customize_template_"
            await start_template_creation(update, context, template_name, customize=True)
            return CREATE_USER_FIELD
        
        elif data == "finish_template_user":
            # Завершаем создание пользователя с шаблоном
            return await finish_create_user(update, context)
        
        elif data == "add_optional_fields":
            # Добавляем дополнительные поля
            optional_fields = ["telegramId", "email", "tag", "expireAt"]
            current_fields = context.user_data["create_user_fields"]
            # Добавляем поля, которых еще нет
            for field in optional_fields:
                if field not in current_fields:
                    current_fields.append(field)
            context.user_data["create_user_fields"] = current_fields
            context.user_data["current_field_index"] += 1  # переходим к следующему полю
            await ask_for_field(update, context)
            return CREATE_USER_FIELD
        
        elif data.startswith("use_template_value_"):
            # Использовать значение из шаблона для поля
            field_name = data[19:]  # убираем "use_template_value_"
            # Значение уже есть в данных пользователя из шаблона
            context.user_data["current_field_index"] += 1
            await ask_for_field(update, context)
            return CREATE_USER_FIELD
        
        elif data.startswith("create_field_"):
            # Handle selection for fields with predefined values
            value = data[13:]  # Берем всё, что идет после "create_field_", чтобы избежать обрезания значений
            fields = context.user_data["create_user_fields"]
            index = context.user_data["current_field_index"]
            field = fields[index]
            
            # Логирование для отладки, чтобы видеть какое значение устанавливается
            logger.info(f"Setting field {field} to value '{value}' from callback data '{data}'")
            
            context.user_data["create_user"][field] = value
            context.user_data["current_field_index"] += 1
            await ask_for_field(update, context)
            return CREATE_USER_FIELD
            
        elif data.startswith("create_date_"):
            # Handle selection for date presets
            date_str = data[12:] # Получаем YYYY-MM-DD из коллбэка
            fields = context.user_data["create_user_fields"]
            index = context.user_data["current_field_index"]
            field = fields[index]
            
            if field == "expireAt":
                # Конвертируем дату в нужный формат
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    value = date_obj.strftime("%Y-%m-%dT00:00:00.000Z")
                    context.user_data["create_user"][field] = value
                    
                    # Показываем сообщение о выбранной дате
                    await query.edit_message_text(
                        f"✅ Выбрана дата истечения: {date_str}",
                        parse_mode="Markdown"
                    )
                    
                    # Переходим к следующему полю
                    context.user_data["current_field_index"] += 1
                    await ask_for_field(update, context)
                except ValueError as e:
                    logger.error(f"Error parsing date: {e}")
                    await query.edit_message_text(
                        "❌ Ошибка при обработке даты. Пожалуйста, выберите другую дату или введите вручную.",
                        parse_mode="Markdown"
                    )
            
            return CREATE_USER_FIELD
            
        elif data.startswith("create_traffic_"):
            # Handle selection for traffic limit presets
            try:
                # Отладочный лог для анализа входящих данных
                logger.debug(f"Processing traffic selection with data: '{data}'")
                
                # Получаем значение в байтах из коллбэка
                traffic_bytes_str = data[14:]  # отрезаем префикс 'create_traffic_'
                logger.debug(f"Extracted traffic value string: '{traffic_bytes_str}'")
                
                fields = context.user_data["create_user_fields"]
                index = context.user_data["current_field_index"]
                field = fields[index]
                
                if field == "trafficLimitBytes":
                    # Преобразуем строку в число
                    value = int(traffic_bytes_str)
                    context.user_data["create_user"][field] = value
                    
                    # Форматируем значение в читаемый вид
                    from modules.utils.formatters import format_bytes
                    readable_value = format_bytes(value)
                    
                    # Для безлимитного трафика (0) показываем особое сообщение
                    if value == 0:
                        readable_value = "Безлимитный"
                    
                    # Показываем сообщение о выбранном лимите
                    await query.edit_message_text(
                        f"✅ Выбран лимит трафика: {readable_value}",
                        parse_mode="Markdown"
                    )
                    
                    # Переходим к следующему полю
                    context.user_data["current_field_index"] += 1
                    await ask_for_field(update, context)
            except ValueError as e:
                logger.error(f"Error parsing traffic limit: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при обработке лимита трафика. Пожалуйста, выберите другое значение или введите вручную.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Unexpected error processing traffic limit: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Произошла ошибка. Пожалуйста, попробуйте другое значение или обратитесь к администратору.",
                    parse_mode="Markdown"
                )
            
            return CREATE_USER_FIELD
            
        elif data.startswith("create_desc_"):
            try:
                # Отладочный лог для анализа входящих данных
                logger.debug(f"Processing description template with data: '{data}'")
                
                # Получаем текст описания из коллбэка
                description = data[12:]  # отрезаем префикс 'create_desc_'
                logger.debug(f"Extracted description: '{description}'")
                
                fields = context.user_data["create_user_fields"]
                index = context.user_data["current_field_index"]
                field = fields[index]
                
                if field == "description":
                    context.user_data["create_user"][field] = description
                    
                    # Показываем сообщение о выбранном шаблоне
                    await query.edit_message_text(
                        f"✅ Выбрано описание: {description}",
                        parse_mode="Markdown"
                    )
                    
                    # Переходим к следующему полю
            except Exception as e:
                logger.error(f"Unexpected error processing description template: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Произошла ошибка при обработке шаблона описания. Пожалуйста, введите описание вручную.",
                    parse_mode="Markdown"
                )
                context.user_data["current_field_index"] += 1
                await ask_for_field(update, context)
            
            return CREATE_USER_FIELD
            
        elif data.startswith("create_device_"):
            # Handle selection for device limit presets
            try:
                # Отладочный лог для анализа входящих данных
                logger.debug(f"Processing device limit selection with data: '{data}'")
                
                # Получаем значение лимита устройств из коллбэка
                device_limit_str = data[14:]  # отрезаем префикс 'create_device_'
                logger.debug(f"Extracted device limit value string: '{device_limit_str}'")
                
                fields = context.user_data["create_user_fields"]
                index = context.user_data["current_field_index"]
                field = fields[index]
                
                if field == "hwidDeviceLimit":
                    # Преобразуем строку в число
                    value = int(device_limit_str)
                    context.user_data["create_user"][field] = value
                    
                    # Формируем читаемое представление (с правильным окончанием для числа устройств)
                    if value == 0:
                        readable_value = "Без лимита"
                    elif value == 1:
                        readable_value = "1 устройство"
                    elif value in [2, 3, 4]:
                        readable_value = f"{value} устройства"
                    else:
                        readable_value = f"{value} устройств"
                    
                    # Если установлен лимит устройств > 0, нужно также установить trafficLimitStrategy = NO_RESET
                    if value > 0:
                        # Явно устанавливаем стратегию NO_RESET
                        context.user_data["create_user"]["trafficLimitStrategy"] = "NO_RESET"
                        logger.info(f"Auto-setting trafficLimitStrategy=NO_RESET for user with hwidDeviceLimit={value}")
                    
                    # Показываем сообщение о выбранном лимите
                    await query.edit_message_text(
                        f"✅ Выбран лимит устройств: {readable_value}",
                        parse_mode="Markdown"
                    )
                    
                    # Переходим к следующему полю
                    context.user_data["current_field_index"] += 1
                    await ask_for_field(update, context)
            except ValueError as e:
                logger.error(f"Error parsing device limit: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при обработке лимита устройств. Пожалуйста, выберите другое значение или введите вручную.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Unexpected error processing device limit: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Произошла ошибка. Пожалуйста, попробуйте другое значение или обратитесь к администратору.",
                    parse_mode="Markdown"
                )
            
            return CREATE_USER_FIELD

    else:  # Text input
        try:
            fields = context.user_data["create_user_fields"]
            index = context.user_data["current_field_index"]
            field = fields[index]
            value = update.message.text.strip()
            
            # Process the value based on the field
            if field == "username":
                # Validate username format
                if not re.match(r"^[a-zA-Z0-9_-]{6,34}$", value):
                    keyboard = [[InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ Неверный формат имени пользователя. Используйте только буквы, цифры, подчеркивания и дефисы. Длина должна быть от 6 до 34 символов.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return CREATE_USER_FIELD
            
            elif field == "expireAt":
                try:
                    # Validate date format
                    date_obj = datetime.strptime(value, "%Y-%m-%d")
                    value = date_obj.strftime("%Y-%m-%dT00:00:00.000Z")
                except ValueError:
                    keyboard = [[InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ Неверный формат даты. Используйте YYYY-MM-DD.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return CREATE_USER_FIELD
            
            elif field == "trafficLimitBytes":
                try:
                    value = int(value)
                    if value < 0:
                        raise ValueError("Traffic limit cannot be negative")
                except ValueError:
                    keyboard = [[InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ Неверный формат числа. Введите целое число >= 0.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return CREATE_USER_FIELD
            
            elif field == "telegramId":
                try:
                    value = int(value)
                except ValueError:
                    keyboard = [[InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ Неверный формат Telegram ID. Введите целое число.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return CREATE_USER_FIELD
            
            elif field == "tag":
                if value and not re.match(r"^[A-Z0-9_]{1,16}$", value):
                    keyboard = [[InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ Неверный формат тега. Используйте только ЗАГЛАВНЫЕ буквы, цифры и подчеркивания. Максимальная длина - 16 символов.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return CREATE_USER_FIELD
            
            elif field == "email":
                if value and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
                    keyboard = [[InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ Неверный формат email.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return CREATE_USER_FIELD
                    
            elif field == "hwidDeviceLimit":
                try:
                    value = int(value)
                    if value < 0:
                        raise ValueError("Device limit cannot be negative")
                    
                    # Если установлен лимит устройств > 0, нужно также установить trafficLimitStrategy = NO_RESET
                    if value > 0:
                        # Явно устанавливаем стратегию NO_RESET
                        context.user_data["create_user"]["trafficLimitStrategy"] = "NO_RESET"
                        logger.info(f"Auto-setting trafficLimitStrategy=NO_RESET for user with hwidDeviceLimit={value}")
                except ValueError:
                    keyboard = [[InlineKeyboardButton("⏩ Пропустить", callback_data="skip_field")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ Неверный формат числа. Введите целое число >= 0.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    return CREATE_USER_FIELD
            
            # Store the value and move to the next field
            context.user_data["create_user"][field] = value
            
            # Если устанавливается лимит устройств, проверим и установим правильную стратегию трафика
            if field == "hwidDeviceLimit" and isinstance(value, int) and value > 0:
                context.user_data["create_user"]["trafficLimitStrategy"] = "NO_RESET"
                logger.info(f"Setting trafficLimitStrategy=NO_RESET because hwidDeviceLimit={value}")
                
            context.user_data["current_field_index"] += 1
            
            # Log the current state of the user creation data
            logger.debug(f"Current user creation data: {context.user_data['create_user']}")
            
            # Ask for the next field
            await ask_for_field(update, context)
            return CREATE_USER_FIELD
            
        except Exception as e:
            # Handle any unexpected errors
            logger.error(f"Error in handle_create_user_input: {e}")
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Произошла ошибка при обработке ввода: {str(e)}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return USER_MENU

async def finish_create_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish creating a user"""
    user_data = context.user_data["create_user"]

    # Generate random username if not provided (20 characters, alphanumeric)
    if "username" not in user_data or not user_data["username"]:
        characters = string.ascii_letters + string.digits
        random_username = ''.join(random.choice(characters) for _ in range(20))
        user_data["username"] = random_username
        logger.info(f"Generated random username: {random_username}")

    # Set default values for required fields if not provided
    if "trafficLimitStrategy" not in user_data:
        user_data["trafficLimitStrategy"] = "NO_RESET"
    
    # Set default traffic limit (100 GB in bytes) if not provided
    if "trafficLimitBytes" not in user_data:
        user_data["trafficLimitBytes"] = 100 * 1024 * 1024 * 1024  # 100 GB in bytes
    
    # Set default device limit if not provided
    if "hwidDeviceLimit" not in user_data:
        user_data["hwidDeviceLimit"] = 1
    
    # Set default description if not provided
    if "description" not in user_data or not user_data["description"]:
        user_data["description"] = f"Автоматически созданный пользователь {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    # Set default reset day if not provided
    if "resetDay" not in user_data:
        user_data["resetDay"] = 1

    # Если установлен лимит устройств (hwidDeviceLimit), убедимся, что стратегия сброса трафика установлена правильно
    if "hwidDeviceLimit" in user_data and user_data.get("hwidDeviceLimit", 0) > 0:
        # Принудительно устанавливаем NO_RESET для корректной работы с лимитом устройств
        user_data["trafficLimitStrategy"] = "NO_RESET"
        logger.info(f"Setting trafficLimitStrategy=NO_RESET for user with hwidDeviceLimit={user_data['hwidDeviceLimit']}")

    if "expireAt" not in user_data:
        # Default to 30 days from now
        user_data["expireAt"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")

    # Log data for debugging
    logger.debug(f"Creating user with data: {user_data}")
    logger.info(f"Creating user with trafficLimitStrategy: {user_data.get('trafficLimitStrategy')}")

    # Create the user
    result = await UserAPI.create_user(user_data)

    if result:
        keyboard = [
            [InlineKeyboardButton("👁️ Просмотр пользователя", callback_data=f"view_{result['uuid']}")],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"✅ Пользователь успешно создан!\n\n"
        message += f"👤 Имя: {escape_markdown(result['username'])}\n"
        message += f"🆔 UUID: `{result['uuid']}`\n"
        message += f"🔑 Короткий UUID: `{result['shortUuid']}`\n"
        message += f"📝 UUID подписки: `{result['subscriptionUuid']}`\n\n"
        message += f"🔗 URL подписки: `{result['subscriptionUrl']}`\n"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return MAIN_MENU
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="create_user")],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        error_message = "❌ Не удалось создать пользователя. "
        
        # Check for specific validation errors
        if "username" not in user_data:
            error_message += "Отсутствует имя пользователя."
        elif "trafficLimitStrategy" not in user_data:
            error_message += "Отсутствует стратегия сброса трафика."
        elif "expireAt" not in user_data:
            error_message += "Отсутствует дата истечения."
        else:
            error_message += "Пожалуйста, проверьте введенные данные."
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=error_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=error_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return MAIN_MENU

async def show_user_hwid_devices(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show user HWID devices"""
    devices = await UserAPI.get_user_hwid_devices(uuid)
    user = context.user_data.get("current_user") or await UserAPI.get_user_by_uuid(uuid)
    
    if not devices:
        keyboard = [
            [InlineKeyboardButton("➕ Добавить устройство", callback_data=f"add_hwid_{uuid}")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"view_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"📱 *Устройства HWID пользователя {escape_markdown(user['username'])}*\n\n"
            f"Устройства не найдены. Вы можете добавить новое устройство.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return SELECTING_USER
    
    message = f"📱 *Устройства HWID пользователя {escape_markdown(user['username'])}*\n\n"
    
    for i, device in enumerate(devices):
        message += f"{i+1}. HWID: `{device['hwid']}`\n"
        if device.get("platform"):
            message += f"   📱 Платформа: {escape_markdown(device['platform'])}\n"
        if device.get("osVersion"):
            message += f"   🖥️ Версия ОС: {escape_markdown(device['osVersion'])}\n"
        if device.get("deviceModel"):
            message += f"   📱 Модель: {escape_markdown(device['deviceModel'])}\n"
        if device.get("createdAt"):
            message += f"   🕒 Добавлено: {device['createdAt'][:10]}\n"
        message += "\n"
    
    # Add action buttons
    keyboard = [
        [InlineKeyboardButton("➕ Добавить устройство", callback_data=f"add_hwid_{uuid}")],
        [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]
    ]
    
    # Add delete buttons for each device
    for i, device in enumerate(devices):
        keyboard.append([
            InlineKeyboardButton(f"❌ Удалить {i+1}", callback_data=f"del_hwid_{uuid}_{device['hwid']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SELECTING_USER

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show user statistics"""
    user = context.user_data.get("current_user") or await UserAPI.get_user_by_uuid(uuid)
    
    # Get usage for last 30 days
    end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    usage = await UserAPI.get_user_usage_by_range(uuid, start_date, end_date)
    
    if not usage:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"view_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Статистика не найдена или ошибка при получении данных.\n\nПользователь: {escape_markdown(user['username'])}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return SELECTING_USER
    
    message = f"📊 *Статистика пользователя {escape_markdown(user['username'])}*\n\n"
    
    # Current usage
    message += f"📈 *Текущее использование*:\n"
    message += f"  • Использовано: {format_bytes(user['usedTrafficBytes'])}\n"
    message += f"  • Лимит: {format_bytes(user['trafficLimitBytes'])}\n"
    
    if user['trafficLimitBytes'] > 0:
        percent = (user['usedTrafficBytes'] / user['trafficLimitBytes']) * 100
        message += f"  • Процент: {percent:.2f}%\n"
    
    message += f"  • За все время: {format_bytes(user['lifetimeUsedTrafficBytes'])}\n\n"
    
    # Usage by node
    if usage:
        message += f"📊 *Использование по серверам (за 30 дней)*:\n"
        
        # Group by node
        node_usage = {}
        for entry in usage:
            node_uuid = entry.get("nodeUuid")
            node_name = entry.get("nodeName", "Неизвестный сервер")
            total = entry.get("total", 0)
            
            if node_uuid not in node_usage:
                node_usage[node_uuid] = {
                    "name": node_name,
                    "total": 0
                }
            
            node_usage[node_uuid]["total"] += total
        
        # Sort by usage
        sorted_nodes = sorted(node_usage.values(), key=lambda x: x["total"], reverse=True)
        
        for i, node in enumerate(sorted_nodes):
            message += f"  • {escape_markdown(node['name'])}: {format_bytes(node['total'])}\n"
    
    # Add action buttons
    keyboard = [
        [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")],
        [InlineKeyboardButton("🔄 Обновить статистику", callback_data=f"stats_{uuid}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SELECTING_USER

async def start_add_hwid(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Start adding a HWID device"""
    user = context.user_data.get("current_user") or await UserAPI.get_user_by_uuid(uuid)
    
    context.user_data["add_hwid_uuid"] = uuid
    
    keyboard = [[InlineKeyboardButton("🔙 Отмена", callback_data=f"hwid_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"📱 *Добавление устройства HWID для пользователя {escape_markdown(user['username'])}*\n\n"
        f"Введите HWID устройства:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    context.user_data["waiting_for"] = "hwid"
    return WAITING_FOR_INPUT

async def delete_hwid_device(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid, hwid):
    """Delete a HWID device"""
    user = context.user_data.get("current_user") or await UserAPI.get_user_by_uuid(uuid)
    
    # Confirm deletion
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_del_hwid_{uuid}_{hwid}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"hwid_{uuid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"⚠️ *Удаление устройства HWID*\n\n"
        f"Вы уверены, что хотите удалить устройство с HWID `{hwid}` "
        f"для пользователя {escape_markdown(user['username'])}?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SELECTING_USER

async def confirm_delete_hwid_device(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid, hwid):
    """Confirm and delete a HWID device"""
    result = await UserAPI.delete_user_hwid_device(uuid, hwid)
    
    if result:
        message = f"✅ Устройство с HWID `{hwid}` успешно удалено."
    else:
        message = f"❌ Не удалось удалить устройство с HWID `{hwid}`."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к устройствам", callback_data=f"hwid_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SELECTING_USER

async def handle_hwid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle HWID input"""
    uuid = context.user_data.get("add_hwid_uuid")
    if not uuid:
        await update.message.reply_text("❌ Ошибка: UUID пользователя не найден.")
        return SELECTING_USER
    
    hwid = update.message.text.strip()
    
    # Добавляем устройство
    result = await UserAPI.add_user_hwid_device(uuid, hwid)
    
    if result:
        keyboard = [[InlineKeyboardButton("🔙 Назад к устройствам", callback_data=f"hwid_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Устройство с HWID `{hwid}` успешно добавлено.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        keyboard = [[InlineKeyboardButton("🔙 Назад к устройствам", callback_data=f"hwid_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ Не удалось добавить устройство с HWID `{hwid}`.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return SELECTING_USER

def register_user_handlers(application):
    """Register user handlers"""
    # This function would register all the user-related handlers
    pass
async def confirm_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Confirm user deletion with extra protection"""
    try:
        user = await UserAPI.get_user_by_uuid(uuid)
        if not user:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Пользователь не найден.",
                reply_markup=reply_markup
            )
            return USER_MENU
        
        # Store user data for deletion
        context.user_data["delete_user"] = user
        context.user_data["action"] = "delete"
        context.user_data["uuid"] = uuid
        
        # Create warning message with user details
        message = f"🚨 *ВНИМАНИЕ! УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ* 🚨\n\n"
        message += f"⚠️ Вы собираетесь **НАВСЕГДА** удалить пользователя:\n\n"
        message += f"👤 **Имя:** `{escape_markdown(user['username'])}`\n"
        message += f"🆔 **UUID:** `{user['uuid']}`\n"
        message += f"📊 **Статус:** {user['status']}\n"
        message += f"📈 **Использовано трафика:** {format_bytes(user['usedTrafficBytes'])}\n"
        message += f"📅 **Дата истечения:** {user.get('expireAt', 'Не указана')[:10]}\n\n"
        
        message += f"💀 **ЭТО ДЕЙСТВИЕ НЕЛЬЗЯ ОТМЕНИТЬ!**\n\n"
        message += f"🔴 Будет удалено:\n"
        message += f"• Вся статистика пользователя\n"
        message += f"• Все устройства HWID\n"
        message += f"• История использования\n"
        message += f"• Настройки и конфигурация\n\n"
        
        message += f"🛡️ **Для подтверждения введите имя пользователя:**\n"
        message += f"Введите: `{user['username']}`"
        
        keyboard = [
            [InlineKeyboardButton("❌ ОТМЕНА", callback_data=f"view_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Set state to wait for username confirmation
        context.user_data["waiting_for"] = "delete_confirmation"
        return WAITING_FOR_INPUT
        
    except Exception as e:
        logger.error(f"Error in confirm_delete_user: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Ошибка при подготовке удаления пользователя.",
            reply_markup=reply_markup
        )
        return USER_MENU

async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle username confirmation for user deletion"""
    try:
        user_to_delete = context.user_data.get("delete_user")
        if not user_to_delete:
            await update.message.reply_text("❌ Ошибка: данные пользователя для удаления не найдены.")
            return USER_MENU
        
        entered_username = update.message.text.strip()
        expected_username = user_to_delete['username']
        
        # Check if entered username matches exactly
        if entered_username != expected_username:
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data=f"view_{user_to_delete['uuid']}")],
                [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{user_to_delete['uuid']}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ **Неверное имя пользователя!**\n\n"
                f"Введено: `{escape_markdown(entered_username)}`\n"
                f"Ожидается: `{escape_markdown(expected_username)}`\n\n"
                f"Попробуйте еще раз или отмените операцию.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return WAITING_FOR_INPUT
        
        # Username matches, show final confirmation
        message = f"✅ **Имя пользователя подтверждено!**\n\n"
        message += f"🚨 **ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ!**\n\n"
        message += f"Пользователь `{escape_markdown(expected_username)}` будет удален навсегда.\n\n"
        message += f"**Вы абсолютно уверены?**"
        
        keyboard = [
            [InlineKeyboardButton("🗑️ ДА, УДАЛИТЬ НАВСЕГДА", callback_data="final_delete_user")],
            [InlineKeyboardButton("❌ НЕТ, ОТМЕНИТЬ", callback_data=f"view_{user_to_delete['uuid']}")],
            [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{user_to_delete['uuid']}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return CONFIRM_ACTION
        
    except Exception as e:
        logger.error(f"Error in handle_delete_confirmation: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке подтверждения.")
        return USER_MENU

async def execute_user_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the actual user deletion"""
    try:
        user_to_delete = context.user_data.get("delete_user")
        if not user_to_delete:
            await update.callback_query.edit_message_text("❌ Ошибка: данные пользователя для удаления не найдены.")
            return USER_MENU
        
        uuid = user_to_delete['uuid']
        username = user_to_delete['username']
        
        # Show deletion in progress
        await update.callback_query.edit_message_text(
            f"🗑️ Удаление пользователя `{escape_markdown(username)}`...\n\nПожалуйста, подождите...",
            parse_mode="Markdown"
        )
        
        # Perform the deletion
        result = await UserAPI.delete_user(uuid)
        
        # Clear stored deletion data
        context.user_data.pop("delete_user", None)
        context.user_data.pop("action", None)
        context.user_data.pop("uuid", None)
        context.user_data.pop("waiting_for", None)
        
        if result:
            keyboard = [
                [InlineKeyboardButton("📋 Список пользователей", callback_data="list_users")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"✅ **Пользователь успешно удален!**\n\n"
                f"👤 Имя: `{escape_markdown(username)}`\n"
                f"🆔 UUID: `{uuid}`\n\n"
                f"🗑️ Все данные пользователя были удалены навсегда.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            # Log the deletion for audit purposes
            logger.warning(f"User deleted: {username} (UUID: {uuid}) by admin {update.effective_user.id}")
            
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"user_action_delete_{uuid}")],
                [InlineKeyboardButton("🔙 Назад к списку", callback_data="list_users")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"❌ **Не удалось удалить пользователя!**\n\n"
                f"👤 Имя: `{escape_markdown(username)}`\n"
                f"🆔 UUID: `{uuid}`\n\n"
                f"Возможные причины:\n"
                f"• Пользователь уже удален\n"
                f"• Ошибка соединения с сервером\n"
                f"• Недостаточно прав доступа\n\n"
                f"Попробуйте еще раз или обратитесь к администратору.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return USER_MENU
        
    except Exception as e:
        logger.error(f"Error in execute_user_deletion: {e}")
        
        # Clear stored deletion data
        context.user_data.pop("delete_user", None)
        context.user_data.pop("action", None)
        context.user_data.pop("uuid", None)
        context.user_data.pop("waiting_for", None)
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад к списку", callback_data="list_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ **Критическая ошибка при удалении пользователя!**\n\n"
            f"Ошибка: `{str(e)}`\n\n"
            f"Обратитесь к администратору системы.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return USER_MENU
    