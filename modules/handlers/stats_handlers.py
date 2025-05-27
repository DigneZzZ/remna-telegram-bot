from aiogram import Router, types
from aiogram.filters import Text
import logging

from modules.handlers_aiogram.auth import AuthFilter

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(Text("stats"), AuthFilter())
async def handle_stats_menu(callback: types.CallbackQuery):
    """Handle stats menu - placeholder"""
    await callback.answer()
    await callback.message.edit_text(
        "🚧 <b>Статистика системы</b>\n\n"
        "Детальная статистика системы будет добавлена в следующем обновлении.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu")
        ]])
    )

def register_stats_handlers(dp):
    """Register stats handlers"""
    dp.include_router(router)
