from aiogram import Router, types, F
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from modules.handlers_aiogram.auth import AuthFilter
from modules.handlers_aiogram.states import HostStates
from modules.api.client import RemnaAPI
from modules.utils.formatters_aiogram import (
    format_bytes, format_datetime, escape_markdown
)

logger = logging.getLogger(__name__)

router = Router()

# ================ HOST MENU ================

@router.callback_query(Text("hosts"), AuthFilter())
async def handle_hosts_menu(callback: types.CallbackQuery, state: FSMContext):
    """Handle hosts menu selection"""
    await callback.answer()
    await state.clear()
    await show_hosts_menu(callback)

async def show_hosts_menu(callback: types.CallbackQuery):
    """Show hosts menu"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📋 Список всех хостов", callback_data="list_hosts"))
    builder.row(types.InlineKeyboardButton(text="➕ Создать хост", callback_data="create_host"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu"))

    message = "🌐 **Управление хостами**\n\n"
    message += "Выберите действие:"

    await callback.message.edit_text(
        text=message,
        reply_markup=builder.as_markup()
    )

# ================ LIST HOSTS ================

@router.callback_query(Text("list_hosts"), AuthFilter())
async def list_hosts(callback: types.CallbackQuery, state: FSMContext):
    """List all hosts"""
    await callback.answer()
    await callback.message.edit_text("🌐 Загрузка списка хостов...")

    try:
        sdk = RemnaAPI.get_sdk()
        hosts_response = await sdk.hosts.get_all_hosts()

        if not hosts_response or not hosts_response.hosts:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts"))
            
            await callback.message.edit_text(
                "❌ Хосты не найдены или ошибка при получении списка.",
                reply_markup=builder.as_markup()
            )
            return

        hosts = hosts_response.hosts
        message = f"🌐 **Хосты** ({len(hosts)}):\n\n"

        for i, host in enumerate(hosts):
            status_emoji = "🟢" if host.is_active else "🔴"
            
            message += f"{i+1}. {status_emoji} **{escape_markdown(host.remark)}**\n"
            message += f"   🌐 Адрес: `{host.address}:{host.port}`\n"
            if host.inbound_uuid:
                message += f"   🔌 Inbound: `{host.inbound_uuid[:8]}...`\n"
            message += "\n"

        # Add action buttons
        builder = InlineKeyboardBuilder()
        
        for host in hosts:
            builder.row(types.InlineKeyboardButton(
                text=f"👁️ {host.remark[:20]}...", 
                callback_data=f"view_host_{host.uuid}"
            ))
        
        # Add back button
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts"))

        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        logger.error(f"Error listing hosts: {e}")
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts"))
        
        await callback.message.edit_text(
            "❌ Ошибка при получении списка хостов.",
            reply_markup=builder.as_markup()
        )

# ================ HOST DETAILS ================

@router.callback_query(Text(startswith="view_host_"), AuthFilter())
async def show_host_details(callback: types.CallbackQuery, state: FSMContext):
    """Show host details"""
    await callback.answer()
    
    try:
        uuid = callback.data.split("_")[2]
        
        sdk = RemnaAPI.get_sdk()
        host_response = await sdk.hosts.get_host_by_uuid(uuid)
        
        if not host_response or not host_response.host:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_hosts"))
            
            await callback.message.edit_text(
                "❌ Хост не найден или ошибка при получении данных.",
                reply_markup=builder.as_markup()
            )
            return
        
        host = host_response.host
        
        # Format host details
        message = f"🌐 **Детали хоста**\n\n"
        message += f"**📝 Название:** {escape_markdown(host.remark)}\n"
        message += f"**🌐 Адрес:** `{host.address}`\n"
        message += f"**🔌 Порт:** `{host.port}`\n"
        message += f"**📊 Статус:** {'🟢 Активен' if host.is_active else '🔴 Неактивен'}\n"
        
        if host.inbound_uuid:
            message += f"**🔌 Inbound UUID:** `{host.inbound_uuid}`\n"
        
        if hasattr(host, 'path') and host.path:
            message += f"**🛣️ Путь:** `{host.path}`\n"
            
        if hasattr(host, 'sni') and host.sni:
            message += f"**🔒 SNI:** `{host.sni}`\n"
            
        if hasattr(host, 'host_header') and host.host_header:
            message += f"**🏠 Host:** `{host.host_header}`\n"
            
        if hasattr(host, 'alpn') and host.alpn:
            message += f"**🔄 ALPN:** `{host.alpn}`\n"
            
        if hasattr(host, 'fingerprint') and host.fingerprint:
            message += f"**👆 Fingerprint:** `{host.fingerprint}`\n"
            
        if hasattr(host, 'allow_insecure'):
            message += f"**🔐 Allow Insecure:** {'Да' if host.allow_insecure else 'Нет'}\n"
            
        if hasattr(host, 'security_layer') and host.security_layer:
            message += f"**🛡️ Security Layer:** `{host.security_layer}`\n"
        
        # Create action buttons
        builder = InlineKeyboardBuilder()
        
        if host.is_active:
            builder.row(types.InlineKeyboardButton(text="🔴 Отключить", callback_data=f"disable_host_{uuid}"))
        else:
            builder.row(types.InlineKeyboardButton(text="🟢 Включить", callback_data=f"enable_host_{uuid}"))
        
        builder.row(types.InlineKeyboardButton(text="📝 Редактировать", callback_data=f"edit_host_{uuid}"))
        builder.row(types.InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_host_{uuid}"))
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

@router.callback_query(Text(startswith="enable_host_"), AuthFilter())
async def enable_host(callback: types.CallbackQuery, state: FSMContext):
    """Enable host"""
    await callback.answer()
    
    try:
        uuid = callback.data.split("_")[2]
        
        sdk = RemnaAPI.get_sdk()
        success = await sdk.hosts.enable_host(uuid)
        
        if success:
            await callback.answer("🟢 Хост успешно включен.", show_alert=True)
        else:
            await callback.answer("❌ Не удалось включить хост.", show_alert=True)
        
        # Refresh host details
        await show_host_details(callback, state)
        
    except Exception as e:
        logger.error(f"Error enabling host: {e}")
        await callback.answer("❌ Ошибка при включении хоста.", show_alert=True)

@router.callback_query(Text(startswith="disable_host_"), AuthFilter())
async def disable_host(callback: types.CallbackQuery, state: FSMContext):
    """Disable host"""
    await callback.answer()
    
    try:
        uuid = callback.data.split("_")[2]
        
        sdk = RemnaAPI.get_sdk()
        success = await sdk.hosts.disable_host(uuid)
        
        if success:
            await callback.answer("🔴 Хост успешно отключен.", show_alert=True)
        else:
            await callback.answer("❌ Не удалось отключить хост.", show_alert=True)
        
        # Refresh host details
        await show_host_details(callback, state)
        
    except Exception as e:
        logger.error(f"Error disabling host: {e}")
        await callback.answer("❌ Ошибка при отключении хоста.", show_alert=True)

@router.callback_query(Text(startswith="delete_host_"), AuthFilter())
async def delete_host_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Confirm host deletion"""
    await callback.answer()
    
    try:
        uuid = callback.data.split("_")[2]
        
        # Store uuid for confirmation
        await state.update_data(deleting_host_uuid=uuid)
        
        sdk = RemnaAPI.get_sdk()
        host_response = await sdk.hosts.get_host_by_uuid(uuid)
        
        if not host_response or not host_response.host:
            await callback.answer("❌ Хост не найден.", show_alert=True)
            return
        
        host = host_response.host
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_host_{uuid}"),
            types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_host_{uuid}")
        )
        
        message = f"❌ **Подтверждение удаления хоста**\n\n"
        message += f"**Хост:** {escape_markdown(host.remark)}\n"
        message += f"**Адрес:** `{host.address}:{host.port}`\n\n"
        message += f"⚠️ **ВНИМАНИЕ!** Это действие нельзя отменить.\n\n"
        message += f"Вы уверены, что хотите удалить этот хост?"
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error preparing host deletion: {e}")
        await callback.answer("❌ Ошибка при подготовке удаления.", show_alert=True)

