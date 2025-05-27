from datetime import datetime
import logging
from typing import Optional, Union, Dict, Any

logger = logging.getLogger(__name__)

async def safe_edit_message(callback_query, text, reply_markup=None, parse_mode="Markdown"):
    """Safely edit message text with error handling for 'Message is not modified'"""
    try:
        await callback_query.message.edit_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "not modified" in error_msg or "message is not modified" in error_msg:
            # Сообщение уже имеет такой же текст, просто отвечаем на callback
            logger.debug("Message content unchanged, skipping update")
            try:
                await callback_query.answer()
            except Exception:
                pass  # Ignore if callback already answered
            return True
        else:
            # Другая ошибка, логируем ее
            logger.error(f"Error editing message: {e}")
            try:
                await callback_query.answer("❌ Ошибка при обновлении сообщения")
            except Exception:
                pass
            return False

def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    if not bytes_value:
        return "0 B"  # Handle None or empty values
    
    # Если bytes_value строка, попробуем преобразовать в число
    if isinstance(bytes_value, str):
        try:
            bytes_value = float(bytes_value)
        except (ValueError, TypeError):
            return bytes_value  # Если не удалось преобразовать, возвращаем как есть
    
    if bytes_value == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def escape_markdown(text):
    """Escape Markdown special characters for Telegram (aiogram MarkdownV2)"""
    if text is None:
        return ""
    
    text = str(text)
    
    # Экранирование для MarkdownV2 (aiogram использует MarkdownV2)
    escape_chars = [
        ('\\', '\\\\'),  # Backslash должен быть первым
        ('_', '\\_'),
        ('*', '\\*'),
        ('[', '\\['),
        (']', '\\]'),
        ('(', '\\('),
        (')', '\\)'),
        ('~', '\\~'),
        ('`', '\\`'),
        ('>', '\\>'),
        ('#', '\\#'),
        ('+', '\\+'),
        ('-', '\\-'),
        ('=', '\\='),
        ('|', '\\|'),
        ('{', '\\{'),
        ('}', '\\}'),
        ('.', '\\.'),
        ('!', '\\!')
    ]
    
    for char, escaped in escape_chars:
        text = text.replace(char, escaped)
    
    return text

def format_user_details(user):
    """Format user details for display with remnawave SDK objects"""
    try:
        # Форматирование даты истечения
        if hasattr(user, 'expire_at') and user.expire_at:
            try:
                if isinstance(user.expire_at, str):
                    expire_date = datetime.fromisoformat(user.expire_at.replace('Z', '+00:00'))
                else:
                    expire_date = user.expire_at
                days_left = (expire_date - datetime.now().astimezone()).days
                expire_status = "🟢" if days_left > 7 else "🟡" if days_left > 0 else "🔴"
                expire_text = f"{expire_date.strftime('%Y-%m-%d')} ({days_left} дней)"
            except Exception:
                expire_status = "📅"
                expire_text = str(user.expire_at) if user.expire_at else "Не указано"
        else:
            expire_status = "📅"
            expire_text = "Не указано"
    
        # Форматирование статуса
        status_emoji = "✅" if user.is_active else "❌"
        
        message = f"👤 *Пользователь:* {escape_markdown(user.username)}\n"
        message += f"🆔 *UUID:* `{user.uuid}`\n"
        
        if hasattr(user, 'short_uuid') and user.short_uuid:
            message += f"🔑 *Короткий UUID:* `{user.short_uuid}`\n"
        
        if hasattr(user, 'subscription_uuid') and user.subscription_uuid:
            message += f"📝 *UUID подписки:* `{user.subscription_uuid}`\n"
        
        message += "\n"
        
        # URL подписки
        if hasattr(user, 'subscription_url') and user.subscription_url:
            message += f"🔗 *URL подписки:*\n```\n{user.subscription_url}\n```\n\n"
        else:
            message += f"🔗 *URL подписки:* Не указан\n\n"
        
        message += f"📊 *Статус:* {status_emoji} {'Активен' if user.is_active else 'Неактивен'}\n"
        
        # Трафик
        used_traffic = getattr(user, 'used_traffic', 0) or 0
        traffic_limit = getattr(user, 'traffic_limit', 0) or 0
        message += f"📈 *Трафик:* {format_bytes(used_traffic)}"
        if traffic_limit > 0:
            message += f"/{format_bytes(traffic_limit)}"
        else:
            message += "/Безлимитный"
        message += "\n"
        
        if hasattr(user, 'traffic_reset_strategy') and user.traffic_reset_strategy:
            message += f"🔄 *Стратегия сброса:* {user.traffic_reset_strategy}\n"
        
        message += f"{expire_status} *Истекает:* {expire_text}\n\n"
        
        # Дополнительные поля
        if hasattr(user, 'description') and user.description:
            message += f"📝 *Описание:* {escape_markdown(str(user.description))}\n"
        
        if hasattr(user, 'tag') and user.tag:
            message += f"🏷️ *Тег:* {escape_markdown(str(user.tag))}\n"
        
        if hasattr(user, 'telegram_id') and user.telegram_id:
            message += f"📱 *Telegram ID:* {user.telegram_id}\n"
        
        if hasattr(user, 'email') and user.email:
            message += f"📧 *Email:* {escape_markdown(str(user.email))}\n"
        
        if hasattr(user, 'device_limit') and user.device_limit:
            message += f"📱 *Лимит устройств:* {user.device_limit}\n"
        
        # Даты создания и обновления
        if hasattr(user, 'created_at') and user.created_at:
            created_date = user.created_at
            if isinstance(created_date, str):
                created_date = created_date[:10]
            else:
                created_date = created_date.strftime('%Y-%m-%d')
            message += f"\n⏱️ *Создан:* {created_date}\n"
        
        if hasattr(user, 'updated_at') and user.updated_at:
            updated_date = user.updated_at
            if isinstance(updated_date, str):
                updated_date = updated_date[:10]
            else:
                updated_date = updated_date.strftime('%Y-%m-%d')
            message += f"🔄 *Обновлен:* {updated_date}\n"
        
        return message
        
    except Exception as e:
        logger.error(f"Error in format_user_details: {e}")
        # Fallback форматирование без Markdown
        return format_user_details_safe(user)

