import customtkinter as ctk
from ui.modal_windows import AddAttackModal, DataViewModal
from ui.grouping_tool import GroupingTool
from ui.view_manager import ViewManager
from ui.materialized_view_manager import MaterializedViewManager
from ui.cte_builder import CTEBuilder


class MainWindow:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.current_module = None
        self.setup_main_window()

    def setup_main_window(self):
        """Настройка главного окна с кнопками"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Управление базой данных DDoS атак",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 30))

        # Основной контейнер с навигацией и содержимым
        self.setup_main_container(main_frame)

    def setup_main_container(self, parent):
        """Настройка основного контейнера с навигацией и содержимым"""
        # Основной фрейм с навигацией и рабочим пространством
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        # Разделитель на навигацию и рабочую область
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        
        # Панель навигации
        nav_frame = ctk.CTkFrame(container, width=200, corner_radius=0)
        nav_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        nav_frame.grid_propagate(False)
        
        # Рабочая область
        self.workspace_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.workspace_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Настройка панели навигации
        self.setup_navigation_panel(nav_frame)
        
        # Показать основной экран по умолчанию
        self.show_main_dashboard()

    def setup_navigation_panel(self, parent):
        """Настройка панели навигации"""
        # Заголовок навигации
        nav_label = ctk.CTkLabel(
            parent,
            text="Навигация",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        nav_label.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Основные разделы
        sections = [
            ("📊 Главная", self.show_main_dashboard, "primary"),
            ("➕ Добавить атаку", self.open_add_attack_modal, "success"),
            ("👁️ Просмотр данных", self.open_data_view_modal, "warning"),
            ("🔍 Расширенный поиск", self.show_advanced_search, "info"),
            ("📋 Подзапросы", self.show_subqueries, "secondary")
        ]
        
        for text, command, color in sections:
            btn = ctk.CTkButton(
                parent,
                text=text,
                command=command,
                fg_color=self.app.colors.get(color, self.app.colors["primary"]),
                hover_color=self.app.colors.get(f"{color}_hover", self.app.colors["primary_hover"]),
                anchor="w",
                height=40
            )
            btn.pack(fill="x", padx=10, pady=2)
        
        # Разделитель
        separator = ctk.CTkFrame(parent, height=2, fg_color="gray30")
        separator.pack(fill="x", padx=20, pady=15)
        
        # Расширенные функции (новые модули)
        advanced_label = ctk.CTkLabel(
            parent,
            text="Расширенные функции",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        advanced_label.pack(pady=(0, 10), padx=20, anchor="w")
        
        advanced_sections = [
            ("📈 Группировка данных", self.show_grouping_tool, "primary"),
            ("👁️ Представления", self.show_view_manager, "info"),
            ("💾 Материализованные представления", self.show_materialized_view_manager, "success"),
            ("🔗 CTE Конструктор", self.show_cte_builder, "warning")
        ]
        
        for text, command, color in advanced_sections:
            btn = ctk.CTkButton(
                parent,
                text=text,
                command=command,
                fg_color=self.app.colors.get(color, self.app.colors["primary"]),
                hover_color=self.app.colors.get(f"{color}_hover", self.app.colors["primary_hover"]),
                anchor="w",
                height=35
            )
            btn.pack(fill="x", padx=10, pady=2)
        
        # База данных
        separator2 = ctk.CTkFrame(parent, height=2, fg_color="gray30")
        separator2.pack(fill="x", padx=20, pady=15)
        
        db_label = ctk.CTkLabel(
            parent,
            text="Управление БД",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        db_label.pack(pady=(0, 10), padx=20, anchor="w")
        
        # Кнопка создания схемы
        ctk.CTkButton(
            parent,
            text="🛠️ Создать схему БД",
            command=self.create_schema,
            fg_color=self.app.colors["primary"],
            hover_color=self.app.colors["primary_hover"],
            anchor="w",
            height=35
        ).pack(fill="x", padx=10, pady=2)
        
        # Информация о системе
        self.setup_system_info(parent)

    def setup_system_info(self, parent):
        """Настройка информации о системе"""
        separator = ctk.CTkFrame(parent, height=2, fg_color="gray30")
        separator.pack(fill="x", padx=20, pady=15)
        
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Информация о базе данных
        try:
            db_info = self.app.api_client.get_database_info()
            db_name = db_info.get('name', 'Неизвестно')
            db_size = db_info.get('size_mb', 0)
            
            ctk.CTkLabel(
                info_frame,
                text=f"📁 База: {db_name}",
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                info_frame,
                text=f"📊 Размер: {db_size:.2f} MB",
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w", pady=2)
            
        except:
            ctk.CTkLabel(
                info_frame,
                text="📁 База данных не подключена",
                font=ctk.CTkFont(size=11, slant="italic")
            ).pack(anchor="w", pady=2)
        
        # Версия приложения
        ctk.CTkLabel(
            info_frame,
            text=f"⚙️ Версия: {self.app.version}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=2)

    def clear_workspace(self):
        """Очистка рабочей области"""
        for widget in self.workspace_frame.winfo_children():
            widget.destroy()
        self.current_module = None

    def show_main_dashboard(self):
        """Показать главную панель"""
        self.clear_workspace()
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.workspace_frame,
            text="Главная панель управления",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Приветственное сообщение
        welcome_frame = ctk.CTkFrame(self.workspace_frame)
        welcome_frame.pack(fill="x", padx=20, pady=10)
        
        welcome_text = """
        Добро пожаловать в систему управления базой данных DDoS атак!
        
        Используйте панель навигации слева для доступа к функциям:
        
        • Добавить атаку - добавление новых записей об атаках
        • Просмотр данных - отображение и фильтрация данных
        • Расширенный поиск - сложные запросы к базе данных
        • Подзапросы - работа с вложенными запросами
        
        Расширенные функции SQL:
        
        • Группировка данных - ROLLUP, CUBE, GROUPING SETS
        • Представления - создание и управление VIEW
        • Материализованные представления - оптимизация запросов
        • CTE Конструктор - построение запросов с WITH
        
        Для начала работы создайте схему базы данных, если это еще не сделано.
        """
        
        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text=welcome_text,
            font=ctk.CTkFont(size=13),
            justify="left"
        )
        welcome_label.pack(padx=20, pady=20)
        
        # Быстрые действия
        self.create_quick_actions()

    def create_quick_actions(self):
        """Создание быстрых действий на главной панели"""
        quick_frame = ctk.CTkFrame(self.workspace_frame)
        quick_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            quick_frame,
            text="Быстрые действия:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        actions_frame = ctk.CTkFrame(quick_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        actions = [
            ("➕ Добавить атаку", self.open_add_attack_modal, "success"),
            ("👁️ Просмотреть данные", self.open_data_view_modal, "warning"),
            ("🛠️ Создать схему", self.create_schema, "primary"),
            ("📊 Группировка", self.show_grouping_tool, "info")
        ]
        
        for i, (text, command, color) in enumerate(actions):
            btn = ctk.CTkButton(
                actions_frame,
                text=text,
                command=command,
                fg_color=self.app.colors[color],
                height=40,
                font=ctk.CTkFont(size=13)
            )
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
            actions_frame.grid_columnconfigure(i%2, weight=1)
        
        actions_frame.grid_rowconfigure(0, weight=1)
        actions_frame.grid_rowconfigure(1, weight=1)

    def show_grouping_tool(self):
        """Показать инструмент группировки"""
        self.clear_workspace()
        self.current_module = GroupingTool(self.workspace_frame, self.app)
        self.app.logger.log_info("Открыт инструмент группировки данных")

    def show_view_manager(self):
        """Показать менеджер представлений"""
        self.clear_workspace()
        self.current_module = ViewManager(self.workspace_frame, self.app)
        self.app.logger.log_info("Открыт менеджер представлений")

    def show_materialized_view_manager(self):
        """Показать менеджер материализованных представлений"""
        self.clear_workspace()
        self.current_module = MaterializedViewManager(self.workspace_frame, self.app)
        self.app.logger.log_info("Открыт менеджер материализованных представлений")

    def show_cte_builder(self):
        """Показать конструктор CTE"""
        self.clear_workspace()
        self.current_module = CTEBuilder(self.workspace_frame, self.app)
        self.app.logger.log_info("Открыт конструктор CTE")

    def show_advanced_search(self):
        """Показать расширенный поиск"""
        self.clear_workspace()
        # Здесь будет интеграция с существующим модулем расширенного поиска
        # Временно показываем заглушку
        placeholder_label = ctk.CTkLabel(
            self.workspace_frame,
            text="Расширенный поиск (будет реализован позже)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        placeholder_label.pack(pady=50)
        self.app.logger.log_info("Открыт расширенный поиск")

    def show_subqueries(self):
        """Показать работу с подзапросами"""
        self.clear_workspace()
        # Здесь будет интеграция с существующим модулем подзапросов
        # Временно показываем заглушку
        placeholder_label = ctk.CTkLabel(
            self.workspace_frame,
            text="Работа с подзапросами (будет реализован позже)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        placeholder_label.pack(pady=50)
        self.app.logger.log_info("Открыта работа с подзапросами")

    def create_schema(self):
        """Создание схемы БД"""
        try:
            self.app.logger.log_info("Создание схемы базы данных...")
            result = self.app.api_client.initialize_database()

            if result.get('success') or result.get('status') == 'already_exists':
                self.app.logger.log_database_operation("CREATE_SCHEMA", True)
                if result.get('status') == 'already_exists':
                    self.app.show_success("Таблицы уже существуют в базе данных!")
                else:
                    self.app.show_success("Схема базы данных успешно создана!")
            else:
                self.app.logger.log_database_operation("CREATE_SCHEMA", False)
                self.app.show_error("Не удалось создать схему базы данных")

        except Exception as e:
            # Если таблицы уже существуют - это не ошибка
            if "409" in str(e) or "already exists" in str(e).lower():
                self.app.logger.log_database_operation("CREATE_SCHEMA", True)
                self.app.show_success("Таблицы уже существуют в базе данных!")
            else:
                self.app.logger.log_error(f"Ошибка создания схемы БД: {e}")
                self.app.logger.log_database_operation("CREATE_SCHEMA", False)
                self.app.show_error(f"Ошибка создания схемы: {e}")

    def open_add_attack_modal(self):
        """Открытие модального окна добавления новой атаки"""
        self.app.logger.log_info("Открытие модального окна добавления атаки")
        AddAttackModal(self.parent, self.app)

    def open_data_view_modal(self):
        """Открытие модального окна просмотра данных"""
        self.app.logger.log_info("Открытие модального окна просмотра данных")
        DataViewModal(self.parent, self.app)