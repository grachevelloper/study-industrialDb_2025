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
        main_frame = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔍 Advanced Search Builder",
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

        # Основное условие
        main_card = ctk.CTkFrame(filters_frame, fg_color="#2a2a4a", corner_radius=10)
        main_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(main_card, text="🎯 Main Search Condition", 
                    font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", padx=15, pady=(10, 5))

        # Основное условие - горизонтальное расположение
        main_condition_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        main_condition_frame.pack(fill="x", padx=15, pady=10)

        # Поля для основного условия с подписями
        fields = ["name", "frequency", "danger", "attack_type", "created_at"]
        
        # Строка 1: Поле и оператор
        row1_frame = ctk.CTkFrame(main_condition_frame, fg_color="transparent")
        row1_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row1_frame, text="Search in:", width=80).pack(side="left", padx=2)
        self.main_field = ctk.CTkComboBox(row1_frame, values=fields, width=150)
        self.main_field.pack(side="left", padx=2)
        self.main_field.set("name")

        ctk.CTkLabel(row1_frame, text="Condition:", width=80).pack(side="left", padx=2)
        operators = ["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN"]
        self.main_operator = ctk.CTkComboBox(row1_frame, values=operators, width=100)
        self.main_operator.pack(side="left", padx=2)
        self.main_operator.set("=")

        # Строка 2: Значение
        row2_frame = ctk.CTkFrame(main_condition_frame, fg_color="transparent")
        row2_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row2_frame, text="Search for:", width=80).pack(side="left", padx=2)
        self.main_value = ctk.CTkEntry(row2_frame, placeholder_text="Enter value to search...", width=250)
        self.main_value.pack(side="left", padx=2)

        # Подзапросы
        subquery_card = ctk.CTkFrame(filters_frame, fg_color="#2a2a4a", corner_radius=10)
        subquery_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(subquery_card, text="🔗 Additional Conditions (Subqueries)", 
                    font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", padx=15, pady=(10, 5))

        # Операторы подзапросов
        operator_frame = ctk.CTkFrame(subquery_card, fg_color="transparent")
        operator_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(operator_frame, text="Combine with:", width=100).pack(side="left", padx=2)
        self.subquery_operator = ctk.CTkComboBox(operator_frame, 
                                               values=["ANY", "ALL", "EXISTS"], 
                                               width=120)
        self.subquery_operator.pack(side="left", padx=2)
        self.subquery_operator.set("ANY")
        
        ctk.CTkLabel(operator_frame, text="(how to combine multiple conditions)").pack(side="left", padx=10)

        # Список подзапросов
        subquery_list_frame = ctk.CTkFrame(subquery_card, fg_color="transparent")
        subquery_list_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Заголовок списка
        list_header = ctk.CTkFrame(subquery_list_frame, fg_color="transparent")
        list_header.pack(fill="x")
        ctk.CTkLabel(list_header, text="Current Additional Conditions:", 
                    font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        # Кнопки управления подзапросами
        buttons_frame = ctk.CTkFrame(list_header, fg_color="transparent")
        buttons_frame.pack(side="right")
        
        ctk.CTkButton(buttons_frame, text="➕ Add Condition", 
                     command=self.add_subquery, 
                     width=120, height=30).pack(side="left", padx=2)
        ctk.CTkButton(buttons_frame, text="🗑️ Remove Last", 
                     command=self.remove_subquery, 
                     width=120, height=30,
                     fg_color="#d63031").pack(side="left", padx=2)

        # Список условий
        self.subqueries_listbox = ctk.CTkTextbox(subquery_list_frame, height=80, border_width=1)
        self.subqueries_listbox.pack(fill="x", pady=5)
        self.subqueries_listbox.insert("1.0", "No additional conditions added")
        self.subqueries_listbox.configure(state="disabled")

        # Кнопка очистки
        ctk.CTkButton(subquery_list_frame, text="🧹 Clear All Conditions", 
                     command=self.clear_subqueries,
                     fg_color="#e17055", width=150).pack(anchor="e", pady=5)

    def create_controls_section(self, parent):
        """Создание секции управления"""
        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(fill="x", pady=15)

        # Основные кнопки действий
        action_buttons = ctk.CTkFrame(controls_frame, fg_color="transparent")
        action_buttons.pack(fill="x")

        ctk.CTkButton(action_buttons, text="🚀 Search Now", 
                     command=self.apply_filters,
                     fg_color=self.app.colors["success"],
                     height=40,
                     font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

        ctk.CTkButton(action_buttons, text="📋 Show SQL", 
                     command=self.show_sql,
                     fg_color=self.app.colors["primary"],
                     height=40).pack(side="left", padx=5)

        ctk.CTkButton(action_buttons, text="🔄 Reset All", 
                     command=self.reset_filters,
                     fg_color=self.app.colors["warning"],
                     height=40).pack(side="left", padx=5)

        # Подсказка
        help_label = ctk.CTkLabel(controls_frame, 
                                 text="💡 Tip: Start with main condition, add subqueries for complex searches",
                                 text_color="gray", font=ctk.CTkFont(size=12))
        help_label.pack(pady=10)

    def create_results_section(self, parent):
        """Создание секции результатов"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="both", expand=True, pady=10)

        # Заголовок с счетчиком результатов
        results_header = ctk.CTkFrame(results_frame, fg_color="transparent")
        results_header.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(results_header, text="📊 Search Results", 
                    font=ctk.CTkFont(weight="bold", size=16)).pack(side="left")
        
        self.results_count = ctk.CTkLabel(results_header, text="No results yet",
                                         text_color="gray")
        self.results_count.pack(side="right")

        self.results_text = ctk.CTkTextbox(results_frame, wrap="none", font=ctk.CTkFont(family="Consolas"))
        self.results_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def add_subquery(self):
        """Добавление нового подзапроса"""
        dialog = SubqueryDialog(self.parent, self.app)
        self.app.window.wait_window(dialog)
        
        if dialog.result:
            self.subqueries.append(dialog.result)
            self.update_subqueries_list()

    def remove_subquery(self):
        """Удаление выбранного подзапроса"""
        if self.subqueries:
            self.subqueries.pop()
            self.update_subqueries_list()
        else:
            messagebox.showinfo("Info", "No conditions to remove")

    def clear_subqueries(self):
        """Очистка всех подзапросов"""
        if self.subqueries:
            self.subqueries = []
            self.update_subqueries_list()
            messagebox.showinfo("Cleared", "All additional conditions removed")

    def update_subqueries_list(self):
        """Обновление списка подзапросов"""
        self.subqueries_listbox.configure(state="normal")
        self.subqueries_listbox.delete("1.0", "end")
        
        if not self.subqueries:
            self.subqueries_listbox.insert("1.0", "No additional conditions added")
            self.subqueries_listbox.configure(state="disabled")
            return

        for i, sq in enumerate(self.subqueries, 1):
            self.subqueries_listbox.insert("end", 
                f"Condition {i}: WHERE {sq['field']} {sq['operator']} '{sq['value']}'\n")
        
        self.subqueries_listbox.configure(state="disabled")

    def apply_filters(self):
        """Применение фильтров"""
        try:
            # Проверка основного условия
            if not self.main_value.get().strip():
                messagebox.showwarning("Warning", "Please enter a search value in the main condition")
                return

            # Собираем условия
            conditions = []
            params = []

            # Основное условие
            if self.main_field.get() and self.main_operator.get() and self.main_value.get():
                field = self.main_field.get()
                operator = self.main_operator.get()
                value = self.main_value.get()
                
                conditions.append(f"{field} {operator} ?")
                params.append(value)

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
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def reset_filters(self):
        """Сброс фильтров"""
        self.main_field.set("name")
        self.main_operator.set("=")
        self.main_value.delete(0, "end")
        self.subqueries = []
        self.update_subqueries_list()
        self.subquery_operator.set("ANY")
        self.results_text.delete("1.0", "end")
        self.results_count.configure(text="No results yet")
        messagebox.showinfo("Reset", "All filters have been reset")

    def show_sql(self):
        """Показать SQL запрос"""
        if not self.main_value.get().strip():
            messagebox.showwarning("Warning", "Please enter a search value first")
            return

        conditions = []
        
        # Основное условие
        if self.main_field.get() and self.main_operator.get() and self.main_value.get():
            field = self.main_field.get()
            operator = self.main_operator.get()
            value = self.main_value.get()
            conditions.append(f"{field} {operator} '{value}'")

        # Подзапросы
        for subquery in self.subqueries:
            operator = self.subquery_operator.get()
            if operator == "EXISTS":
                conditions.append(f"EXISTS (SELECT 1 FROM attacks WHERE {subquery['field']} {subquery['operator']} '{subquery['value']}')")
            else:
                conditions.append(f"{subquery['field']} {operator} (SELECT {subquery['field']} FROM attacks WHERE {subquery['field']} {subquery['operator']} '{subquery['value']}')")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM attacks WHERE {where_clause}"

        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"📋 Generated SQL Query:\n\n{sql}\n\n💡 Copy this query to use in other tools")

    def show_results(self, results, query):
        """Показать результаты запроса"""
        self.results_text.delete("1.0", "end")
        
        # Обновляем счетчик
        self.results_count.configure(text=f"Found: {len(results)} records")
        
        # Показываем запрос и результаты
        self.results_text.insert("1.0", f"🔍 Search Query:\n{query}\n\n")
        self.results_text.insert("end", f"📊 Found {len(results)} records:\n\n")
        
        if results:
            for i, result in enumerate(results, 1):
                self.results_text.insert("end", f"#{i}:\n")
                for key, value in result.items():
                    self.results_text.insert("end", f"  {key}: {value}\n")
                self.results_text.insert("end", "\n")
        else:
            self.results_text.insert("end", "❌ No records found matching your criteria")

class SubqueryDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.result = None
        self.title("➕ Add Search Condition")
        self.geometry("400x300")
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Add Additional Search Condition", 
                    font=ctk.CTkFont(weight="bold", size=16)).pack(pady=(0, 20))

        # Поля формы
        fields = ["name", "frequency", "danger", "attack_type", "created_at"]
        
        ctk.CTkLabel(main_frame, text="Search Field:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        self.field_combo = ctk.CTkComboBox(main_frame, values=fields)
        self.field_combo.pack(fill="x", pady=(0, 15))
        self.field_combo.set("name")

        operators = ["=", "!=", ">", "<", ">=", "<=", "LIKE"]
        ctk.CTkLabel(main_frame, text="Condition Type:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        self.operator_combo = ctk.CTkComboBox(main_frame, values=operators)
        self.operator_combo.pack(fill="x", pady=(0, 15))
        self.operator_combo.set("=")

        ctk.CTkLabel(main_frame, text="Value to Match:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        self.value_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter value...")
        self.value_entry.pack(fill="x", pady=(0, 20))

        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(button_frame, text="✅ Add Condition", 
                     command=self.on_ok,
                     fg_color=self.app.colors["success"]).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="❌ Cancel", 
                     command=self.destroy).pack(side="right", padx=5)

    def on_ok(self):
        """Обработка нажатия OK"""
        if not self.value_entry.get().strip():
            messagebox.showwarning("Warning", "Please enter a value")
            return
            
        self.result = {
            'field': self.field_combo.get(),
            'operator': self.operator_combo.get(),
            'value': self.value_entry.get()
        }
        self.destroy()