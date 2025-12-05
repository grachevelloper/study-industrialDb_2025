# ui/cte_builder.py
import customtkinter as ctk
from tkinter import messagebox
import re

class CTEBuilder:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        
        # Используем CTE из приложения, чтобы они сохранялись между вкладками
        if not hasattr(app, 'cte_definitions'):
            app.cte_definitions = []
        
        self.available_tables = []
        self.table_columns_cache = {}
        
        self.setup_ui()
        self.load_available_tables()
        self.update_saved_cte_list()
        
    def setup_ui(self):
        """Настройка простого интерфейса конструктора CTE"""
        # Основной фрейм
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Левая часть - создание CTE
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Правая часть - список сохраненных CTE
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=False, padx=(5, 0), ipadx=10)
        
        # === ЛЕВАЯ ЧАСТЬ: Создание CTE ===
        
        # Заголовок
        title_label = ctk.CTkLabel(
            left_frame,
            text="Create New CTE",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Фрейм с основной информацией
        info_frame = ctk.CTkFrame(left_frame)
        info_frame.pack(fill="x", pady=(0, 10))
        
        # Имя CTE
        ctk.CTkLabel(info_frame, text="CTE Name:").pack(side="left", padx=(10, 5))
        self.cte_name_entry = ctk.CTkEntry(info_frame, width=200, placeholder_text="user_stats")
        self.cte_name_entry.pack(side="left", padx=(0, 20))
        
        # Быстрые вставки
        quick_frame = ctk.CTkFrame(left_frame)
        quick_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(quick_frame, text="Quick Insert:").pack(side="left", padx=(10, 5))
        
        quick_buttons = [
            ("SELECT FROM", self.insert_select_template),
            ("JOIN", self.insert_join_template),
            ("WHERE", self.insert_where_template),
            ("GROUP BY", self.insert_group_by_template),
        ]
        
        for text, cmd in quick_buttons:
            btn = ctk.CTkButton(quick_frame, text=text, command=cmd, width=90)
            btn.pack(side="left", padx=2)
        
        # Поле для SQL запроса
        query_frame = ctk.CTkFrame(left_frame)
        query_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Панель доступных таблиц
        tables_frame = ctk.CTkFrame(query_frame, fg_color="transparent")
        tables_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        ctk.CTkLabel(tables_frame, text="Tables:").pack(side="left")
        
        self.tables_var = ctk.StringVar(value="")
        self.tables_dropdown = ctk.CTkOptionMenu(
            tables_frame,
            values=[""] + self.available_tables,
            variable=self.tables_var,
            width=150,
            command=self.on_table_selected
        )
        self.tables_dropdown.pack(side="left", padx=5)
        
        # Поле ввода SQL
        self.query_text = ctk.CTkTextbox(query_frame, wrap="word")
        self.query_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Подсказка по умолчанию
        self.query_text.insert("1.0", """-- Write your CTE query here
-- Use quick insert buttons above

SELECT 
    user_id,
    COUNT(*) as attack_count,
    AVG(damage) as avg_damage
FROM attacks
WHERE 1=1""")
        
        # Кнопки управления
        button_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        ctk.CTkButton(button_frame, text="Save CTE", command=self.save_cte,
                     fg_color="green", width=100).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form,
                     width=100).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, text="Test Query", command=self.test_query,
                     width=100).pack(side="left", padx=2)
        
        # === ПРАВАЯ ЧАСТЬ: Список CTE ===
        
        ctk.CTkLabel(
            right_frame,
            text="Saved CTEs",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(0, 10))
        
        # Фрейм для кнопок управления CTE
        cte_buttons_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        cte_buttons_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkButton(cte_buttons_frame, text="Refresh", command=self.update_saved_cte_list,
                     width=80).pack(side="left", padx=2)
        ctk.CTkButton(cte_buttons_frame, text="Use", command=self.use_selected_cte,
                     fg_color="blue", width=80).pack(side="left", padx=2)
        
        # Список CTE с прокруткой
        self.cte_list_frame = ctk.CTkScrollableFrame(right_frame, height=300)
        self.cte_list_frame.pack(fill="both", expand=True)
        
        # Переменная для выбранного CTE
        self.selected_cte_var = ctk.StringVar(value="")
        
        # Кнопка для генерации полного запроса
        ctk.CTkButton(left_frame, text="Generate Full Query", 
                     command=self.generate_full_query,
                     height=30).pack(pady=(10, 0))
        
        # Поле для результата
        self.result_text = ctk.CTkTextbox(left_frame, height=100)
        self.result_text.pack(fill="x", pady=(5, 0))
        self.result_text.insert("1.0", "Full SQL will appear here...")
        self.result_text.configure(state="disabled")
    
    def load_available_tables(self):
        """Загрузка списка доступных таблиц"""
        try:
            query = """
            SELECT name 
            FROM sqlite_master 
            WHERE type = 'table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
            results = self.app.api_client.execute_custom_query(query)
            self.available_tables = [row[0] for row in results] if results else []
            
            # Обновляем dropdown
            if hasattr(self, 'tables_dropdown'):
                self.tables_dropdown.configure(values=[""] + self.available_tables)
                
        except Exception as e:
            self.available_tables = ["attacks", "users", "logs", "items", "monsters"]
            print(f"Could not load tables: {e}")
    
    def on_table_selected(self, table_name):
        """Обработка выбора таблицы"""
        if not table_name:
            return
            
        # Вставляем базовый SELECT для выбранной таблицы
        base_query = f"SELECT *\nFROM {table_name}\nWHERE 1=1"
        self.query_text.delete("1.0", "end")
        self.query_text.insert("1.0", base_query)
    
    def insert_select_template(self):
        """Вставка шаблона SELECT"""
        template = """SELECT 
    column1,
    column2,
    column3
