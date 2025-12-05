# ui/cte_builder.py
import customtkinter as ctk
from tkinter import messagebox, ttk
from typing import List, Dict, Optional
import json
import re

class CTEBuilder:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.cte_definitions = []  # Список CTE определений
        self.current_cte_index = -1
        self.table_columns_cache = {}  # Кэш столбцов таблиц
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса конструктора CTE"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Common Table Expressions (CTE) Builder",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Основной фрейм с вкладками
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Вкладка: Список CTE
        self.cte_list_tab = self.tabview.add("CTE Definitions")
        self.setup_cte_list_tab()
        
        # Вкладка: Конструктор CTE
        self.cte_builder_tab = self.tabview.add("CTE Builder")
        self.setup_cte_builder_tab()
        
        # Вкладка: Основной запрос
        self.main_query_tab = self.tabview.add("Main Query")
        self.setup_main_query_tab()
        
        # Вкладка: Предварительный просмотр
        self.preview_tab = self.tabview.add("Preview & Execute")
        self.setup_preview_tab()
        
        # Загружаем доступные таблицы
        self.load_available_tables()

    def setup_cte_list_tab(self):
        """Настройка вкладки списка CTE"""
        main_frame = ctk.CTkFrame(self.cte_list_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель управления CTE
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(controls_frame, text="Add New CTE", 
                     command=self.add_new_cte,
                     fg_color=self.app.colors["success"],
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(controls_frame, text="Edit Selected", 
                     command=self.edit_selected_cte,
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(controls_frame, text="Delete Selected", 
                     command=self.delete_selected_cte,
                     fg_color=self.app.colors["warning"],
                     width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(controls_frame, text="Move Up", 
                     command=self.move_cte_up,
                     width=100).pack(side="left", padx=5)
        
        ctk.CTkButton(controls_frame, text="Move Down", 
                     command=self.move_cte_down,
                     width=100).pack(side="left", padx=5)
        
        # Список CTE
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        # Дерево для отображения CTE
        columns = ("name", "type", "columns", "query_length", "depends_on")
        self.cte_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # Настройка колонок
        self.cte_tree.heading("name", text="CTE Name")
        self.cte_tree.heading("type", text="Type")
        self.cte_tree.heading("columns", text="Columns")
        self.cte_tree.heading("query_length", text="Query Length")
        self.cte_tree.heading("depends_on", text="Depends On")
        
        self.cte_tree.column("name", width=150)
        self.cte_tree.column("type", width=100)
        self.cte_tree.column("columns", width=200)
        self.cte_tree.column("query_length", width=100)
        self.cte_tree.column("depends_on", width=150)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.cte_tree.yview)
        self.cte_tree.configure(yscrollcommand=scrollbar.set)
        
        self.cte_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Привязка события выбора
        self.cte_tree.bind("<<TreeviewSelect>>", self.on_cte_selected)

    def setup_cte_builder_tab(self):
        """Настройка вкладки конструктора CTE"""
        main_frame = ctk.CTkFrame(self.cte_builder_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Верхняя панель с информацией о CTE
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(info_frame, text="CTE Definition", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Имя CTE
        name_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(name_frame, text="CTE Name:", width=100).pack(side="left")
        self.cte_name_entry = ctk.CTkEntry(name_frame, placeholder_text="Enter CTE name (e.g., user_stats)")
        self.cte_name_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Тип CTE
        type_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        type_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(type_frame, text="CTE Type:", width=100).pack(side="left")
        
        self.cte_type_var = ctk.StringVar(value="REGULAR")
        type_options = ["REGULAR", "RECURSIVE"]
        self.cte_type_combo = ctk.CTkComboBox(type_frame, 
                                             values=type_options,
                                             variable=self.cte_type_var,
                                             width=150)
        self.cte_type_combo.pack(side="left", padx=(10, 20))
        
        # Опции для рекурсивного CTE
        self.recursive_options_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        
        recursive_frame = ctk.CTkFrame(self.recursive_options_frame, fg_color="transparent")
        recursive_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(recursive_frame, text="Anchor Columns:", width=120).pack(side="left")
        self.anchor_columns_entry = ctk.CTkEntry(recursive_frame, 
                                                placeholder_text="id, parent_id, level",
                                                width=200)
        self.anchor_columns_entry.pack(side="left", padx=(10, 20))
        
        ctk.CTkLabel(recursive_frame, text="Max Depth:").pack(side="left")
        self.max_depth_entry = ctk.CTkEntry(recursive_frame, width=80, placeholder_text="10")
        self.max_depth_entry.pack(side="left", padx=(10, 0))
        
        # Секция построения запроса
        query_frame = ctk.CTkFrame(main_frame)
        query_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(query_frame, text="CTE Query Builder", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Панель быстрых действий
        quick_actions_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        quick_actions_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        action_buttons = [
            ("Select From Table", self.insert_select_from_table),
            ("Join Tables", self.insert_join_template),
            ("Use Another CTE", self.insert_cte_reference),
            ("Aggregate Data", self.insert_aggregation_template),
            ("Filter Data", self.insert_where_template)
        ]
        
        for text, command in action_buttons:
            btn = ctk.CTkButton(quick_actions_frame, text=text, command=command, width=140)
            btn.pack(side="left", padx=2)
        
        # Поле для SQL запроса CTE
        self.cte_query_text = ctk.CTkTextbox(query_frame, height=200)
        self.cte_query_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Панель предпросмотра столбцов
        columns_frame = ctk.CTkFrame(main_frame)
        columns_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(columns_frame, text="Detected Columns", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        columns_preview_frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
        columns_preview_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.columns_text = ctk.CTkTextbox(columns_preview_frame, height=60)
        self.columns_text.pack(fill="x")
        self.columns_text.insert("1.0", "Columns will be detected from query...")
        self.columns_text.configure(state="disabled")
        
        # Кнопки управления CTE
        cte_buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        cte_buttons_frame.pack(fill="x")
        
        ctk.CTkButton(cte_buttons_frame, text="Save CTE", 
                     command=self.save_cte,
                     fg_color=self.app.colors["success"]).pack(side="left", padx=5)
        
        ctk.CTkButton(cte_buttons_frame, text="Validate Query", 
                     command=self.validate_cte_query).pack(side="left", padx=5)
        
        ctk.CTkButton(cte_buttons_frame, text="Detect Columns", 
                     command=self.detect_columns_from_query).pack(side="left", padx=5)
        
        ctk.CTkButton(cte_buttons_frame, text="Clear Form", 
                     command=self.clear_cte_form).pack(side="left", padx=5)

    def setup_main_query_tab(self):
        """Настройка вкладки основного запроса"""
        main_frame = ctk.CTkFrame(self.main_query_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Информация о доступных CTE
        cte_info_frame = ctk.CTkFrame(main_frame)
        cte_info_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(cte_info_frame, text="Available CTEs for Main Query", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Список доступных CTE
        available_cte_frame = ctk.CTkFrame(cte_info_frame, fg_color="transparent")
        available_cte_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.available_cte_text = ctk.CTkTextbox(available_cte_frame, height=80)
        self.available_cte_text.pack(fill="x")
        self.available_cte_text.insert("1.0", "No CTEs defined yet. Add CTEs in the 'CTE Definitions' tab.")
        self.available_cte_text.configure(state="disabled")
        
        # Конструктор основного запроса
        query_frame = ctk.CTkFrame(main_frame)
        query_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(query_frame, text="Main Query (Final SELECT)", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Панель быстрых действий для основного запроса
        main_actions_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        main_actions_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        main_action_buttons = [
            ("Select All Columns", self.insert_select_all),
            ("Join CTEs", self.insert_cte_join),
            ("Aggregate Results", self.insert_main_aggregation),
            ("Order Results", self.insert_order_by),
            ("Limit Results", self.insert_limit)
        ]
        
        for text, command in main_action_buttons:
            btn = ctk.CTkButton(main_actions_frame, text=text, command=command, width=130)
            btn.pack(side="left", padx=2)
        
        # Поле для основного запроса
        self.main_query_text = ctk.CTkTextbox(query_frame, height=200)
        self.main_query_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Шаблоны для основного запроса
        templates_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        templates_frame.pack(fill="x")
        
        ctk.CTkLabel(templates_frame, text="Quick Templates:", 
                    font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 10))
        
        template_buttons = [
            ("Simple Report", self.apply_simple_report_template),
            ("Hierarchical Data", self.apply_hierarchical_template),
            ("Time Series", self.apply_time_series_template),
            ("Data Analysis", self.apply_analysis_template)
        ]
        
        for text, command in template_buttons:
            btn = ctk.CTkButton(templates_frame, text=text, command=command, width=120)
            btn.pack(side="left", padx=2)

    def setup_preview_tab(self):
        """Настройка вкладки предварительного просмотра и выполнения"""
        main_frame = ctk.CTkFrame(self.preview_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель управления выполнением
        execute_frame = ctk.CTkFrame(main_frame)
        execute_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(execute_frame, text="Query Execution", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        execute_buttons_frame = ctk.CTkFrame(execute_frame, fg_color="transparent")
        execute_buttons_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkButton(execute_buttons_frame, text="Generate Full Query", 
                     command=self.generate_full_query,
                     fg_color=self.app.colors["primary"]).pack(side="left", padx=5)
        
        ctk.CTkButton(execute_buttons_frame, text="Execute Query", 
                     command=self.execute_full_query,
                     fg_color=self.app.colors["success"]).pack(side="left", padx=5)
        
        ctk.CTkButton(execute_buttons_frame, text="Explain Query", 
                     command=self.explain_query).pack(side="left", padx=5)
        
        ctk.CTkButton(execute_buttons_frame, text="Export Results", 
                     command=self.export_query_results).pack(side="left", padx=5)
        
        ctk.CTkButton(execute_buttons_frame, text="Clear All", 
                     command=self.clear_all_cte,
                     fg_color=self.app.colors["warning"]).pack(side="left", padx=5)
        
        # Предпросмотр полного SQL
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(preview_frame, text="Full SQL Preview", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.full_sql_text = ctk.CTkTextbox(preview_frame, wrap="none")
        self.full_sql_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Результаты выполнения
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(results_frame, text="Execution Results", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.results_text = ctk.CTkTextbox(results_frame, wrap="none")
        self.results_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Статусная строка
        self.status_label = ctk.CTkLabel(main_frame, text="Ready", 
                                        font=ctk.CTkFont(size=12, slant="italic"))
        self.status_label.pack(anchor="w", pady=(5, 0))

    def load_available_tables(self):
        """Загрузка списка доступных таблиц из БД"""
        try:
            # Получаем список таблиц
            query = """
            SELECT name 
            FROM sqlite_master 
            WHERE type = 'table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
            
            results = self.app.api_client.execute_custom_query(query)
            self.available_tables = [row[0] for row in results] if results else []
            
            # Кэшируем столбцы для каждой таблицы
            for table in self.available_tables:
                self.cache_table_columns(table)
                
        except Exception as e:
            self.available_tables = ["attacks", "users", "logs"]  # Заглушки при ошибке
            messagebox.showwarning("Warning", f"Could not load tables: {e}")

    def cache_table_columns(self, table_name):
        """Кэширование столбцов таблицы"""
        try:
            query = f"PRAGMA table_info({table_name})"
            results = self.app.api_client.execute_custom_query(query)
            
            columns = []
            for row in results:
                columns.append(row[1])  # Имя столбца
            
            self.table_columns_cache[table_name] = columns
            
        except:
            self.table_columns_cache[table_name] = []

    def add_new_cte(self):
        """Добавление нового CTE"""
        # Сбрасываем форму
        self.current_cte_index = -1
        self.clear_cte_form()
        
        # Переключаемся на вкладку конструктора
        self.tabview.set("CTE Builder")
        
        # Устанавливаем имя по умолчанию
        next_number = len(self.cte_definitions) + 1
        default_name = f"cte_{next_number}"
        self.cte_name_entry.insert(0, default_name)

    def edit_selected_cte(self):
        """Редактирование выбранного CTE"""
        selection = self.cte_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a CTE to edit")
            return
        
        item = self.cte_tree.item(selection[0])
        cte_name = item['values'][0]
        
        # Находим CTE в списке
        for i, cte in enumerate(self.cte_definitions):
            if cte['name'] == cte_name:
                self.current_cte_index = i
                self.load_cte_into_form(cte)
                
                # Переключаемся на вкладку конструктора
                self.tabview.set("CTE Builder")
                break

    def delete_selected_cte(self):
        """Удаление выбранного CTE"""
        selection = self.cte_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a CTE to delete")
            return
        
        item = self.cte_tree.item(selection[0])
        cte_name = item['values'][0]
        
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Delete CTE '{cte_name}'?"):
            return
        
        # Удаляем из списка
        self.cte_definitions = [
            cte for cte in self.cte_definitions 
            if cte['name'] != cte_name
        ]
        
        # Обновляем дерево
        self.update_cte_tree()
        
        # Обновляем список доступных CTE
        self.update_available_cte_list()
        
        messagebox.showinfo("Success", f"CTE '{cte_name}' deleted")

    def move_cte_up(self):
        """Перемещение CTE вверх в списке"""
        selection = self.cte_tree.selection()
        if not selection:
            return
        
        item_index = self.cte_tree.index(selection[0])
        if item_index > 0:
            # Перемещаем в списке
            self.cte_definitions.insert(item_index - 1, 
                                      self.cte_definitions.pop(item_index))
            
            # Обновляем дерево
            self.update_cte_tree()
            
            # Выделяем перемещенный элемент
            self.cte_tree.selection_set(self.cte_tree.get_children()[item_index - 1])

    def move_cte_down(self):
        """Перемещение CTE вниз в списке"""
        selection = self.cte_tree.selection()
        if not selection:
            return
        
        item_index = self.cte_tree.index(selection[0])
        if item_index < len(self.cte_definitions) - 1:
            # Перемещаем в списке
            self.cte_definitions.insert(item_index + 1, 
                                      self.cte_definitions.pop(item_index))
            
            # Обновляем дерево
            self.update_cte_tree()
            
            # Выделяем перемещенный элемент
            self.cte_tree.selection_set(self.cte_tree.get_children()[item_index + 1])

    def on_cte_selected(self, event):
        """Обработка выбора CTE в дереве"""
        selection = self.cte_tree.selection()
        if selection:
            item = self.cte_tree.item(selection[0])
            cte_name = item['values'][0]
            self.status_label.configure(text=f"Selected: {cte_name}")

    def load_cte_into_form(self, cte):
        """Загрузка данных CTE в форму"""
        self.clear_cte_form()
        
        # Заполняем поля формы
        self.cte_name_entry.insert(0, cte.get('name', ''))
        self.cte_type_var.set(cte.get('type', 'REGULAR'))
        
        # Для рекурсивных CTE
        if cte.get('type') == 'RECURSIVE':
            self.anchor_columns_entry.insert(0, cte.get('anchor_columns', ''))
            self.max_depth_entry.insert(0, cte.get('max_depth', '10'))
        
        # SQL запрос
        self.cte_query_text.insert("1.0", cte.get('query', ''))
        
        # Столбцы
        columns = cte.get('columns', [])
        if columns:
            self.columns_text.configure(state="normal")
            self.columns_text.delete("1.0", "end")
            self.columns_text.insert("1.0", ", ".join(columns))
            self.columns_text.configure(state="disabled")
        
        # Обновляем отображение опций рекурсивного CTE
        self.on_cte_type_changed()

    def clear_cte_form(self):
        """Очистка формы CTE"""
        self.cte_name_entry.delete(0, "end")
        self.cte_type_var.set("REGULAR")
        self.anchor_columns_entry.delete(0, "end")
        self.max_depth_entry.delete(0, "end")
        self.cte_query_text.delete("1.0", "end")
        
        self.columns_text.configure(state="normal")
        self.columns_text.delete("1.0", "end")
        self.columns_text.insert("1.0", "Columns will be detected from query...")
        self.columns_text.configure(state="disabled")
        
        # Скрываем опции рекурсивного CTE
        self.recursive_options_frame.pack_forget()

    def save_cte(self):
        """Сохранение CTE"""
        cte_name = self.cte_name_entry.get().strip()
        cte_type = self.cte_type_var.get()
        query = self.cte_query_text.get("1.0", "end").strip()
        
        if not cte_name:
            messagebox.showwarning("Warning", "Please enter CTE name")
            return
        
        if not query:
            messagebox.showwarning("Warning", "Please enter CTE query")
            return
        
        # Проверяем имя
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', cte_name):
            messagebox.showwarning("Warning", 
                                 "CTE name must start with a letter or underscore and contain only alphanumeric characters and underscores")
            return
        
        # Проверяем, что имя не дублируется (кроме текущего CTE при редактировании)
        for i, cte in enumerate(self.cte_definitions):
            if cte['name'] == cte_name and i != self.current_cte_index:
                messagebox.showwarning("Warning", f"CTE with name '{cte_name}' already exists")
                return
        
        # Детектируем столбцы
        columns = self.detect_columns_from_query(silent=True)
        
        # Создаем объект CTE
        cte_data = {
            'name': cte_name,
            'type': cte_type,
            'query': query,
            'columns': columns,
            'depends_on': self.find_cte_dependencies(query)
        }
        
        # Добавляем параметры для рекурсивных CTE
        if cte_type == 'RECURSIVE':
            cte_data['anchor_columns'] = self.anchor_columns_entry.get().strip()
            cte_data['max_depth'] = self.max_depth_entry.get().strip()
        
        # Сохраняем или обновляем
        if self.current_cte_index >= 0:
            self.cte_definitions[self.current_cte_index] = cte_data
        else:
            self.cte_definitions.append(cte_data)
        
        # Обновляем дерево
        self.update_cte_tree()
        
        # Обновляем список доступных CTE
        self.update_available_cte_list()
        
        # Очищаем форму
        self.clear_cte_form()
        self.current_cte_index = -1
        
        messagebox.showinfo("Success", f"CTE '{cte_name}' saved successfully")
        
        # Переключаемся на список CTE
        self.tabview.set("CTE Definitions")

    def update_cte_tree(self):
        """Обновление дерева CTE"""
        # Очищаем дерево
        for item in self.cte_tree.get_children():
            self.cte_tree.delete(item)
        
        # Заполняем заново
        for cte in self.cte_definitions:
            self.cte_tree.insert("", "end", values=(
                cte['name'],
                cte['type'],
                ", ".join(cte.get('columns', []))[:30] + ("..." if len(cte.get('columns', [])) > 3 else ""),
                len(cte.get('query', '')),
                ", ".join(cte.get('depends_on', []))[:20] or "None"
            ))

    def update_available_cte_list(self):
        """Обновление списка доступных CTE"""
        self.available_cte_text.configure(state="normal")
        self.available_cte_text.delete("1.0", "end")
        
        if not self.cte_definitions:
            self.available_cte_text.insert("1.0", "No CTEs defined yet. Add CTEs in the 'CTE Definitions' tab.")
        else:
            self.available_cte_text.insert("1.0", "Available CTEs:\n\n")
            
            for cte in self.cte_definitions:
                columns_str = ", ".join(cte.get('columns', []))
                self.available_cte_text.insert("end", 
                    f"• {cte['name']} ({cte['type']})\n"
                    f"  Columns: {columns_str}\n"
                    f"  Depends on: {', '.join(cte.get('depends_on', [])) or 'None'}\n\n")
        
        self.available_cte_text.configure(state="disabled")

    def find_cte_dependencies(self, query):
        """Поиск зависимостей от других CTE в запросе"""
        dependencies = []
        
        if not self.cte_definitions:
            return dependencies
        
        # Ищем упоминания других CTE в запросе
        for cte in self.cte_definitions:
            cte_name = cte['name']
            # Ищем упоминание CTE в запросе (как таблица в FROM/JOIN)
            pattern = rf'\b{cte_name}\b'
            if re.search(pattern, query, re.IGNORECASE):
                dependencies.append(cte_name)
        
        return dependencies

    def detect_columns_from_query(self, silent=False):
        """Детектирование столбцов из SQL запроса"""
        query = self.cte_query_text.get("1.0", "end").strip()
        
        if not query:
            if not silent:
                messagebox.showwarning("Warning", "No query to analyze")
            return []
        
        try:
            # Пытаемся выполнить запрос с LIMIT 0 или использовать EXPLAIN
            # Для простоты используем эвристический анализ
            
            columns = []
            
            # Эвристика 1: Ищем SELECT ... FROM
            select_match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_clause = select_match.group(1)
                
                # Разбиваем по запятым
                parts = [p.strip() for p in re.split(r',\s*(?![^()]*\))', select_clause)]
                
                for part in parts:
                    # Извлекаем имя столбца (после AS или как есть)
                    as_match = re.search(r'(?:AS\s+)?([\w]+)$', part, re.IGNORECASE)
                    if as_match:
                        columns.append(as_match.group(1))
                    else:
                        # Берем последнее слово
                        last_word = re.findall(r'\b(\w+)\b', part)
                        if last_word:
                            columns.append(last_word[-1])
            
            # Эвристика 2: Если запрос простой SELECT * FROM
            if not columns and re.search(r'SELECT\s*\*\s+FROM', query, re.IGNORECASE):
                # Пытаемся получить столбцы из таблицы
                table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
                if table_match:
                    table_name = table_match.group(1)
                    if table_name in self.table_columns_cache:
                        columns = self.table_columns_cache[table_name]
            
            # Обновляем поле столбцов
            self.columns_text.configure(state="normal")
            self.columns_text.delete("1.0", "end")
            
            if columns:
                self.columns_text.insert("1.0", ", ".join(columns))
                if not silent:
                    messagebox.showinfo("Columns Detected", 
                                      f"Detected {len(columns)} columns: {', '.join(columns)}")
            else:
                self.columns_text.insert("1.0", "Could not detect columns automatically")
                if not silent:
                    messagebox.showwarning("Warning", "Could not detect columns from query")
            
            self.columns_text.configure(state="disabled")
            
            return columns
            
        except Exception as e:
            if not silent:
                messagebox.showerror("Error", f"Failed to detect columns: {e}")
            return []

    def validate_cte_query(self):
        """Валидация SQL запроса CTE"""
        query = self.cte_query_text.get("1.0", "end").strip()
        
        if not query:
            messagebox.showwarning("Warning", "Please enter CTE query")
            return
        
        try:
            # Пробуем выполнить EXPLAIN
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            result = self.app.api_client.execute_custom_query(explain_query)
            
            if result:
                messagebox.showinfo("Query Valid", 
                                  "SQL query syntax is valid!\n\n" +
                                  "Query plan generated successfully.")
            else:
                messagebox.showwarning("Warning", "Query returned no execution plan")
                
        except Exception as e:
            messagebox.showerror("SQL Error", f"Invalid SQL: {e}")

    def on_cte_type_changed(self):
        """Обработка изменения типа CTE"""
        cte_type = self.cte_type_var.get()
        
        if cte_type == "RECURSIVE":
            self.recursive_options_frame.pack(fill="x", padx=15, pady=5)
            
            # Вставляем шаблон для рекурсивного CTE
            if not self.cte_query_text.get("1.0", "end").strip():
                self.insert_recursive_template()
        else:
            self.recursive_options_frame.pack_forget()

    def insert_select_from_table(self):
        """Вставка шаблона SELECT FROM таблицы"""
        # Диалог выбора таблицы
        dialog = TableSelectorDialog(self.parent, self.available_tables)
        self.wait_window(dialog)
        
        if dialog.selected_table:
            table_name = dialog.selected_table
            
            # Получаем столбцы таблицы
            columns = self.table_columns_cache.get(table_name, [])
            
            if not columns:
                # Пытаемся загрузить столбцы
                self.cache_table_columns(table_name)
                columns = self.table_columns_cache.get(table_name, [])
            
            # Формируем запрос
            if columns:
                columns_str = ",\n    ".join(columns)
                template = f"SELECT \n    {columns_str}\nFROM {table_name}\nWHERE 1=1"
            else:
                template = f"SELECT *\nFROM {table_name}\nWHERE 1=1"
            
            self.cte_query_text.insert("insert", template)

    def insert_join_template(self):
        """Вставка шаблона JOIN"""
        template = """SELECT 
    t1.column1,
    t1.column2,
    t2.column3,
    t3.column4
FROM table1 t1
INNER JOIN table2 t2 ON t1.id = t2.table1_id
LEFT JOIN table3 t3 ON t1.id = t3.table1_id
WHERE t1.column1 = 'value'
  AND t2.column3 > 100"""
        self.cte_query_text.insert("insert", template)

    def insert_cte_reference(self):
        """Вставка ссылки на другой CTE"""
        if not self.cte_definitions:
            messagebox.showwarning("Warning", "No CTEs defined yet")
            return
        
        # Диалог выбора CTE
        cte_names = [cte['name'] for cte in self.cte_definitions]
        dialog = CTESelectorDialog(self.parent, cte_names)
        self.wait_window(dialog)
        
        if dialog.selected_cte:
            template = f"SELECT *\nFROM {dialog.selected_cte}\nWHERE 1=1"
            self.cte_query_text.insert("insert", template)

    def insert_aggregation_template(self):
        """Вставка шаблона агрегации"""
        template = """SELECT 
    category,
    DATE(date_column) as day,
    COUNT(*) as count,
    SUM(value) as total_value,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value
FROM source_table
WHERE date_column > DATE('now', '-30 days')
GROUP BY category, DATE(date_column)
HAVING COUNT(*) > 5"""
        self.cte_query_text.insert("insert", template)

    def insert_where_template(self):
        """Вставка шаблона WHERE"""
        template = """WHERE 
    column1 = 'value'
    AND column2 BETWEEN 100 AND 200
    AND column3 IN ('option1', 'option2', 'option3')
    AND column4 LIKE '%pattern%'
    AND (column5 IS NULL OR column6 = 'active')
    AND column7 > (SELECT AVG(column7) FROM other_table)"""
        self.cte_query_text.insert("insert", template)

    def insert_recursive_template(self):
        """Вставка шаблона рекурсивного CTE"""
        template = """-- Anchor member (base case)
SELECT 
    id,
    name,
    parent_id,
    1 as level,
    name as path
FROM hierarchical_table
WHERE parent_id IS NULL

UNION ALL

-- Recursive member
SELECT 
    t.id,
    t.name,
    t.parent_id,
    r.level + 1,
    r.path || ' -> ' || t.name
FROM hierarchical_table t
INNER JOIN cte_name r ON t.parent_id = r.id
WHERE r.level < 10  -- Prevent infinite recursion"""
        self.cte_query_text.insert("insert", template)

    def insert_select_all(self):
        """Вставка SELECT * в основной запрос"""
        if not self.cte_definitions:
            messagebox.showwarning("Warning", "No CTEs defined yet")
            return
        
        # Выбираем последний CTE по умолчанию
        last_cte = self.cte_definitions[-1]['name']
        template = f"SELECT *\nFROM {last_cte}"
        self.main_query_text.insert("insert", template)

    def insert_cte_join(self):
        """Вставка JOIN между CTE в основном запросе"""
        if len(self.cte_definitions) < 2:
            messagebox.showwarning("Warning", "Need at least 2 CTEs to create a JOIN")
            return
        
        # Берем два последних CTE
        cte1 = self.cte_definitions[-2]['name']
        cte2 = self.cte_definitions[-1]['name']
        
        template = f"""SELECT 
    a.*,
    b.*
FROM {cte1} a
INNER JOIN {cte2} b ON a.id = b.{cte1}_id"""
        self.main_query_text.insert("insert", template)

    def insert_main_aggregation(self):
        """Вставка агрегации в основной запрос"""
        if not self.cte_definitions:
            messagebox.showwarning("Warning", "No CTEs defined yet")
            return
        
        last_cte = self.cte_definitions[-1]['name']
        
        template = f"""SELECT 
    category_column,
    COUNT(*) as record_count,
    SUM(value_column) as total_value,
    AVG(value_column) as average_value
FROM {last_cte}
GROUP BY category_column
HAVING COUNT(*) > 1
ORDER BY total_value DESC"""
        self.main_query_text.insert("insert", template)

    def insert_order_by(self):
        """Вставка ORDER BY в основной запрос"""
        template = "\nORDER BY column1 ASC, column2 DESC"
        self.main_query_text.insert("insert", template)

    def insert_limit(self):
        """Вставка LIMIT в основной запрос"""
        template = "\nLIMIT 100"
        self.main_query_text.insert("insert", template)

    def apply_simple_report_template(self):
        """Применение шаблона простого отчета"""
        if not self.cte_definitions:
            messagebox.showwarning("Warning", "No CTEs defined yet")
            return
        
        last_cte = self.cte_definitions[-1]['name']
        
        template = f"""-- Simple report template
SELECT 
    *,
    CASE 
        WHEN value_column > 100 THEN 'High'
        WHEN value_column > 50 THEN 'Medium'
        ELSE 'Low'
    END as value_category
FROM {last_cte}
WHERE date_column >= DATE('now', '-7 days')
ORDER BY date_column DESC, value_column DESC
LIMIT 500"""
        
        self.main_query_text.delete("1.0", "end")
        self.main_query_text.insert("1.0", template)

    def apply_hierarchical_template(self):
        """Применение шаблона иерархических данных"""
        template = """-- Hierarchical data analysis
WITH RECURSIVE org_hierarchy AS (
    -- Anchor: top-level managers
    SELECT 
        employee_id,
        employee_name,
        manager_id,
        1 as level,
        employee_name as hierarchy_path
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive: subordinates
    SELECT 
        e.employee_id,
        e.employee_name,
        e.manager_id,
        oh.level + 1,
        oh.hierarchy_path || ' -> ' || e.employee_name
    FROM employees e
    INNER JOIN org_hierarchy oh ON e.manager_id = oh.employee_id
    WHERE oh.level < 10
)
SELECT 
    employee_name,
    level,
    hierarchy_path,
    (SELECT COUNT(*) FROM employees WHERE manager_id = org_hierarchy.employee_id) as direct_reports
FROM org_hierarchy
ORDER BY level, employee_name"""
        
        self.main_query_text.delete("1.0", "end")
        self.main_query_text.insert("1.0", template)

    def apply_time_series_template(self):
        """Применение шаблона временных рядов"""
        template = """-- Time series analysis
WITH daily_stats AS (
    SELECT 
        DATE(event_time) as event_date,
        event_type,
        COUNT(*) as event_count,
        SUM(event_value) as total_value,
        AVG(event_value) as avg_value
    FROM events
    WHERE event_time >= DATE('now', '-30 days')
    GROUP BY DATE(event_time), event_type
),
date_series AS (
    SELECT DATE('now', '-30 days') + (value || ' days')::interval as series_date
    FROM generate_series(0, 30) as value
)
SELECT 
    ds.series_date,
    COALESCE(ds2.event_type, 'NO_EVENTS') as event_type,
    COALESCE(ds2.event_count, 0) as event_count,
    COALESCE(ds2.total_value, 0) as total_value
FROM date_series ds
LEFT JOIN daily_stats ds2 ON ds.series_date = ds2.event_date
ORDER BY ds.series_date DESC, ds2.event_count DESC"""
        
        self.main_query_text.delete("1.0", "end")
        self.main_query_text.insert("1.0", template)

    def apply_analysis_template(self):
        """Применение шаблона комплексного анализа"""
        template = """-- Complex data analysis with multiple CTEs
WITH 
-- Step 1: Filter and prepare raw data
filtered_data AS (
    SELECT *
    FROM source_table
    WHERE date_column >= '2024-01-01'
      AND status = 'ACTIVE'
      AND value_column > 0
),

-- Step 2: Calculate aggregates by category
category_stats AS (
    SELECT 
        category,
        COUNT(*) as record_count,
        AVG(value_column) as avg_value,
        STDDEV(value_column) as std_dev,
        MIN(value_column) as min_value,
        MAX(value_column) as max_value
    FROM filtered_data
    GROUP BY category
),

-- Step 3: Identify outliers
outliers AS (
    SELECT 
        fd.*,
        cs.avg_value,
        cs.std_dev,
        CASE 
            WHEN ABS(fd.value_column - cs.avg_value) > 2 * cs.std_dev 
            THEN 'OUTLIER' 
            ELSE 'NORMAL' 
        END as outlier_status
    FROM filtered_data fd
    INNER JOIN category_stats cs ON fd.category = cs.category
)

-- Final analysis
SELECT 
    cs.category,
    cs.record_count,
    cs.avg_value,
    cs.std_dev,
    COUNT(CASE WHEN o.outlier_status = 'OUTLIER' THEN 1 END) as outlier_count,
    ROUND(100.0 * COUNT(CASE WHEN o.outlier_status = 'OUTLIER' THEN 1 END) / cs.record_count, 2) as outlier_percentage
FROM category_stats cs
LEFT JOIN outliers o ON cs.category = o.category
GROUP BY cs.category, cs.record_count, cs.avg_value, cs.std_dev
HAVING cs.record_count > 10
ORDER BY outlier_percentage DESC, cs.record_count DESC"""
        
        self.main_query_text.delete("1.0", "end")
        self.main_query_text.insert("1.0", template)

    def generate_full_query(self):
        """Генерация полного SQL запроса со всеми CTE"""
        if not self.cte_definitions:
            messagebox.showwarning("Warning", "No CTEs defined")
            return
        
        main_query = self.main_query_text.get("1.0", "end").strip()
        if not main_query:
            messagebox.showwarning("Warning", "Please define the main query")
            return
        
        # Формируем полный запрос
        full_sql = "WITH\n"
        
        # Добавляем CTE определения
        cte_definitions = []
        for i, cte in enumerate(self.cte_definitions):
            cte_def = f"  {cte['name']} AS (\n"
            
            # Для рекурсивных CTE добавляем RECURSIVE и якорную часть
            if cte['type'] == 'RECURSIVE' and i == 0:
                full_sql = "WITH RECURSIVE\n"
                cte_def = f"  {cte['name']} AS (\n"
            
            cte_def += f"    {cte['query']}\n"
            cte_def += "  )"
            
            if i < len(self.cte_definitions) - 1:
                cte_def += ","
            
            cte_definitions.append(cte_def)
        
        full_sql += "\n".join(cte_definitions)
        full_sql += f"\n\n{main_query};"
        
        # Отображаем полный SQL
        self.full_sql_text.delete("1.0", "end")
        self.full_sql_text.insert("1.0", full_sql)
        
        # Обновляем статус
        self.status_label.configure(text=f"Generated query with {len(self.cte_definitions)} CTEs")
        
        # Переключаемся на вкладку предпросмотра
        self.tabview.set("Preview & Execute")

    def execute_full_query(self):
        """Выполнение полного SQL запроса"""
        full_sql = self.full_sql_text.get("1.0", "end").strip()
        
        if not full_sql:
            messagebox.showwarning("Warning", "No query to execute. Generate query first.")
            return
        
        try:
            # Выполняем запрос
            results = self.app.api_client.execute_custom_query(full_sql)
            
            # Очищаем результаты
            self.results_text.delete("1.0", "end")
            
            if not results:
                self.results_text.insert("1.0", "Query executed successfully. No results returned.")
                self.status_label.configure(text="Query executed: 0 rows returned")
                return
            
            # Отображаем результаты
            self.results_text.insert("1.0", f"Query executed successfully.\n")
            self.results_text.insert("end", f"Returned {len(results)} rows:\n\n")
            
            # Заголовки
            if hasattr(results[0], '_fields'):
                headers = results[0]._fields
                self.results_text.insert("end", " | ".join(headers) + "\n")
                self.results_text.insert("end", "-" * (len(" | ".join(headers))) + "\n\n")
            
            # Данные (первые 100 строк)
            for i, row in enumerate(results[:100], 1):
                self.results_text.insert("end", f"{i}. {row}\n")
            
            if len(results) > 100:
                self.results_text.insert("end", f"\n... and {len(results) - 100} more rows\n")
            
            self.status_label.configure(text=f"Query executed: {len(results)} rows returned")
            
        except Exception as e:
            messagebox.showerror("Execution Error", f"Failed to execute query: {e}")
            self.status_label.configure(text=f"Execution failed: {str(e)[:50]}...")

    def explain_query(self):
        """Выполнение EXPLAIN для запроса"""
        full_sql = self.full_sql_text.get("1.0", "end").strip()
        
        if not full_sql:
            messagebox.showwarning("Warning", "No query to explain. Generate query first.")
            return
        
        try:
            # Выполняем EXPLAIN
            explain_sql = f"EXPLAIN QUERY PLAN {full_sql}"
            results = self.app.api_client.execute_custom_query(explain_sql)
            
            # Отображаем план выполнения
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", "Query Execution Plan:\n\n")
            
            if results:
                for row in results:
                    self.results_text.insert("end", f"{row}\n")
            else:
                self.results_text.insert("end", "No execution plan available")
            
            self.status_label.configure(text="Query plan generated")
            
        except Exception as e:
            messagebox.showerror("Explain Error", f"Failed to explain query: {e}")

    def export_query_results(self):
        """Экспорт результатов запроса"""
        results_text = self.results_text.get("1.0", "end").strip()
        
        if not results_text or "No results" in results_text or "Query executed" not in results_text:
            messagebox.showwarning("Warning", "No results to export. Execute query first.")
            return
        
        try:
            from tkinter import filedialog
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="cte_query_results"
            )
            
            if not file_path:
                return
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # Записываем SQL запрос
                f.write("-- Generated SQL Query:\n")
                f.write(self.full_sql_text.get("1.0", "end"))
                f.write("\n\n-- Execution Results:\n")
                f.write(results_text)
            
            messagebox.showinfo("Success", f"Results exported to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")

    def clear_all_cte(self):
        """Очистка всех CTE и результатов"""
        if not messagebox.askyesno("Confirm Clear", 
                                  "Clear all CTEs, queries and results?"):
            return
        
        # Очищаем все данные
        self.cte_definitions = []
        self.current_cte_index = -1
        
        # Очищаем формы
        self.clear_cte_form()
        self.main_query_text.delete("1.0", "end")
        self.full_sql_text.delete("1.0", "end")
        self.results_text.delete("1.0", "end")
        
        # Обновляем дерево и списки
        self.update_cte_tree()
        self.update_available_cte_list()
        
        self.status_label.configure(text="All data cleared")
        
        messagebox.showinfo("Cleared", "All CTEs and queries have been cleared")


class TableSelectorDialog(ctk.CTkToplevel):
    """Диалог выбора таблицы"""
    def __init__(self, parent, tables):
        super().__init__(parent)
        self.tables = tables
        self.selected_table = None
        self.title("Select Table")
        self.geometry("400x300")
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса диалога"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="Select a table:", 
                    font=ctk.CTkFont(weight="bold")).pack(pady=(0, 10))
        
        # Список таблиц
        self.table_listbox = ctk.CTkTextbox(main_frame, height=150)
        self.table_listbox.pack(fill="both", expand=True, pady=(0, 10))
        
        for table in self.tables:
            self.table_listbox.insert("end", f"{table}\n")
        
        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="OK", 
                     command=self.on_ok).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", 
                     command=self.destroy).pack(side="right", padx=5)
        
    def on_ok(self):
        """Обработка нажатия OK"""
        try:
            # Получаем выделенную таблицу
            selection = self.table_listbox.get("sel.first", "sel.last")
            if selection:
                self.selected_table = selection.strip()
                self.destroy()
        except:
            messagebox.showwarning("Warning", "Please select a table from the list")


class CTESelectorDialog(ctk.CTkToplevel):
    """Диалог выбора CTE"""
    def __init__(self, parent, cte_names):
        super().__init__(parent)
        self.cte_names = cte_names
        self.selected_cte = None
        self.title("Select CTE")
        self.geometry("400x300")
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса диалога"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="Select a CTE:", 
                    font=ctk.CTkFont(weight="bold")).pack(pady=(0, 10))
        
        # Список CTE
        self.cte_listbox = ctk.CTkTextbox(main_frame, height=150)
        self.cte_listbox.pack(fill="both", expand=True, pady=(0, 10))
        
        for cte in self.cte_names:
            self.cte_listbox.insert("end", f"{cte}\n")
        
        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="OK", 
                     command=self.on_ok).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", 
                     command=self.destroy).pack(side="right", padx=5)
        
    def on_ok(self):
        """Обработка нажатия OK"""
        try:
            # Получаем выделенный CTE
            selection = self.cte_listbox.get("sel.first", "sel.last")
            if selection:
                self.selected_cte = selection.strip()
                self.destroy()
        except:
            messagebox.showwarning("Warning", "Please select a CTE from the list")