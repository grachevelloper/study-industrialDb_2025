import customtkinter as ctk
from tkinter import messagebox, ttk
import re

class RegexSearchTool:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса поиска по регулярным выражениям"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔍 Advanced Text Search with SIMILAR TO",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Основные настройки поиска
        self.create_search_settings(main_frame)
        
        # Параметры регулярных выражений
        self.create_regex_patterns(main_frame)
        
        # Кнопки выполнения
        self.create_action_buttons(main_frame)
        
        # Результаты
        self.create_results_section(main_frame)

    def create_search_settings(self, parent):
        """Настройки таблицы и столбца"""
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(settings_frame, text="Search Settings", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        # Выбор таблицы
        table_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        table_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(table_frame, text="Table:").pack(side="left")
        self.table_combo = ctk.CTkComboBox(table_frame, 
                                         values=self.get_available_tables(),
                                         width=200,
                                         command=self.on_table_selected)
        self.table_combo.pack(side="left", padx=(10, 20))
        self.table_combo.set("attacks")

        # Выбор столбца
        ctk.CTkLabel(table_frame, text="Column:").pack(side="left")
        self.column_combo = ctk.CTkComboBox(table_frame, values=[], width=200)
        self.column_combo.pack(side="left", padx=(10, 0))

        # Загружаем столбцы для выбранной таблицы
        self.on_table_selected("attacks")

    def create_regex_patterns(self, parent):
        """Паттерны регулярных выражений"""
        patterns_frame = ctk.CTkFrame(parent)
        patterns_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(patterns_frame, text="Regex Patterns", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        # Основной паттерн
        pattern_main_frame = ctk.CTkFrame(patterns_frame, fg_color="transparent")
        pattern_main_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(pattern_main_frame, text="Pattern:").pack(side="left")
        self.pattern_entry = ctk.CTkEntry(pattern_main_frame, 
                                        placeholder_text="Enter SIMILAR TO pattern...",
                                        width=300)
        self.pattern_entry.pack(side="left", padx=(10, 20), fill="x", expand=True)

        # Отрицание
        self.negation_var = ctk.BooleanVar()
        ctk.CTkCheckBox(pattern_main_frame, text="NOT SIMILAR TO", 
                       variable=self.negation_var).pack(side="left")

        # Предопределенные паттерны
        self.create_predefined_patterns(patterns_frame)

    def create_predefined_patterns(self, parent):
        """Предопределенные регулярные выражения"""
        predefined_frame = ctk.CTkFrame(parent, fg_color="transparent")
        predefined_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(predefined_frame, text="Quick Patterns:").pack(anchor="w")
        
        patterns_subframe = ctk.CTkFrame(predefined_frame, fg_color="transparent")
        patterns_subframe.pack(fill="x", pady=5)

        patterns = [
            ("Starts with letter", "[A-Za-z]%"),
            ("Ends with digit", "%[0-9]"),
            ("Contains numbers", "%[0-9]%"),
            ("Exactly 5 characters", "_____"),
            ("IP address pattern", "[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}"),
            ("Email pattern", "%@%.%"),
            ("Only letters", "[A-Za-z]*"),
            ("Mixed letters and numbers", "%[A-Za-z]%[0-9]%")
        ]

        for i, (desc, pattern) in enumerate(patterns):
            btn = ctk.CTkButton(
                patterns_subframe,
                text=desc,
                width=140,
                height=25,
                command=lambda p=pattern: self.set_pattern(p)
            )
            btn.pack(side="left", padx=2, pady=2)

    def create_action_buttons(self, parent):
        """Кнопки выполнения"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=15)

        ctk.CTkButton(
            button_frame,
            text="🔍 Execute Search",
            command=self.execute_search,
            fg_color=self.app.colors["primary"],
            width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="🔄 Test Pattern",
            command=self.test_pattern,
            fg_color=self.app.colors["warning"],
            width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="🗑️ Clear Results",
            command=self.clear_results,
            fg_color=self.app.colors["danger"],
            width=120
        ).pack(side="left", padx=5)

    def create_results_section(self, parent):
        """Секция результатов"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(results_frame, text="Search Results", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        # Таблица результатов
        self.results_tree = ttk.Treeview(results_frame, height=15)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        h_scroll = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.results_tree.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        v_scroll.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))
        h_scroll.pack(side="bottom", fill="x", padx=(15, 15), pady=(0, 0))

        # Статус
        self.status_label = ctk.CTkLabel(results_frame, text="No search executed yet")
        self.status_label.pack(pady=5)

    def get_available_tables(self):
        """Получение списка таблиц"""
        try:
            return self.app.api_client.get_all_tables()
        except:
            return ["attacks", "targets"]

    def on_table_selected(self, choice):
        """Обработка выбора таблицы"""
        try:
            schema = self.app.api_client.get_table_schema(choice)
            columns = [col['name'] for col in schema]
            self.column_combo.configure(values=columns)
            if columns:
                self.column_combo.set(columns[0])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load columns: {e}")

    def set_pattern(self, pattern):
        """Установка предопределенного паттерна"""
        self.pattern_entry.delete(0, "end")
        self.pattern_entry.insert(0, pattern)

    def test_pattern(self):
        """Тестирование паттерна"""
        pattern = self.pattern_entry.get().strip()
        if not pattern:
            messagebox.showwarning("Warning", "Please enter a pattern to test")
            return

        test_dialog = PatternTestDialog(self.parent, pattern)
        if test_dialog.result:
            messagebox.showinfo("Pattern Test", f"Test string: '{test_dialog.result}'\nPattern would match: {test_dialog.matched}")

    def execute_search(self):
        """Выполнение поиска"""
        table = self.table_combo.get()
        column = self.column_combo.get()
        pattern = self.pattern_entry.get().strip()
        negation = self.negation_var.get()

        if not pattern:
            messagebox.showerror("Error", "Please enter a search pattern")
            return

        try:
            # Формируем SQL запрос
            if negation:
                sql = f"SELECT * FROM {table} WHERE {column} NOT SIMILAR TO ?"
            else:
                sql = f"SELECT * FROM {table} WHERE {column} SIMILAR TO ?"

            results = self.app.api_client.execute_custom_query(sql, (pattern,))
            
            self.display_results(results)
            self.status_label.configure(text=f"Found {len(results)} records")
            
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")

    def display_results(self, results):
        """Отображение результатов"""
        # Очищаем таблицу
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        if not results:
            return

        # Устанавливаем колонки
        columns = list(results[0].keys())
        self.results_tree["columns"] = columns
        self.results_tree["show"] = "headings"

        # Настраиваем заголовки
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)

        # Заполняем данные
        for row in results:
            values = [str(row[col]) for col in columns]
            self.results_tree.insert("", "end", values=values)

    def clear_results(self):
        """Очистка результатов"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.status_label.configure(text="Results cleared")

class PatternTestDialog(ctk.CTkToplevel):
    """Диалог для тестирования паттернов"""
    def __init__(self, parent, pattern):
        super().__init__(parent)
        self.pattern = pattern
        self.result = None
        self.matched = False
        
        self.title("Test Pattern")
        self.geometry("400x200")
        self.resizable(False, False)
        
        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Enter test string:").pack(anchor="w", pady=(0, 5))
        self.test_entry = ctk.CTkEntry(main_frame, width=300)
        self.test_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(main_frame, text=f"Pattern: {self.pattern}").pack(anchor="w", pady=(0, 10))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(button_frame, text="Test", command=self.on_test).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def on_test(self):
        test_string = self.test_entry.get().strip()
        if test_string:
            self.result = test_string
            # Эмуляция SIMILAR TO для демонстрации
            try:
                # Простая эмуляция - в реальности нужно использовать SQL
                pattern = self.pattern.replace('%', '.*').replace('_', '.')
                self.matched = bool(re.match(pattern, test_string))
            except:
                self.matched = False
            self.destroy()