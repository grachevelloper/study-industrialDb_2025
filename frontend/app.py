import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.header import Header
from ui.forms import AttackForm
from ui.table import AttackTable
from ui.dashboard import Dashboard
from api.client import DDOSDatabaseClient
import threading
from tkinter import messagebox
import uuid
import json
from datetime import datetime


class DDoSAttackApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("DDoS Attack Manager")
        self.window.geometry("1400x800")
        self.window.minsize(1200, 700)

        # Инициализация клиента БД вместо API клиента
        self.api_client = DDOSDatabaseClient()

        # Загрузка данных с сервера
        self.attacks = []

        # Цветовая схема
        self.colors = {
            "primary": "#2b5876",
            "secondary": "#4e4376",
            "accent": "#ff6b6b",
            "success": "#4ecdc4",
            "warning": "#ffd166",
            "danger": "#ff6b6b",
            "dark_bg": "#1a1a2e",
            "card_bg": "#16213e",
            "text_light": "#ffffff",
            "text_muted": "#b0b0b0"
        }

        # Enum значения для формы (только разрешенные типы)
        self.frequency_levels = ["low", "medium", "high", "very_high", "continuous"]
        self.danger_levels = ["low", "medium", "high", "critical"]
        self.attack_types = ["volumetric", "protocol", "application", "amplification"]
        self.protocols = ["tcp", "udp", "dns", "http", "https", "icmp"]

        self.current_edit_id = None
        self.setup_ui()

    def setup_ui(self):
        """Создание интерфейса с тремя вкладками"""
        # Основной фрейм
        main_frame = ctk.CTkFrame(self.window, fg_color=self.colors["dark_bg"])
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Создание layout
        self.create_layout(main_frame)

    def create_layout(self, parent):
        """Создание основного layout"""
        # Основной контейнер
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=0, pady=0)

        # Инициализация компонентов UI
        self.sidebar = Sidebar(container, self)
        self.header = Header(container, self)
        self.content_frame = self.create_content_frame(container)

        # Показываем главную страницу по умолчанию
        self.show_dashboard()

    def create_content_frame(self, parent):
        """Создание контентной области"""
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        return content_frame

    def clear_content(self):
        """Очистить контентную область"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        """Показать главную страницу"""
        self.clear_content()
        self.header.set_title("Main Dashboard")
        Dashboard(self.content_frame, self)

    def show_attack_form(self):
        """Показать форму добавления атаки"""
        self.clear_content()
        self.header.set_title("Add New Attack")
        AttackForm(self.content_frame, self)

    def show_attacks_list(self):
        """Показать таблицу с атаками"""
        self.clear_content()
        self.header.set_title("View Attacks Table")
        AttackTable(self.content_frame, self)

    # НОВЫЕ МЕТОДЫ ДЛЯ ДОПОЛНИТЕЛЬНОЙ ФУНКЦИОНАЛЬНОСТИ
    def show_alter_table_manager(self):
        """Показать менеджер ALTER TABLE операций"""
        self.clear_content()
        self.header.set_title("Database Structure Manager")
        try:
            from ui.alter_table_manager import AlterTableManager
            AlterTableManager(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load Alter Table Manager: {e}")

    def show_advanced_query_builder(self):
        """Показать расширенный построитель запросов"""
        self.clear_content()
        self.header.set_title("Advanced Query Builder")
        try:
            from ui.advanced_query_builder import AdvancedQueryBuilder
            AdvancedQueryBuilder(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load Query Builder: {e}")

    def show_text_search_tool(self):
        """Показать инструмент текстового поиска"""
        self.clear_content()
        self.header.set_title("Advanced Text Search")
        try:
            from ui.text_search_tool import TextSearchTool
            TextSearchTool(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load Text Search Tool: {e}")

    def show_string_functions_tool(self):
        """Показать инструмент строковых функций"""
        self.clear_content()
        self.header.set_title("String Functions")
        try:
            from ui.string_functions_tool import StringFunctionsTool
            StringFunctionsTool(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load String Functions Tool: {e}")
            
    def show_subquery_filters(self):
        """Показать окно фильтров с подзапросами"""
        self.clear_content()
        self.header.set_title("Subquery Filters")
        try:
            from ui.subquery_filters import SubqueryFilters
            SubqueryFilters(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load Subquery Filters: {e}")

    def show_custom_types_manager(self):
        """Показать менеджер пользовательских типов"""
        self.clear_content()
        self.header.set_title("Custom Types Manager")
        try:
            from ui.custom_types_manager import CustomTypesManager
            CustomTypesManager(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load Custom Types Manager: {e}")

    def show_join_wizard(self):
        """Показать мастер соединений JOIN"""
        self.clear_content()
        self.header.set_title("JOIN Wizard")
        try:
            from ui.join_wizard import JoinWizard
            JoinWizard(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load JOIN Wizard: {e}")

    # МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЬСКИМИ ТИПАМИ (через api_client)
    def create_custom_type(self, name, type_class, values):
        """Создание пользовательского типа через API клиент"""
        return self.api_client.create_custom_type(name, type_class, values)

    def get_custom_types(self):
        """Получение всех пользовательских типов через API клиент"""
        return self.api_client.get_custom_types()

    def delete_custom_type(self, type_id):
        """Удаление пользовательского типа через API клиент"""
        return self.api_client.delete_custom_type(type_id)

    def execute_custom_query(self, query, params=()):
        """Выполнение произвольного SQL запроса через API клиент"""
        return self.api_client.execute_custom_query(query, params)

    def refresh_attacks(self):
        """Обновление списка атак с сервера"""
        def refresh_thread():
            try:
                attacks = self.api_client.get_all_attacks()
                self.window.after(0, lambda: self.on_attacks_loaded(attacks))
            except Exception as e:
                self.window.after(0, lambda: self.show_error(f"Failed to refresh attacks: {e}"))

        thread = threading.Thread(target=refresh_thread)
        thread.daemon = True
        thread.start()

    def on_attacks_loaded(self, attacks):
        """Обработка загруженных атак"""
        self.attacks = attacks
        self.update_stats()

    def update_stats(self):
        """Обновление статистики"""
        if hasattr(self, 'sidebar'):
            self.sidebar.update_stats()
        if hasattr(self, 'header'):
            self.header.update_stats()

    def show_regex_search_tool(self):
        """Показать инструмент регулярных выражений"""
        self.clear_content()
        self.header.set_title("Advanced Text Search")
        try:
            from ui.regex_search_tool import RegexSearchTool
            RegexSearchTool(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load Regex Search Tool: {e}")

    def show_aggregation_tool(self):
        """Показать инструмент агрегирования"""
        self.clear_content()
        self.header.set_title("Aggregation Tool")
        try:
            from ui.aggregation_tool import AggregationTool
            AggregationTool(self.content_frame, self)
        except ImportError as e:
            self.show_error(f"Module not found: {e}")
        except Exception as e:
            self.show_error(f"Failed to load Aggregation Tool: {e}")

    def show_error(self, message):
        """Показ ошибки"""
        messagebox.showerror("Error", message)

    def show_success(self, message):
        """Показ успеха"""
        messagebox.showinfo("Success", message)

    def run(self):
        """Запуск приложения"""
        self.window.mainloop()