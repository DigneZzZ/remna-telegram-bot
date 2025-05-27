from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from modules.handlers.auth import AuthFilter
from modules.handlers.states import InboundStates
from modules.api.client import RemnaAPI
from modules.api.inbounds import get_all_inbounds, get_inbound_by_uuid
from modules.utils.formatters_aiogram import (
    format_bytes, format_datetime, escape_markdown
)

logger = logging.getLogger(__name__)

router = Router()

# ================ UTILITY FUNCTIONS ================

def format_inbound_details(inbound: dict) -> str:
    """Format inbound details for display"""
    try:
        tag = escape_markdown(inbound.get('tag', 'Unknown'))
        inbound_id = inbound.get('id', 'N/A')
        uuid = inbound.get('uuid', 'N/A')
        protocol = inbound.get('protocol', 'Unknown')
        port = inbound.get('port', 'N/A')
        
        # Build details text
        details = f"🔌 **Inbound: {tag}**\n\n"
        
        # Basic information
        details += f"**📊 Основная информация:**\n"
        details += f"• ID: {inbound_id}\n"
        details += f"• UUID: `{uuid}`\n"
        details += f"• Протокол: {protocol}\n"
        details += f"• Порт: {port}\n"
        
        # Status
        is_enabled = inbound.get('isEnabled', True)
        status_emoji = "🟢" if is_enabled else "🔴"
        details += f"• Статус: {status_emoji} {'Включен' if is_enabled else 'Отключен'}\n"
        
        # Settings if available
        if inbound.get('settings'):
            details += f"\n**⚙️ Настройки:**\n"
            settings = inbound.get('settings', {})
            
            if isinstance(settings, dict):
                if settings.get('clients'):
                    clients_count = len(settings.get('clients', []))
                    details += f"• Клиентов: {clients_count}\n"
                
                if settings.get('decryption'):
                    details += f"• Шифрование: {settings.get('decryption')}\n"
                
                if settings.get('network'):
                    details += f"• Сеть: {settings.get('network')}\n"
        
        # Stream settings if available
        if inbound.get('streamSettings'):
            details += f"\n**🌐 Потоковые настройки:**\n"
            stream = inbound.get('streamSettings', {})
            
            if isinstance(stream, dict):
                if stream.get('network'):
                    details += f"• Сеть: {stream.get('network')}\n"
                
                if stream.get('security'):
                    details += f"• Безопасность: {stream.get('security')}\n"
                
                # TLS settings
                if stream.get('tlsSettings'):
                    tls = stream.get('tlsSettings', {})
                    if tls.get('serverName'):
                        details += f"• Сервер: {escape_markdown(tls.get('serverName'))}\n"
        
        # Created/Updated timestamps
        if inbound.get('createdAt'):
            details += f"\n**📅 Временные метки:**\n"
            details += f"• Создан: {format_datetime(inbound.get('createdAt'))}\n"
        
        if inbound.get('updatedAt'):
            details += f"• Обновлен: {format_datetime(inbound.get('updatedAt'))}\n"
        
        return details
        
    except Exception as e:
        logger.error(f"Error formatting inbound details: {e}")
        return f"❌ Ошибка форматирования данных inbound: {e}"

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
    builder.row(types.InlineKeyboardButton(text="📊 Статистика Inbounds", callback_data="inbounds_stats"))
    builder.row(types.InlineKeyboardButton(text="➕ Создать Inbound", callback_data="create_inbound"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "🔌 **Управление Inbounds**\n\n"
    
    try:
        # Получаем краткую статистику для превью
        inbounds_list = await get_all_inbounds()
        
        if inbounds_list:
            total_inbounds = len(inbounds_list)
            active_inbounds = sum(1 for inbound in inbounds_list if inbound.get('isEnabled', True))
            
            message += f"**📈 Статистика:**\n"
            message += f"• Всего Inbounds: {total_inbounds}\n"
            message += f"• Активных: {active_inbounds}\n"
            message += f"• Неактивных: {total_inbounds - active_inbounds}\n\n"
        else:
            message += f"**📈 Статистика:** Недоступна\n\n"
        
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
        inbounds_list = await get_all_inbounds()
        
        if not inbounds_list:
            await callback.message.edit_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
                ]])
            )
            return
        
        # Сохраняем список в состоянии для пагинации
        await state.update_data(inbounds=inbounds_list, page=0)
        await state.set_state(InboundStates.selecting_inbound)
        
        await show_inbounds_page(callback.message, inbounds_list, 0, state)
        
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
        tag = inbound.get('tag', 'Unknown')
        protocol = inbound.get('protocol', 'Unknown')
        port = inbound.get('port', 'N/A')
        
        # Статус
        status_emoji = "🟢" if inbound.get('isEnabled', True) else "🔴"
        
        inbound_name = f"{status_emoji} {tag}"
        inbound_info = f" ({protocol}, :{port})"
        
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
        types.InlineKeyboardButton(text="📊 Статистика", callback_data="inbounds_stats")
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
    except Exception:
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

