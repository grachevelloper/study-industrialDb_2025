import customtkinter as ctk
from tkinter import messagebox
import json

class SubqueryFilters:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.subqueries = []
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса фильтров с подзапросами"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Subquery Filters Builder",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Основной фрейм с фильтрами
        self.create_filters_section(main_frame)

        # Кнопки управления
        self.create_controls_section(main_frame)

        # Область результатов
        self.create_results_section(main_frame)

    def create_filters_section(self, parent):
        """Создание секции фильтров"""
        filters_frame = ctk.CTkFrame(parent)
        filters_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(filters_frame, text="Main Condition", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # Основное условие
        main_condition_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        main_condition_frame.pack(fill="x", padx=15, pady=5)

        # Поля для основного условия
        fields = ["name", "frequency", "danger", "attack_type", "created_at"]
        self.main_field = ctk.CTkComboBox(main_condition_frame, values=fields, width=120)
        self.main_field.pack(side="left", padx=2)
        self.main_field.set("name")

        operators = ["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN"]
        self.main_operator = ctk.CTkComboBox(main_condition_frame, values=operators, width=80)
        self.main_operator.pack(side="left", padx=2)
        self.main_operator.set("=")

        self.main_value = ctk.CTkEntry(main_condition_frame, placeholder_text="Value", width=150)
        self.main_value.pack(side="left", padx=2)

        # Подзапросы
        ctk.CTkLabel(filters_frame, text="Subqueries", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))

        subquery_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        subquery_frame.pack(fill="x", padx=15, pady=5)

        # Список подзапросов
        self.subqueries_listbox = ctk.CTkTextbox(subquery_frame, height=100)
        self.subqueries_listbox.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Кнопки управления подзапросами
        subquery_buttons_frame = ctk.CTkFrame(subquery_frame, fg_color="transparent", width=100)
        subquery_buttons_frame.pack(side="right", fill="y")

        ctk.CTkButton(subquery_buttons_frame, text="Add Subquery", 
                     command=self.add_subquery, width=100).pack(pady=2)
        ctk.CTkButton(subquery_buttons_frame, text="Remove", 
                     command=self.remove_subquery, width=100).pack(pady=2)
        ctk.CTkButton(subquery_buttons_frame, text="Clear All", 
                     command=self.clear_subqueries, width=100).pack(pady=2)

        # Операторы подзапросов
        ctk.CTkLabel(filters_frame, text="Subquery Operator", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))

        operator_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        operator_frame.pack(fill="x", padx=15, pady=5)

        self.subquery_operator = ctk.CTkComboBox(operator_frame, 
                                               values=["ANY", "ALL", "EXISTS"], width=120)
        self.subquery_operator.pack(side="left", padx=2)
        self.subquery_operator.set("ANY")

    def create_controls_section(self, parent):
        """Создание секции управления"""
        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(fill="x", pady=10)

        ctk.CTkButton(controls_frame, text="Apply Filters", 
                     command=self.apply_filters,
                     fg_color=self.app.colors["success"]).pack(side="left", padx=5)

        ctk.CTkButton(controls_frame, text="Reset Filters", 
                     command=self.reset_filters,
                     fg_color=self.app.colors["warning"]).pack(side="left", padx=5)

        ctk.CTkButton(controls_frame, text="Show SQL", 
                     command=self.show_sql,
                     fg_color=self.app.colors["primary"]).pack(side="left", padx=5)

    def create_results_section(self, parent):
        """Создание секции результатов"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(results_frame, text="Results", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        self.results_text = ctk.CTkTextbox(results_frame, wrap="none")
        self.results_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def add_subquery(self):
        """Добавление нового подзапроса"""
        dialog = SubqueryDialog(self.parent, self.app)
        if dialog.result:
            self.subqueries.append(dialog.result)
            self.update_subqueries_list()

    def remove_subquery(self):
        """Удаление выбранного подзапроса"""
        if self.subqueries:
            self.subqueries.pop()
            self.update_subqueries_list()

    def clear_subqueries(self):
        """Очистка всех подзапросов"""
        self.subqueries = []
        self.update_subqueries_list()

    def update_subqueries_list(self):
        """Обновление списка подзапросов"""
        self.subqueries_listbox.delete("1.0", "end")
        for i, sq in enumerate(self.subqueries):
            self.subqueries_listbox.insert("end", 
                f"Subquery {i+1}: {sq['field']} {sq['operator']} {sq['value']}\n")

    def apply_filters(self):
        """Применение фильтров"""
        try:
            # Собираем условия
            conditions = []
            params = []

            # Основное условие
            if self.main_field.get() and self.main_operator.get() and self.main_value.get():
                conditions.append(f"{self.main_field.get()} {self.main_operator.get()} ?")
                params.append(self.main_value.get())

            # Подзапросы
            for subquery in self.subqueries:
                operator = self.subquery_operator.get()
                if operator == "EXISTS":
                    conditions.append(f"EXISTS (SELECT 1 FROM attacks WHERE {subquery['field']} {subquery['operator']} ?)")
                else:
                    conditions.append(f"{subquery['field']} {operator} (SELECT {subquery['field']} FROM attacks WHERE {subquery['field']} {subquery['operator']} ?)")
                params.append(subquery['value'])

            # Формируем запрос
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM attacks WHERE {where_clause}"

            # Выполняем запрос
            results = self.app.api_client.execute_custom_query(query, params)
            
            # Показываем результаты
            self.show_results(results, query)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filters: {e}")

    def reset_filters(self):
        """Сброс фильтров"""
        self.main_field.set("name")
        self.main_operator.set("=")
        self.main_value.delete(0, "end")
        self.subqueries = []
        self.update_subqueries_list()
        self.subquery_operator.set("ANY")
        self.results_text.delete("1.0", "end")

    def show_sql(self):
        """Показать SQL запрос"""
        conditions = []
        
        if self.main_field.get() and self.main_operator.get() and self.main_value.get():
            conditions.append(f"{self.main_field.get()} {self.main_operator.get()} '{self.main_value.get()}'")

        for subquery in self.subqueries:
            operator = self.subquery_operator.get()
            if operator == "EXISTS":
                conditions.append(f"EXISTS (SELECT 1 FROM attacks WHERE {subquery['field']} {subquery['operator']} '{subquery['value']}')")
            else:
                conditions.append(f"{subquery['field']} {operator} (SELECT {subquery['field']} FROM attacks WHERE {subquery['field']} {subquery['operator']} '{subquery['value']}')")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM attacks WHERE {where_clause}"

        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"Generated SQL:\n\n{sql}")

    def show_results(self, results, query):
        """Показать результаты запроса"""
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"Query: {query}\n\n")
        self.results_text.insert("end", f"Found {len(results)} records:\n\n")
        
        for i, result in enumerate(results, 1):
            self.results_text.insert("end", f"{i}. {result}\n\n")

class SubqueryDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.result = None
        self.title("Add Subquery")
        self.geometry("300x200")
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        fields = ["name", "frequency", "danger", "attack_type", "created_at"]
        ctk.CTkLabel(main_frame, text="Field:").pack(anchor="w", pady=(0, 5))
        self.field_var = ctk.StringVar(value="name")
        self.field_combo = ctk.CTkComboBox(main_frame, values=fields, variable=self.field_var)
        self.field_combo.pack(fill="x", pady=(0, 10))

        operators = ["=", "!=", ">", "<", ">=", "<=", "LIKE"]
        ctk.CTkLabel(main_frame, text="Operator:").pack(anchor="w", pady=(0, 5))
        self.operator_var = ctk.StringVar(value="=")
        self.operator_combo = ctk.CTkComboBox(main_frame, values=operators, variable=self.operator_var)
        self.operator_combo.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(main_frame, text="Value:").pack(anchor="w", pady=(0, 5))
        self.value_entry = ctk.CTkEntry(main_frame)
        self.value_entry.pack(fill="x", pady=(0, 15))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(button_frame, text="OK", command=self.on_ok).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)

    def on_ok(self):
        """Обработка нажатия OK"""
        if self.field_var.get() and self.operator_var.get() and self.value_entry.get():
            self.result = {
                'field': self.field_var.get(),
                'operator': self.operator_var.get(),
                'value': self.value_entry.get()
            }
            self.destroy()