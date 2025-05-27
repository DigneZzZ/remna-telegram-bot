from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from modules.handlers.auth import AuthFilter
from modules.handlers.states import HostStates
from modules.api.client import RemnaAPI
from modules.api.hosts import get_all_hosts, get_host_by_uuid
from modules.utils.formatters_aiogram import (
    format_bytes, format_datetime, escape_markdown
)

logger = logging.getLogger(__name__)

router = Router()

# ================ HOST MENU ================

@router.callback_query(F.data == "hosts", AuthFilter())
async def handle_hosts_menu(callback: types.CallbackQuery, state: FSMContext):
    """Handle hosts menu selection"""
    await callback.answer()
    await state.clear()
    await show_hosts_menu(callback)

async def show_hosts_menu(callback: types.CallbackQuery):
    """Show hosts menu"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📋 Список всех хостов", callback_data="list_hosts"))
    builder.row(types.InlineKeyboardButton(text="📊 Статистика хостов", callback_data="hosts_stats"))
    builder.row(types.InlineKeyboardButton(text="➕ Создать хост", callback_data="create_host"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "🌐 **Управление хостами**\n\n"
    
    try:
        # Получаем краткую статистику для превью
        hosts_list = await get_all_hosts()
        
        if hosts_list:
            total_hosts = len(hosts_list)
            active_hosts = sum(1 for host in hosts_list if host.get('isActive', True))
            
            message += f"**📈 Статистика:**\n"
            message += f"• Всего хостов: {total_hosts}\n"
            message += f"• Активных: {active_hosts}\n"
            message += f"• Неактивных: {total_hosts - active_hosts}\n\n"
        else:
            message += f"**📈 Статистика:** Недоступна\n\n"
        
    except Exception as e:
        logger.error(f"Error getting hosts stats: {e}")
        message += "**📈 Статистика:** Недоступна\n\n"
    
    message += "Выберите действие:"

    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

# ================ LIST HOSTS ================

@router.callback_query(F.data == "list_hosts", AuthFilter())
async def list_hosts(callback: types.CallbackQuery, state: FSMContext):
    """List all hosts"""
    await callback.answer()
    await callback.message.edit_text("🌐 Загрузка списка хостов...")

    try:
        hosts_list = await get_all_hosts()

        if not hosts_list:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts"))
            
            await callback.message.edit_text(
                "❌ Хосты не найдены или ошибка при получении списка.",
                reply_markup=builder.as_markup()
            )
            return

        # Сохраняем список в состоянии для пагинации
        await state.update_data(hosts=hosts_list, page=0)
        await state.set_state(HostStates.selecting_host)
        
        await show_hosts_page(callback.message, hosts_list, 0, state)

    except Exception as e:
        logger.error(f"Error listing hosts: {e}")
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts"))
        
        await callback.message.edit_text(
            "❌ Ошибка при получении списка хостов.",
            reply_markup=builder.as_markup()
        )

async def show_hosts_page(message: types.Message, hosts: list, page: int, state: FSMContext, per_page: int = 8):
    """Show hosts page with pagination"""
    total_pages = (len(hosts) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_hosts = hosts[start_idx:end_idx]
    
    builder = InlineKeyboardBuilder()
    
    # Список хостов на текущей странице
    for host in page_hosts:
        remark = host.get('remark', 'Unknown')
        address = host.get('address', 'Unknown')
        port = host.get('port', 'N/A')
        
        # Статус
        status_emoji = "🟢" if host.get('isActive', True) else "🔴"
        
        host_name = f"{status_emoji} {remark}"
        host_info = f" ({address}:{port})"
        
        if len(host_name + host_info) > 60:
            display_name = host_name[:50] + "..."
        else:
            display_name = host_name + host_info
        
        builder.row(types.InlineKeyboardButton(
            text=display_name,
            callback_data=f"view_host:{host.get('uuid', '')}"
        ))
    
    # Пагинация
    if total_pages > 1:
        pagination_buttons = []
        
        if page > 0:
            pagination_buttons.append(types.InlineKeyboardButton(
                text="◀️ Пред",
                callback_data=f"hosts_page:{page-1}"
            ))
        
        pagination_buttons.append(types.InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="noop"
        ))
        
        if page < total_pages - 1:
            pagination_buttons.append(types.InlineKeyboardButton(
                text="След ▶️",
                callback_data=f"hosts_page:{page+1}"
            ))
        
        builder.row(*pagination_buttons)
    
    # Кнопки управления
    builder.row(
        types.InlineKeyboardButton(text="🔄 Обновить", callback_data="list_hosts"),
        types.InlineKeyboardButton(text="📊 Статистика", callback_data="hosts_stats")
    )
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts"))
    
    message_text = f"🌐 **Список хостов** ({len(hosts)} всего)\n"
    message_text += f"📄 Страница {page + 1} из {total_pages}\n\n"
    message_text += "Выберите хост для просмотра подробной информации:"
    
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

@router.callback_query(F.data.startswith("hosts_page:"), AuthFilter())
async def handle_hosts_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Handle hosts pagination"""
    await callback.answer()
    
    page = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    hosts = data.get('hosts', [])
    
    await state.update_data(page=page)
    await show_hosts_page(callback.message, hosts, page, state)

