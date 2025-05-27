from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import logging
import asyncio

from modules.handlers.auth import AuthFilter
from modules.handlers.states import BulkStates
from modules.api.client import RemnaAPI
from modules.utils.formatters_aiogram import (
    format_bytes, format_datetime, escape_markdown
)

logger = logging.getLogger(__name__)

router = Router()

# ================ BULK OPERATIONS MENU ================

@router.callback_query(F.data == "bulk", AuthFilter())
async def handle_bulk_menu(callback: types.CallbackQuery, state: FSMContext):
    """Handle bulk operations menu selection"""
    await callback.answer()
    await state.clear()
    await show_bulk_menu(callback)

async def show_bulk_menu(callback: types.CallbackQuery):
    """Show bulk operations menu"""
    builder = InlineKeyboardBuilder()
    
    # Основные массовые операции
    builder.row(types.InlineKeyboardButton(text="🔄 Сбросить трафик всем", callback_data="bulk_reset_all_traffic"))
    builder.row(types.InlineKeyboardButton(text="⚡ Сбросить превысившим лимит", callback_data="bulk_reset_overlimit"))
    builder.row(types.InlineKeyboardButton(text="❌ Удалить неактивных", callback_data="bulk_delete_inactive"))
    builder.row(types.InlineKeyboardButton(text="❌ Удалить истекших", callback_data="bulk_delete_expired"))
    
    # Дополнительные операции
    builder.row(types.InlineKeyboardButton(text="📅 Продлить всем на месяц", callback_data="bulk_extend_month"))
    builder.row(types.InlineKeyboardButton(text="🔄 Обновить всех пользователей", callback_data="bulk_update_all"))
    
    # Операции с inbound'ами
    builder.row(types.InlineKeyboardButton(text="🔌 Операции с Inbounds", callback_data="bulk_inbounds"))
    
    # Операции с нодами
    builder.row(types.InlineKeyboardButton(text="🖥️ Операции с серверами", callback_data="bulk_nodes"))
    
    # Статистика и экспорт
    builder.row(
        types.InlineKeyboardButton(text="📊 Статистика операций", callback_data="bulk_stats"),
        types.InlineKeyboardButton(text="📄 Экспорт данных", callback_data="bulk_export")
    )
    
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "🔄 **Массовые операции**\n\n"
    
    try:
        # Получаем краткую статистику для информации
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if users_response and users_response.users:
            total_users = len(users_response.users)
            active_users = sum(1 for user in users_response.users if user.is_active)
            inactive_users = total_users - active_users
            
            # Подсчет истекших и превысивших лимит
            now = datetime.now()
            expired_users = 0
            overlimit_users = 0
            
            for user in users_response.users:
                # Истекшие
                if user.expire_at:
                    try:
                        expire_date = datetime.fromisoformat(user.expire_at.replace('Z', '+00:00'))
                        if expire_date < now:
                            expired_users += 1
                    except:
                        pass
                
                # Превысившие лимит
                if user.traffic_limit and user.used_traffic:
                    if user.used_traffic >= user.traffic_limit:
                        overlimit_users += 1
            
            message += f"**📈 Текущее состояние:**\n"
            message += f"• Всего пользователей: {total_users}\n"
            message += f"• Активных: {active_users}\n"
            message += f"• Неактивных: {inactive_users}\n"
            message += f"• Истекших: {expired_users}\n"
            message += f"• Превысивших лимит: {overlimit_users}\n\n"
        
    except Exception as e:
        logger.error(f"Error getting bulk stats: {e}")
        message += "**📈 Статистика:** Недоступна\n\n"
    
    message += "⚠️ **ВНИМАНИЕ!** Эти операции затрагивают множество пользователей одновременно.\n\n"
    message += "Выберите действие:"

    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

# ================ TRAFFIC OPERATIONS ================