FROM table_name
WHERE 1=1"""
        self.insert_at_cursor(template)
    
    def insert_join_template(self):
        """Вставка шаблона JOIN"""
        template = """INNER JOIN other_table ON main_table.id = other_table.main_id
LEFT JOIN third_table ON main_table.id = third_table.main_id"""
        self.insert_at_cursor(template)
    
    def insert_where_template(self):
        """Вставка шаблона WHERE"""
        template = """WHERE 
    column1 = 'value'
    AND column2 > 100
    AND column3 IN ('option1', 'option2')
    AND column4 LIKE '%search%'"""
        self.insert_at_cursor(template)
    
    def insert_group_by_template(self):
        """Вставка шаблона GROUP BY"""
        template = """GROUP BY column1, column2
HAVING COUNT(*) > 1
ORDER BY column1"""
        self.insert_at_cursor(template)
    
    def insert_at_cursor(self, text):
        """Вставка текста в позицию курсора"""
        self.query_text.insert(ctk.INSERT, text)
    
    def save_cte(self):
        """Сохранение CTE"""
        cte_name = self.cte_name_entry.get().strip()
        query = self.query_text.get("1.0", "end").strip()
        
        if not cte_name:
            messagebox.showwarning("Warning", "Please enter CTE name")
            return
            
        if not query:
            messagebox.showwarning("Warning", "Please enter CTE query")
            return
        
        # Простая валидация имени
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', cte_name):
            messagebox.showwarning("Warning", 
                                 "CTE name must start with letter or underscore")
            return
        
        # Проверяем дубликаты
        for i, cte in enumerate(self.app.cte_definitions):
            if cte['name'] == cte_name:
                if not messagebox.askyesno("Confirm", 
                                          f"CTE '{cte_name}' already exists. Overwrite?"):
                    return
                # Удаляем старый
                self.app.cte_definitions.pop(i)
                break
        
        # Сохраняем CTE в приложении
        cte_data = {
            'name': cte_name,
            'query': query,
            'columns': self.detect_columns(query)
        }
        
        self.app.cte_definitions.append(cte_data)
        
        # Обновляем список сохраненных CTE
        self.update_saved_cte_list()
        
        messagebox.showinfo("Success", f"CTE '{cte_name}' saved")
        self.clear_form()
    
    def detect_columns(self, query):
        """Простое детектирование столбцов из запроса"""
        columns = []
        
        # Пытаемся найти SELECT ... FROM
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            
            # Если SELECT *
            if '*' in select_clause:
                return ["*"]
            
            # Разбиваем на части
            parts = [p.strip() for p in re.split(r',\s*(?![^()]*\))', select_clause)]
            
            for part in parts:
                # Ищем AS alias
                as_match = re.search(r'AS\s+["\']?(\w+)["\']?$', part, re.IGNORECASE)
                if as_match:
                    columns.append(as_match.group(1))
                else:
                    # Берем последнее слово
                    words = re.findall(r'\b(\w+)\b', part)
                    if words:
                        columns.append(words[-1])
        
        return columns if columns else ["*"]
    
    def update_saved_cte_list(self):
        """Обновление списка сохраненных CTE"""
        # Очищаем фрейм
        for widget in self.cte_list_frame.winfo_children():
            widget.destroy()
        
        if not self.app.cte_definitions:
            label = ctk.CTkLabel(self.cte_list_frame, text="No CTEs saved yet")
            label.pack(pady=10)
            return
        
        # Создаем радиокнопки для каждого CTE
        for cte in self.app.cte_definitions:
            frame = ctk.CTkFrame(self.cte_list_frame, corner_radius=5)
            frame.pack(fill="x", pady=2, padx=2)
            
            # Радиокнопка для выбора
            rb = ctk.CTkRadioButton(
                frame,
                text=cte['name'],
                variable=self.selected_cte_var,
                value=cte['name'],
                width=150,
                command=lambda c=cte: self.on_cte_selected(c)
            )
            rb.pack(side="left", padx=(5, 10))
            
            # Кнопка удаления
            delete_btn = ctk.CTkButton(
                frame,
                text="✕",
                width=30,
                height=20,
                fg_color="red",
                command=lambda c=cte['name']: self.delete_cte(c)
            )
            delete_btn.pack(side="right", padx=5)
    
    def on_cte_selected(self, cte):
        """Обработка выбора CTE"""
        self.selected_cte_var.set(cte['name'])
        # Можно добавить дополнительную логику, например, показ деталей CTE
    
    def use_selected_cte(self):
        """Использование выбранного CTE в запросе"""
        cte_name = self.selected_cte_var.get()
        if not cte_name:
            messagebox.showwarning("Warning", "Please select a CTE")
            return
        
        # Находим CTE
        cte = None
        for c in self.app.cte_definitions:
            if c['name'] == cte_name:
                cte = c
                break
        
        if not cte:
            messagebox.showwarning("Warning", f"CTE '{cte_name}' not found")
            return
        
        # Вставляем использование CTE в запрос
        template = f"SELECT *\nFROM {cte_name}\nWHERE 1=1"
        self.query_text.delete("1.0", "end")
        self.query_text.insert("1.0", template)
        
        # Переключаемся на поле ввода
        self.query_text.focus_set()
        
        messagebox.showinfo("Info", f"Using CTE '{cte_name}'")
    
    def delete_cte(self, cte_name):
        """Удаление CTE"""
        if not messagebox.askyesno("Confirm Delete", f"Delete CTE '{cte_name}'?"):
            return
        
        # Удаляем из списка
        self.app.cte_definitions = [
            cte for cte in self.app.cte_definitions 
            if cte['name'] != cte_name
        ]
        
        # Обновляем список
        self.update_saved_cte_list()
        
        # Сбрасываем выбор
        self.selected_cte_var.set("")
        
        messagebox.showinfo("Success", f"CTE '{cte_name}' deleted")
    
    def test_query(self):
        """Тестирование запроса"""
        query = self.query_text.get("1.0", "end").strip()
        if not query:
            messagebox.showwarning("Warning", "No query to test")
            return
        
        # Добавляем LIMIT для теста
        if "LIMIT" not in query.upper():
            test_query = query + "\nLIMIT 10"
        else:
            test_query = query
        
        try:
            # Выполняем запрос
            results = self.app.api_client.execute_custom_query(test_query)
            
            if results:
                msg = f"Query executed successfully!\nReturned {len(results)} rows"
                if len(results) > 0:
                    # Показываем первую строку
                    msg += f"\nFirst row: {results[0]}"
                messagebox.showinfo("Test Results", msg)
            else:
                messagebox.showinfo("Test Results", "Query executed successfully (no rows returned)")
                
        except Exception as e:
            messagebox.showerror("Query Error", f"Failed to execute query:\n{str(e)}")
    
    def clear_form(self):
        """Очистка формы"""
        self.cte_name_entry.delete(0, "end")
        self.query_text.delete("1.0", "end")
        
        # Вставляем подсказку
        self.query_text.insert("1.0", """-- Write your CTE query here