def format_user_details_safe(user):
    """Format user details for display without Markdown (safe fallback)"""
    try:
        # Базовая информация
        message = f"👤 Пользователь: {user.username}\n"
        message += f"🆔 UUID: {user.uuid}\n"
        
        # Статус
        status_emoji = "✅" if user.is_active else "❌"
        message += f"📊 Статус: {status_emoji} {'Активен' if user.is_active else 'Неактивен'}\n"
        
        # Трафик
        used_traffic = getattr(user, 'used_traffic', 0) or 0
        traffic_limit = getattr(user, 'traffic_limit', 0) or 0
        message += f"📈 Трафик: {format_bytes(used_traffic)}"
        if traffic_limit > 0:
            message += f"/{format_bytes(traffic_limit)}"
        else:
            message += "/Безлимитный"
        message += "\n"
        
        # Дата истечения
        if hasattr(user, 'expire_at') and user.expire_at:
            expire_text = str(user.expire_at)[:10] if isinstance(user.expire_at, str) else user.expire_at.strftime('%Y-%m-%d')
            message += f"📅 Истекает: {expire_text}\n"
        
        return message
        
    except Exception as e:
        logger.error(f"Error in format_user_details_safe: {e}")
        return f"👤 Пользователь: {getattr(user, 'username', 'Неизвестен')}\n🆔 UUID: {getattr(user, 'uuid', 'Неизвестен')}"

def format_node_details(node):
    """Format node details for display with remnawave SDK objects"""
    try:
        status_emoji = "🟢" if node.is_connected and not node.is_disabled else "🔴"

        message = f"*Информация о сервере*\n\n"
        message += f"{status_emoji} *Имя*: {escape_markdown(node.name)}\n"
        message += f"🆔 *UUID*: `{node.uuid}`\n"
        message += f"🌐 *Адрес*: {escape_markdown(node.address)}:{node.port}\n\n"

        message += f"📊 *Статус*:\n"
        message += f"  • Подключен: {'✅' if node.is_connected else '❌'}\n"
        message += f"  • Отключен: {'✅' if node.is_disabled else '❌'}\n"

        if hasattr(node, 'is_online'):
            message += f"  • Онлайн: {'✅' if node.is_online else '❌'}\n"

        if hasattr(node, 'xray_version') and node.xray_version:
            message += f"\n📦 *Версия Xray*: {escape_markdown(node.xray_version)}\n"

        message += f"🌍 *Страна*: {node.country_code}\n"
        
        if hasattr(node, 'consumption_multiplier'):
            message += f"📊 *Множитель потребления*: {node.consumption_multiplier}x\n"

        return message
        
    except Exception as e:
        logger.error(f"Error in format_node_details: {e}")
        return f"🖥️ Сервер: {getattr(node, 'name', 'Неизвестен')}\n🆔 UUID: {getattr(node, 'uuid', 'Неизвестен')}"

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return "Не указано"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def truncate_text(text: str, max_length: int = 30) -> str:
    """Truncate text to specified length"""
    if not text:
        return ""
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."