@router.callback_query(F.data == "bulk_reset_all_traffic", AuthFilter())
async def bulk_reset_all_traffic_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm reset traffic for all users"""
    await callback.answer()
    
    try:
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        total_users = len(users_response.users) if users_response and users_response.users else 0
        users_with_traffic = sum(1 for user in users_response.users if user.used_traffic and user.used_traffic > 0) if users_response and users_response.users else 0
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Да, сбросить всем", callback_data="confirm_reset_all_traffic"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="bulk")
        )
        
        message = f"🔄 **Сброс трафика всем пользователям**\n\n"
        message += f"**Затронуто будет:**\n"
        message += f"• Всего пользователей: {total_users}\n"
        message += f"• С использованным трафиком: {users_with_traffic}\n\n"
        message += f"⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n"
        message += f"У всех пользователей будет обнулен счетчик использованного трафика.\n\n"
        message += f"Продолжить?"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting users for traffic reset: {e}")
        await callback.answer("❌ Ошибка при получении данных пользователей", show_alert=True)

@router.callback_query(F.data == "confirm_reset_all_traffic", AuthFilter())
async def confirm_reset_all_traffic(callback: types.CallbackQuery, state: FSMContext):
    """Reset traffic for all users"""
    await callback.answer()
    await callback.message.edit_text("🔄 Сбрасываю трафик всем пользователям...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем всех пользователей
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.message.edit_text(
                "❌ Пользователи не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
                ]])
            )
            return
        
        # Сбрасываем трафик по частям для избежания таймаутов
        success_count = 0
        error_count = 0
        total_users = len(users_response.users)
        
        # Обрабатываем пользователей группами по 10
        for i in range(0, total_users, 10):
            batch = users_response.users[i:i+10]
            
            # Обновляем прогресс
            if i > 0:
                progress = (i / total_users) * 100
                await callback.message.edit_text(
                    f"🔄 Сбрасываю трафик... {progress:.1f}% ({i}/{total_users})"
                )
            
            # Обрабатываем текущую группу
            for user in batch:
                try:
                    if user.used_traffic and user.used_traffic > 0:
                        # Сбрасываем трафик через SDK
                        success = await sdk.users.reset_user_traffic(user.uuid)
                        if success:
                            success_count += 1
                        else:
                            error_count += 1
                except Exception as e:
                    logger.error(f"Error resetting traffic for user {user.uuid}: {e}")
                    error_count += 1
            
            # Небольшая пауза между группами
            await asyncio.sleep(0.1)
        
        # Результат операции
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk"))
        
        if success_count > 0:
            message = f"✅ **Сброс трафика завершен**\n\n"
            message += f"• Успешно обработано: {success_count}\n"
            if error_count > 0:
                message += f"• Ошибок: {error_count}\n"
            message += f"• Всего пользователей: {total_users}"
        else:
            message = f"❌ **Не удалось сбросить трафик**\n\n"
            message += f"Возможные причины:\n"
            message += f"• Нет пользователей с трафиком\n"
            message += f"• Ошибки API\n"
            message += f"• Проблемы подключения"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error in bulk traffic reset: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при сбросе трафика",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
            ]])
        )

# ================ RESET OVERLIMIT TRAFFIC ================

@router.callback_query(F.data == "bulk_reset_overlimit", AuthFilter())
async def bulk_reset_overlimit_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm reset traffic for users who exceeded limit"""
    await callback.answer()
    
    try:
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.answer("❌ Пользователи не найдены", show_alert=True)
            return
        
        # Находим пользователей, превысивших лимит
        overlimit_users = []
        for user in users_response.users:
            if user.traffic_limit and user.used_traffic:
                if user.used_traffic >= user.traffic_limit:
                    overlimit_users.append(user)
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Да, сбросить превысившим", callback_data="confirm_reset_overlimit"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="bulk")
        )
        
        message = f"⚡ **Сброс трафика пользователям, превысившим лимит**\n\n"
        message += f"**Будет обработано:** {len(overlimit_users)} пользователей\n\n"
        
        if len(overlimit_users) > 0:
            # Показываем примеры пользователей для сброса
            message += f"**Примеры пользователей:**\n"
            for i, user in enumerate(overlimit_users[:5]):
                usage_percent = (user.used_traffic / user.traffic_limit * 100) if user.traffic_limit > 0 else 0
                traffic_info = f" ({format_bytes(user.used_traffic)}/{format_bytes(user.traffic_limit)} - {usage_percent:.1f}%)"
                message += f"• {escape_markdown(user.username)}{traffic_info}\n"
            
            if len(overlimit_users) > 5:
                message += f"• ... и еще {len(overlimit_users) - 5}\n"
        
        message += f"\n💡 **Действие:** Трафик будет сброшен до 0, лимиты останутся без изменений.\n"
        message += f"⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n\n"
        message += f"Продолжить?"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting overlimit users: {e}")
        await callback.answer("❌ Ошибка при получении данных пользователей", show_alert=True)

