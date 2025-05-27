"""
Хелперы для создания клавиатур и навигации в Aiogram
"""
from typing import List, Dict, Any, Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from modules.api.sdk_client import RemnaSDK
import math

class KeyboardHelper:
    """Хелпер для создания клавиатур"""
    
    @staticmethod
    def create_pagination_keyboard(
        items: List[Dict[str, Any]], 
        page: int = 0, 
        items_per_page: int = 10,
        callback_prefix: str = "select",
        page_callback_prefix: str = "page",
        include_back: bool = True,
        back_callback: str = "back",
        name_field: str = "name",
        id_field: str = "uuid"
    ) -> Tuple[InlineKeyboardMarkup, Dict[str, Any]]:
        """Создать клавиатуру с пагинацией"""
        
        total_items = len(items)
        total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
        
        # Убедимся, что page в допустимых границах
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_items = items[start_idx:end_idx]
        
        keyboard = []
        items_data = {}
        
        # Добавляем кнопки для элементов на текущей странице
        for item in page_items:
            item_id = item.get(id_field, "")
            item_name = item.get(name_field, "Unknown")
            
            # Сохраняем данные элемента для последующего использования
            items_data[item_id] = item
            
            # Обрезаем длинные названия
            display_name = item_name[:30] + "..." if len(item_name) > 30 else item_name
            
            keyboard.append([
                InlineKeyboardButton(
                    text=display_name,
                    callback_data=f"{callback_prefix}_{item_id}"
                )
            ])
        
        # Добавляем кнопки навигации если есть больше одной страницы
        if total_pages > 1:
            nav_buttons = []
            
            # Кнопка "Предыдущая"
            if page > 0:
                nav_buttons.append(
                    InlineKeyboardButton(
                        text="◀️ Пред", 
                        callback_data=f"{page_callback_prefix}_{page - 1}"
                    )
                )
            
            # Информация о странице
            nav_buttons.append(
                InlineKeyboardButton(
                    text=f"{page + 1}/{total_pages}",
                    callback_data="noop"
                )
            )
            
            # Кнопка "Следующая"
            if page < total_pages - 1:
                nav_buttons.append(
                    InlineKeyboardButton(
                        text="След ▶️",
                        callback_data=f"{page_callback_prefix}_{page + 1}"
                    )
                )
            
            keyboard.append(nav_buttons)
        
        # Добавляем кнопку "Назад"
        if include_back:
            keyboard.append([
                InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard), items_data

class SelectionHelper:
    """Хелпер для создания списков выбора"""
    
    @staticmethod
    async def get_users_selection_keyboard(
        callback_prefix: str = "select_user",
        page: int = 0,
        items_per_page: int = 10,
        include_back: bool = True,
        search_query: str = None,
        **filter_kwargs
    ) -> Tuple[InlineKeyboardMarkup, Dict[str, Any]]:
        """Получить клавиатуру для выбора пользователей"""
        
        try:
            # Получаем пользователей с фильтрами
            filter_params = {
                'limit': 1000,  # Получаем все для локальной фильтрации
                'offset': 0,
                **filter_kwargs
            }
            
            users_response = await RemnaSDK.get_all_users(**filter_params)
            users = users_response.get('users', [])
            
            # Применяем поиск если есть
            if search_query:
                search_query = search_query.lower()
                users = [
                    user for user in users 
                    if search_query in user.get('username', '').lower() or 
                       search_query in user.get('email', '').lower()
                ]
            
            # Форматируем элементы для отображения
            formatted_users = []
            for user in users:
                status_emoji = "✅" if user.get('isActive', False) else "❌"
                name = f"{status_emoji} {user.get('username', 'Unknown')}"
                
                formatted_users.append({
                    'uuid': user.get('uuid'),
                    'name': name,
                    'email': user.get('email', ''),
                    'isActive': user.get('isActive', False),
                    **user  # Включаем все данные пользователя
                })
            
            return KeyboardHelper.create_pagination_keyboard(
                items=formatted_users,
                page=page,
                items_per_page=items_per_page,
                callback_prefix=callback_prefix,
                page_callback_prefix="page_users",
                include_back=include_back,
                back_callback="back_to_users",
                name_field="name",
                id_field="uuid"
            )
            
        except Exception as e:
            # В случае ошибки возвращаем пустую клавиатуру
            keyboard = []
            if include_back:
                keyboard.append([
                    InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_users")
                ])
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard), {}
    
    @staticmethod
    async def get_nodes_selection_keyboard(
        callback_prefix: str = "select_node",
        page: int = 0,
        items_per_page: int = 10,
        include_back: bool = True
    ) -> Tuple[InlineKeyboardMarkup, Dict[str, Any]]:
        """Получить клавиатуру для выбора нод"""
        
        try:
            nodes = await RemnaSDK.get_all_nodes()
            
            # Форматируем ноды для отображения
            formatted_nodes = []
            for node in nodes:
                # Определяем статус
                is_disabled = node.get('isDisabled', True)
                is_connected = node.get('isConnected', False)
                
                if is_disabled:
                    status_emoji = "❌"
                elif is_connected:
                    status_emoji = "✅"
                else:
                    status_emoji = "⚠️"
                
                name = f"{status_emoji} {node.get('name', 'Unknown')}"
                
                formatted_nodes.append({
                    'uuid': node.get('uuid'),
                    'name': name,
                    'address': node.get('address', ''),
                    'port': node.get('port', ''),
                    'isDisabled': is_disabled,
                    'isConnected': is_connected,
                    **node  # Включаем все данные ноды
                })
            
            return KeyboardHelper.create_pagination_keyboard(
                items=formatted_nodes,
                page=page,
                items_per_page=items_per_page,
                callback_prefix=callback_prefix,
                page_callback_prefix="page_nodes",
                include_back=include_back,
                back_callback="back_to_nodes",
                name_field="name",
                id_field="uuid"
            )
            
        except Exception as e:
            # В случае ошибки возвращаем пустую клавиатуру
            keyboard = []
            if include_back:
                keyboard.append([
                    InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_nodes")
                ])
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard), {}
    
    @staticmethod
    async def get_inbounds_selection_keyboard(
        callback_prefix: str = "select_inbound",
        page: int = 0,
        items_per_page: int = 10,
        include_back: bool = True,
        show_details: bool = False
    ) -> Tuple[InlineKeyboardMarkup, Dict[str, Any]]:
        """Получить клавиатуру для выбора inbound'ов"""
        
        try:
            inbounds = await RemnaSDK.get_all_inbounds()
            
            # Форматируем inbound'ы для отображения
            formatted_inbounds = []
            for inbound in inbounds:
                tag = inbound.get('tag', 'Unknown')
                protocol = inbound.get('type', 'Unknown')
                port = inbound.get('port', 'N/A')
                
                if show_details:
                    name = f"📡 {tag} ({protocol}:{port})"
                else:
                    name = f"📡 {tag}"
                
                formatted_inbounds.append({
                    'uuid': inbound.get('uuid'),
                    'name': name,
                    'tag': tag,
                    'type': protocol,
                    'port': port,
                    **inbound  # Включаем все данные inbound'а
                })
            
            return KeyboardHelper.create_pagination_keyboard(
                items=formatted_inbounds,
                page=page,
                items_per_page=items_per_page,
                callback_prefix=callback_prefix,
                page_callback_prefix="page_inbounds",
                include_back=include_back,
                back_callback="back_to_inbounds",
                name_field="name",
                id_field="uuid"
            )
            
        except Exception as e:
            # В случае ошибки возвращаем пустую клавиатуру
            keyboard = []
            if include_back:
                keyboard.append([
                    InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_inbounds")
                ])
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard), {}
    
    @staticmethod
    async def get_hosts_selection_keyboard(
        callback_prefix: str = "select_host",
        page: int = 0,
        items_per_page: int = 10,
        include_back: bool = True
    ) -> Tuple[InlineKeyboardMarkup, Dict[str, Any]]:
        """Получить клавиатуру для выбора хостов"""
        
        try:
            hosts = await RemnaSDK.get_all_hosts()
            
            # Форматируем хосты для отображения
            formatted_hosts = []
            for host in hosts:
                remark = host.get('remark', 'Unknown')
                address = host.get('address', '')
                port = host.get('port', '')
                
                name = f"🌐 {remark}"
                if address:
                    name += f" ({address}:{port})"
                
                formatted_hosts.append({
                    'uuid': host.get('uuid'),
                    'name': name,
                    'remark': remark,
                    'address': address,
                    'port': port,
                    **host  # Включаем все данные хоста
                })
            
            return KeyboardHelper.create_pagination_keyboard(
                items=formatted_hosts,
                page=page,
                items_per_page=items_per_page,
                callback_prefix=callback_prefix,
                page_callback_prefix="page_hosts",
                include_back=include_back,
                back_callback="back_to_hosts",
                name_field="name",
                id_field="uuid"
            )
            
        except Exception as e:
            # В случае ошибки возвращаем пустую клавиатуру
            keyboard = []
            if include_back:
                keyboard.append([
                    InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_hosts")
                ])
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard), {}

class MenuHelper:
    """Хелпер для создания меню"""
    
    @staticmethod
    def create_main_menu() -> InlineKeyboardMarkup:
        """Создать главное меню"""
        keyboard = [
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="users")],
            [InlineKeyboardButton(text="🖥️ Серверы", callback_data="nodes")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton(text="🌐 Хосты", callback_data="hosts")],
            [InlineKeyboardButton(text="📡 Inbound'ы", callback_data="inbounds")],
            [InlineKeyboardButton(text="📦 Массовые операции", callback_data="bulk")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def create_back_to_main_keyboard() -> InlineKeyboardMarkup:
        """Создать клавиатуру с кнопкой возврата в главное меню"""
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]])
    
    @staticmethod
    def create_yes_no_keyboard(
        yes_callback: str, 
        no_callback: str,
        yes_text: str = "✅ Да",
        no_text: str = "❌ Нет"
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру Да/Нет"""
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=yes_text, callback_data=yes_callback),
            InlineKeyboardButton(text=no_text, callback_data=no_callback)
        ]])
    
    @staticmethod
    def create_cancel_keyboard(cancel_callback: str = "cancel") -> InlineKeyboardMarkup:
        """Создать клавиатуру с кнопкой отмены"""
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)
        ]])