@router.callback_query(Text(startswith="confirm_delete_host_"), AuthFilter())
async def confirm_delete_host(callback: types.CallbackQuery, state: FSMContext):
    """Delete host after confirmation"""
    await callback.answer()
    
    try:
        uuid = callback.data.split("_")[3]
        
        sdk = RemnaAPI.get_sdk()
        success = await sdk.hosts.delete_host(uuid)
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 К списку хостов", callback_data="list_hosts"))
        
        if success:
            message = "✅ **Хост успешно удален**\n\n"
            message += "Хост был удален из системы."
        else:
            message = "❌ **Ошибка при удалении хоста**\n\n"
            message += "Не удалось удалить хост. Попробуйте позже."
        
        await callback.message.edit_text(
            text=message,
            reply_markup=builder.as_markup()
        )
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error deleting host: {e}")
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 К списку хостов", callback_data="list_hosts"))
        
        await callback.message.edit_text(
            "❌ Ошибка при удалении хоста.",
            reply_markup=builder.as_markup()
        )
        await state.clear()

# ================ EDIT HOST ================

@router.callback_query(Text(startswith="edit_host_"), AuthFilter())
async def start_edit_host(callback: types.CallbackQuery, state: FSMContext):
    """Start editing a host"""
    await callback.answer()
    
    try:
        uuid = callback.data.split("_")[2]
        
        # Get host details
        sdk = RemnaAPI.get_sdk()
        host_response = await sdk.hosts.get_host_by_uuid(uuid)
        
        if not host_response or not host_response.host:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="list_hosts"))
            
            await callback.message.edit_text(
                "❌ Хост не найден.",
                reply_markup=builder.as_markup()
            )
            return
        
        host = host_response.host
        
        # Store host data in state
        await state.update_data(editing_host=host.dict(), host_uuid=uuid)
        await state.set_state(HostStates.editing)
        
        # Create edit menu
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📝 Название", callback_data=f"eh_remark_{uuid}"))
        builder.row(types.InlineKeyboardButton(text="🌐 Адрес", callback_data=f"eh_address_{uuid}"))
        builder.row(types.InlineKeyboardButton(text="🔌 Порт", callback_data=f"eh_port_{uuid}"))
        
        # Optional fields (if supported by SDK)
        if hasattr(host, 'path'):
            builder.row(types.InlineKeyboardButton(text="🛣️ Путь", callback_data=f"eh_path_{uuid}"))
        if hasattr(host, 'sni'):
            builder.row(types.InlineKeyboardButton(text="🔒 SNI", callback_data=f"eh_sni_{uuid}"))
        if hasattr(host, 'host_header'):
            builder.row(types.InlineKeyboardButton(text="🏠 Host", callback_data=f"eh_host_{uuid}"))
        
        builder.row(types.InlineKeyboardButton(text="🔙 Назад к деталям", callback_data=f"view_host_{uuid}"))
        
        message = f"📝 **Редактирование хоста: {escape_markdown(host.remark)}**\n\n"
        message += f"📌 **Текущие значения:**\n"
        message += f"• Название: `{host.remark}`\n"
        message += f"• Адрес: `{host.address}`\n"
        message += f"• Порт: `{host.port}`\n"
        
        if hasattr(host, 'path') and host.path:
            message += f"• Путь: `{host.path}`\n"
        if hasattr(host, 'sni') and host.sni:
            message += f"• SNI: `{host.sni}`\n"
        if hasattr(host, 'host_header') and host.host_header:
            message += f"• Host: `{host.host_header}`\n"
        
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