@router.callback_query(F.data == "confirm_reset_overlimit", AuthFilter())
async def confirm_reset_overlimit(callback: types.CallbackQuery, state: FSMContext):
    """Reset traffic for users who exceeded limit"""
    await callback.answer()
    await callback.message.edit_text("⚡ Сбрасываю трафик пользователям, превысившим лимит...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем всех пользователей
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.message.edit_text(
                "❌ Пользователи не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
                ]])
            )
            return
        
        # Фильтруем пользователей, превысивших лимит
        overlimit_users = []
        for user in users_response.users:
            if user.traffic_limit and user.used_traffic:
                if user.used_traffic >= user.traffic_limit:
                    overlimit_users.append(user)
        
        if not overlimit_users:
            await callback.message.edit_text(
                "ℹ️ Пользователей, превысивших лимит, не найдено",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
                ]])
            )
            return
        
        # Сбрасываем трафик превысившим лимит
        success_count = 0
        error_count = 0
        
        for i, user in enumerate(overlimit_users):
            try:
                # Обновляем прогресс каждые 5 пользователей
                if i > 0 and i % 5 == 0:
                    progress = (i / len(overlimit_users)) * 100
                    await callback.message.edit_text(
                        f"⚡ Сбрасываю трафик превысившим... {progress:.1f}% ({i}/{len(overlimit_users)})"
                    )
                
                success = await sdk.users.reset_user_traffic(user.uuid)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error resetting traffic for overlimit user {user.uuid}: {e}")
                error_count += 1
        
        # Результат операции
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk"))
        
        message = f"✅ **Сброс трафика превысившим лимит завершен**\n\n"
        message += f"• Успешно сброшено: {success_count}\n"
        if error_count > 0:
            message += f"• Ошибок: {error_count}\n"
        message += f"• Всего обработано: {len(overlimit_users)}\n\n"
        message += f"💡 **Результат:** Пользователи могут снова использовать VPN."
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error in bulk reset overlimit: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при сбросе трафика превысивших лимит",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
            ]])
        )

# ================ DELETE OPERATIONS ================