# ================ VIEW INBOUND DETAILS ================

@router.callback_query(F.data.startswith("view_inbound:"), AuthFilter())
async def view_inbound(callback: types.CallbackQuery, state: FSMContext):
    """View inbound details"""
    await callback.answer()
    
    inbound_uuid = callback.data.split(":", 1)[1]
    await show_inbound_details(callback.message, inbound_uuid, state)

async def show_inbound_details(message: types.Message, uuid: str, state: FSMContext):
    """Show inbound details"""
    try:
        # Получаем детальную информацию об inbound
        inbound = await get_inbound_by_uuid(uuid)
        
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
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_inbound:{uuid}"),
            types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_inbound:{uuid}")
        )
        
        # Состояние inbound'а
        is_enabled = inbound.get('isEnabled', True)
        if is_enabled:
            builder.row(types.InlineKeyboardButton(text="⏸️ Отключить", callback_data=f"disable_inbound:{uuid}"))
        else:
            builder.row(types.InlineKeyboardButton(text="▶️ Включить", callback_data=f"enable_inbound:{uuid}"))
        
        # Управление (placeholder функции)
        builder.row(
            types.InlineKeyboardButton(text="👥 Пользователи", callback_data=f"inbound_users:{uuid}"),
            types.InlineKeyboardButton(text="🖥️ Серверы", callback_data=f"inbound_nodes:{uuid}")
        )
        
        # Дополнительные функции
        builder.row(
            types.InlineKeyboardButton(text="📋 Экспорт", callback_data=f"export_inbound:{uuid}"),
            types.InlineKeyboardButton(text="📊 Статистика", callback_data=f"inbound_stats:{uuid}")
        )
        
        # Опасные действия
        builder.row(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_inbound:{uuid}"))
        
        # Навигация
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="list_inbounds"))
        
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

@router.callback_query(F.data.startswith("enable_inbound:"), AuthFilter())
async def enable_inbound(callback: types.CallbackQuery, state: FSMContext):
    """Enable inbound"""
    await callback.answer("▶️ Включение Inbound...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        # Используем прямой HTTP вызов для включения inbound
        api_client = RemnaAPI()
        result = await api_client.put(f"inbounds/{uuid}/enable")
        
        if result:
            await callback.answer("✅ Inbound включен", show_alert=True)
            # Обновляем информацию об inbound
            await show_inbound_details(callback.message, uuid, state)
        else:
            await callback.answer("❌ Ошибка при включении", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error enabling inbound: {e}")
        await callback.answer("❌ Ошибка при включении Inbound", show_alert=True)

@router.callback_query(F.data.startswith("disable_inbound:"), AuthFilter())
async def disable_inbound(callback: types.CallbackQuery, state: FSMContext):
    """Disable inbound"""
    await callback.answer("⏸️ Отключение Inbound...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        # Используем прямой HTTP вызов для отключения inbound
        api_client = RemnaAPI()
        result = await api_client.put(f"inbounds/{uuid}/disable")
        
        if result:
            await callback.answer("⏸️ Inbound отключен", show_alert=True)
            # Обновляем информацию об inbound
            await show_inbound_details(callback.message, uuid, state)
        else:
            await callback.answer("❌ Ошибка при отключении", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error disabling inbound: {e}")
        await callback.answer("❌ Ошибка при отключении Inbound", show_alert=True)

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
        f"Inbound будет удален из системы.\n\n"
        f"Продолжить?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("confirm_delete_inbound:"), AuthFilter())
async def confirm_delete_inbound(callback: types.CallbackQuery, state: FSMContext):
    """Confirm inbound deletion"""
    await callback.answer("🗑️ Удаление Inbound...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        # Используем прямой HTTP вызов для удаления inbound
        api_client = RemnaAPI()
        result = await api_client.delete(f"inbounds/{uuid}")
        
        if result:
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
        inbounds_list = await get_all_inbounds()
        
        if not inbounds_list:
            await callback.message.edit_text(
                "❌ Не удалось получить статистику Inbounds",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
                ]])
            )
            return
        
        # Анализируем данные
        total_inbounds = len(inbounds_list)
        enabled_inbounds = sum(1 for ib in inbounds_list if ib.get('isEnabled', True))
        disabled_inbounds = total_inbounds - enabled_inbounds
        
        # Статистика по протоколам
        protocol_stats = {}
        port_usage = {}
        
        for inbound in inbounds_list:
            # Статистика по протоколам
            protocol = inbound.get('protocol', 'Unknown')
            if protocol not in protocol_stats:
                protocol_stats[protocol] = {'total': 0, 'enabled': 0}
            protocol_stats[protocol]['total'] += 1
            if inbound.get('isEnabled', True):
                protocol_stats[protocol]['enabled'] += 1
            
            # Статистика по портам
            port = inbound.get('port')
            if port:
                if port not in port_usage:
                    port_usage[port] = 0
                port_usage[port] += 1
        
        # Формируем сообщение
        message_text = "📊 **Статистика Inbounds**\n\n"
        
        # Общая статистика
        message_text += "**📈 Общая статистика:**\n"
        message_text += f"• Всего Inbounds: {total_inbounds}\n"
        message_text += f"• Включенных: {enabled_inbounds}\n"
        message_text += f"• Отключенных: {disabled_inbounds}\n\n"
        
        # Статистика по протоколам
        if protocol_stats:
            message_text += "**🔧 По протоколам:**\n"
            for protocol, stats in sorted(protocol_stats.items()):
                percentage = (stats['total'] / total_inbounds) * 100
                message_text += f"• {protocol}: {stats['enabled']}/{stats['total']} ({percentage:.1f}%)\n"
            message_text += "\n"
        
        # Наиболее используемые порты
        if port_usage:
            sorted_ports = sorted(port_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            message_text += "**🔢 Популярные порты:**\n"
            for port, count in sorted_ports:
                message_text += f"• Порт {port}: {count} inbound(ов)\n"
            message_text += "\n"
        
        # Дополнительная аналитика
        if total_inbounds > 0:
            enabled_percentage = (enabled_inbounds / total_inbounds) * 100
            message_text += f"**📊 Анализ:**\n"
            message_text += f"• Процент активных: {enabled_percentage:.1f}%\n"
            
            if disabled_inbounds > 0:
                message_text += f"• ⚠️ Есть отключенные inbound'ы\n"
            
            if len(set(port for ib in inbounds_list if ib.get('port'))) != len([ib for ib in inbounds_list if ib.get('port')]):
                message_text += f"• ⚠️ Есть дублирующиеся порты\n"
        
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

# ================ PLACEHOLDER HANDLERS ================

@router.callback_query(F.data == "create_inbound", AuthFilter())
async def create_inbound_placeholder(callback: types.CallbackQuery):
    """Create inbound placeholder"""
    await callback.answer()
    
    await callback.message.edit_text(
        "➕ **Создание Inbound**\n\n"
        "🔧 Функция создания Inbound в разработке\n\n"
        "Планируется реализация:\n"
        "• Выбор протокола и настроек\n"
        "• Автоматическое назначение портов\n"
        "• Шаблоны конфигурации\n"
        "• Валидация параметров",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="📋 К списку Inbounds", callback_data="list_inbounds"),
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="inbounds")
        ]])
    )

