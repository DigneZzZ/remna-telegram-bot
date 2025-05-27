from aiogram import Router, types
from aiogram.filters import Text
import logging

from modules.handlers_aiogram.auth import AuthFilter

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(Text("bulk"), AuthFilter())
async def handle_bulk_menu(callback: types.CallbackQuery):
    """Handle bulk operations menu - placeholder"""
    await callback.answer()
    await callback.message.edit_text(
        "🚧 <b>Массовые операции</b>\n\n"
        "Функция массовых операций будет добавлена в следующем обновлении.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="main_menu")
        ]])
    )

def register_bulk_handlers(dp):
    """Register bulk handlers"""
    dp.include_router(router)
