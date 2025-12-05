# ui/materialized_view_manager.py
import customtkinter as ctk
from tkinter import messagebox, ttk
from typing import List, Dict, Optional
import json
from datetime import datetime

class MaterializedViewManager:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.current_materialized_views = []
        self.refresh_schedules = []
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса управления материализованными представлениями"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Materialized View Manager",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Основной фрейм с вкладками
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Вкладка: Список материализованных представлений
        self.mv_list_tab = self.tabview.add("Materialized Views")
        self.setup_mv_list_tab()
        
        # Вкладка: Создание материализованного представления
        self.create_mv_tab = self.tabview.add("Create Materialized View")
        self.setup_create_mv_tab()
        
        # Вкладка: Управление обновлениями
        self.refresh_tab = self.tabview.add("Refresh Management")
        self.setup_refresh_tab()
        
        # Вкладка: Статистика использования
        self.stats_tab = self.tabview.add("Usage Statistics")
        self.setup_stats_tab()

        # Загружаем список материализованных представлений при запуске
        self.load_materialized_views()

    def setup_mv_list_tab(self):
        """Настройка вкладки списка материализованных представлений"""
        main_frame = ctk.CTkFrame(self.mv_list_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель управления
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(controls_frame, text="Refresh List", 
                     command=self.load_materialized_views,
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(controls_frame, text="Refresh Selected", 
                     command=self.refresh_selected_mv,
                     fg_color=self.app.colors["info"],
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(controls_frame, text="Refresh All", 
                     command=self.refresh_all_mv,
                     fg_color=self.app.colors["success"],
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(controls_frame, text="Delete Selected", 
                     command=self.delete_selected_mv,
                     fg_color=self.app.colors["warning"],
                     width=120).pack(side="left", padx=5)
        
        # Информационная панель
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))
        
        self.last_refresh_label = ctk.CTkLabel(info_frame, 
                                              text="Last refresh: Never",
                                              font=ctk.CTkFont(size=12, slant="italic"))
        self.last_refresh_label.pack(side="left", padx=5)
        
        self.total_size_label = ctk.CTkLabel(info_frame, 
                                            text="Total size: 0 KB",
                                            font=ctk.CTkFont(size=12, slant="italic"))
        self.total_size_label.pack(side="right", padx=5)
        
        # Список материализованных представлений
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        # Дерево для отображения материализованных представлений
        columns = ("name", "rows", "size_kb", "last_refresh", "refresh_mode", "status")
        self.mv_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Настройка колонок
        self.mv_tree.heading("name", text="Materialized View")
        self.mv_tree.heading("rows", text="Rows")
        self.mv_tree.heading("size_kb", text="Size (KB)")
        self.mv_tree.heading("last_refresh", text="Last Refresh")
        self.mv_tree.heading("refresh_mode", text="Refresh Mode")
        self.mv_tree.heading("status", text="Status")
        
        self.mv_tree.column("name", width=200)
        self.mv_tree.column("rows", width=80)
        self.mv_tree.column("size_kb", width=100)
        self.mv_tree.column("last_refresh", width=150)
        self.mv_tree.column("refresh_mode", width=120)
        self.mv_tree.column("status", width=100)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.mv_tree.yview)
        self.mv_tree.configure(yscrollcommand=scrollbar.set)
        
        self.mv_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Привязка события двойного клика
        self.mv_tree.bind("<Double-1>", self.on_mv_double_click)
        
        # Контекстное меню
        self.setup_context_menu()

    def setup_context_menu(self):
        """Настройка контекстного меню для дерева"""
        self.context_menu = ctk.CTkMenu(self.parent, tearoff=0)
        self.context_menu.add_command(label="Refresh", command=self.refresh_selected_mv)
        self.context_menu.add_command(label="Show Data", command=self.show_mv_data)
        self.context_menu.add_command(label="Show Structure", command=self.show_mv_structure)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_selected_mv)
        
        # Привязка события правой кнопки мыши
        self.mv_tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Показать контекстное меню"""
        try:
            item = self.mv_tree.identify_row(event.y)
            if item:
                self.mv_tree.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def setup_create_mv_tab(self):
        """Настройка вкладки создания материализованного представления"""
        main_frame = ctk.CTkFrame(self.create_mv_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Форма создания
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="x", pady=(0, 15))
        
        # Название материализованного представления
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(name_frame, text="MV Name:", width=120).pack(side="left")
        self.mv_name_entry = ctk.CTkEntry(name_frame, placeholder_text="Enter materialized view name")
        self.mv_name_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Режим обновления
        refresh_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        refresh_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(refresh_frame, text="Refresh Mode:", width=120).pack(side="left")
        
        self.refresh_mode_var = ctk.StringVar(value="ON DEMAND")
        refresh_modes = ["ON DEMAND", "ON COMMIT", "FAST", "COMPLETE"]
        self.refresh_mode_combo = ctk.CTkComboBox(refresh_frame, 
                                                 values=refresh_modes,
                                                 variable=self.refresh_mode_var,
                                                 width=200)
        self.refresh_mode_combo.pack(side="left", padx=(10, 0))
        
        # Параметры построения
        build_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        build_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(build_frame, text="Build Options:", width=120).pack(side="left")
        
        self.build_option_var = ctk.StringVar(value="IMMEDIATE")
        immediate_rb = ctk.CTkRadioButton(build_frame, text="Build Immediately", 
                                         variable=self.build_option_var, value="IMMEDIATE")
        immediate_rb.pack(side="left", padx=(10, 20))
        
        deferred_rb = ctk.CTkRadioButton(build_frame, text="Defer Build", 
                                        variable=self.build_option_var, value="DEFERRED")
        deferred_rb.pack(side="left")
        
        # SQL запрос
        query_frame = ctk.CTkFrame(main_frame)
        query_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(query_frame, text="SQL Query for Materialized View:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Шаблоны для сложных запросов
        templates_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        templates_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        template_buttons = [
            ("Aggregation MV", self.insert_aggregation_template),
            ("Join MV", self.insert_join_template),
            ("Window Function MV", self.insert_window_template),
            ("Hierarchy MV", self.insert_hierarchy_template)
        ]
        
        for text, command in template_buttons:
            btn = ctk.CTkButton(templates_frame, text=text, command=command, width=140)
            btn.pack(side="left", padx=2)
        
        # Поле для SQL запроса
        self.mv_query_text = ctk.CTkTextbox(query_frame, height=150)
        self.mv_query_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Параметры индексации
        index_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        index_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(index_frame, text="Indexing Options:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(0, 5))
        
        index_options_frame = ctk.CTkFrame(index_frame, fg_color="transparent")
        index_options_frame.pack(fill="x", padx=15, pady=5)
        
        self.create_index_var = ctk.BooleanVar(value=True)
        index_checkbox = ctk.CTkCheckBox(index_options_frame, text="Create default index",
                                        variable=self.create_index_var)
        index_checkbox.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(index_options_frame, text="Index Columns:").pack(side="left")
        self.index_columns_entry = ctk.CTkEntry(index_options_frame, width=150, 
                                               placeholder_text="col1, col2, ...")
        self.index_columns_entry.pack(side="left", padx=(10, 0))
        
        # Кнопки создания
        create_buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        create_buttons_frame.pack(fill="x")
        
        ctk.CTkButton(create_buttons_frame, text="Create MV", 
                     command=self.create_materialized_view,
                     fg_color=self.app.colors["success"]).pack(side="left", padx=5)
        
        ctk.CTkButton(create_buttons_frame, text="Validate Query", 
                     command=self.validate_mv_query).pack(side="left", padx=5)
        
        ctk.CTkButton(create_buttons_frame, text="Estimate Size", 
                     command=self.estimate_mv_size).pack(side="left", padx=5)
        
        ctk.CTkButton(create_buttons_frame, text="Clear Form", 
                     command=self.clear_mv_form).pack(side="left", padx=5)

    def setup_refresh_tab(self):
        """Настройка вкладки управления обновлениями"""
        main_frame = ctk.CTkFrame(self.refresh_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель настройки расписания
        schedule_frame = ctk.CTkFrame(main_frame)
        schedule_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(schedule_frame, text="Refresh Schedule", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Выбор MV для расписания
        mv_select_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
        mv_select_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(mv_select_frame, text="Materialized View:", width=120).pack(side="left")
        self.schedule_mv_combo = ctk.CTkComboBox(mv_select_frame, width=200)
        self.schedule_mv_combo.pack(side="left", padx=(10, 0))
        
        # Настройка расписания
        schedule_config_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
        schedule_config_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(schedule_config_frame, text="Schedule Type:", width=120).pack(side="left")
        
        self.schedule_type_var = ctk.StringVar(value="HOURLY")
        schedule_types = ["HOURLY", "DAILY", "WEEKLY", "MONTHLY", "CUSTOM"]
        self.schedule_type_combo = ctk.CTkComboBox(schedule_config_frame, 
                                                  values=schedule_types,
                                                  variable=self.schedule_type_var,
                                                  width=120)
        self.schedule_type_combo.pack(side="left", padx=(10, 20))
        
        # Время для расписания
        ctk.CTkLabel(schedule_config_frame, text="Time (HH:MM):").pack(side="left")
        self.schedule_time_entry = ctk.CTkEntry(schedule_config_frame, width=80, 
                                               placeholder_text="14:30")
        self.schedule_time_entry.pack(side="left", padx=(10, 20))
        
        # Кнопки расписания
        ctk.CTkButton(schedule_config_frame, text="Add Schedule", 
                     command=self.add_refresh_schedule,
                     width=120).pack(side="right")
        
        # Список активных расписаний
        schedules_frame = ctk.CTkFrame(main_frame)
        schedules_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(schedules_frame, text="Active Refresh Schedules", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Таблица расписаний
        columns = ("mv_name", "schedule_type", "next_refresh", "last_run", "status")
        self.schedules_tree = ttk.Treeview(schedules_frame, columns=columns, show="headings", height=8)
        
        self.schedules_tree.heading("mv_name", text="Materialized View")
        self.schedules_tree.heading("schedule_type", text="Schedule")
        self.schedules_tree.heading("next_refresh", text="Next Refresh")
        self.schedules_tree.heading("last_run", text="Last Run")
        self.schedules_tree.heading("status", text="Status")
        
        self.schedules_tree.column("mv_name", width=200)
        self.schedules_tree.column("schedule_type", width=100)
        self.schedules_tree.column("next_refresh", width=150)
        self.schedules_tree.column("last_run", width=150)
        self.schedules_tree.column("status", width=100)
        
        scrollbar = ttk.Scrollbar(schedules_frame, orient="vertical", command=self.schedules_tree.yview)
        self.schedules_tree.configure(yscrollcommand=scrollbar.set)
        
        self.schedules_tree.pack(side="left", fill="both", expand=True, padx=(15, 0))
        scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=5)
        
        # Кнопки управления расписаниями
        schedule_buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        schedule_buttons_frame.pack(fill="x")
        
        ctk.CTkButton(schedule_buttons_frame, text="Run Scheduled Now", 
                     command=self.run_scheduled_refresh).pack(side="left", padx=5)
        
        ctk.CTkButton(schedule_buttons_frame, text="Remove Schedule", 
                     command=self.remove_schedule).pack(side="left", padx=5)
        
        ctk.CTkButton(schedule_buttons_frame, text="Disable All", 
                     command=self.disable_all_schedules).pack(side="left", padx=5)

    def setup_stats_tab(self):
        """Настройка вкладки статистики использования"""
        main_frame = ctk.CTkFrame(self.stats_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель статистики
        stats_panel_frame = ctk.CTkFrame(main_frame)
        stats_panel_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(stats_panel_frame, text="Performance Statistics", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Показатели в виде карточек
        metrics_frame = ctk.CTkFrame(stats_panel_frame, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=15, pady=10)
        
        # Создаем метрики
        self.metrics = {}
        metric_configs = [
            ("total_mv", "Total MVs", "0"),
            ("total_rows", "Total Rows", "0"),
            ("total_size", "Total Size", "0 KB"),
            ("avg_refresh_time", "Avg Refresh Time", "0 ms"),
            ("last_24h_refreshes", "Last 24h Refreshes", "0"),
            ("hit_ratio", "Cache Hit Ratio", "0%")
        ]
        
        for i, (key, label, value) in enumerate(metric_configs):
            metric_frame = ctk.CTkFrame(metrics_frame)
            metric_frame.pack(side="left", fill="both", expand=True, padx=2)
            
            ctk.CTkLabel(metric_frame, text=label, 
                        font=ctk.CTkFont(size=11)).pack(pady=(10, 5))
            
            value_label = ctk.CTkLabel(metric_frame, text=value, 
                                      font=ctk.CTkFont(size=16, weight="bold"))
            value_label.pack(pady=(0, 10))
            
            self.metrics[key] = value_label
        
        # Графики и детальная статистика
        detail_frame = ctk.CTkFrame(main_frame)
        detail_frame.pack(fill="both", expand=True)
        
        # Вкладки детальной статистики
        detail_tabs = ctk.CTkTabview(detail_frame)
        detail_tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Вкладка использования
        usage_tab = detail_tabs.add("Usage Patterns")
        self.setup_usage_tab(usage_tab)
        
        # Вкладка производительности
        perf_tab = detail_tabs.add("Performance")
        self.setup_performance_tab(perf_tab)
        
        # Вкладка рекомендаций
        recommendations_tab = detail_tabs.add("Recommendations")
        self.setup_recommendations_tab(recommendations_tab)

    def setup_usage_tab(self, parent):
        """Настройка вкладки шаблонов использования"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Usage Statistics by MV", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
        # Таблица использования
        usage_text = ctk.CTkTextbox(frame, height=200)
        usage_text.pack(fill="both", expand=True)
        
        # Заглушка для данных
        usage_text.insert("1.0", "Usage statistics will be displayed here\n\n")
        usage_text.insert("end", "1. Query count per MV\n")
        usage_text.insert("end", "2. Average execution time\n")
        usage_text.insert("end", "3. User access patterns\n")
        usage_text.insert("end", "4. Peak usage times\n")
        
        usage_text.configure(state="disabled")

    def setup_performance_tab(self, parent):
        """Настройка вкладки производительности"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Performance Metrics", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
        # Показатели производительности
        perf_text = ctk.CTkTextbox(frame, height=200)
        perf_text.pack(fill="both", expand=True)
        
        # Заглушка для данных
        perf_text.insert("1.0", "Performance metrics will be displayed here\n\n")
        perf_text.insert("end", "1. Refresh duration history\n")
        perf_text.insert("end", "2. Index usage statistics\n")
        perf_text.insert("end", "3. Cache effectiveness\n")
        perf_text.insert("end", "4. Disk I/O patterns\n")
        
        perf_text.configure(state="disabled")

    def setup_recommendations_tab(self, parent):
        """Настройка вкладки рекомендаций"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Optimization Recommendations", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 10))
        
        # Рекомендации
        rec_text = ctk.CTkTextbox(frame, height=200)
        rec_text.pack(fill="both", expand=True)
        
        # Заглушка для рекомендаций
        rec_text.insert("1.0", "Optimization recommendations will be displayed here\n\n")
        rec_text.insert("end", "1. Index suggestions\n")
        rec_text.insert("end", "2. Refresh schedule optimization\n")
        rec_text.insert("end", "3. Partitioning recommendations\n")
        rec_text.insert("end", "4. Storage optimization tips\n")
        
        rec_text.configure(state="disabled")

    def load_materialized_views(self):
        """Загрузка списка материализованных представлений из БД"""
        try:
            # Получаем список материализованных представлений
            # Для SQLite - эмуляция, так как нет native поддержки
            query = """
            SELECT name, type, tbl_name, sql 
            FROM sqlite_master 
            WHERE type = 'materialized view' OR name LIKE 'mv_%'
            ORDER BY name
            """
            
            results = self.app.api_client.execute_custom_query(query)
            self.current_materialized_views = []
            
            # Очищаем дерево
            for item in self.mv_tree.get_children():
                self.mv_tree.delete(item)
            
            # Обновляем комбобокс
            mv_names = []
            
            # Заполняем список
            for row in results:
                mv_name = row[0]
                mv_type = row[1]
                table_name = row[2]
                sql_definition = row[3] if row[3] else ""
                
                # Получаем статистику
                row_count = self.get_mv_row_count(mv_name)
                size_kb = self.estimate_mv_size_kb(mv_name)
                last_refresh = self.get_last_refresh_time(mv_name)
                
                # Определяем статус
                status = "ACTIVE" if row_count > 0 else "EMPTY"
                
                # Добавляем в дерево
                self.mv_tree.insert("", "end", values=(
                    mv_name,
                    row_count,
                    size_kb,
                    last_refresh,
                    "ON DEMAND",
                    status
                ))
                
                # Сохраняем для использования
                self.current_materialized_views.append({
                    'name': mv_name,
                    'type': mv_type,
                    'table_name': table_name,
                    'sql': sql_definition,
                    'row_count': row_count,
                    'size_kb': size_kb,
                    'last_refresh': last_refresh,
                    'status': status
                })
                
                mv_names.append(mv_name)
            
            # Обновляем комбобоксы
            self.schedule_mv_combo.configure(values=mv_names)
            
            # Обновляем статистику
            self.update_metrics()
            
            messagebox.showinfo("Success", f"Loaded {len(results)} materialized views")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load materialized views: {e}")

    def get_mv_row_count(self, mv_name):
        """Получение количества строк в материализованном представлении"""
        try:
            query = f"SELECT COUNT(*) FROM {mv_name}"
            result = self.app.api_client.execute_custom_query(query)
            return result[0][0] if result else 0
        except:
            return 0

    def estimate_mv_size_kb(self, mv_name):
        """Оценка размера материализованного представления в КБ"""
        try:
            # Простая эмуляция - можно улучшить для реальной БД
            query = f"SELECT COUNT(*) FROM {mv_name}"
            result = self.app.api_client.execute_custom_query(query)
            row_count = result[0][0] if result else 0
            
            # Предполагаем средний размер строки ~100 байт
            estimated_size = (row_count * 100) // 1024
            return f"{estimated_size} KB"
        except:
            return "N/A"

    def get_last_refresh_time(self, mv_name):
        """Получение времени последнего обновления"""
        try:
            # Эмуляция - в реальной БД можно использовать системные таблицы
            query = "SELECT datetime('now', 'localtime')"
            result = self.app.api_client.execute_custom_query(query)
            return result[0][0] if result else "Never"
        except:
            return "Never"

    def update_metrics(self):
        """Обновление метрик статистики"""
        total_mvs = len(self.current_materialized_views)
        total_rows = sum(mv.get('row_count', 0) for mv in self.current_materialized_views)
        
        # Обновляем метрики
        self.metrics['total_mv'].configure(text=str(total_mvs))
        self.metrics['total_rows'].configure(text=str(total_rows))
        
        # Обновляем статусные метки
        if total_mvs > 0:
            last_mv = self.current_materialized_views[-1]
            self.last_refresh_label.configure(
                text=f"Last refresh: {last_mv.get('last_refresh', 'Never')}"
            )
            
            # Общий размер
            total_size = 0
            for mv in self.current_materialized_views:
                size_str = mv.get('size_kb', '0 KB')
                if 'KB' in size_str:
                    total_size += int(size_str.replace(' KB', ''))
            
            self.total_size_label.configure(text=f"Total size: {total_size} KB")

    def refresh_selected_mv(self):
        """Обновление выбранного материализованного представления"""
        selection = self.mv_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a materialized view")
            return
        
        item = self.mv_tree.item(selection[0])
        mv_name = item['values'][0]
        
        if not messagebox.askyesno("Confirm Refresh", 
                                  f"Refresh materialized view '{mv_name}'?"):
            return
        
        try:
            # Выполняем обновление
            # Для SQLite - эмуляция через пересоздание
            refresh_query = f"DROP VIEW IF EXISTS {mv_name};"
            
            # Находим определение MV
            mv_info = None
            for mv in self.current_materialized_views:
                if mv['name'] == mv_name:
                    mv_info = mv
                    break
            
            if mv_info and 'sql' in mv_info:
                # Извлекаем SQL из CREATE MATERIALIZED VIEW
                sql = mv_info['sql']
                if "CREATE MATERIALIZED VIEW" in sql.upper():
                    # Удаляем префикс создания
                    sql = sql.split("AS", 1)[1].strip()
                
                # Создаем заново
                create_query = f"CREATE VIEW {mv_name} AS {sql}"
                refresh_query += create_query
            
            self.app.api_client.execute_custom_query(refresh_query)
            
            # Обновляем информацию
            self.load_materialized_views()
            
            messagebox.showinfo("Success", f"Materialized view '{mv_name}' refreshed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh: {e}")

    def refresh_all_mv(self):
        """Обновление всех материализованных представлений"""
        if not self.current_materialized_views:
            messagebox.showwarning("Warning", "No materialized views to refresh")
            return
        
        if not messagebox.askyesno("Confirm Refresh All", 
                                  f"Refresh all {len(self.current_materialized_views)} materialized views?"):
            return
        
        try:
            # Обновляем все MV
            for mv in self.current_materialized_views:
                mv_name = mv['name']
                
                # Эмуляция обновления
                refresh_query = f"DROP VIEW IF EXISTS {mv_name};"
                
                if 'sql' in mv:
                    sql = mv['sql']
                    if "CREATE MATERIALIZED VIEW" in sql.upper():
                        sql = sql.split("AS", 1)[1].strip()
                    
                    create_query = f"CREATE VIEW {mv_name} AS {sql}"
                    refresh_query += create_query
                
                self.app.api_client.execute_custom_query(refresh_query)
            
            # Обновляем список
            self.load_materialized_views()
            
            messagebox.showinfo("Success", f"All materialized views refreshed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh all: {e}")

    def delete_selected_mv(self):
        """Удаление выбранного материализованного представления"""
        selection = self.mv_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a materialized view to delete")
            return
        
        item = self.mv_tree.item(selection[0])
        mv_name = item['values'][0]
        
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete materialized view '{mv_name}'?"):
            return
        
        try:
            # Выполняем удаление
            drop_query = f"DROP VIEW {mv_name}"
            self.app.api_client.execute_custom_query(drop_query)
            
            # Обновляем список
            self.load_materialized_views()
            
            messagebox.showinfo("Success", f"Materialized view '{mv_name}' deleted successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")

    def on_mv_double_click(self, event):
        """Обработка двойного клика по материализованному представлению"""
        selection = self.mv_tree.selection()
        if selection:
            # Показываем диалог с деталями
            item = self.mv_tree.item(selection[0])
            mv_name = item['values'][0]
            
            # Находим информацию о MV
            mv_info = None
            for mv in self.current_materialized_views:
                if mv['name'] == mv_name:
                    mv_info = mv
                    break
            
            if mv_info:
                dialog = MaterializedViewDetailsDialog(self.parent, mv_info)
                dialog.grab_set()

    def show_mv_data(self):
        """Показать данные материализованного представления"""
        selection = self.mv_tree.selection()
        if not selection:
            return
        
        item = self.mv_tree.item(selection[0])
        mv_name = item['values'][0]
        
        # Открываем диалог с данными
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Data: {mv_name}")
        dialog.geometry("800x500")
        
        # Загружаем данные
        try:
            query = f"SELECT * FROM {mv_name} LIMIT 100"
            results = self.app.api_client.execute_custom_query(query)
            
            # Отображаем данные
            text_widget = ctk.CTkTextbox(dialog, wrap="none")
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            
            if results:
                # Заголовки
                if hasattr(results[0], '_fields'):
                    headers = results[0]._fields
                    text_widget.insert("1.0", " | ".join(headers) + "\n")
                    text_widget.insert("end", "-" * (len(headers) * 15) + "\n\n")
                
                # Данные
                for row in results:
                    text_widget.insert("end", f"{row}\n")
            else:
                text_widget.insert("1.0", "No data available")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
            dialog.destroy()

    def show_mv_structure(self):
        """Показать структуру материализованного представления"""
        selection = self.mv_tree.selection()
        if not selection:
            return
        
        item = self.mv_tree.item(selection[0])
        mv_name = item['values'][0]
        
        # Получаем структуру
        try:
            query = f"PRAGMA table_info({mv_name})"
            structure = self.app.api_client.execute_custom_query(query)
            
            dialog = ctk.CTkToplevel(self.parent)
            dialog.title(f"Structure: {mv_name}")
            dialog.geometry("600x400")
            
            text_widget = ctk.CTkTextbox(dialog, wrap="none")
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            
            if structure:
                text_widget.insert("1.0", f"Structure of '{mv_name}':\n\n")
                text_widget.insert("end", "CID | Name | Type | NotNull | Default | PK\n")
                text_widget.insert("end", "-" * 60 + "\n")
                
                for col in structure:
                    text_widget.insert("end", 
                        f"{col[0]:3} | {col[1]:15} | {col[2]:10} | {col[3]:7} | {str(col[4]):8} | {col[5]}\n")
            else:
                text_widget.insert("1.0", "No structure information available")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load structure: {e}")

    def insert_aggregation_template(self):
        """Вставка шаблона для агрегационного MV"""
        template = """-- Materialized view for aggregated data
SELECT 
    attack_type,
    severity,
    COUNT(*) as attack_count,
    AVG(danger) as avg_danger,
    MIN(created_at) as first_attack,
    MAX(created_at) as last_attack,
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_severity_count
FROM attacks
GROUP BY attack_type, severity"""
        self.mv_query_text.insert("insert", template)

    def insert_join_template(self):
        """Вставка шаблона для MV с JOIN"""
        template = """-- Materialized view with JOIN operations
SELECT 
    a.name as attack_name,
    a.attack_type,
    a.severity,
    s.source_ip,
    s.source_country,
    s.reputation_score,
    t.target_name,
    t.target_type,
    t.criticality
FROM attacks a
LEFT JOIN attack_sources s ON a.source_id = s.id
LEFT JOIN attack_targets t ON a.target_id = t.id
WHERE a.danger > 5
  AND a.created_at > DATE('now', '-30 days')"""
        self.mv_query_text.insert("insert", template)

    def insert_window_template(self):
        """Вставка шаблона для MV с оконными функциями"""
        template = """-- Materialized view with window functions
SELECT 
    attack_type,
    name,
    danger,
    created_at,
    ROW_NUMBER() OVER (PARTITION BY attack_type ORDER BY danger DESC) as danger_rank,
    AVG(danger) OVER (PARTITION BY attack_type) as avg_danger_by_type,
    COUNT(*) OVER (PARTITION BY attack_type) as attacks_by_type,
    LAG(name) OVER (PARTITION BY attack_type ORDER BY created_at) as prev_attack
FROM attacks
WHERE created_at > DATE('now', '-90 days')"""
        self.mv_query_text.insert("insert", template)

    def insert_hierarchy_template(self):
        """Вставка шаблона для иерархического MV"""
        template = """-- Materialized view for hierarchical/rollup data
SELECT 
    DATE(created_at) as attack_date,
    attack_type,
    severity,
    COUNT(*) as daily_count,
    SUM(danger) as total_danger,
    AVG(danger) as avg_danger
FROM attacks
GROUP BY DATE(created_at), attack_type, severity
WITH ROLLUP
HAVING attack_date IS NOT NULL  -- Exclude grand total"""
        self.mv_query_text.insert("insert", template)

    def validate_mv_query(self):
        """Валидация SQL запроса для MV"""
        sql = self.mv_query_text.get("1.0", "end").strip()
        if not sql:
            messagebox.showwarning("Warning", "Please enter SQL query")
            return
        
        try:
            # Проверяем, что это SELECT запрос
            if not sql.lower().startswith("select"):
                messagebox.showwarning("Warning", "Materialized view must be based on SELECT query")
                return
            
            # Пробуем выполнить объяснение
            explain_query = f"EXPLAIN QUERY PLAN {sql}"
            result = self.app.api_client.execute_custom_query(explain_query)
            
            if result:
                messagebox.showinfo("Query Valid", 
                                  "SQL query is valid for materialized view!\n\n" +
                                  "Query plan generated successfully.")
            else:
                messagebox.showwarning("Warning", "Query returned no execution plan")
                
        except Exception as e:
            messagebox.showerror("SQL Error", f"Invalid SQL: {e}")

    def estimate_mv_size(self):
        """Оценка размера будущего материализованного представления"""
        sql = self.mv_query_text.get("1.0", "end").strip()
        if not sql:
            messagebox.showwarning("Warning", "Please enter SQL query first")
            return
        
        try:
            # Получаем примерные данные для оценки
            # Используем LIMIT для тестового выполнения
            test_query = f"{sql} LIMIT 1000"
            result = self.app.api_client.execute_custom_query(test_query)
            
            if not result:
                messagebox.showinfo("Estimation", 
                                  "Estimated size: 0 rows\nQuery returns no data")
                return
            
            # Простая эмуляция оценки
            # В реальном приложении можно использовать EXPLAIN ANALYZE
            estimated_rows = 1000  # Базовая оценка
            row_size = 100  # Предполагаемый средний размер строки в байтах
            
            total_size_kb = (estimated_rows * row_size) // 1024
            total_size_mb = total_size_kb // 1024
            
            messagebox.showinfo("Size Estimation", 
                              f"Estimated statistics:\n\n"
                              f"• Approximate rows: {estimated_rows:,}\n"
                              f"• Row size: ~{row_size} bytes\n"
                              f"• Total size: {total_size_kb:,} KB ({total_size_mb:,} MB)\n\n"
                              f"Note: This is a rough estimate based on sample data.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to estimate size: {e}")

    def create_materialized_view(self):
        """Создание нового материализованного представления"""
        mv_name = self.mv_name_entry.get().strip()
        sql = self.mv_query_text.get("1.0", "end").strip()
        refresh_mode = self.refresh_mode_var.get()
        build_option = self.build_option_var.get()
        
        if not mv_name:
            messagebox.showwarning("Warning", "Please enter materialized view name")
            return
        
        if not sql:
            messagebox.showwarning("Warning", "Please enter SQL query")
            return
        
        # Проверяем имя
        if not mv_name.replace("_", "").isalnum():
            messagebox.showwarning("Warning", 
                                 "Materialized view name can only contain letters, numbers and underscores")
            return
        
        # Формируем SQL для создания
        create_sql = f"CREATE MATERIALIZED VIEW {mv_name}"
        
        # Добавляем параметры обновления
        if refresh_mode != "ON DEMAND":
            create_sql += f" REFRESH {refresh_mode}"
        
        # Добавляем параметры построения
        if build_option == "DEFERRED":
            create_sql += " BUILD DEFERRED"
        
        create_sql += f" AS\n{sql}"
        
        # Добавляем индекс, если нужно
        if self.create_index_var.get():
            index_columns = self.index_columns_entry.get().strip()
            if index_columns:
                index_sql = f"\n\nCREATE INDEX idx_{mv_name} ON {mv_name}({index_columns});"
                create_sql += index_sql
        
        try:
            # Выполняем создание
            self.app.api_client.execute_custom_query(create_sql)
            
            # Обновляем список
            self.load_materialized_views()
            
            # Очищаем форму
            self.clear_mv_form()
            
            messagebox.showinfo("Success", 
                              f"Materialized view '{mv_name}' created successfully\n\n" +
                              f"Refresh mode: {refresh_mode}\n" +
                              f"Build option: {build_option}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create materialized view: {e}")

    def clear_mv_form(self):
        """Очистка формы создания MV"""
        self.mv_name_entry.delete(0, "end")
        self.mv_query_text.delete("1.0", "end")
        self.refresh_mode_var.set("ON DEMAND")
        self.build_option_var.set("IMMEDIATE")
        self.create_index_var.set(True)
        self.index_columns_entry.delete(0, "end")

    def add_refresh_schedule(self):
        """Добавление расписания обновления"""
        mv_name = self.schedule_mv_combo.get()
        schedule_type = self.schedule_type_var.get()
        schedule_time = self.schedule_time_entry.get().strip()
        
        if not mv_name:
            messagebox.showwarning("Warning", "Please select a materialized view")
            return
        
        if schedule_type == "CUSTOM" and not schedule_time:
            messagebox.showwarning("Warning", "Please enter schedule time for custom schedule")
            return
        
        # Создаем запись расписания
        schedule = {
            'mv_name': mv_name,
            'schedule_type': schedule_type,
            'schedule_time': schedule_time if schedule_time else "00:00",
            'next_refresh': self.calculate_next_refresh(schedule_type, schedule_time),
            'last_run': "Never",
            'status': "ACTIVE"
        }
        
        self.refresh_schedules.append(schedule)
        
        # Добавляем в дерево
        self.schedules_tree.insert("", "end", values=(
            schedule['mv_name'],
            schedule['schedule_type'],
            schedule['next_refresh'],
            schedule['last_run'],
            schedule['status']
        ))
        
        messagebox.showinfo("Success", 
                          f"Schedule added for '{mv_name}'\n" +
                          f"Type: {schedule_type}\n" +
                          f"Next refresh: {schedule['next_refresh']}")

    def calculate_next_refresh(self, schedule_type, schedule_time):
        """Вычисление времени следующего обновления"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        if schedule_type == "HOURLY":
            next_time = now + timedelta(hours=1)
        elif schedule_type == "DAILY":
            next_time = now + timedelta(days=1)
        elif schedule_type == "WEEKLY":
            next_time = now + timedelta(weeks=1)
        elif schedule_type == "MONTHLY":
            next_time = now + timedelta(days=30)
        else:  # CUSTOM
            try:
                # Парсим время HH:MM
                hour, minute = map(int, schedule_time.split(':'))
                next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
            except:
                next_time = now + timedelta(days=1)
        
        return next_time.strftime("%Y-%m-%d %H:%M:%S")

    def run_scheduled_refresh(self):
        """Запуск запланированных обновлений"""
        if not self.refresh_schedules:
            messagebox.showwarning("Warning", "No active schedules to run")
            return
        
        # Фильтруем активные расписания
        active_schedules = [s for s in self.refresh_schedules if s['status'] == "ACTIVE"]
        
        if not active_schedules:
            messagebox.showwarning("Warning", "No active schedules found")
            return
        
        try:
            for schedule in active_schedules:
                mv_name = schedule['mv_name']
                
                # Обновляем MV
                self.refresh_materialized_view_by_name(mv_name)
                
                # Обновляем информацию о последнем запуске
                schedule['last_run'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                schedule['next_refresh'] = self.calculate_next_refresh(
                    schedule['schedule_type'], 
                    schedule['schedule_time']
                )
            
            # Обновляем дерево расписаний
            self.update_schedules_tree()
            
            messagebox.showinfo("Success", 
                              f"Ran {len(active_schedules)} scheduled refreshes")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run scheduled refreshes: {e}")

    def refresh_materialized_view_by_name(self, mv_name):
        """Обновление материализованного представления по имени"""
        try:
            # Эмуляция обновления
            refresh_query = f"DROP VIEW IF EXISTS {mv_name};"
            
            # Находим определение
            for mv in self.current_materialized_views:
                if mv['name'] == mv_name and 'sql' in mv:
                    sql = mv['sql']
                    if "CREATE MATERIALIZED VIEW" in sql.upper():
                        sql = sql.split("AS", 1)[1].strip()
                    
                    create_query = f"CREATE VIEW {mv_name} AS {sql}"
                    refresh_query += create_query
                    break
            
            self.app.api_client.execute_custom_query(refresh_query)
            
        except Exception as e:
            raise Exception(f"Failed to refresh {mv_name}: {e}")

    def update_schedules_tree(self):
        """Обновление дерева расписаний"""
        # Очищаем дерево
        for item in self.schedules_tree.get_children():
            self.schedules_tree.delete(item)
        
        # Заполняем заново
        for schedule in self.refresh_schedules:
            self.schedules_tree.insert("", "end", values=(
                schedule['mv_name'],
                schedule['schedule_type'],
                schedule['next_refresh'],
                schedule['last_run'],
                schedule['status']
            ))

    def remove_schedule(self):
        """Удаление выбранного расписания"""
        selection = self.schedules_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a schedule to remove")
            return
        
        item = self.schedules_tree.item(selection[0])
        mv_name = item['values'][0]
        schedule_type = item['values'][1]
        
        # Удаляем из списка
        self.refresh_schedules = [
            s for s in self.refresh_schedules 
            if not (s['mv_name'] == mv_name and s['schedule_type'] == schedule_type)
        ]
        
        # Обновляем дерево
        self.update_schedules_tree()
        
        messagebox.showinfo("Success", f"Schedule removed for '{mv_name}'")

    def disable_all_schedules(self):
        """Отключение всех расписаний"""
        if not self.refresh_schedules:
            messagebox.showwarning("Warning", "No active schedules")
            return
        
        if not messagebox.askyesno("Confirm Disable", 
                                  "Disable all refresh schedules?"):
            return
        
        # Помечаем все как отключенные
        for schedule in self.refresh_schedules:
            schedule['status'] = "DISABLED"
        
        # Обновляем дерево
        self.update_schedules_tree()
        
        messagebox.showinfo("Success", "All schedules disabled")


class MaterializedViewDetailsDialog(ctk.CTkToplevel):
    """Диалог для отображения деталей материализованного представления"""
    def __init__(self, parent, mv_info):
        super().__init__(parent)
        self.mv_info = mv_info
        self.title(f"Materialized View: {mv_info['name']}")
        self.geometry("700x500")
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса диалога"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"Materialized View: {self.mv_info['name']}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Вкладки
        tabview = ctk.CTkTabview(main_frame)
        tabview.pack(fill="both", expand=True)
        
        # Вкладка информации
        info_tab = tabview.add("Information")
        self.setup_info_tab(info_tab)
        
        # Вкладка SQL
        sql_tab = tabview.add("SQL Definition")
        self.setup_sql_tab(sql_tab)
        
        # Вкладка статистики
        stats_tab = tabview.add("Statistics")
        self.setup_stats_tab(stats_tab)
        
        # Кнопка закрытия
        ctk.CTkButton(main_frame, text="Close", command=self.destroy).pack(pady=(10, 0))

    def setup_info_tab(self, parent):
        """Настройка вкладки информации"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Информационные поля
        fields = [
            ("Name:", self.mv_info['name']),
            ("Type:", self.mv_info['type'].upper()),
            ("Status:", self.mv_info.get('status', 'UNKNOWN')),
            ("Rows:", str(self.mv_info.get('row_count', 0))),
            ("Size:", self.mv_info.get('size_kb', 'N/A')),
            ("Last Refresh:", self.mv_info.get('last_refresh', 'Never')),
            ("Base Table:", self.mv_info.get('table_name', 'N/A')),
        ]
        
        for label, value in fields:
            field_frame = ctk.CTkFrame(frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(field_frame, text=label, width=120, 
                        font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(field_frame, text=value).pack(side="left", padx=(10, 0))

    def setup_sql_tab(self, parent):
        """Настройка вкладки SQL"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # SQL определение
        sql_text = ctk.CTkTextbox(frame, wrap="word")
        sql_text.pack(fill="both", expand=True)
        
        sql = self.mv_info.get('sql', 'No SQL definition available')
        sql_text.insert("1.0", sql)
        sql_text.configure(state="disabled")

    def setup_stats_tab(self, parent):
        """Настройка вкладки статистики"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Статистика
        stats_text = ctk.CTkTextbox(frame, wrap="word")
        stats_text.pack(fill="both", expand=True)
        
        # Формируем статистику
        stats = [
            f"Materialized View Statistics for '{self.mv_info['name']}':\n",
            f"\nStorage:",
            f"  • Row count: {self.mv_info.get('row_count', 0):,}",
            f"  • Estimated size: {self.mv_info.get('size_kb', 'N/A')}",
            f"\nPerformance:",
            f"  • Last refresh: {self.mv_info.get('last_refresh', 'Never')}",
            f"  • Status: {self.mv_info.get('status', 'UNKNOWN')}",
            f"\nMetadata:",
            f"  • Created from: {self.mv_info.get('table_name', 'N/A')}",
            f"  • Object type: {self.mv_info.get('type', 'UNKNOWN')}",
        ]
        
        stats_text.insert("1.0", "\n".join(stats))
        stats_text.configure(state="disabled")