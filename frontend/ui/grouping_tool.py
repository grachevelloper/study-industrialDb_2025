# ui/grouping_tool.py
import customtkinter as ctk
from tkinter import messagebox
from typing import List, Dict, Optional

class GroupingTool:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.selected_columns = []
        self.grouping_options = []
        self.aggregations = []
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса расширенной группировки"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Advanced Grouping Tool",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Основной фрейм с настройками группировки
        self.create_grouping_section(main_frame)

        # Секция агрегаций
        self.create_aggregation_section(main_frame)

        # Секция настроек группировки
        self.create_grouping_options_section(main_frame)

        # Кнопки управления
        self.create_controls_section(main_frame)

        # Область результатов
        self.create_results_section(main_frame)

    def create_grouping_section(self, parent):
        """Создание секции выбора столбцов для группировки"""
        grouping_frame = ctk.CTkFrame(parent)
        grouping_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(grouping_frame, text="Grouping Columns", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # Фрейм с выбором столбцов
        columns_frame = ctk.CTkFrame(grouping_frame, fg_color="transparent")
        columns_frame.pack(fill="x", padx=15, pady=5)

        # Получаем список столбцов из БД
        self.table_columns = self.get_table_columns()
        
        # Выбор столбцов для группировки
        ctk.CTkLabel(columns_frame, text="Available Columns:").pack(anchor="w")
        
        columns_select_frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
        columns_select_frame.pack(fill="x", pady=5)
        
        # Используем CTkScrollableFrame для выбора столбцов вместо CTkTextbox
        self.available_columns_frame = ctk.CTkScrollableFrame(columns_select_frame, height=100, width=200)
        self.available_columns_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Создаем чекбоксы для каждого столбца
        self.column_checkboxes = {}
        for column in self.table_columns:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(self.available_columns_frame, text=column, variable=var,
                               command=lambda col=column, v=var: self.on_column_checkbox_change(col, v))
            cb.pack(anchor="w", pady=2)
            self.column_checkboxes[column] = var
        
        # Кнопки для выбора столбцов
        select_buttons_frame = ctk.CTkFrame(columns_select_frame, fg_color="transparent", width=100)
        select_buttons_frame.pack(side="right", fill="y")
        
        ctk.CTkButton(select_buttons_frame, text="Add Selected", 
                     command=self.add_selected_columns, width=100).pack(pady=2)
        ctk.CTkButton(select_buttons_frame, text="Clear All", 
                     command=self.clear_selected_columns, width=100).pack(pady=2)
        
        # Выбранные столбцы для группировки
        ctk.CTkLabel(columns_frame, text="Selected Grouping Columns:").pack(anchor="w", pady=(10, 5))
        
        self.selected_columns_frame = ctk.CTkScrollableFrame(columns_frame, height=100)
        self.selected_columns_frame.pack(fill="x", pady=5)

    def create_aggregation_section(self, parent):
        """Создание секции выбора агрегатных функций"""
        aggregation_frame = ctk.CTkFrame(parent)
        aggregation_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(aggregation_frame, text="Aggregation Functions", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # Фрейм для добавления агрегаций
        agg_form_frame = ctk.CTkFrame(aggregation_frame, fg_color="transparent")
        agg_form_frame.pack(fill="x", padx=15, pady=5)

        # Выбор столбца
        ctk.CTkLabel(agg_form_frame, text="Column:").grid(row=0, column=0, sticky="w", padx=2)
        self.agg_column_combo = ctk.CTkComboBox(agg_form_frame, values=self.table_columns, width=150)
        self.agg_column_combo.grid(row=0, column=1, padx=2, pady=5)
        
        # Выбор функции
        ctk.CTkLabel(agg_form_frame, text="Function:").grid(row=0, column=2, sticky="w", padx=10)
        agg_functions = ["COUNT", "SUM", "AVG", "MIN", "MAX", "STDDEV", "VARIANCE"]
        self.agg_function_combo = ctk.CTkComboBox(agg_form_frame, values=agg_functions, width=120)
        self.agg_function_combo.grid(row=0, column=3, padx=2, pady=5)
        self.agg_function_combo.set("COUNT")
        
        # Кнопка добавления
        ctk.CTkButton(agg_form_frame, text="Add Aggregation", 
                     command=self.add_aggregation, width=120).grid(row=0, column=4, padx=10)

        # Список выбранных агрегаций
        ctk.CTkLabel(aggregation_frame, text="Selected Aggregations:").pack(anchor="w", padx=15, pady=(10, 5))
        
        self.aggregations_frame = ctk.CTkScrollableFrame(aggregation_frame, height=80)
        self.aggregations_frame.pack(fill="x", padx=15, pady=(0, 5))

        # Кнопки управления агрегациями
        agg_buttons_frame = ctk.CTkFrame(aggregation_frame, fg_color="transparent")
        agg_buttons_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkButton(agg_buttons_frame, text="Clear All Aggregations", 
                     command=self.clear_aggregations).pack(side="left", padx=2)

    def create_grouping_options_section(self, parent):
        """Создание секции выбора типа группировки"""
        options_frame = ctk.CTkFrame(parent)
        options_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(options_frame, text="Grouping Type", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # Радиокнопки для выбора типа группировки
        grouping_type_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        grouping_type_frame.pack(fill="x", padx=15, pady=5)
        
        self.grouping_type_var = ctk.StringVar(value="GROUP BY")
        
        grouping_types = [
            ("Standard GROUP BY", "GROUP BY"),
            ("ROLLUP (Hierarchical)", "ROLLUP"),
            ("CUBE (All Combinations)", "CUBE"),
            ("GROUPING SETS (Custom)", "GROUPING SETS")
        ]
        
        for text, value in grouping_types:
            rb = ctk.CTkRadioButton(grouping_type_frame, text=text, 
                                   variable=self.grouping_type_var, value=value,
                                   command=self.on_grouping_type_changed)
            rb.pack(anchor="w", pady=2)

        # Дополнительные опции для GROUPING SETS
        self.groupsets_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        
        ctk.CTkLabel(self.groupsets_frame, text="Define GROUPING SETS:").pack(anchor="w", pady=5)
        
        groupsets_input_frame = ctk.CTkFrame(self.groupsets_frame, fg_color="transparent")
        groupsets_input_frame.pack(fill="x", pady=5)
        
        # Создаем фрейм с меткой вместо placeholder_text
        groupsets_container = ctk.CTkFrame(groupsets_input_frame)
        groupsets_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        help_label = ctk.CTkLabel(groupsets_container, 
                                 text="Enter grouping sets separated by semicolons\nExample: (col1, col2); (col1); ()",
                                 text_color="gray")
        help_label.pack(anchor="w", padx=5, pady=2)
        
        self.groupsets_entry = ctk.CTkTextbox(groupsets_container, height=60)
        self.groupsets_entry.pack(fill="x", expand=True, padx=5, pady=(0, 5))
        
        ctk.CTkButton(groupsets_input_frame, text="Parse Sets", 
                     command=self.parse_groupsets, width=100).pack(side="right")

        # Фрейм для настроек детализации
        detail_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        detail_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(detail_frame, text="Detail Level:").pack(side="left", padx=2)
        
        self.detail_level_combo = ctk.CTkComboBox(detail_frame, 
                                                 values=["All Levels", "Level 1 Only", "Level 2 Only", "Level 3 Only"],
                                                 width=150)
        self.detail_level_combo.pack(side="left", padx=10)
        self.detail_level_combo.set("All Levels")
        
        # Скрываем фрейм GROUPING SETS по умолчанию
        self.groupsets_frame.pack_forget()

    def create_controls_section(self, parent):
        """Создание секции управления"""
        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(fill="x", pady=10)

        ctk.CTkButton(controls_frame, text="Generate Query", 
                     command=self.generate_query,
                     fg_color=self.app.colors["primary"]).pack(side="left", padx=5)

        ctk.CTkButton(controls_frame, text="Execute Query", 
                     command=self.execute_query,
                     fg_color=self.app.colors["success"]).pack(side="left", padx=5)

        ctk.CTkButton(controls_frame, text="Clear All", 
                     command=self.clear_all,
                     fg_color=self.app.colors["warning"]).pack(side="left", padx=5)

        ctk.CTkButton(controls_frame, text="Export Results", 
                     command=self.export_results).pack(side="left", padx=5)

    def create_results_section(self, parent):
        """Создание секции результатов"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(results_frame, text="Results", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        # Вкладки для SQL и результатов
        self.results_tabs = ctk.CTkTabview(results_frame)
        self.results_tabs.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Вкладка SQL
        self.sql_tab = self.results_tabs.add("Generated SQL")
        self.sql_text = ctk.CTkTextbox(self.sql_tab, wrap="none")
        self.sql_text.pack(fill="both", expand=True)
        
        # Вкладка результатов
        self.results_tab = self.results_tabs.add("Query Results")
        self.results_text = ctk.CTkTextbox(self.results_tab, wrap="none")
        self.results_text.pack(fill="both", expand=True)
        
        # Вкладка статистики
        self.stats_tab = self.results_tabs.add("Statistics")
        self.stats_text = ctk.CTkTextbox(self.stats_tab)
        self.stats_text.pack(fill="both", expand=True)

    def get_table_columns(self) -> List[str]:
        """Получение списка столбцов из таблицы"""
        try:
            # Получаем информацию о таблице из БД
            query = "PRAGMA table_info(attacks)"  # Для SQLite
            result = self.app.api_client.execute_custom_query(query)
            return [row[1] for row in result]  # row[1] - имя столбца
        except:
            # Возвращаем стандартный список, если не удалось получить из БД
            return ["name", "frequency", "danger", "attack_type", "created_at", 
                    "description", "mitigation", "source_ip", "target_ip", "severity"]

    def on_column_checkbox_change(self, column, var):
        """Обработка изменения состояния чекбокса"""
        pass  # Мы будем обрабатывать это в add_selected_columns

    def add_selected_columns(self):
        """Добавление выбранных столбцов для группировки"""
        selected = []
        for column, var in self.column_checkboxes.items():
            if var.get() and column not in self.selected_columns:
                self.selected_columns.append(column)
                selected.append(column)
                var.set(False)  # Сбрасываем чекбокс
        
        if selected:
            self.update_selected_columns_list()
            # Обновляем список в комбобоксе агрегаций
            current_values = list(self.agg_column_combo.cget("values"))
            for col in selected:
                if col not in current_values:
                    current_values.append(col)
            self.agg_column_combo.configure(values=current_values)
            messagebox.showinfo("Info", f"Added {len(selected)} columns to grouping")

    def clear_selected_columns(self):
        """Очистка всех выбранных столбцов"""
        self.selected_columns = []
        self.update_selected_columns_list()
        
        # Сбрасываем все чекбоксы
        for var in self.column_checkboxes.values():
            var.set(False)

    def update_selected_columns_list(self):
        """Обновление списка выбранных столбцов"""
        # Очищаем фрейм
        for widget in self.selected_columns_frame.winfo_children():
            widget.destroy()
        
        # Добавляем текущие выбранные столбцы
        for i, column in enumerate(self.selected_columns, 1):
            row_frame = ctk.CTkFrame(self.selected_columns_frame, fg_color="transparent", height=30)
            row_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row_frame, text=f"{i}. {column}", width=150).pack(side="left", padx=5)
            
            # Кнопка удаления
            ctk.CTkButton(row_frame, text="Remove", width=80, height=24,
                         command=lambda col=column: self.remove_single_column(col)).pack(side="right", padx=5)

    def remove_single_column(self, column):
        """Удаление одного столбца из выбранных"""
        if column in self.selected_columns:
            self.selected_columns.remove(column)
            self.update_selected_columns_list()

    def add_aggregation(self):
        """Добавление агрегатной функции"""
        column = self.agg_column_combo.get()
        func = self.agg_function_combo.get()
        
        if not column:
            messagebox.showwarning("Warning", "Please select a column for aggregation")
            return
        
        agg = {"column": column, "function": func}
        self.aggregations.append(agg)
        
        # Обновляем список агрегаций
        self.update_aggregations_list()

    def update_aggregations_list(self):
        """Обновление списка агрегаций"""
        # Очищаем фрейм
        for widget in self.aggregations_frame.winfo_children():
            widget.destroy()
        
        # Добавляем текущие агрегации
        for i, agg in enumerate(self.aggregations, 1):
            row_frame = ctk.CTkFrame(self.aggregations_frame, fg_color="transparent", height=30)
            row_frame.pack(fill="x", pady=2)
            
            display_name = f"{agg['function']}({agg['column']})"
            ctk.CTkLabel(row_frame, text=f"{i}. {display_name}", width=200).pack(side="left", padx=5)
            
            # Кнопка удаления
            ctk.CTkButton(row_frame, text="Remove", width=80, height=24,
                         command=lambda idx=i-1: self.remove_aggregation(idx)).pack(side="right", padx=5)

    def remove_aggregation(self, index):
        """Удаление агрегации по индексу"""
        if 0 <= index < len(self.aggregations):
            self.aggregations.pop(index)
            self.update_aggregations_list()

    def clear_aggregations(self):
        """Очистка всех агрегаций"""
        self.aggregations = []
        self.update_aggregations_list()

    def parse_groupsets(self):
        """Парсинг GROUPING SETS из текста"""
        text = self.groupsets_entry.get("1.0", "end").strip()
        if not text:
            return
        
        # Пример парсинга: (col1, col2); (col1); ()
        sets = [s.strip() for s in text.split(';')]
        self.grouping_options = sets
        messagebox.showinfo("Info", f"Parsed {len(sets)} grouping sets")

    def generate_query(self):
        """Генерация SQL запроса с группировкой"""
        try:
            # Проверяем, что есть столбцы для группировки
            if not self.selected_columns:
                messagebox.showwarning("Warning", "Please select at least one grouping column")
                return
            
            # Проверяем, что есть агрегации
            if not self.aggregations:
                messagebox.showwarning("Warning", "Please add at least one aggregation function")
                return
            
            # Формируем SELECT часть
            select_parts = []
            
            # Столбцы группировки
            select_parts.extend(self.selected_columns)
            
            # Агрегатные функции
            for agg in self.aggregations:
                if agg['function'].upper() == 'COUNT' and agg['column'] == '*':
                    select_parts.append(f"COUNT(*)")
                else:
                    select_parts.append(f"{agg['function']}({agg['column']}) AS {agg['function']}_{agg['column']}")
            
            select_clause = ", ".join(select_parts)
            
            # Формируем GROUP BY часть
            grouping_type = self.grouping_type_var.get()
            group_by_clause = ""
            
            if grouping_type == "GROUP BY":
                group_by_clause = f"GROUP BY {', '.join(self.selected_columns)}"
            
            elif grouping_type == "ROLLUP":
                group_by_clause = f"GROUP BY ROLLUP({', '.join(self.selected_columns)})"
            
            elif grouping_type == "CUBE":
                group_by_clause = f"GROUP BY CUBE({', '.join(self.selected_columns)})"
            
            elif grouping_type == "GROUPING SETS":
                if not self.grouping_options:
                    messagebox.showwarning("Warning", "Please define GROUPING SETS")
                    return
                group_by_clause = f"GROUP BY GROUPING SETS({', '.join(self.grouping_options)})"
            
            # Добавляем сортировку
            order_by_clause = f"ORDER BY {', '.join(self.selected_columns)}"
            
            # Формируем полный запрос
            sql = f"SELECT {select_clause}\nFROM attacks\n{group_by_clause}\n{order_by_clause}"
            
            # Показываем SQL
            self.sql_text.delete("1.0", "end")
            self.sql_text.insert("1.0", sql)
            
            # Переключаемся на вкладку SQL
            self.results_tabs.set("Generated SQL")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate query: {e}")

    def execute_query(self):
        """Выполнение сгенерированного запроса"""
        try:
            sql = self.sql_text.get("1.0", "end").strip()
            if not sql:
                messagebox.showwarning("Warning", "No query to execute. Please generate a query first.")
                return
            
            # Выполняем запрос
            results = self.app.api_client.execute_custom_query(sql)
            
            # Показываем результаты
            self.show_results(results)
            
            # Генерируем статистику
            self.generate_statistics(results)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute query: {e}")

    def show_results(self, results):
        """Отображение результатов запроса"""
        self.results_text.delete("1.0", "end")
        
        if not results:
            self.results_text.insert("1.0", "No results found.")
            return
        
        # Отображаем результаты
        self.results_text.insert("1.0", f"Found {len(results)} records:\n\n")
        
        # Пытаемся получить названия столбцов
        try:
            if results and hasattr(results[0], '_fields'):
                headers = results[0]._fields
            else:
                # Если нет _fields, создаем заголовки
                headers = [f"Column_{i+1}" for i in range(len(results[0]))] if results else []
            
            if headers:
                header_line = " | ".join(headers)
                self.results_text.insert("end", f"{header_line}\n")
                self.results_text.insert("end", "-" * len(header_line) + "\n")
        except:
            pass
        
        for i, row in enumerate(results, 1):
            self.results_text.insert("end", f"{i}. {row}\n")
        
        # Переключаемся на вкладку результатов
        self.results_tabs.set("Query Results")

    def generate_statistics(self, results):
        """Генерация статистики по результатам"""
        if not results:
            self.stats_text.delete("1.0", "end")
            self.stats_text.insert("1.0", "No data for statistics.")
            return
        
        self.stats_text.delete("1.0", "end")
        
        # Базовая статистика
        total_records = len(results)
        self.stats_text.insert("1.0", f"Total Records: {total_records}\n\n")
        
        # Статистика по уровням группировки
        if self.selected_columns and results:
            try:
                grouping_levels = 0
                for row in results:
                    # Преобразуем row в список, если это необходимо
                    if hasattr(row, '_asdict'):
                        row_data = list(row._asdict().values())
                    elif isinstance(row, (list, tuple)):
                        row_data = list(row)
                    else:
                        row_data = [row]
                    
                    # Подсчитываем NULL значения в первых N столбцах (группирующих)
                    null_count = sum(1 for val in row_data[:len(self.selected_columns)] if val is None)
                    grouping_levels = max(grouping_levels, len(self.selected_columns) - null_count)
                
                self.stats_text.insert("end", f"Grouping Levels Detected: {grouping_levels}\n")
            except:
                pass
        
        self.stats_text.insert("end", f"Grouping Type: {self.grouping_type_var.get()}\n")
        self.stats_text.insert("end", f"Detail Level: {self.detail_level_combo.get()}\n\n")
        
        # Информация о структуре результатов
        if results:
            try:
                if hasattr(results[0], '_fields'):
                    self.stats_text.insert("end", "Result Columns:\n")
                    for i, col in enumerate(results[0]._fields):
                        self.stats_text.insert("end", f"  {i+1}. {col}\n")
            except:
                pass

    def clear_all(self):
        """Очистка всех настроек и результатов"""
        self.selected_columns = []
        self.aggregations = []
        self.grouping_options = []
        
        # Очищаем все фреймы с выбранными элементами
        for widget in self.selected_columns_frame.winfo_children():
            widget.destroy()
        
        for widget in self.aggregations_frame.winfo_children():
            widget.destroy()
        
        # Очищаем текстовые поля
        self.sql_text.delete("1.0", "end")
        self.results_text.delete("1.0", "end")
        self.stats_text.delete("1.0", "end")
        self.groupsets_entry.delete("1.0", "end")
        
        # Сбрасываем значения
        self.grouping_type_var.set("GROUP BY")
        self.detail_level_combo.set("All Levels")
        
        # Скрываем фрейм GROUPING SETS
        self.groupsets_frame.pack_forget()
        
        messagebox.showinfo("Info", "All settings have been cleared")

    def export_results(self):
        """Экспорт результатов в файл"""
        try:
            # Запрашиваем путь для сохранения
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Получаем данные для экспорта
            results_text = self.results_text.get("1.0", "end").strip()
            if not results_text:
                messagebox.showwarning("Warning", "No results to export")
                return
            
            # Сохраняем в файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(results_text)
            
            messagebox.showinfo("Success", f"Results exported to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {e}")

    def on_grouping_type_changed(self):
        """Обработка изменения типа группировки"""
        grouping_type = self.grouping_type_var.get()
        
        if grouping_type == "GROUPING SETS":
            self.groupsets_frame.pack(fill="x", padx=15, pady=5)
        else:
            self.groupsets_frame.pack_forget()