@router.callback_query(F.data == "bulk_delete_inactive", AuthFilter())
async def bulk_delete_inactive_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm delete inactive users"""
    await callback.answer()
    
    try:
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.answer("❌ Пользователи не найдены", show_alert=True)
            return
        
        inactive_users = [user for user in users_response.users if not user.is_active]
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Да, удалить неактивных", callback_data="confirm_delete_inactive"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="bulk")
        )
        
        message = f"❌ **Удаление неактивных пользователей**\n\n"
        message += f"**Будет удалено:** {len(inactive_users)} пользователей\n\n"
        
        if len(inactive_users) > 0:
            # Показываем примеры пользователей для удаления
            message += f"**Примеры пользователей:**\n"
            for i, user in enumerate(inactive_users[:5]):
                message += f"• {escape_markdown(user.username)}\n"
            
            if len(inactive_users) > 5:
                message += f"• ... и еще {len(inactive_users) - 5}\n"
        
        message += f"\n⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n"
        message += f"Все неактивные пользователи будут удалены из системы.\n\n"
        message += f"Продолжить?"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting inactive users: {e}")
        await callback.answer("❌ Ошибка при получении данных пользователей", show_alert=True)

@router.callback_query(F.data == "confirm_delete_inactive", AuthFilter())
async def confirm_delete_inactive(callback: types.CallbackQuery, state: FSMContext):
    """Delete all inactive users"""
    await callback.answer()
    await callback.message.edit_text("❌ Удаляю неактивных пользователей...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем всех пользователей
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.message.edit_text(
                "❌ Пользователи не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
                ]])
            )
            return
        
        # Фильтруем неактивных пользователей
        inactive_users = [user for user in users_response.users if not user.is_active]
        
        if not inactive_users:
            await callback.message.edit_text(
                "ℹ️ Неактивных пользователей не найдено",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
                ]])
            )
            return
        
        # Удаляем пользователей
        success_count = 0
        error_count = 0
        
        for i, user in enumerate(inactive_users):
            try:
                # Обновляем прогресс каждые 5 пользователей
                if i > 0 and i % 5 == 0:
                    progress = (i / len(inactive_users)) * 100
                    await callback.message.edit_text(
                        f"❌ Удаляю неактивных... {progress:.1f}% ({i}/{len(inactive_users)})"
                    )
                
                success = await sdk.users.delete_user(user.uuid)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error deleting user {user.uuid}: {e}")
                error_count += 1
        
        # Результат операции
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk"))
        
        message = f"✅ **Удаление неактивных завершено**\n\n"
        message += f"• Успешно удалено: {success_count}\n"
        if error_count > 0:
            message += f"• Ошибок: {error_count}\n"
        message += f"• Всего обработано: {len(inactive_users)}"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error in bulk delete inactive: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при удалении неактивных пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
            ]])
        )

@router.callback_query(F.data == ("bulk_delete_expired"), AuthFilter())
async def bulk_delete_expired_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm delete expired users"""
    await callback.answer()
    
    try:
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.answer("❌ Пользователи не найдены", show_alert=True)
            return
        
        # Находим истекших пользователей
        now = datetime.now()
        expired_users = []
        
        for user in users_response.users:
            if user.expire_at:
                try:
                    expire_date = datetime.fromisoformat(user.expire_at.replace('Z', '+00:00'))
                    if expire_date < now:
                        expired_users.append(user)
                except:
                    pass
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Да, удалить истекших", callback_data="confirm_delete_expired"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="bulk")
        )
        
        message = f"❌ **Удаление пользователей с истекшим сроком**\n\n"
        message += f"**Будет удалено:** {len(expired_users)} пользователей\n\n"
        
        if len(expired_users) > 0:
            # Показываем примеры пользователей для удаления
            message += f"**Примеры пользователей:**\n"
            for i, user in enumerate(expired_users[:5]):
                expire_date = ""
                if user.expire_at:
                    try:
                        expire_dt = datetime.fromisoformat(user.expire_at.replace('Z', '+00:00'))
                        expire_date = f" (истек {expire_dt.strftime('%d.%m.%Y')})"
                    except:
                        pass
                message += f"• {escape_markdown(user.username)}{expire_date}\n"
            
            if len(expired_users) > 5:
                message += f"• ... и еще {len(expired_users) - 5}\n"
        
        message += f"\n⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n"
        message += f"Все пользователи с истекшим сроком будут удалены из системы.\n\n"
        message += f"Продолжить?"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting expired users: {e}")
        await callback.answer("❌ Ошибка при получении данных пользователей", show_alert=True)

