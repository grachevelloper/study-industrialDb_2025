import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import List, Dict, Optional
import json
import re

class ViewManager:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.current_views = []
        self.current_view_structure = None
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса управления представлениями"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="View Manager",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Основной фрейм с вкладками
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Вкладка: Список представлений
        self.views_list_tab = self.tabview.add("Views List")
        self.setup_views_list_tab()
        
        # Вкладка: Создание представления
        self.create_view_tab = self.tabview.add("Create View")
        self.setup_create_view_tab()
        
        # Вкладка: Просмотр данных
        self.view_data_tab = self.tabview.add("View Data")
        self.setup_view_data_tab()
        
        # Вкладка: Структура представления
        self.view_structure_tab = self.tabview.add("View Structure")
        self.setup_view_structure_tab()

        # Загружаем список представлений при запуске
        self.load_views_list()
    
    def load_views_list(self):
        try:
            # Вместо использования get_all_views(), выполняем запрос напрямую
            query = """
            SELECT name, type, tbl_name, sql 
            FROM sqlite_master 
            WHERE type = 'view'
            ORDER BY name
            """
            
            results = self.app.api_client.execute_custom_query(query)
            self.current_views = []
            
            # Очищаем контейнер
            for widget in self.views_container.winfo_children():
                widget.destroy()
            
            if not results:
                # Нет представлений
                no_views_label = ctk.CTkLabel(self.views_container, 
                                            text="No views found in database",
                                            font=ctk.CTkFont(size=12, slant="italic"))
                no_views_label.pack(pady=20)
                self.view_selector_combo.configure(values=[])
                self.struct_view_selector_combo.configure(values=[])
                return
            
            for i, row in enumerate(results):
                view_name = row[0]
                view_type = row[1]
                table_name = row[2]
                sql_definition = row[3] if row[3] else ""
                
                try:
                    count_result = self.app.api_client.execute_custom_query(
                        f"SELECT COUNT(*) FROM `{view_name}`"
                    )
                    row_count = count_result[0][0] if count_result and count_result[0] else 0
                except:
                    row_count = 0
                
                view_frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
                view_frame.pack(fill="x", pady=5, padx=5)
                
                name_label = ctk.CTkLabel(view_frame, text=view_name, width=200,
                                        anchor="w", font=ctk.CTkFont(size=12))
                name_label.grid(row=0, column=0, padx=5, sticky="w")
                
                count_label = ctk.CTkLabel(view_frame, text=str(row_count), width=80,
                                        anchor="w")
                count_label.grid(row=0, column=1, padx=5, sticky="w")
                
                actions_frame = ctk.CTkFrame(view_frame, fg_color="transparent")
                actions_frame.grid(row=0, column=2, padx=5, sticky="w")
                
                view_btn = ctk.CTkButton(actions_frame, text="View Data", width=80,
                                    command=lambda vn=view_name: self.view_view_data(vn))
                view_btn.pack(side="left", padx=2)
                
                delete_btn = ctk.CTkButton(actions_frame, text="Delete", width=60,
                                        command=lambda vn=view_name: self.delete_view(vn),
                                        fg_color="#ff6b6b")
                delete_btn.pack(side="left", padx=2)
                
                self.current_views.append({
                    'name': view_name,
                    'type': view_type,
                    'table_name': table_name,
                    'sql': sql_definition,
                    'row_count': row_count
                })
            
            view_names = [view['name'] for view in self.current_views]
            self.view_selector_combo.configure(values=view_names)
            self.struct_view_selector_combo.configure(values=view_names)
            
            if view_names:
                self.view_selector_combo.set(view_names[0])
                self.struct_view_selector_combo.set(view_names[0])
            
            self.app.window.title(f"DDoS Attack Manager - {len(results)} views loaded")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load views: {str(e)[:100]}")

    def setup_views_list_tab(self):
        """Настройка вкладки списка представлений"""
        main_frame = ctk.CTkFrame(self.views_list_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель управления
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(controls_frame, text="Refresh List", 
                     command=self.load_views_list,
                     width=120).pack(side="left", padx=5)
        
        # Список представлений с прокруткой
        list_frame = ctk.CTkScrollableFrame(main_frame, height=400)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Заголовки таблицы
        headers_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        headers_frame.pack(fill="x", pady=(0, 10))
        
        headers = ["View Name", "Rows", "Actions"]
        widths = [200, 80, 150]
        
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, 
                               font=ctk.CTkFont(weight="bold"),
                               width=widths[i])
            label.grid(row=0, column=i, padx=5, sticky="w")
        
        # Контейнер для списка представлений
        self.views_container = ctk.CTkFrame(list_frame, fg_color="transparent")
        self.views_container.pack(fill="both", expand=True)

    def setup_create_view_tab(self):
        """Настройка вкладки создания представления"""
        main_frame = ctk.CTkFrame(self.create_view_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Форма создания представления
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="x", pady=(0, 15))
        
        # Название представления
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(name_frame, text="View Name:", width=100).pack(side="left")
        self.view_name_entry = ctk.CTkEntry(name_frame, placeholder_text="Enter view name")
        self.view_name_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Информация о требованиях к имени
        info_label = ctk.CTkLabel(name_frame, 
                                 text="(letters, numbers, underscores only)",
                                 text_color="gray",
                                 font=ctk.CTkFont(size=10))
        info_label.pack(side="left", padx=10)
        
        # SQL запрос
        query_frame = ctk.CTkFrame(main_frame)
        query_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(query_frame, text="SQL Query:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Кнопки для помощи в создании запроса
        query_help_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        query_help_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        templates = [
            ("SELECT", "SELECT id, name, danger FROM attacks WHERE danger = 'high'"),
            ("JOIN", "SELECT a.name, t.target_ip FROM attacks a JOIN targets t ON a.target_id = t.id"),
            ("WHERE", "WHERE danger = 'high' AND frequency = 'very_high'"),
            ("GROUP BY", "SELECT attack_type, COUNT(*) as count FROM attacks GROUP BY attack_type")
        ]
        
        for text, template in templates:
            btn = ctk.CTkButton(query_help_frame, text=text, 
                              command=lambda t=template: self.insert_template(t),
                              width=120)
            btn.pack(side="left", padx=2)
        
        # Поле для SQL запроса
        self.query_text = ctk.CTkTextbox(query_frame, height=150)
        self.query_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Информация о запросе
        query_info = ctk.CTkLabel(query_frame, 
                                 text="Only SELECT queries are allowed in views",
                                 text_color="gray",
                                 font=ctk.CTkFont(size=10))
        query_info.pack(anchor="w", padx=15, pady=(0, 5))
        
        # Кнопки создания
        create_buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        create_buttons_frame.pack(fill="x")
        
        ctk.CTkButton(create_buttons_frame, text="Create View", 
                     command=self.create_view,
                     fg_color="#4ecdc4").pack(side="left", padx=5)
        
        ctk.CTkButton(create_buttons_frame, text="Validate SQL", 
                     command=self.validate_sql).pack(side="left", padx=5)
        
        ctk.CTkButton(create_buttons_frame, text="Clear Form", 
                     command=self.clear_create_form).pack(side="left", padx=5)

    def setup_view_data_tab(self):
        """Настройка вкладки просмотра данных"""
        main_frame = ctk.CTkFrame(self.view_data_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель выбора представления
        selection_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        selection_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(selection_frame, text="Select View:").pack(side="left", padx=(0, 10))
        
        self.view_selector_combo = ctk.CTkComboBox(selection_frame, width=200)
        self.view_selector_combo.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(selection_frame, text="Load Data", 
                     command=self.load_view_data).pack(side="left", padx=5)
        
        ctk.CTkButton(selection_frame, text="Export Data", 
                     command=self.export_view_data).pack(side="left", padx=5)
        
        # Кнопка обновления списка
        ctk.CTkButton(selection_frame, text="Refresh Views", 
                     command=self.load_views_list,
                     width=120).pack(side="right", padx=5)
        
        # Отображение данных
        data_frame = ctk.CTkFrame(main_frame)
        data_frame.pack(fill="both", expand=True)
        
        # Текст с результатами
        self.data_text = ctk.CTkTextbox(data_frame, wrap="none")
        self.data_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Статусная строка
        self.data_status_label = ctk.CTkLabel(main_frame, text="Select a view to load data", 
                                            font=ctk.CTkFont(size=12))
        self.data_status_label.pack(anchor="w", pady=(5, 0))

    def setup_view_structure_tab(self):
        """Настройка вкладки структуры представления"""
        main_frame = ctk.CTkFrame(self.view_structure_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель выбора представления
        struct_selection_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        struct_selection_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(struct_selection_frame, text="Select View:").pack(side="left", padx=(0, 10))
        
        self.struct_view_selector_combo = ctk.CTkComboBox(struct_selection_frame, width=200)
        self.struct_view_selector_combo.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(struct_selection_frame, text="Show Structure", 
                     command=self.show_view_structure).pack(side="left", padx=5)
        
        ctk.CTkButton(struct_selection_frame, text="Show Definition", 
                     command=self.show_view_definition).pack(side="left", padx=5)
        
        # Отображение структуры
        structure_frame = ctk.CTkFrame(main_frame)
        structure_frame.pack(fill="both", expand=True)
        
        # Текст со структурой
        self.structure_text = ctk.CTkTextbox(structure_frame, wrap="none")
        self.structure_text.pack(fill="both", expand=True, padx=5, pady=5)

    def load_views_list(self):
        """Загрузка списка представлений из БД"""
        try:
            # Используем метод из DatabaseManager
            results = self.app.api_client.get_all_views()
            self.current_views = results
            
            # Очищаем контейнер
            for widget in self.views_container.winfo_children():
                widget.destroy()
            
            if not results:
                # Нет представлений
                no_views_label = ctk.CTkLabel(self.views_container, 
                                             text="No views found in database",
                                             font=ctk.CTkFont(size=12, slant="italic"))
                no_views_label.pack(pady=20)
                self.view_selector_combo.configure(values=[])
                self.struct_view_selector_combo.configure(values=[])
                return
            
            # Заполняем список
            for i, view in enumerate(results):
                view_name = view.get('name', '')
                row_count = view.get('row_count', 0)
                if row_count is None:
                    row_count = 0
                
                # Создаем фрейм для каждого представления
                view_frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
                view_frame.pack(fill="x", pady=5, padx=5)
                
                # Имя представления
                name_label = ctk.CTkLabel(view_frame, text=view_name, width=200,
                                        anchor="w", font=ctk.CTkFont(size=12))
                name_label.grid(row=0, column=0, padx=5, sticky="w")
                
                # Количество строк
                count_label = ctk.CTkLabel(view_frame, text=str(row_count), width=80,
                                         anchor="w")
                count_label.grid(row=0, column=1, padx=5, sticky="w")
                
                # Кнопки действий
                actions_frame = ctk.CTkFrame(view_frame, fg_color="transparent")
                actions_frame.grid(row=0, column=2, padx=5, sticky="w")
                
                # Кнопка просмотра данных
                view_btn = ctk.CTkButton(actions_frame, text="View Data", width=80,
                                       command=lambda vn=view_name: self.view_view_data(vn))
                view_btn.pack(side="left", padx=2)
                
                # Кнопка удаления
                delete_btn = ctk.CTkButton(actions_frame, text="Delete", width=60,
                                         command=lambda vn=view_name: self.delete_view(vn),
                                         fg_color="#ff6b6b")
                delete_btn.pack(side="left", padx=2)
            
            # Обновляем комбобоксы
            view_names = [view.get('name', '') for view in results]
            self.view_selector_combo.configure(values=view_names)
            self.struct_view_selector_combo.configure(values=view_names)
            
            if view_names:
                self.view_selector_combo.set(view_names[0])
                self.struct_view_selector_combo.set(view_names[0])
            
            # Обновляем статус
            self.app.window.title(f"DDoS Attack Manager - {len(results)} views loaded")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load views: {str(e)[:100]}")

    def insert_template(self, template):
        """Вставка шаблона SQL"""
        self.query_text.insert("insert", template)

    def validate_sql(self):
        """Валидация SQL запроса"""
        sql = self.query_text.get("1.0", "end").strip()
        if not sql:
            messagebox.showwarning("Warning", "Please enter SQL query")
            return
        
        # Проверка базового синтаксиса
        if not sql.lower().strip().startswith("select"):
            messagebox.showwarning("Warning", "Only SELECT queries can be used in views")
            return
        
        # Проверяем наличие запрещенных операторов
        forbidden_keywords = ["insert", "update", "delete", "drop", "alter", "create table"]
        for keyword in forbidden_keywords:
            if f" {keyword} " in sql.lower():
                messagebox.showerror("Error", f"View queries cannot contain '{keyword.upper()}' statements")
                return
        
        try:
            # Пробуем выполнить EXPLAIN QUERY PLAN для проверки синтаксиса
            result = self.app.api_client.execute_custom_query(f"EXPLAIN QUERY PLAN {sql}")
            
            if result:
                messagebox.showinfo("SQL Valid", "✓ SQL query syntax is valid!\nThe query can be used to create a view.")
            else:
                messagebox.showwarning("Warning", "Query returned no execution plan")
                
        except Exception as e:
            error_msg = str(e)
            if "no such table" in error_msg.lower():
                messagebox.showwarning("Warning", 
                    "Query references non-existent tables. Please check table names.")
            elif "syntax error" in error_msg.lower():
                messagebox.showerror("Syntax Error", f"Invalid SQL syntax:\n{error_msg[:100]}")
            else:
                messagebox.showerror("Validation Error", f"Failed to validate SQL: {error_msg[:100]}")

    def create_view(self):
        """Создание нового представления"""
        view_name = self.view_name_entry.get().strip()
        sql = self.query_text.get("1.0", "end").strip()
        
        if not view_name:
            messagebox.showwarning("Warning", "Please enter view name")
            return
        
        if not sql:
            messagebox.showwarning("Warning", "Please enter SQL query")
            return
        
        # Проверяем имя представления
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', view_name):
            messagebox.showwarning("Warning", 
                "View name must:\n- Start with a letter or underscore\n- Contain only letters, numbers and underscores")
            return
        
        # Проверяем, что это SELECT запрос
        sql_lower = sql.lower().strip()
        if not sql_lower.startswith("select"):
            messagebox.showwarning("Warning", "Views can only be created from SELECT queries")
            return
        
        # Проверяем наличие запрещенных операторов
        forbidden_in_view = ["insert ", "update ", "delete ", "drop ", "alter ", "create table "]
        for forbidden in forbidden_in_view:
            if forbidden in sql_lower:
                messagebox.showerror("Error", 
                    f"View queries cannot contain '{forbidden.strip().upper()}' statements")
                return
        
        # Проверяем, не существует ли уже такое представление
        for view in self.current_views:
            if view.get('name', '').lower() == view_name.lower():
                if not messagebox.askyesno("View Exists", 
                                          f"View '{view_name}' already exists. Replace it?"):
                    return
                # Удаляем существующее представление
                try:
                    self.app.api_client.drop_view(view_name)
                except:
                    pass
                break
        
        try:
            # Используем метод create_view из DatabaseManager
            success = self.app.api_client.create_view(
                view_name=view_name,
                query=sql,
                view_type='REGULAR',
                is_materialized=False,
                description=''
            )
            
            if success:
                # Обновляем список представлений
                self.load_views_list()
                
                # Очищаем форму
                self.clear_create_form()
                
                messagebox.showinfo("Success", 
                    f"View '{view_name}' created successfully!\n\nYou can now use it in queries like:\nSELECT * FROM `{view_name}`")
            else:
                messagebox.showerror("Error", f"Failed to create view '{view_name}'")
            
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                messagebox.showerror("Error", f"View '{view_name}' already exists")
            elif "syntax error" in error_msg.lower():
                messagebox.showerror("SQL Syntax Error", 
                    f"Invalid SQL syntax in view definition:\n{error_msg[:150]}")
            else:
                messagebox.showerror("Error", f"Failed to create view:\n{error_msg[:150]}")

    def clear_create_form(self):
        """Очистка формы создания"""
        self.view_name_entry.delete(0, "end")
        self.query_text.delete("1.0", "end")

    def view_view_data(self, view_name):
        """Просмотр данных представления"""
        self.tabview.set("View Data")
        self.view_selector_combo.set(view_name)
        self.load_view_data()

    def delete_view(self, view_name):
        """Удаление представления"""
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete view '{view_name}'?\n\nThis action cannot be undone."):
            return
        
        try:
            # Используем метод drop_view из DatabaseManager
            success = self.app.api_client.drop_view(view_name)
            
            if success:
                # Обновляем список
                self.load_views_list()
                
                # Обновляем комбобоксы, если удаленное представление было выбрано
                if self.view_selector_combo.get() == view_name:
                    if self.current_views:
                        self.view_selector_combo.set(self.current_views[0].get('name', ''))
                    else:
                        self.view_selector_combo.set("")
                
                if self.struct_view_selector_combo.get() == view_name:
                    if self.current_views:
                        self.struct_view_selector_combo.set(self.current_views[0].get('name', ''))
                    else:
                        self.struct_view_selector_combo.set("")
                
                messagebox.showinfo("Success", f"View '{view_name}' deleted successfully")
            else:
                messagebox.showerror("Error", f"Failed to delete view '{view_name}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete view: {e}")

    def load_view_data(self):
        """Загрузка данных из выбранного представления"""
        view_name = self.view_selector_combo.get()
        if not view_name:
            messagebox.showwarning("Warning", "Please select a view")
            return
        
        try:
            # Безопасный запрос с экранированием имени
            query = f"SELECT * FROM `{view_name}` LIMIT 100"
            results = self.app.api_client.execute_custom_query(query)
            
            # Очищаем текстовое поле
            self.data_text.delete("1.0", "end")
            
            if not results:
                self.data_text.insert("1.0", f"No data found in view '{view_name}'")
                self.data_status_label.configure(text=f"View '{view_name}': 0 rows")
                return
            
            # Отображаем данные
            self.data_text.insert("1.0", f"Data from view '{view_name}':\n\n")
            
            # Определяем количество столбцов
            if results:
                # Получаем количество столбцов из первой строки
                if isinstance(results[0], (tuple, list)):
                    num_columns = len(results[0])
                    # Создаем заголовки
                    headers = [f"Column_{i+1}" for i in range(num_columns)]
                    header_line = " | ".join(headers)
                    self.data_text.insert("end", f"{header_line}\n")
                    self.data_text.insert("end", "-" * len(header_line) + "\n\n")
            
            # Отображаем данные
            for i, row in enumerate(results, 1):
                # Форматируем строку для отображения
                if isinstance(row, (tuple, list)):
                    # Для кортежей/списков
                    formatted_row = " | ".join([str(cell)[:30] + "..." if len(str(cell)) > 30 else str(cell) for cell in row])
                else:
                    # Для других типов
                    formatted_row = str(row)
                
                self.data_text.insert("end", f"{i:3}. {formatted_row}\n")
            
            # Получаем общее количество строк
            try:
                count_query = f"SELECT COUNT(*) FROM `{view_name}`"
                count_result = self.app.api_client.execute_custom_query(count_query)
                total_rows = count_result[0][0] if count_result and count_result[0] else len(results)
            except:
                total_rows = len(results)
            
            # Обновляем статус
            showing = min(len(results), 100)
            self.data_status_label.configure(
                text=f"View '{view_name}': Showing {showing} of {total_rows} rows"
            )
            
        except Exception as e:
            error_msg = str(e)
            self.data_text.delete("1.0", "end")
            self.data_text.insert("1.0", f"Error loading data from '{view_name}':\n{error_msg}")
            self.data_status_label.configure(text=f"Error loading view '{view_name}'")

    def export_view_data(self):
        """Экспорт данных представления в файл"""
        view_name = self.view_selector_combo.get()
        if not view_name:
            messagebox.showwarning("Warning", "Please select a view")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialfile=f"{view_name}_export"
            )
            
            if not file_path:
                return
            
            # Показываем индикатор прогресса
            progress = ctk.CTkLabel(self.parent, text="Exporting data...", fg_color="yellow")
            progress.place(relx=0.5, rely=0.5, anchor="center")
            self.parent.update()
            
            try:
                # Получаем все данные
                query = f"SELECT * FROM `{view_name}`"
                results = self.app.api_client.execute_custom_query(query)
                
                if not results:
                    messagebox.showwarning("Warning", "No data to export")
                    progress.destroy()
                    return
                
                # Экспортируем в выбранный формат
                if file_path.endswith('.json'):
                    # Экспорт в JSON
                    data_list = []
                    for row in results:
                        if hasattr(row, '_asdict'):
                            data_list.append(row._asdict())
                        elif isinstance(row, (tuple, list)):
                            # Преобразуем кортеж в словарь
                            data_list.append({f"col_{i}": val for i, val in enumerate(row)})
                        else:
                            data_list.append({"data": str(row)})
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data_list, f, indent=2, ensure_ascii=False)
                    
                    file_type = "JSON"
                
                else:
                    # Экспорт в CSV/TXT
                    with open(file_path, 'w', encoding='utf-8') as f:
                        # Если есть информация о столбцах
                        if results and hasattr(results[0], '_fields'):
                            # Используем названия столбцов из _fields
                            f.write(",".join(results[0]._fields) + "\n")
                            
                            for row in results:
                                values = [f'"{str(v)}"' if ',' in str(v) else str(v) 
                                         for v in row._asdict().values()]
                                f.write(",".join(values) + "\n")
                        else:
                            # Без заголовков
                            for row in results:
                                if isinstance(row, (tuple, list)):
                                    values = [f'"{str(v)}"' if ',' in str(v) else str(v) 
                                             for v in row]
                                else:
                                    values = [str(row)]
                                f.write(",".join(values) + "\n")
                    
                    file_type = "CSV" if file_path.endswith('.csv') else "text"
                
                messagebox.showinfo("Success", 
                    f"Exported {len(results)} rows from '{view_name}' to:\n{file_path}\n\nFormat: {file_type}")
                
            finally:
                # Убираем индикатор прогресса
                progress.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)[:150]}")

    def show_view_structure(self):
        view_name = self.struct_view_selector_combo.get()
        if not view_name:
            messagebox.showwarning("Warning", "Please select a view")
            return
        
        try:
            # Метод 1: Пробуем получить структуру через PRAGMA
            try:
                structure = self.app.api_client.execute_custom_query(f"PRAGMA table_info(`{view_name}`)")
            except:
                structure = []
            
            # Метод 2: Если PRAGMA не работает, анализируем запрос представления
            if not structure:
                # Получаем определение представления
                query = "SELECT sql FROM sqlite_master WHERE type = 'view' AND name = ?"
                result = self.app.api_client.execute_custom_query(query, (view_name,))
                
                if not result or not result[0][0]:
                    self.structure_text.delete("1.0", "end")
                    self.structure_text.insert("1.0", 
                        f"No structure information available for view '{view_name}'")
                    return
                
                sql_definition = result[0][0]
                
                # Парсим SQL для извлечения структуры
                structure = self._parse_view_structure_from_sql(sql_definition)
            
            # Очищаем текстовое поле
            self.structure_text.delete("1.0", "end")
            
            if not structure:
                self.structure_text.insert("1.0", 
                    f"Cannot determine structure for view '{view_name}'\n\n"
                    f"This is a known limitation in SQLite for some views.\n"
                    f"Try querying the view directly to see its columns.")
                return
            
            # Отображаем структуру
            self.structure_text.insert("1.0", f"Structure of view '{view_name}':\n\n")
            self.structure_text.insert("end", "Column Name | Type | Not Null | Default | Primary Key\n")
            self.structure_text.insert("end", "-" * 80 + "\n")
            
            for col in structure:
                # Обрабатываем разные форматы результатов
                if isinstance(col, (tuple, list)) and len(col) >= 6:
                    # Результат из PRAGMA table_info
                    col_name = col[1]
                    col_type = col[2] or 'TEXT'
                    not_null = "Yes" if col[3] else "No"
                    default_val = str(col[4]) if col[4] is not None else "NULL"
                    pk = "Yes" if col[5] else "No"
                elif isinstance(col, dict):
                    # Результат из парсинга SQL
                    col_name = col.get('name', 'Unknown')
                    col_type = col.get('type', 'TEXT')
                    not_null = col.get('not_null', 'No')
                    default_val = col.get('default', 'NULL')
                    pk = col.get('pk', 'No')
                else:
                    continue
                
                self.structure_text.insert("end", 
                    f"{col_name:11} | {col_type:10} | {not_null:8} | {default_val:8} | {pk:12}\n")
            
            self.structure_text.insert("end", f"\nTotal columns: {len(structure)}")
            
        except Exception as e:
            error_msg = str(e)
            self.structure_text.delete("1.0", "end")
            self.structure_text.insert("1.0", 
                f"Error getting structure for '{view_name}':\n{error_msg}\n\n"
                f"Try using 'Show Definition' instead.")

    def _parse_view_structure_from_sql(self, sql_definition: str) -> List[Dict[str, str]]:
        """Парсинг структуры из SQL определения представления"""
        try:
            # Извлекаем часть SELECT из определения
            # Ищем "AS" после CREATE VIEW ... AS
            parts = sql_definition.upper().split('AS')
            if len(parts) < 2:
                return []
            
            select_part = 'AS'.join(parts[1:]).strip()
            
            # Более простой метод: выполним запрос с LIMIT 0
            # Это покажет нам столбцы без возвращения данных
            view_name_match = re.search(r'CREATE VIEW\s+(\w+)', sql_definition, re.IGNORECASE)
            if not view_name_match:
                return []
            
            view_name = view_name_match.group(1)
            try:
                # Пробуем выполнить запрос с LIMIT 0
                test_query = f"SELECT * FROM `{view_name}` LIMIT 0"
                cursor = self.app.api_client.execute_custom_query(test_query, return_cursor=True)
                
                if cursor and cursor.description:
                    columns = []
                    for desc in cursor.description:
                        columns.append({
                            'name': desc[0],
                            'type': desc[1] or 'TEXT',
                            'not_null': 'No',  # Не можем определить из cursor
                            'default': 'NULL',
                            'pk': 'No'
                        })
                    return columns
            except:
                pass
            
            # Альтернативный метод: анализируем список столбцов после SELECT
            lines = sql_definition.upper().split('\n')
            select_line_idx = -1
            for i, line in enumerate(lines):
                if 'SELECT' in line:
                    select_line_idx = i
                    break
            
            if select_line_idx == -1:
                return []
            
            # Простая эвристика для извлечения столбцов
            columns = []
            in_select = False
            for line in lines[select_line_idx:]:
                if 'SELECT' in line:
                    in_select = True
                    line = line[line.find('SELECT') + 6:].strip()
                
                if 'FROM' in line and in_select:
                    line = line[:line.find('FROM')].strip()
                    in_select = False
                
                # Разбиваем по запятым для получения столбцов
                if in_select:
                    # Убираем комментарии
                    line = re.sub(r'--.*$', '', line)
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        if part and not part.startswith('FROM'):
                            # Извлекаем имя столбца (после AS или перед AS)
                            if ' AS ' in part.upper():
                                col_parts = part.upper().split(' AS ')
                                col_name = col_parts[1].strip().strip('"').strip("'").strip('`')
                            else:
                                # Берем последнюю часть после точки или как есть
                                col_name = part.split('.')[-1].strip().strip('"').strip("'").strip('`')
                            
                            if col_name and col_name not in ['', 'SELECT', 'FROM']:
                                columns.append({
                                    'name': col_name,
                                    'type': 'TEXT',  # По умолчанию
                                    'not_null': 'No',
                                    'default': 'NULL',
                                    'pk': 'No'
                                })
            
            return columns
            
        except Exception as e:
            print(f"Error parsing view structure: {e}")
            return []   
     
    def show_view_definition(self):
        """Показать определение выбранного представления"""
        view_name = self.struct_view_selector_combo.get()
        if not view_name:
            messagebox.showwarning("Warning", "Please select a view")
            return
        
        try:
            # Получаем информацию о представлении
            query = "SELECT name, type, tbl_name, sql FROM sqlite_master WHERE type = 'view' AND name = ?"
            result = self.app.api_client.execute_custom_query(query, (view_name,))
            
            if not result:
                self.structure_text.delete("1.0", "end")
                self.structure_text.insert("1.0", 
                    f"View '{view_name}' not found in database.")
                return
            
            # Очищаем текстовое поле
            self.structure_text.delete("1.0", "end")
            
            sql_definition = result[0][3] if len(result[0]) > 3 else 'No definition available'
            
            self.structure_text.insert("1.0", f"SQL Definition of view '{view_name}':\n\n")
            self.structure_text.insert("end", "-" * 80 + "\n\n")
            
            # Форматируем SQL для лучшего отображения
            formatted_sql = sql_definition.replace("CREATE VIEW", "\nCREATE VIEW")
            formatted_sql = formatted_sql.replace("SELECT", "\nSELECT")
            formatted_sql = formatted_sql.replace("FROM", "\nFROM")
            formatted_sql = formatted_sql.replace("WHERE", "\nWHERE")
            formatted_sql = formatted_sql.replace("GROUP BY", "\nGROUP BY")
            formatted_sql = formatted_sql.replace("ORDER BY", "\nORDER BY")
            formatted_sql = formatted_sql.replace("JOIN", "\nJOIN")
            formatted_sql = formatted_sql.replace("ON", "\n    ON")
            
            self.structure_text.insert("end", formatted_sql)
            
            # Добавляем информацию о представлении
            self.structure_text.insert("end", f"\n\n" + "-" * 80 + "\n")
            self.structure_text.insert("end", f"View type: view\n")
            
            # Находим представление в списке для дополнительной информации
            for view in self.current_views:
                if view.get('name') == view_name:
                    self.structure_text.insert("end", f"Rows: {view.get('row_count', 'N/A')}\n")
                    break
            
        except Exception as e:
            self.structure_text.delete("1.0", "end")
            self.structure_text.insert("1.0", 
                f"Error getting definition for '{view_name}':\n{str(e)}")