@router.callback_query(F.data.startswith("edit_inbound:"), AuthFilter())
async def edit_inbound_placeholder(callback: types.CallbackQuery, state: FSMContext):
    """Edit inbound placeholder"""
    await callback.answer()
    
    uuid = callback.data.split(":", 1)[1]
    
    await callback.message.edit_text(
        "✏️ **Редактирование Inbound**\n\n"
        "🔧 Функция редактирования Inbound в разработке\n\n"
        "Доступные операции:\n"
        "• Включение/отключение\n"
        "• Просмотр статистики\n"
        "• Экспорт конфигурации\n"
        "• Удаление",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 К Inbound", callback_data=f"view_inbound:{uuid}"),
            types.InlineKeyboardButton(text="📋 К списку", callback_data="list_inbounds")
        ]])
    )

@router.callback_query(F.data.startswith(("inbound_users:", "inbound_nodes:", "export_inbound:", "inbound_stats:")), AuthFilter())
async def handle_inbound_features_placeholder(callback: types.CallbackQuery):
    """Handle placeholder inbound features"""
    await callback.answer()
    
    action = callback.data.split(":", 1)[0]
    uuid = callback.data.split(":", 1)[1]
    
    feature_names = {
        "inbound_users": "Управление пользователями",
        "inbound_nodes": "Управление серверами",
        "export_inbound": "Экспорт конфигурации",
        "inbound_stats": "Детальная статистика"
    }
    
    feature_name = feature_names.get(action, "Функция")
    
    await callback.message.edit_text(
        f"🔧 **{feature_name}**\n\n"
        f"Функция в разработке\n\n"
        f"Планируется реализация:\n"
        f"• Полный функционал управления\n"
        f"• Интеграция с API\n"
        f"• Расширенные возможности\n"
        f"• Детальная аналитика",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 К Inbound", callback_data=f"view_inbound:{uuid}")
        ]])
    )

# ================ NO-OP CALLBACK ================

@router.callback_query(F.data == "noop", AuthFilter())
async def noop_callback(callback: types.CallbackQuery):
    """No-operation callback for pagination display"""
    await callback.answer()

logger.info("Inbound handlers module loaded successfully (SDK-free version)")