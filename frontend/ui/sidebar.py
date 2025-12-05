import customtkinter as ctk
from datetime import datetime


class Sidebar:
    def __init__(self, parent, app):
        self.app = app
        self.setup_ui(parent)

    def setup_ui(self, parent):
        """Создание боковой панели с прокруткой"""
        # Основной контейнер для сайдбара
        sidebar_container = ctk.CTkFrame(parent, width=280, fg_color="transparent")
        sidebar_container.pack(side="left", fill="y", padx=(0, 5), pady=0)
        sidebar_container.pack_propagate(False)

        # Canvas для прокрутки
        canvas = ctk.CTkCanvas(sidebar_container, bg=self.app.colors["card_bg"], 
                              highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(sidebar_container, orientation="vertical", 
                                    command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color=self.app.colors["card_bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковка canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Функция для прокрутки колесом мыши
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        # Создаем содержимое сайдбара внутри scrollable_frame
        self.create_sidebar_content(scrollable_frame)

    def create_sidebar_content(self, parent):
        """Создание содержимого боковой панели"""
        # Логотип
        self.create_logo_section(parent)

        # Навигация
        self.create_navigation_section(parent)

        # Статистика
        self.create_stats_section(parent)

    def create_logo_section(self, parent):
        """Создание секции с логотипом"""
        logo_frame = ctk.CTkFrame(parent, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(logo_frame, text="🛡️", font=ctk.CTkFont(size=24)).pack()
        ctk.CTkLabel(logo_frame, text="DDoS Manager",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.app.colors["text_light"]).pack(pady=(5, 0))
        
        # Версия и статус
        ctk.CTkLabel(logo_frame, text="Advanced SQL Edition",
                     font=ctk.CTkFont(size=10, slant="italic"),
                     text_color=self.app.colors["text_muted"]).pack(pady=(2, 0))

    def create_navigation_section(self, parent):
        """Создание секции навигации - УПРОЩЕННАЯ ВЕРСИЯ"""
        nav_frame = ctk.CTkFrame(parent, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15, pady=(0, 20))

        # Основная навигация
        ctk.CTkLabel(nav_frame, text="Основные функции",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        main_nav_buttons = [
            ("🏠 Главная", self.app.show_dashboard),
            ("➕ Добавить атаку", self.app.show_attack_form),
            ("📋 Просмотр данных", self.app.show_attacks_list),
        ]

        for text, command in main_nav_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

        separator = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator.pack(fill="x", pady=12)

        # Расширенные SQL функции - ГРУППИРОВАННЫЕ
        ctk.CTkLabel(nav_frame, text="SQL Анализ",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        sql_analysis_buttons = [
            ("📊 Группировка", self.app.show_grouping_tool),
            ("📈 Агрегации", self.app.show_aggregation_tool),
            ("👁️ Представления", self.app.show_view_manager),
            ("💾 Матер. представления", self.app.show_materialized_view_manager),
            ("🔄 CTE", self.app.show_cte_builder),
        ]

        for text, command in sql_analysis_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

        separator2 = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator2.pack(fill="x", pady=12)

        # Поиск и фильтрация
        ctk.CTkLabel(nav_frame, text="Поиск и фильтрация",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        search_buttons = [
            ("🔍 Текстовый поиск", self.app.show_text_search_tool),
            ("🎛️ Фильтры", self.app.show_subquery_filters),
            ("🔄 Regex поиск", self.app.show_regex_search_tool),
            ("🔍 Конструктор запросов", self.app.show_advanced_query_builder),
        ]

        for text, command in search_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

        separator3 = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator3.pack(fill="x", pady=12)

        # Расширенные функции
        ctk.CTkLabel(nav_frame, text="Расширенные функции",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        advanced_buttons = [
            ("🔗 Мастер JOIN", self.app.show_join_wizard),
            ("📖 Строковые функции", self.app.show_string_functions_tool),
            ("🎨 Пользовательские типы", self.app.show_custom_types_manager),
            ("🔧 Структура БД", self.app.show_alter_table_manager),
        ]

        for text, command in advanced_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

        separator4 = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator4.pack(fill="x", pady=12)

        # Система
        ctk.CTkLabel(nav_frame, text="Система",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        system_buttons = [
            ("🛠️ Создать схему", self.app.create_schema),
            ("📊 Статистика", self.app.show_database_stats),
            ("📝 Логи", self.app.show_logs),
            ("⚙️ Настройки", self.app.show_settings),
        ]

        for text, command in system_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

    def create_stats_section(self, parent):
        """Создание секции статистики"""
        stats_frame = ctk.CTkFrame(parent, fg_color="#2a2a4a", corner_radius=8)
        stats_frame.pack(fill="x", padx=15, pady=(0, 20))

        ctk.CTkLabel(stats_frame, text="Статистика",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # Динамическая статистика
        self.stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=15, pady=(0, 10))
        
        self.update_stats()

    def update_stats(self):
        """Обновление статистики"""
        # Очищаем старую статистику
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        try:
            # Упрощенная статистика
            stats_items = [
                ("📊 Атак:", str(len(self.app.attacks)) if hasattr(self.app, 'attacks') else "0"),
                ("⏱️ Время:", datetime.now().strftime("%H:%M")),
                ("🔄 Версия:", "SQL Edition"),
            ]
            
            for icon_text, value in stats_items:
                stat_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent", height=25)
                stat_frame.pack(fill="x", pady=2)
                stat_frame.pack_propagate(False)
                
                ctk.CTkLabel(stat_frame, text=icon_text, 
                        font=ctk.CTkFont(size=11),
                        width=80, anchor="w").pack(side="left")
                ctk.CTkLabel(stat_frame, text=value, 
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=self.app.colors["text_light"]).pack(side="right")
                    
        except Exception as e:
            # Если произошла ошибка
            error_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            error_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(error_frame, text="Ошибка загрузки",
                    font=ctk.CTkFont(size=11)).pack(anchor="w")