@router.callback_query(Text(startswith="eh_"), StateFilter(HostStates.editing), AuthFilter())
async def start_edit_host_field(callback: types.CallbackQuery, state: FSMContext):
    """Start editing a specific host field"""
    await callback.answer()
    
    try:
        parts = callback.data.split("_")
        field = parts[1]  # remark, address, port, etc.
        uuid = parts[2]
        
        data = await state.get_data()
        host = data.get("editing_host")
        
        if not host:
            await callback.answer("❌ Данные хоста потеряны.", show_alert=True)
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
            "host": {
                "title": "Host заголовок",
                "current": host.get("host_header", ""),
                "example": "Например: api.example.com",
                "validation": "доменное имя (может быть пустым)"
            }
        }
        
        if field not in field_info:
            await callback.answer("❌ Неизвестное поле.", show_alert=True)
            return
        
        info = field_info[field]
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_host_{uuid}"))
        
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
        await callback.answer("❌ Ошибка при подготовке редактирования.", show_alert=True)

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
        
        elif field in ["path", "sni", "host"]:
            # These fields can be empty
            validated_value = user_input if user_input else ""
        
        if error_message:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_host_{uuid}"))
            
            await message.answer(
                f"❌ {error_message}\n\nПопробуйте еще раз:",
                reply_markup=builder.as_markup()
            )
            return
        
        # Update host via SDK
        try:
            sdk = RemnaAPI.get_sdk()
            update_data = {field: validated_value}
            
            success = await sdk.hosts.update_host(uuid, update_data)
            
            if success:
                # Update stored host data
                host[field] = validated_value
                await state.update_data(editing_host=host)
                
                # Clear editing state
                await state.set_state(HostStates.editing)
                
                builder = InlineKeyboardBuilder()
                builder.row(types.InlineKeyboardButton(text="✅ Продолжить редактирование", callback_data=f"edit_host_{uuid}"))
                builder.row(types.InlineKeyboardButton(text="📋 Показать детали", callback_data=f"view_host_{uuid}"))
                builder.row(types.InlineKeyboardButton(text="🔙 К списку хостов", callback_data="list_hosts"))
                
                await message.answer(
                    f"✅ Поле '{field}' успешно обновлено!",
                    reply_markup=builder.as_markup()
                )
                
            else:
                builder = InlineKeyboardBuilder()
                builder.row(types.InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"eh_{field}_{uuid}"))
                builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_host_{uuid}"))
                
                await message.answer(
                    "❌ Ошибка при обновлении хоста. Проверьте данные и попробуйте снова.",
                    reply_markup=builder.as_markup()
                )
                
        except Exception as e:
            logger.error(f"Error updating host via SDK: {e}")
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_host_{uuid}"))
            
            await message.answer(
                "❌ Ошибка при обновлении хоста через API.",
                reply_markup=builder.as_markup()
            )
            
    except Exception as e:
        logger.error(f"Error handling host field input: {e}")
        await message.answer("❌ Произошла ошибка при обработке ввода.")
        await state.clear()

