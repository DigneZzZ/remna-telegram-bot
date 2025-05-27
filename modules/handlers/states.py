"""
FSM States для всех handlers в Aiogram боте
"""
from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """Состояния для управления пользователями"""
    selecting_user = State()
    viewing_user = State()
    creating_user = State()
    editing_user = State()
    confirming_delete = State()
    search_username = State()
    search_telegram_id = State()
    
    # Создание пользователя
    enter_username = State()
    enter_telegram_id = State()
    enter_description = State()
    enter_traffic_limit = State()
    select_nodes = State()
    
    # Редактирование пользователя
    edit_field_selection = State()
    edit_username = State()
    edit_telegram_id = State()
    edit_description = State()
    edit_traffic_limit = State()
    edit_nodes = State()
    enter_edit_telegram_id = State()
    enter_edit_traffic_limit = State()
    enter_edit_description = State()
    
    # Поиск пользователей
    search_username = State()
    search_telegram_id = State()
    search_description = State()
    # Device management states
    managing_devices = State()
    
    # Template creation states (extending existing ones)
    template_selection = State()


class NodeStates(StatesGroup):
    """Состояния для управления нодами"""
    selecting_node = State()
    viewing_node = State()
    creating_node = State()
    editing_node = State()
    confirming_delete = State()
    confirming_restart = State()
    
    # Создание ноды
    enter_name = State()
    enter_address = State()
    enter_port = State()
    enter_api_host = State()
    enter_api_port = State()
    enter_usage_coefficient = State()
    
    # Редактирование ноды
    edit_field_selection = State()
    edit_name = State()
    edit_address = State()
    edit_port = State()
    edit_api_host = State()
    edit_api_port = State()
    edit_usage_coefficient = State()


class InboundStates(StatesGroup):
    """Состояния для управления inbounds"""
    selecting_inbound = State()
    viewing_inbound = State()
    creating_inbound = State()
    editing_inbound = State()
    confirming_delete = State()
    
    # Создание inbound
    enter_remark = State()
    enter_port = State()
    enter_protocol = State()
    enter_settings = State()
    enter_stream_settings = State()
    select_node = State()
    
    # Дополнительные состояния для создания inbound
    entering_inbound_name = State()
    entering_inbound_port = State()
    entering_inbound_settings = State()
    selecting_protocol = State()
    
    # Редактирование inbound
    edit_field_selection = State()
    edit_remark = State()
    edit_port = State()
    edit_protocol = State()
    edit_settings = State()
    edit_stream_settings = State()
    edit_node = State()
    editing_field = State()


class HostStates(StatesGroup):
    """Состояния для управления хостов"""
    selecting_host = State()
    viewing_host = State()
    creating_host = State()
    editing_host = State()
    editing = State()
    editing_field = State()
    confirming_delete = State()
    
    # Создание хоста - ИСПРАВЛЕННЫЕ СОСТОЯНИЯ
    entering_host_name = State()        # Используется в host_handlers.py
    entering_host_address = State()     # Используется в host_handlers.py
    entering_host_port = State()        # Используется в host_handlers.py
    selecting_inbound = State()         # Используется в host_handlers.py
    
    # Старые состояния (для совместимости, если где-то используются)
    enter_name = State()
    enter_domain = State()
    enter_port = State()
    enter_path = State()
    enter_certificate = State()
    
    # Редактирование хоста
    edit_field_selection = State()
    edit_name = State()
    edit_domain = State()
    edit_port = State()
    edit_path = State()
    edit_certificate = State()


class SystemStates(StatesGroup):
    """Состояния для системной статистики"""
    viewing_system_stats = State()
    selecting_stats_period = State()
    viewing_bandwidth_stats = State()
    viewing_node_performance = State()
    exporting_data = State()


class BulkStates(StatesGroup):
    """Состояния для массовых операций"""
    selecting_operation = State()
    confirming_operation = State()
    
    # Массовый сброс трафика
    bulk_traffic_reset_confirm = State()
    
    # Массовое удаление пользователей
    bulk_delete_users_confirm = State()
    bulk_delete_inactive_confirm = State()
    
    # Массовая очистка
    bulk_cleanup_confirm = State()
    
    # Выбор критериев
    select_users_criteria = State()
    enter_inactive_days = State()


class StatsStates(StatesGroup):
    """Состояния для статистики"""
    viewing_stats = State()
    selecting_period = State()
    viewing_detailed_stats = State()
    viewing_node_stats = State()
    viewing_user_stats = State()


class SettingsStates(StatesGroup):
    """Состояния для настроек бота"""
    viewing_settings = State()
    editing_setting = State()
    
    # Настройки панели
    panel_settings = State()
    editing_panel_setting = State()
    
    # Настройки уведомлений
    notification_settings = State()
    editing_notification = State()


class SearchStates(StatesGroup):
    """Состояния для поиска"""
    global_search = State()
    entering_search_term = State()
    viewing_search_results = State()
    
    # Фильтры поиска
    applying_filters = State()
    selecting_filter_type = State()