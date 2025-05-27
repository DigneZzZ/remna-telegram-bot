from aiogram import Router, types
from aiogram.filters import Text
import logging

from modules.handlers_aiogram.auth import AuthFilter

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(Text("nodes"), AuthFilter())
async def handle_nodes_menu(callback: types.CallbackQuery):
    """Handle nodes menu - placeholder"""
    await callback.answer()
    await callback.message.edit_text(
        "🚧 <b>Управление серверами</b>\n\n"
        "Функция управления серверами будет добавлена в следующем обновлении.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu")
        ]])
    )

def register_node_handlers(dp):
    """Register node handlers"""
    dp.include_router(router)