@router.callback_query(F.data == "confirm_delete_expired", AuthFilter())
async def confirm_delete_expired(callback: types.CallbackQuery, state: FSMContext):
    """Delete all expired users"""
    await callback.answer()
    await callback.message.edit_text("❌ Удаляю пользователей с истекшим сроком...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем всех пользователей
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.message.edit_text(
                "❌ Пользователи не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
                ]])
            )
            return
        
        # Фильтруем истекших пользователей
        now = datetime.now()
        expired_users = []
        
        for user in users_response.users:
            if user.expire_at:
                try:
                    expire_date = datetime.fromisoformat(user.expire_at.replace('Z', '+00:00'))
                    if expire_date < now:
                        expired_users.append(user)
                except:
                    pass
        
        if not expired_users:
            await callback.message.edit_text(
                "ℹ️ Пользователей с истекшим сроком не найдено",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
                ]])
            )
            return
        
        # Удаляем пользователей
        success_count = 0
        error_count = 0
        
        for i, user in enumerate(expired_users):
            try:
                # Обновляем прогресс каждые 5 пользователей
                if i > 0 and i % 5 == 0:
                    progress = (i / len(expired_users)) * 100
                    await callback.message.edit_text(
                        f"❌ Удаляю истекших... {progress:.1f}% ({i}/{len(expired_users)})"
                    )
                
                success = await sdk.users.delete_user(user.uuid)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error deleting expired user {user.uuid}: {e}")
                error_count += 1
        
        # Результат операции
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk"))
        
        message = f"✅ **Удаление истекших завершено**\n\n"
        message += f"• Успешно удалено: {success_count}\n"
        if error_count > 0:
            message += f"• Ошибок: {error_count}\n"
        message += f"• Всего обработано: {len(expired_users)}"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error in bulk delete expired: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при удалении истекших пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
            ]])
        )

# ================ EXTEND OPERATIONS ================

