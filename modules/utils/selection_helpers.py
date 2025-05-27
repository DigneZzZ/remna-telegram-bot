"""
Helper functions for user-friendly selection of entities (users, inbounds, nodes)
instead of working with UUIDs directly
"""
import logging
from typing import List, Dict, Optional, Tuple
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from modules.api.users import get_all_users
from modules.api.nodes import get_all_nodes
from modules.api.client import RemnaAPI
from modules.utils.formatters_aiogram import escape_markdown

logger = logging.getLogger(__name__)

class SelectionHelper:
    """Helper class for entity selection with user-friendly interface"""
    
    @staticmethod
    async def get_users_selection_keyboard(
        page: int = 0, 
        per_page: int = 8,
        callback_prefix: str = "select_user",
        include_back: bool = True,
        max_per_row: int = 1
    ) -> Tuple[InlineKeyboardMarkup, Dict]:
        """
        Create keyboard for user selection with pagination
        Returns: (keyboard, users_data)
        """
        try:
            users = await get_all_users()
            if not users:
                builder = InlineKeyboardBuilder()
                if include_back:
                    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
                return builder.as_markup(), {}
            
            total_users = len(users)
            total_pages = (total_users + per_page - 1) // per_page
            
            start_idx = page * per_page
            end_idx = min(start_idx + per_page, total_users)
            
            builder = InlineKeyboardBuilder()
            users_data = {}
            
            # Add user buttons
            for i in range(start_idx, end_idx):
                user = users[i]
                status_emoji = "✅" if user.is_active else "❌"
                display_name = f"{status_emoji} {user.username}"
                
                callback_data = f"{callback_prefix}_{user.uuid}"
                users_data[user.uuid] = user
                
                builder.row(InlineKeyboardButton(text=display_name, callback_data=callback_data))
            
            # Add pagination if needed
            if total_pages > 1:
                pagination_buttons = []
                if page > 0:
                    pagination_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"users_page_{page-1}"))
                
                pagination_buttons.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="page_info"))
                
                if page < total_pages - 1:
                    pagination_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"users_page_{page+1}"))
                
                builder.row(*pagination_buttons)
            
            if include_back:
                builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
            
            return builder.as_markup(), users_data
            
        except Exception as e:
            logger.error(f"Error creating users selection keyboard: {e}")
            builder = InlineKeyboardBuilder()
            if include_back:
                builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
            return builder.as_markup(), {}
    
    @staticmethod
    async def get_inbounds_selection_keyboard(
        callback_prefix: str = "select_inbound",
        include_back: bool = True,
        max_per_row: int = 1
    ) -> Tuple[InlineKeyboardMarkup, Dict]:
        """
        Create keyboard for inbound selection
        Returns: (keyboard, inbounds_data)
        """
        try:
            sdk = RemnaAPI.get_sdk()
            inbounds = await sdk.inbounds.get_all_inbounds()
            if not inbounds:
                builder = InlineKeyboardBuilder()
                if include_back:
                    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
                return builder.as_markup(), {}
            
            builder = InlineKeyboardBuilder()
            inbounds_data = {}
            
            for inbound in inbounds:
                display_name = f"🔌 {inbound.tag} ({inbound.type}, :{inbound.port})"
                callback_data = f"{callback_prefix}_{inbound.uuid}"
                inbounds_data[inbound.uuid] = inbound
                
                builder.row(InlineKeyboardButton(text=display_name, callback_data=callback_data))
            
            if include_back:
                builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
            
            return builder.as_markup(), inbounds_data
            
        except Exception as e:
            logger.error(f"Error creating inbounds selection keyboard: {e}")
            builder = InlineKeyboardBuilder()
            if include_back:
                builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
            return builder.as_markup(), {}
    
    @staticmethod
    async def get_nodes_selection_keyboard(
        callback_prefix: str = "select_node",
        include_back: bool = True
    ) -> Tuple[InlineKeyboardMarkup, Dict]:
        """
        Create keyboard for node selection
        Returns: (keyboard, nodes_data)
        """
        try:
            nodes = await get_all_nodes()
            if not nodes:
                builder = InlineKeyboardBuilder()
                if include_back:
                    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
                return builder.as_markup(), {}
            
            builder = InlineKeyboardBuilder()
            nodes_data = {}
            
            for node in nodes:
                status_emoji = "🟢" if node.is_connected and not node.is_disabled else "🔴"
                display_name = f"{status_emoji} {node.name} ({node.country_code})"
                
                callback_data = f"{callback_prefix}_{node.uuid}"
                nodes_data[node.uuid] = node
                
                builder.row(InlineKeyboardButton(text=display_name, callback_data=callback_data))
            
            if include_back:
                builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
            
            return builder.as_markup(), nodes_data
            
        except Exception as e:
            logger.error(f"Error creating nodes selection keyboard: {e}")
            builder = InlineKeyboardBuilder()
            if include_back:
                builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back"))
            return builder.as_markup(), {}
    
    @staticmethod
    async def search_users_by_query(query: str, search_type: str = "username") -> List[Dict]:
        """
        Search users by different criteria
        search_type: username, telegram_id, email, tag
        """
        try:
            sdk = RemnaAPI.get_sdk()
            
            if search_type == "username":
                try:
                    user = await sdk.users.get_user_by_username(query)
                    return [user] if user else []
                except:
                    return []
            elif search_type == "telegram_id":
                # Ищем через все пользователи и фильтруем по telegram_id
                users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
                if users_response and users_response.users:
                    matching_users = [user for user in users_response.users 
                                    if hasattr(user, 'telegram_id') and str(user.telegram_id) == str(query)]
                    return matching_users
                return []
            elif search_type == "email":
                # Ищем через все пользователи и фильтруем по email
                users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
                if users_response and users_response.users:
                    matching_users = [user for user in users_response.users 
                                    if hasattr(user, 'email') and user.email and query.lower() in user.email.lower()]
                    return matching_users
                return []
            else:
                return []
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    @staticmethod
    def create_user_info_keyboard(user_uuid: str, action_prefix: str = "user_action") -> InlineKeyboardMarkup:
        """Create keyboard with user actions"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"{action_prefix}_edit_{user_uuid}"),
            InlineKeyboardButton(text="🔄 Обновить данные", callback_data=f"{action_prefix}_refresh_{user_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="🚫 Отключить", callback_data=f"{action_prefix}_disable_{user_uuid}"),
            InlineKeyboardButton(text="✅ Включить", callback_data=f"{action_prefix}_enable_{user_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Сбросить трафик", callback_data=f"{action_prefix}_reset_traffic_{user_uuid}"),
            InlineKeyboardButton(text="🔐 Отозвать подписку", callback_data=f"{action_prefix}_revoke_{user_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"{action_prefix}_delete_{user_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_users")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def create_inbound_info_keyboard(inbound_uuid: str, action_prefix: str = "inbound_action") -> InlineKeyboardMarkup:
        """Create keyboard with inbound actions"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="👥 Добавить всем пользователям", callback_data=f"{action_prefix}_add_users_{inbound_uuid}"),
            InlineKeyboardButton(text="👥 Убрать у всех пользователей", callback_data=f"{action_prefix}_remove_users_{inbound_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="🖥️ Добавить на все ноды", callback_data=f"{action_prefix}_add_nodes_{inbound_uuid}"),
            InlineKeyboardButton(text="🖥️ Убрать со всех нод", callback_data=f"{action_prefix}_remove_nodes_{inbound_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_inbounds")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def create_node_info_keyboard(node_uuid: str, action_prefix: str = "node_action") -> InlineKeyboardMarkup:
        """Create keyboard with node actions"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="✅ Включить", callback_data=f"{action_prefix}_enable_{node_uuid}"),
            InlineKeyboardButton(text="🚫 Отключить", callback_data=f"{action_prefix}_disable_{node_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="🔄 Перезапустить", callback_data=f"{action_prefix}_restart_{node_uuid}"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"{action_prefix}_edit_{node_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Статистика", callback_data=f"{action_prefix}_stats_{node_uuid}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"{action_prefix}_delete_{node_uuid}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_nodes")
        )
        
        return builder.as_markup()
    
    @staticmethod
    async def get_user_by_identifier(identifier: str) -> Optional[Dict]:
        """
        Smart user lookup - try to find user by username, UUID, or telegram ID
        """
        try:
            sdk = RemnaAPI.get_sdk()
            
            # Try by username first
            try:
                user = await sdk.users.get_user_by_username(identifier)
                if user:
                    return user
            except Exception:
                pass
            
            # Try by UUID if it looks like UUID
            if len(identifier) == 36 and identifier.count('-') == 4:
                try:
                    user = await sdk.users.get_user_by_uuid(identifier)
                    if user:
                        return user
                except Exception:
                    pass
            
            # Try by telegram ID if it's numeric
            if identifier.isdigit():
                try:
                    users_response = await sdk.users.get_all_users_v2(start=0, size=1000)
                    if users_response and users_response.users:
                        for user in users_response.users:
                            if hasattr(user, 'telegram_id') and str(user.telegram_id) == identifier:
                                return user
                except Exception:
                    pass
            
            return None
        except Exception as e:
            logger.error(f"Error in smart user lookup: {e}")
            return None

    @staticmethod
    async def get_inbound_by_identifier(identifier: str) -> Optional[Dict]:
        """
        Smart inbound lookup - try to find inbound by tag or UUID
        """
        try:
            sdk = RemnaAPI.get_sdk()
            inbounds = await sdk.inbounds.get_all_inbounds()
            if not inbounds:
                return None
            
            # Try by tag first
            for inbound in inbounds:
                if inbound.tag.lower() == identifier.lower():
                    return inbound
            
            # Try by UUID
            for inbound in inbounds:
                if inbound.uuid == identifier:
                    return inbound
            
            return None
        except Exception as e:
            logger.error(f"Error in smart inbound lookup: {e}")
            return None

    @staticmethod
    async def get_node_by_identifier(identifier: str) -> Optional[Dict]:
        """
        Smart node lookup - try to find node by name or UUID
        """
        try:
            nodes = await get_all_nodes()
            if not nodes:
                return None
            
            # Try by name first
            for node in nodes:
                if node.name.lower() == identifier.lower():
                    return node
            
            # Try by UUID
            for node in nodes:
                if node.uuid == identifier:
                    return node
            
            return None
        except Exception as e:
            logger.error(f"Error in smart node lookup: {e}")
            return None