# ================ HOST DETAILS ================

@router.callback_query(F.data.startswith("view_host:"), AuthFilter())
async def show_host_details(callback: types.CallbackQuery, state: FSMContext):
    """Show host details"""
    await callback.answer()
    
    try:
        uuid = callback.data.split(":", 1)[1]
        
        host = await get_host_by_uuid(uuid)
        
        if not host:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_hosts"))
            
            await callback.message.edit_text(
                "❌ Хост не найден или ошибка при получении данных.",
                reply_markup=builder.as_markup()
            )
            return
        
        # Сохраняем текущий хост в состоянии
        await state.update_data(selected_host=host)
        await state.set_state(HostStates.viewing_host)
        
        # Format host details
        message = f"🌐 **Детали хоста**\n\n"
        message += f"**📝 Название:** {escape_markdown(host.get('remark', 'Unknown'))}\n"
        message += f"**🌐 Адрес:** `{host.get('address', 'Unknown')}`\n"
        message += f"**🔌 Порт:** `{host.get('port', 'N/A')}`\n"
        message += f"**📊 Статус:** {'🟢 Активен' if host.get('isActive', True) else '🔴 Неактивен'}\n"
        
        if host.get('inboundUuid'):
            message += f"**🔌 Inbound UUID:** `{host.get('inboundUuid')}`\n"
        
        if host.get('path'):
            message += f"**🛣️ Путь:** `{host.get('path')}`\n"
            
        if host.get('sni'):
            message += f"**🔒 SNI:** `{host.get('sni')}`\n"
            
        if host.get('hostHeader'):
            message += f"**🏠 Host:** `{host.get('hostHeader')}`\n"
            
        if host.get('alpn'):
            message += f"**🔄 ALPN:** `{host.get('alpn')}`\n"
            
        if host.get('fingerprint'):
            message += f"**👆 Fingerprint:** `{host.get('fingerprint')}`\n"
            
        if host.get('allowInsecure') is not None:
            message += f"**🔐 Allow Insecure:** {'Да' if host.get('allowInsecure') else 'Нет'}\n"
            
        if host.get('securityLayer'):
            message += f"**🛡️ Security Layer:** `{host.get('securityLayer')}`\n"
        
        # Временные метки
        if host.get('createdAt'):
            message += f"\n**📅 Временные метки:**\n"
            message += f"• Создан: {format_datetime(host.get('createdAt'))}\n"
        
        if host.get('updatedAt'):
            message += f"• Обновлен: {format_datetime(host.get('updatedAt'))}\n"
        
        # Create action buttons
        builder = InlineKeyboardBuilder()
        
        if host.get('isActive', True):
            builder.row(types.InlineKeyboardButton(text="🔴 Отключить", callback_data=f"disable_host:{uuid}"))
        else:
            builder.row(types.InlineKeyboardButton(text="🟢 Включить", callback_data=f"enable_host:{uuid}"))
        
        builder.row(
            types.InlineKeyboardButton(text="📝 Редактировать", callback_data=f"edit_host:{uuid}"),
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_host:{uuid}")
        )
        builder.row(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_host:{uuid}"))
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="list_hosts"))
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error showing host details: {e}")
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_hosts"))
        
        await callback.message.edit_text(
            "❌ Ошибка при получении данных хоста.",
            reply_markup=builder.as_markup()
        )

