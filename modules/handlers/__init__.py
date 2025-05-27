# Aiogram handlers package

from aiogram import Dispatcher

# Import all routers
from .start_handler import router as start_router
from .menu_handler import router as menu_router
from .user_handlers import router as user_router
from .node_handlers import router as node_router
from .stats_handlers import router as stats_router
from .host_handlers import router as host_router
from .inbound_handlers import router as inbound_router
from .bulk_handlers import router as bulk_router

def register_all_handlers(dp: Dispatcher):
    """Register all handlers with the dispatcher"""
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(user_router)
    dp.include_router(node_router)
    dp.include_router(stats_router)
    dp.include_router(host_router)
    dp.include_router(inbound_router)
    dp.include_router(bulk_router)