-- Use quick insert buttons or type SQL directly""")
    
    def generate_full_query(self):
        """Генерация полного SQL запроса"""
        if not self.app.cte_definitions:
            messagebox.showwarning("Warning", "No CTEs saved yet")
            return
        
        # Получаем основной запрос из текстового поля
        main_query = self.query_text.get("1.0", "end").strip()
        
        # Если поле пустое, используем запрос из последнего CTE
        if not main_query and self.app.cte_definitions:
            last_cte = self.app.cte_definitions[-1]
            main_query = f"SELECT * FROM {last_cte['name']}"
        elif not main_query:
            main_query = "SELECT 'No main query defined' as message"
        
        # Генерируем полный запрос
        full_sql = "WITH\n"
        
        for i, cte in enumerate(self.app.cte_definitions):
            cte_def = f"  {cte['name']} AS (\n"
            cte_def += f"    {cte['query']}\n"
            cte_def += "  )"
            
            if i < len(self.app.cte_definitions) - 1:
                cte_def += ","
            
            full_sql += cte_def + "\n"
        
        full_sql += f"\n{main_query};"
        
        # Показываем результат
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", full_sql)
        self.result_text.configure(state="disabled")
        
        messagebox.showinfo("Success", f"Generated query with {len(self.app.cte_definitions)} CTEs")