@router.callback_query(F.data == "bulk_extend_month", AuthFilter())
async def bulk_extend_month_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm extend all users for one month"""
    await callback.answer()
    
    try:
        sdk = RemnaAPI.get_sdk()
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.answer("❌ Пользователи не найдены", show_alert=True)
            return
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Да, продлить всем", callback_data="confirm_extend_month"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="bulk")
        )
        
        total_users = len(users_response.users)
        
        message = f"📅 **Продление на месяц всем пользователям**\n\n"
        message += f"**Будет затронуто:** {total_users} пользователей\n\n"
        message += f"**Операция:**\n"
        message += f"• Пользователям без срока истечения - установится срок через месяц\n"
        message += f"• Пользователям с существующим сроком - добавится месяц\n\n"
        message += f"⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n\n"
        message += f"Продолжить?"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting users for extend: {e}")
        await callback.answer("❌ Ошибка при получении данных пользователей", show_alert=True)

@router.callback_query(F.data == "confirm_extend_month", AuthFilter())
async def confirm_extend_month(callback: types.CallbackQuery, state: FSMContext):
    """Extend all users for one month"""
    await callback.answer()
    await callback.message.edit_text("📅 Продлеваю всех пользователей на месяц...")
    
    try:
        sdk = RemnaAPI.get_sdk()
        
        # Получаем всех пользователей
        users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
        
        if not users_response or not users_response.users:
            await callback.message.edit_text(
                "❌ Пользователи не найдены",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
                ]])
            )
            return
        
        # Продлеваем пользователей
        success_count = 0
        error_count = 0
        total_users = len(users_response.users)
        
        # Подготавливаем новую дату истечения
        now = datetime.now()
        one_month_later = now + timedelta(days=30)
        
        for i, user in enumerate(users_response.users):
            try:
                # Обновляем прогресс каждые 10 пользователей
                if i > 0 and i % 10 == 0:
                    progress = (i / total_users) * 100
                    await callback.message.edit_text(
                        f"📅 Продлеваю пользователей... {progress:.1f}% ({i}/{total_users})"
                    )
                
                # Определяем новую дату истечения
                if user.expire_at:
                    try:
                        current_expire = datetime.fromisoformat(user.expire_at.replace('Z', '+00:00'))
                        # Если срок еще не истек, добавляем месяц к текущему сроку
                        if current_expire > now:
                            new_expire = current_expire + timedelta(days=30)
                        else:
                            # Если срок истек, устанавливаем месяц от сегодня
                            new_expire = one_month_later
                    except:
                        new_expire = one_month_later
                else:
                    # Если срока не было, устанавливаем месяц от сегодня
                    new_expire = one_month_later
                
                # Обновляем пользователя через SDK
                update_data = {
                    'expire_at': new_expire.isoformat()
                }
                
                success = await sdk.users.update_user(user.uuid, update_data)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error extending user {user.uuid}: {e}")
                error_count += 1
        
        # Результат операции
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk"))
        
        message = f"✅ **Продление на месяц завершено**\n\n"
        message += f"• Успешно продлено: {success_count}\n"
        if error_count > 0:
            message += f"• Ошибок: {error_count}\n"
        message += f"• Всего обработано: {total_users}\n\n"
        message += f"**Новый срок истечения:** {one_month_later.strftime('%d.%m.%Y')}"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error in bulk extend month: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при продлении пользователей",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
            ]])
        )

# ================ PLACEHOLDER OPERATIONS ================

@router.callback_query(F.data == "bulk_update_all", AuthFilter())
async def bulk_update_all_placeholder(callback: types.CallbackQuery):
    """Bulk update all users placeholder"""
    await callback.answer()
    
    await callback.message.edit_text(
        "🔄 **Массовое обновление пользователей**\n\n"
        "🚧 Функция массового обновления находится в разработке.\n\n"
        "**Планируемые возможности:**\n"
        "• Массовое изменение лимитов трафика\n"
        "• Обновление inbound'ов для всех\n"
        "• Изменение настроек безопасности\n"
        "• Синхронизация с серверами\n\n"
        "В текущей версии доступны отдельные операции через меню выше.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
        ]])
    )

@router.callback_query(F.data == "bulk_inbounds", AuthFilter())
async def bulk_inbounds_placeholder(callback: types.CallbackQuery):
    """Bulk inbounds operations placeholder"""
    await callback.answer()
    
    await callback.message.edit_text(
        "🔌 **Массовые операции с Inbounds**\n\n"
        "🚧 Функции массовых операций с Inbound'ами находятся в разработке.\n\n"
        "**Планируемые возможности:**\n"
        "• Добавление конкретного Inbound всем пользователям\n"
        "• Удаление Inbound у всех пользователей\n"
        "• Пересинхронизация Inbound'ов с серверами\n"
        "• Массовое обновление настроек Inbound'ов",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
        ]])
    )

@router.callback_query(F.data == "bulk_nodes", AuthFilter())
async def bulk_nodes_placeholder(callback: types.CallbackQuery):
    """Bulk nodes operations placeholder"""
    await callback.answer()
    
    await callback.message.edit_text(
        "🖥️ **Массовые операции с серверами**\n\n"
        "🚧 Функции массовых операций с серверами находятся в разработке.\n\n"
        "**Планируемые возможности:**\n"
        "• Перезапуск всех серверов\n"
        "• Массовое обновление статистики\n"
        "• Синхронизация настроек\n"
        "• Проверка состояния всех серверов",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
        ]])
    )

@router.callback_query(F.data == "bulk_stats", AuthFilter())
async def bulk_stats_placeholder(callback: types.CallbackQuery):
    """Bulk statistics placeholder"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📊 **Статистика операций**\n\n"
        "🚧 Детальная статистика операций находится в разработке.\n\n"
        "**Планируемые возможности:**\n"
        "• История выполненных операций\n"
        "• Статистика успешности операций\n"
        "• Анализ производительности\n"
        "• Рекомендации по оптимизации",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
        ]])
    )

@router.callback_query(F.data == "bulk_export", AuthFilter())
async def bulk_export_placeholder(callback: types.CallbackQuery):
    """Bulk export placeholder"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📄 **Экспорт данных**\n\n"
        "🚧 Функция экспорта данных находится в разработке.\n\n"
        "**Планируемые форматы экспорта:**\n"
        "• CSV файлы со списками пользователей\n"
        "• JSON дампы конфигураций\n"
        "• Отчеты по статистике\n"
        "• Backup конфигураций",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="bulk")
        ]])
    )

def register_bulk_handlers(dp):
    """Register bulk handlers"""
    dp.include_router(router)