# ================ HOST ACTIONS ================

@router.callback_query(F.data.startswith("enable_host:"), AuthFilter())
async def enable_host(callback: types.CallbackQuery, state: FSMContext):
    """Enable host"""
    await callback.answer("🟢 Включение хоста...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        # Используем прямой HTTP вызов для включения хоста
        api_client = RemnaAPI()
        result = await api_client.put(f"hosts/{uuid}/enable")
        
        if result:
            await callback.answer("✅ Хост включен", show_alert=True)
            # Обновляем информацию о хосте
            callback.data = f"view_host:{uuid}"
            await show_host_details(callback, state)
        else:
            await callback.answer("❌ Ошибка при включении", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error enabling host: {e}")
        await callback.answer("❌ Ошибка при включении хоста", show_alert=True)

@router.callback_query(F.data.startswith("disable_host:"), AuthFilter())
async def disable_host(callback: types.CallbackQuery, state: FSMContext):
    """Disable host"""
    await callback.answer("🔴 Отключение хоста...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        # Используем прямой HTTP вызов для отключения хоста
        api_client = RemnaAPI()
        result = await api_client.put(f"hosts/{uuid}/disable")
        
        if result:
            await callback.answer("⏸️ Хост отключен", show_alert=True)
            # Обновляем информацию о хосте
            callback.data = f"view_host:{uuid}"
            await show_host_details(callback, state)
        else:
            await callback.answer("❌ Ошибка при отключении", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error disabling host: {e}")
        await callback.answer("❌ Ошибка при отключении хоста", show_alert=True)

@router.callback_query(F.data.startswith("refresh_host:"), AuthFilter())
async def refresh_host(callback: types.CallbackQuery, state: FSMContext):
    """Refresh host details"""
    await callback.answer("🔄 Обновление данных...")
    
    uuid = callback.data.split(":", 1)[1]
    callback.data = f"view_host:{uuid}"
    await show_host_details(callback, state)

@router.callback_query(F.data.startswith("delete_host:"), AuthFilter())
async def delete_host_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm host deletion"""
    await callback.answer()
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        # Получаем информацию о хосте
        host = await get_host_by_uuid(uuid)
        
        if not host:
            await callback.answer("❌ Хост не найден", show_alert=True)
            return
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(
            text="🗑️ Да, удалить",
            callback_data=f"confirm_delete_host:{uuid}"
        ))
        builder.row(types.InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"view_host:{uuid}"
        ))
        
        message = f"🗑️ **Подтверждение удаления хоста**\n\n"
        message += f"**Хост:** {escape_markdown(host.get('remark', 'Unknown'))}\n"
        message += f"**Адрес:** `{host.get('address')}:{host.get('port')}`\n\n"
        message += f"⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n"
        message += f"Хост будет удален из системы.\n\n"
        message += f"Продолжить?"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error preparing host deletion: {e}")
        await callback.answer("❌ Ошибка при подготовке удаления", show_alert=True)

@router.callback_query(F.data.startswith("confirm_delete_host:"), AuthFilter())
async def confirm_delete_host(callback: types.CallbackQuery, state: FSMContext):
    """Delete host after confirmation"""
    await callback.answer("🗑️ Удаление хоста...")
    
    uuid = callback.data.split(":", 1)[1]
    
    try:
        # Используем прямой HTTP вызов для удаления хоста
        api_client = RemnaAPI()
        result = await api_client.delete(f"hosts/{uuid}")
        
        if result:
            await callback.answer("✅ Хост удален", show_alert=True)
            await state.clear()
            
            await callback.message.edit_text(
                "✅ **Хост успешно удален**\n\n"
                "Хост был удален из системы.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="📋 К списку хостов", callback_data="list_hosts"),
                    types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
                ]])
            )
        else:
            await callback.answer("❌ Ошибка при удалении", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error deleting host: {e}")
        await callback.answer("❌ Ошибка при удалении хоста", show_alert=True)

# ================ EDIT HOST ================

@router.callback_query(F.data.startswith("edit_host:"), AuthFilter())
async def start_edit_host(callback: types.CallbackQuery, state: FSMContext):
    """Start editing a host"""
    await callback.answer()
    
    try:
        uuid = callback.data.split(":", 1)[1]
        
        # Get host details
        host = await get_host_by_uuid(uuid)
        
        if not host:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_hosts"))
            
            await callback.message.edit_text(
                "❌ Хост не найден.",
                reply_markup=builder.as_markup()
            )
            return
        
        # Store host data in state
        await state.update_data(editing_host=host, host_uuid=uuid)
        await state.set_state(HostStates.editing)
        
        # Create edit menu
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📝 Название", callback_data=f"eh_remark:{uuid}"))
        builder.row(types.InlineKeyboardButton(text="🌐 Адрес", callback_data=f"eh_address:{uuid}"))
        builder.row(types.InlineKeyboardButton(text="🔌 Порт", callback_data=f"eh_port:{uuid}"))
        
        # Optional fields
        if host.get('path') is not None:
            builder.row(types.InlineKeyboardButton(text="🛣️ Путь", callback_data=f"eh_path:{uuid}"))
        if host.get('sni') is not None:
            builder.row(types.InlineKeyboardButton(text="🔒 SNI", callback_data=f"eh_sni:{uuid}"))
        if host.get('hostHeader') is not None:
            builder.row(types.InlineKeyboardButton(text="🏠 Host", callback_data=f"eh_hostHeader:{uuid}"))
        
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к деталям", callback_data=f"view_host:{uuid}"))
        
        message = f"📝 **Редактирование хоста: {escape_markdown(host.get('remark', 'Unknown'))}**\n\n"
        message += f"📌 **Текущие значения:**\n"
        message += f"• Название: `{host.get('remark', 'Unknown')}`\n"
        message += f"• Адрес: `{host.get('address', 'Unknown')}`\n"
        message += f"• Порт: `{host.get('port', 'N/A')}`\n"
        
        if host.get('path'):
            message += f"• Путь: `{host.get('path')}`\n"
        if host.get('sni'):
            message += f"• SNI: `{host.get('sni')}`\n"
        if host.get('hostHeader'):
            message += f"• Host: `{host.get('hostHeader')}`\n"
        
        message += "\nВыберите поле для редактирования:"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error starting host edit: {e}")
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_hosts"))
        
        await callback.message.edit_text(
            "❌ Ошибка при загрузке данных хоста.",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("eh_"), StateFilter(HostStates.editing), AuthFilter())
async def start_edit_host_field(callback: types.CallbackQuery, state: FSMContext):
    """Start editing a specific host field"""
    await callback.answer()
    
    try:
        parts = callback.data.split(":", 1)
        field = parts[0].replace("eh_", "")  # remark, address, port, etc.
        uuid = parts[1]
        
        data = await state.get_data()
        host = data.get("editing_host")
        
        if not host:
            await callback.answer("❌ Данные хоста потеряны", show_alert=True)
            return
        
        # Store field being edited
        await state.update_data(editing_field=field)
        await state.set_state(HostStates.editing_field)
        
        # Get field info
        field_info = {
            "remark": {
                "title": "Название хоста",
                "current": host.get("remark", ""),
                "example": "Например: Main-Host",
                "validation": "текст (обязательно)"
            },
            "address": {
                "title": "Адрес хоста",
                "current": host.get("address", ""),
                "example": "Например: 192.168.1.1 или example.com",
                "validation": "IP адрес или домен (обязательно)"
            },
            "port": {
                "title": "Порт хоста",
                "current": str(host.get("port", "")),
                "example": "Например: 443",
                "validation": "число от 1 до 65535"
            },
            "path": {
                "title": "Путь",
                "current": host.get("path", ""),
                "example": "Например: /api/v1",
                "validation": "путь (может быть пустым)"
            },
            "sni": {
                "title": "SNI (Server Name Indication)",
                "current": host.get("sni", ""),
                "example": "Например: example.com",
                "validation": "доменное имя (может быть пустым)"
            },
            "hostHeader": {
                "title": "Host заголовок",
                "current": host.get("hostHeader", ""),
                "example": "Например: api.example.com",
                "validation": "доменное имя (может быть пустым)"
            }
        }
        
        if field not in field_info:
            await callback.answer("❌ Неизвестное поле", show_alert=True)
            return
        
        info = field_info[field]
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_host:{uuid}"))
        
        message = f"📝 **Редактирование: {info['title']}**\n\n"
        message += f"📌 **Текущее значение:** `{info['current']}`\n\n"
        message += f"💡 {info['example']}\n"
        message += f"✅ **Формат:** {info['validation']}\n\n"
        message += f"✍️ **Введите новое значение:**"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error starting field edit: {e}")
        await callback.answer("❌ Ошибка при подготовке редактирования", show_alert=True)

@router.message(StateFilter(HostStates.editing_field), AuthFilter())
async def handle_host_field_input(message: types.Message, state: FSMContext):
    """Handle input for host field editing"""
    try:
        data = await state.get_data()
        host = data.get("editing_host")
        field = data.get("editing_field")
        uuid = data.get("host_uuid")
        
        if not host or not field or not uuid:
            await message.answer("❌ Ошибка: данные редактирования потеряны.")
            await state.clear()
            return
        
        user_input = message.text.strip()
        
        # Validate input based on field type
        validated_value = None
        error_message = None
        
        if field == "remark":
            if len(user_input) < 1:
                error_message = "Название не может быть пустым."
            elif len(user_input) > 100:
                error_message = "Название слишком длинное (максимум 100 символов)."
            else:
                validated_value = user_input
        
        elif field == "address":
            if len(user_input) < 1:
                error_message = "Адрес не может быть пустым."
            else:
                validated_value = user_input
        
        elif field == "port":
            try:
                port_num = int(user_input)
                if port_num < 1 or port_num > 65535:
                    error_message = "Порт должен быть от 1 до 65535."
                else:
                    validated_value = port_num
            except ValueError:
                error_message = "Порт должен быть числом."
        
        elif field in ["path", "sni", "hostHeader"]:
            # These fields can be empty
            validated_value = user_input if user_input else ""
        
        if error_message:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_host:{uuid}"))
            
            await message.answer(
                f"❌ {error_message}\n\nПопробуйте еще раз:",
                reply_markup=builder.as_markup()
            )
            return
        
        # Update host via HTTP API
        try:
            api_client = RemnaAPI()
            update_data = {field: validated_value}
            
            result = await api_client.put(f"hosts/{uuid}", update_data)
            
            if result:
                # Update stored host data
                host[field] = validated_value
                await state.update_data(editing_host=host)
                
                # Clear editing state
                await state.set_state(HostStates.editing)
                
                builder = InlineKeyboardBuilder()
                builder.row(types.InlineKeyboardButton(text="✅ Продолжить редактирование", callback_data=f"edit_host:{uuid}"))
                builder.row(types.InlineKeyboardButton(text="📋 Показать детали", callback_data=f"view_host:{uuid}"))
                builder.row(types.InlineKeyboardButton(text="🔙 К списку хостов", callback_data="list_hosts"))
                
                await message.answer(
                    f"✅ Поле '{field}' успешно обновлено!",
                    reply_markup=builder.as_markup()
                )
                
            else:
                builder = InlineKeyboardBuilder()
                builder.row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"eh_{field}:{uuid}"))
                builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_host:{uuid}"))
                
                await message.answer(
                    "❌ Ошибка при обновлении хоста. Проверьте данные и попробуйте снова.",
                    reply_markup=builder.as_markup()
                )
                
        except Exception as e:
            logger.error(f"Error updating host via API: {e}")
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_host:{uuid}"))
            
            await message.answer(
                "❌ Ошибка при обновлении хоста через API.",
                reply_markup=builder.as_markup()
            )
            
    except Exception as e:
        logger.error(f"Error handling host field input: {e}")
        await message.answer("❌ Произошла ошибка при обработке ввода.")
        await state.clear()

@router.callback_query(F.data.startswith("cancel_edit_host:"), AuthFilter())
async def handle_cancel_host_edit(callback: types.CallbackQuery, state: FSMContext):
    """Handle canceling host edit"""
    await callback.answer()
    
    try:
        uuid = callback.data.split(":", 1)[1]
        
        # Clear editing state
        await state.clear()
        
        # Return to host details
        callback.data = f"view_host:{uuid}"
        await show_host_details(callback, state)
        
    except Exception as e:
        logger.error(f"Error canceling host edit: {e}")
        await callback.answer("❌ Ошибка при отмене редактирования", show_alert=True)

# ================ HOSTS STATISTICS ================

@router.callback_query(F.data == "hosts_stats", AuthFilter())
async def show_hosts_statistics(callback: types.CallbackQuery):
    """Show hosts statistics"""
    await callback.answer()
    await callback.message.edit_text("📊 Загрузка статистики хостов...")
    
    try:
        hosts_list = await get_all_hosts()
        
        if not hosts_list:
            await callback.message.edit_text(
                "❌ Не удалось получить статистику хостов",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts")
                ]])
            )
            return
        
        # Анализируем данные
        total_hosts = len(hosts_list)
        active_hosts = sum(1 for host in hosts_list if host.get('isActive', True))
        inactive_hosts = total_hosts - active_hosts
        
        # Статистика по портам
        port_usage = {}
        inbound_stats = {}
        
        for host in hosts_list:
            # Статистика по портам
            port = host.get('port')
            if port:
                if port not in port_usage:
                    port_usage[port] = 0
                port_usage[port] += 1
            
            # Статистика по inbound'ам
            inbound_uuid = host.get('inboundUuid')
            if inbound_uuid:
                if inbound_uuid not in inbound_stats:
                    inbound_stats[inbound_uuid] = {'total': 0, 'active': 0}
                inbound_stats[inbound_uuid]['total'] += 1
                if host.get('isActive', True):
                    inbound_stats[inbound_uuid]['active'] += 1
        
        # Формируем сообщение
        message_text = "📊 **Статистика хостов**\n\n"
        
        # Общая статистика
        message_text += "**📈 Общая статистика:**\n"
        message_text += f"• Всего хостов: {total_hosts}\n"
        message_text += f"• Активных: {active_hosts}\n"
        message_text += f"• Неактивных: {inactive_hosts}\n\n"
        
        # Статистика по портам
        if port_usage:
            sorted_ports = sorted(port_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            message_text += "**🔢 Популярные порты:**\n"
            for port, count in sorted_ports:
                message_text += f"• Порт {port}: {count} хост(ов)\n"
            message_text += "\n"
        
        # Статистика по inbound'ам
        if inbound_stats:
            message_text += "**🔌 По Inbound'ам:**\n"
            for inbound_uuid, stats in list(inbound_stats.items())[:5]:
                short_uuid = inbound_uuid[:8] + "..." if len(inbound_uuid) > 8 else inbound_uuid
                message_text += f"• {short_uuid}: {stats['active']}/{stats['total']}\n"
            
            if len(inbound_stats) > 5:
                message_text += f"• ... и еще {len(inbound_stats) - 5}\n"
            message_text += "\n"
        
        # Дополнительная аналитика
        if total_hosts > 0:
            active_percentage = (active_hosts / total_hosts) * 100
            message_text += f"**📊 Анализ:**\n"
            message_text += f"• Процент активных: {active_percentage:.1f}%\n"
            
            if inactive_hosts > 0:
                message_text += f"• ⚠️ Есть неактивные хосты\n"
            
            # Проверяем дублирующиеся порты
            duplicate_ports = [port for port, count in port_usage.items() if count > 1]
            if duplicate_ports:
                message_text += f"• ⚠️ Дублирующиеся порты: {len(duplicate_ports)}\n"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="hosts_stats"),
            types.InlineKeyboardButton(text="📋 Список", callback_data="list_hosts")
        )
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts"))
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting hosts statistics: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики хостов",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts")
            ]])
        )

# ================ CREATE HOST ================

@router.callback_query(F.data == "create_host", AuthFilter())
async def create_host_menu(callback: types.CallbackQuery, state: FSMContext):
    """Show create host menu"""
    await callback.answer()
    
    await state.set_state(HostStates.creating_host)
    await state.set_state(HostStates.entering_host_name)
    
    await callback.message.edit_text(
        "➕ **Создание нового хоста**\n\n"
        "**Шаг 1 из 4:** Название хоста\n\n"
        "Введите название для нового хоста:\n"
        "Например: `Main Server Host`\n\n"
        "💡 Название поможет легко идентифицировать хост в списке",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts")
        ]])
    )

@router.message(StateFilter(HostStates.entering_host_name), AuthFilter())
async def handle_host_name(message: types.Message, state: FSMContext):
    """Handle host name input"""
    remark = message.text.strip()
    
    if not remark or len(remark) < 2:
        await message.answer(
            "❌ Название должно содержать минимум 2 символа.\n"
            "Попробуйте еще раз:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts")
            ]])
        )
        return
    
    if len(remark) > 50:
        await message.answer(
            "❌ Название слишком длинное (максимум 50 символов).\n"
            "Попробуйте еще раз:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts")
            ]])
        )
        return
    
    await state.update_data(create_remark=remark)
    await state.set_state(HostStates.entering_host_address)
    
    await message.answer(
        f"➕ **Создание хоста**\n\n"
        f"**Шаг 2 из 4:** Адрес хоста\n\n"
        f"**Название:** {escape_markdown(remark)}\n\n"
        f"Введите адрес хоста:\n"
        f"• IP адрес: `192.168.1.1`\n"
        f"• Домен: `example.com`\n\n"
        f"💡 Убедитесь, что адрес доступен и корректен",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts")
        ]])
    )

@router.message(StateFilter(HostStates.entering_host_address), AuthFilter())
async def handle_host_address(message: types.Message, state: FSMContext):
    """Handle host address input"""
    address = message.text.strip()
    
    if not address or len(address) < 1:
        await message.answer(
            "❌ Адрес не может быть пустым.\n"
            "Попробуйте еще раз:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts")
            ]])
        )
        return
    
    await state.update_data(create_address=address)
    await state.set_state(HostStates.entering_host_port)
    
    data = await state.get_data()
    remark = data.get('create_remark')
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Использовать 443", callback_data="use_default_host_port:443"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts"))
    
    await message.answer(
        f"➕ **Создание хоста**\n\n"
        f"**Шаг 3 из 4:** Порт хоста\n\n"
        f"**Название:** {escape_markdown(remark)}\n"
        f"**Адрес:** {escape_markdown(address)}\n\n"
        f"Введите порт хоста (рекомендуется 443):\n"
        f"Или используйте рекомендуемый порт кнопкой ниже\n\n"
        f"💡 Порт должен быть в диапазоне 1-65535",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("use_default_host_port:"), AuthFilter())
async def use_default_host_port(callback: types.CallbackQuery, state: FSMContext):
    """Use default port for host"""
    await callback.answer()
    
    port = int(callback.data.split(":", 1)[1])
    await proceed_to_host_inbound(callback.message, state, port)

@router.message(StateFilter(HostStates.entering_host_port), AuthFilter())
async def handle_host_port(message: types.Message, state: FSMContext):
    """Handle host port input"""
    try:
        port = int(message.text.strip())
        
        if port < 1 or port > 65535:
            await message.answer(
                "❌ Порт должен быть в диапазоне 1-65535.\n"
                "Попробуйте еще раз:",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts")
                ]])
            )
            return
        
        await proceed_to_host_inbound(message, state, port)
        
    except ValueError:
        await message.answer(
            "❌ Введите корректный номер порта (число).\n"
            "Попробуйте еще раз:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts")
            ]])
        )

async def proceed_to_host_inbound(message: types.Message, state: FSMContext, port: int):
    """Proceed to inbound selection step"""
    await state.update_data(create_port=port)
    await state.set_state(HostStates.selecting_inbound)
    
    data = await state.get_data()
    remark = data.get('create_remark')
    address = data.get('create_address')
    
    # Попробуем получить список inbound'ов
    try:
        from modules.api.inbounds import get_all_inbounds
        inbounds_list = await get_all_inbounds()
        
        builder = InlineKeyboardBuilder()
        
        if inbounds_list:
            # Показываем доступные inbound'ы
            for inbound in inbounds_list[:5]:  # Первые 5
                tag = inbound.get('tag', 'Unknown')[:20]
                protocol = inbound.get('protocol', 'Unknown')
                builder.row(types.InlineKeyboardButton(
                    text=f"🔌 {tag} ({protocol})",
                    callback_data=f"select_inbound:{inbound.get('uuid', '')}"
                ))
            
            if len(inbounds_list) > 5:
                builder.row(types.InlineKeyboardButton(text="📋 Показать все", callback_data="show_all_inbounds"))
        
        builder.row(types.InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_inbound_selection"))
        builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts"))
        
        inbound_text = ""
        if inbounds_list:
            inbound_text = f"\n\n**Доступные Inbound'ы:** {len(inbounds_list)}"
        else:
            inbound_text = "\n\n**Inbound'ы не найдены.** Можно создать хост без привязки."
        
        await message.answer(
            f"➕ **Создание хоста**\n\n"
            f"**Шаг 4 из 4:** Привязка к Inbound\n\n"
            f"**Название:** {escape_markdown(remark)}\n"
            f"**Адрес:** {escape_markdown(address)}\n"
            f"**Порт:** {port}\n"
            f"{inbound_text}\n\n"
            f"Выберите Inbound для привязки или пропустите этот шаг:",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error getting inbounds for host creation: {e}")
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Создать без Inbound", callback_data="skip_inbound_selection"))
        builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="hosts"))
        
        await message.answer(
            f"➕ **Создание хоста**\n\n"
            f"**Шаг 4 из 4:** Завершение\n\n"
            f"**Название:** {escape_markdown(remark)}\n"
            f"**Адрес:** {escape_markdown(address)}\n"
            f"**Порт:** {port}\n\n"
            f"⚠️ Не удалось загрузить список Inbound'ов.\n"
            f"Хост будет создан без привязки к Inbound.",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("select_inbound:"), AuthFilter())
async def select_inbound_for_host(callback: types.CallbackQuery, state: FSMContext):
    """Select inbound for host creation"""
    await callback.answer()
    
    inbound_uuid = callback.data.split(":", 1)[1]
    await state.update_data(create_inbound_uuid=inbound_uuid)
    
    await finalize_host_creation(callback.message, state)

@router.callback_query(F.data == "skip_inbound_selection", AuthFilter())
async def skip_inbound_selection(callback: types.CallbackQuery, state: FSMContext):
    """Skip inbound selection for host creation"""
    await callback.answer()
    
    await finalize_host_creation(callback.message, state)

async def finalize_host_creation(message: types.Message, state: FSMContext):
    """Finalize host creation"""
    try:
        data = await state.get_data()
        remark = data.get('create_remark')
        address = data.get('create_address')
        port = data.get('create_port')
        inbound_uuid = data.get('create_inbound_uuid')
        
        # Создаем хост через HTTP API
        api_client = RemnaAPI()
        
        host_data = {
            "remark": remark,
            "address": address,
            "port": port,
            "isActive": True
        }
        
        if inbound_uuid:
            host_data["inboundUuid"] = inbound_uuid
        
        result = await api_client.post("hosts", host_data)
        
        if result:
            await state.clear()
            
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="📋 К списку хостов", callback_data="list_hosts"))
            builder.row(types.InlineKeyboardButton(text="➕ Создать еще", callback_data="create_host"))
            builder.row(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
            
            await message.edit_text(
                f"✅ **Хост успешно создан!**\n\n"
                f"**Название:** {escape_markdown(remark)}\n"
                f"**Адрес:** {escape_markdown(address)}\n"
                f"**Порт:** {port}\n"
                f"**Inbound:** {'Привязан' if inbound_uuid else 'Не привязан'}\n\n"
                f"Хост добавлен в систему и готов к использованию.",
                reply_markup=builder.as_markup()
            )
        else:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="create_host"))
            builder.row(types.InlineKeyboardButton(text="🔙 К хостам", callback_data="hosts"))
            
            await message.edit_text(
                "❌ **Ошибка при создании хоста**\n\n"
                "Не удалось создать хост. Проверьте данные и попробуйте снова.",
                reply_markup=builder.as_markup()
            )
            
    except Exception as e:
        logger.error(f"Error creating host: {e}")
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="create_host"))
        builder.row(types.InlineKeyboardButton(text="🔙 К хостам", callback_data="hosts"))
        
        await message.edit_text(
            "❌ **Ошибка при создании хоста**\n\n"
            "Произошла техническая ошибка. Попробуйте позже.",
            reply_markup=builder.as_markup()
        )

# ================ NO-OP CALLBACK ================

@router.callback_query(F.data == "noop", AuthFilter())
async def noop_callback(callback: types.CallbackQuery):
    """No-operation callback for pagination display"""
    await callback.answer()

# ================ BACK TO MAIN MENU ================

@router.callback_query(F.data == "hosts_back_to_main", AuthFilter())
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Return to main menu"""
    await callback.answer()
    await state.clear()
    
    from modules.handlers.start_handler import show_main_menu
    await show_main_menu(callback.message, is_callback=True)

logger.info("Host handlers module loaded successfully (SDK-free version)")