@router.callback_query(Text(startswith="cancel_edit_host_"), AuthFilter())
async def handle_cancel_host_edit(callback: types.CallbackQuery, state: FSMContext):
    """Handle canceling host edit"""
    await callback.answer()
    
    try:
        uuid = callback.data.split("_")[3]
        
        # Clear editing state
        await state.clear()
        
        # Return to host details
        callback.data = f"view_host_{uuid}"
        await show_host_details(callback, state)
        
    except Exception as e:
        logger.error(f"Error canceling host edit: {e}")
        await callback.answer("❌ Ошибка при отмене редактирования.", show_alert=True)

# ================ CREATE HOST (PLACEHOLDER) ================

@router.callback_query(Text("create_host"), AuthFilter())
async def create_host_placeholder(callback: types.CallbackQuery, state: FSMContext):
    """Create host placeholder"""
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="hosts"))
    
    await callback.message.edit_text(
        "🚧 **Создание хоста**\n\n"
        "Функция создания хоста находится в разработке.\n\n"
        "**Планируемые возможности:**\n"
        "• Создание новых хостов\n"
        "• Настройка параметров подключения\n"
        "• Привязка к Inbound'ам\n"
        "• Конфигурация безопасности\n\n"
        "В текущей версии доступно редактирование существующих хостов.",
        reply_markup=builder.as_markup()
    )

# ================ BACK TO MAIN MENU ================

@router.callback_query(Text("hosts_back_to_main"), AuthFilter())
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Return to main menu"""
    await callback.answer()
    await state.clear()
    
    from modules.handlers_aiogram.start_handler import show_main_menu
    await show_main_menu(callback.message)