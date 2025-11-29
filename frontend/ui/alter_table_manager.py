import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
from api.client import DDOSDatabaseClient


class AlterTableManager:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.setup_ui(parent)

    def setup_ui(self, parent):
        """Создание интерфейса для ALTER TABLE операций"""
        container = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок
        title_label = ctk.CTkLabel(
            container,
            text="🛠️ Database Structure Manager",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Создаем вкладки для разных операций
        tabview = ctk.CTkTabview(container)
        tabview.pack(fill="both", expand=True)

        tabview.add("Add Column")
        self.create_add_column_tab(tabview.tab("Add Column"))

        tabview.add("Drop Column")
        self.create_drop_column_tab(tabview.tab("Drop Column"))

        # Вкладка переименования
        tabview.add("Rename")
        self.create_rename_tab(tabview.tab("Rename"))

        # Вкладка ограничений
        tabview.add("Constraints")
        self.create_constraints_tab(tabview.tab("Constraints"))

    def create_add_column_tab(self, parent):
        """Вкладка добавления столбцов"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Add New Column", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))

        # Выбор таблицы
        table_frame = ctk.CTkFrame(frame, fg_color="transparent")
        table_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(table_frame, text="Table:").pack(side="left")
        self.add_col_table = ctk.CTkComboBox(table_frame, values=["attacks", "targets"], width=150)
        self.add_col_table.pack(side="left", padx=(10, 0))
        self.add_col_table.set("attacks")

        name_frame = ctk.CTkFrame(frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(name_frame, text="Column Name:").pack(side="left")
        self.column_name = ctk.CTkEntry(name_frame, placeholder_text="new_column_name")
        self.column_name.pack(side="left", padx=(10, 0), fill="x", expand=True)

        type_frame = ctk.CTkFrame(frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(type_frame, text="Data Type:").pack(side="left")
        
        # Базовые типы данных
        base_types = [
            "VARCHAR(255)", "TEXT", "INTEGER", "BIGINT", "BOOLEAN",
            "TIMESTAMP", "DATE", "FLOAT", "JSONB"
        ]
        
        self.data_type = ctk.CTkComboBox(type_frame, values=base_types, width=150)
        self.data_type.pack(side="left", padx=(10, 0))
        self.data_type.set("VARCHAR(255)")

        # Кнопка для выбора пользовательских типов
        custom_type_btn = ctk.CTkButton(
            type_frame, 
            text="Custom Types", 
            width=100,
            command=self.show_custom_types
        )
        custom_type_btn.pack(side="left", padx=(10, 0))

        constraints_frame = ctk.CTkFrame(frame, fg_color="transparent")
        constraints_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(constraints_frame, text="Constraints:").pack(side="left")

        self.not_null_var = ctk.BooleanVar()
        self.unique_var = ctk.BooleanVar()

        ctk.CTkCheckBox(constraints_frame, text="NOT NULL", variable=self.not_null_var).pack(side="left", padx=(10, 5))
        ctk.CTkCheckBox(constraints_frame, text="UNIQUE", variable=self.unique_var).pack(side="left", padx=5)

        default_frame = ctk.CTkFrame(frame, fg_color="transparent")
        default_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(default_frame, text="Default Value:").pack(side="left")
        self.default_value = ctk.CTkEntry(default_frame, placeholder_text="Optional")
        self.default_value.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # Кнопка выполнения
        ctk.CTkButton(
            frame,
            text="Add Column",
            command=self.execute_add_column,
            fg_color=self.app.colors["success"]
        ).pack(pady=15)

    def show_custom_types(self):
        """Показать диалог выбора пользовательских типов"""
        try:
            custom_types = self.app.api_client.get_custom_types()
            if not custom_types:
                messagebox.showinfo("Info", "No custom types available")
                return

            dialog = CustomTypeSelectionDialog(self.parent, self.app, custom_types)
            self.app.window.wait_window(dialog)
            
            if dialog.selected_type:
                # Обновляем выбранный тип данных
                self.data_type.set(dialog.selected_type)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load custom types: {e}")

    def create_drop_column_tab(self, parent):
        """Вкладка удаления столбцов"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Drop Column", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))

        # Выбор таблицы
        table_frame = ctk.CTkFrame(frame, fg_color="transparent")
        table_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(table_frame, text="Table:").pack(side="left")
        self.drop_col_table = ctk.CTkComboBox(table_frame, values=["attacks", "targets"], width=150)
        self.drop_col_table.pack(side="left", padx=(10, 0))
        self.drop_col_table.set("attacks")
        self.drop_col_table.configure(command=self.load_columns_for_drop)

        # Выбор столбца
        col_frame = ctk.CTkFrame(frame, fg_color="transparent")
        col_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(col_frame, text="Column:").pack(side="left")
        self.column_to_drop = ctk.CTkComboBox(col_frame, values=[], width=200)
        self.column_to_drop.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # Загружаем столбцы при инициализации
        self.load_columns_for_drop()

        # Предупреждение
        warning_label = ctk.CTkLabel(
            frame,
            text="⚠️ Warning: This action cannot be undone!",
            text_color=self.app.colors["danger"],
            font=ctk.CTkFont(weight="bold")
        )
        warning_label.pack(pady=10)

        # Кнопка выполнения
        ctk.CTkButton(
            frame,
            text="Drop Column",
            command=self.execute_drop_column,
            fg_color=self.app.colors["danger"]
        ).pack(pady=15)

    def create_rename_tab(self, parent):
        """Вкладка переименования таблиц и столбцов"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Rename Objects", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))

        # Переименование таблицы
        ctk.CTkLabel(frame, text="Rename Table:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))

        table_rename_frame = ctk.CTkFrame(frame, fg_color="transparent")
        table_rename_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(table_rename_frame, text="From:").pack(side="left")
        self.old_table_name = ctk.CTkComboBox(table_rename_frame, values=["attacks", "targets"], width=120)
        self.old_table_name.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(table_rename_frame, text="To:").pack(side="left", padx=(10, 0))
        self.new_table_name = ctk.CTkEntry(table_rename_frame, placeholder_text="new_table_name")
        self.new_table_name.pack(side="left", padx=(10, 0), fill="x", expand=True)

        ctk.CTkButton(
            table_rename_frame,
            text="Rename Table",
            command=self.execute_rename_table,
            width=120
        ).pack(side="right", padx=(10, 0))

        # Разделитель
        separator = ctk.CTkFrame(frame, height=1, fg_color="#3a3a5a")
        separator.pack(fill="x", pady=15)

        # Переименование столбца
        ctk.CTkLabel(frame, text="Rename Column:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))

        col_rename_frame = ctk.CTkFrame(frame, fg_color="transparent")
        col_rename_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(col_rename_frame, text="Table:").pack(side="left")
        self.rename_col_table = ctk.CTkComboBox(col_rename_frame, values=["attacks", "targets"], width=120)
        self.rename_col_table.pack(side="left", padx=(10, 5))
        self.rename_col_table.configure(command=self.load_columns_for_rename)

        ctk.CTkLabel(col_rename_frame, text="Column:").pack(side="left", padx=(10, 0))
        self.old_column_name = ctk.CTkComboBox(col_rename_frame, values=[], width=120)
        self.old_column_name.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(col_rename_frame, text="New Name:").pack(side="left")
        self.new_column_name = ctk.CTkEntry(col_rename_frame, placeholder_text="new_column_name")
        self.new_column_name.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # Загружаем столбцы
        self.load_columns_for_rename()

        ctk.CTkButton(
            col_rename_frame,
            text="Rename Column",
            command=self.execute_rename_column,
            width=120
        ).pack(side="right", padx=(10, 0))

    def create_constraints_tab(self, parent):
        """Вкладка управления ограничениями"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Manage Constraints", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))

        # Добавление ограничений
        ctk.CTkLabel(frame, text="Add Constraint:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))

        add_constraint_frame = ctk.CTkFrame(frame, fg_color="transparent")
        add_constraint_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(add_constraint_frame, text="Table:").pack(side="left")
        self.constraint_table = ctk.CTkComboBox(add_constraint_frame, values=["attacks", "targets"], width=120)
        self.constraint_table.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(add_constraint_frame, text="Type:").pack(side="left")
        self.constraint_type = ctk.CTkComboBox(add_constraint_frame,
                                               values=["CHECK", "NOT NULL", "UNIQUE", "FOREIGN KEY"],
                                               width=120)
        self.constraint_type.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(add_constraint_frame, text="Condition:").pack(side="left")
        self.constraint_condition = ctk.CTkEntry(add_constraint_frame, placeholder_text="column > 0")
        self.constraint_condition.pack(side="left", padx=(10, 0), fill="x", expand=True)

        ctk.CTkButton(
            add_constraint_frame,
            text="Add Constraint",
            command=self.execute_add_constraint,
            fg_color=self.app.colors["success"],
            width=120
        ).pack(side="right", padx=(10, 0))

    def load_columns_for_drop(self, event=None):
        """Загрузка столбцов для удаления"""
        table_name = self.drop_col_table.get()
        if table_name:
            columns = self.get_table_columns(table_name)
            self.column_to_drop.configure(values=columns)
            if columns:
                self.column_to_drop.set(columns[0])

    def load_columns_for_rename(self, event=None):
        """Загрузка столбцов для переименования"""
        table_name = self.rename_col_table.get()
        if table_name:
            columns = self.get_table_columns(table_name)
            self.old_column_name.configure(values=columns)
            if columns:
                self.old_column_name.set(columns[0])

    def get_table_columns(self, table_name):
        """Получение списка столбцов таблицы"""
        try:
            conn = self.app.api_client.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM pragma_table_info(?)
                ORDER BY cid
            """, (table_name,))

            columns = [row[0] for row in cursor.fetchall()]
            conn.close()
            return columns
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load columns: {e}")
            return []
    
    def execute_add_column(self):
        """Выполнение добавления столбца"""
        table = self.add_col_table.get()
        column = self.column_name.get().strip()
        data_type = self.data_type.get()

        if not column:
            messagebox.showerror("Error", "Please enter column name")
            return

        # Формируем SQL запрос
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {data_type}"

        # Добавляем ограничения
        if self.not_null_var.get():
            sql += " NOT NULL"
        if self.unique_var.get():
            sql += " UNIQUE"

        # Добавляем значение по умолчанию
        default_val = self.default_value.get().strip()
        if default_val:
            # Для пользовательских типов и текстовых значений используем кавычки
            if any(keyword in data_type.upper() for keyword in ['VARCHAR', 'TEXT', 'CHAR']) or self.is_custom_type(data_type):
                sql += f" DEFAULT '{default_val}'"
            else:
                sql += f" DEFAULT {default_val}"

        self.execute_sql_transaction(sql, f"Column '{column}' added successfully")

    def is_custom_type(self, data_type):
        """Проверяет, является ли тип пользовательским"""
        try:
            custom_types = self.app.api_client.get_custom_types()
            custom_type_names = [t['name'] for t in custom_types]
            return data_type in custom_type_names
        except:
            return False

    def execute_drop_column(self):
        """Выполнение удаления столбца"""
        table = self.drop_col_table.get()
        column = self.column_to_drop.get()

        if not column:
            messagebox.showerror("Error", "Please select column to drop")
            return

        # Подтверждение
        result = messagebox.askyesno(
            "Confirm Drop",
            f"Are you sure you want to drop column '{column}' from table '{table}'?\n\nThis action cannot be undone!"
        )

        if result:
            sql = f"ALTER TABLE {table} DROP COLUMN {column}"
            self.execute_sql_transaction(sql, f"Column '{column}' dropped successfully")

    def execute_rename_table(self):
        """Выполнение переименования таблицы"""
        old_name = self.old_table_name.get()
        new_name = self.new_table_name.get().strip()

        if not new_name:
            messagebox.showerror("Error", "Please enter new table name")
            return

        sql = f"ALTER TABLE {old_name} RENAME TO {new_name}"
        self.execute_sql_transaction(sql, f"Table renamed from '{old_name}' to '{new_name}'")

    def execute_rename_column(self):
        """Выполнение переименования столбца"""
        table = self.rename_col_table.get()
        old_name = self.old_column_name.get()
        new_name = self.new_column_name.get().strip()

        if not new_name:
            messagebox.showerror("Error", "Please enter new column name")
            return

        sql = f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}"
        self.execute_sql_transaction(sql, f"Column renamed from '{old_name}' to '{new_name}'")

    def execute_add_constraint(self):
        """Выполнение добавления ограничения"""
        table = self.constraint_table.get()
        constraint_type = self.constraint_type.get()
        condition = self.constraint_condition.get().strip()

        if constraint_type in ["CHECK", "FOREIGN KEY"] and not condition:
            messagebox.showerror("Error", f"Please enter condition for {constraint_type} constraint")
            return

        # Генерируем имя ограничения
        constraint_name = f"{table}_{constraint_type.lower()}_{condition.split()[0] if condition else 'constr'}"

        if constraint_type == "CHECK":
            sql = f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} CHECK ({condition})"
        elif constraint_type == "NOT NULL":
            sql = f"ALTER TABLE {table} ALTER COLUMN {condition} SET NOT NULL"
        elif constraint_type == "UNIQUE":
            sql = f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} UNIQUE ({condition})"
        elif constraint_type == "FOREIGN KEY":
            # Предполагаем формат: column REFERENCES table(column)
            sql = f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} FOREIGN KEY ({condition})"

        self.execute_sql_transaction(sql, f"Constraint '{constraint_type}' added successfully")

    def execute_sql_transaction(self, sql, success_message):
        """Выполнение SQL в транзакции"""

        def execute_thread():
            try:
                conn = self.app.api_client.db.get_connection()
                cursor = conn.cursor()

                # Выполняем SQL
                cursor.execute(sql)
                conn.commit()
                conn.close()

                self.app.window.after(0, lambda: messagebox.showinfo("Success", success_message))

            except Exception as e:
                self.app.window.after(0, lambda: messagebox.showerror("Error", f"SQL Error: {e}"))

        thread = threading.Thread(target=execute_thread)
        thread.daemon = True
        thread.start()


class CustomTypeSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, custom_types):
        super().__init__(parent)
        self.app = app
        self.custom_types = custom_types
        self.selected_type = None
        self.title("Select Custom Type")
        self.geometry("400x300")
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса выбора типа"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Select Custom Type", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 15))

        # Список типов
        self.types_tree = ttk.Treeview(main_frame, columns=("Type", "Values"), show="headings", height=10)
        self.types_tree.heading("Type", text="Type Name")
        self.types_tree.heading("Values", text="Values/Fields")
        self.types_tree.column("Type", width=150)
        self.types_tree.column("Values", width=200)
        
        # Добавляем типы в список
        for type_data in self.custom_types:
            values_text = str(type_data['values'])[:50] + "..." if len(str(type_data['values'])) > 50 else str(type_data['values'])
            self.types_tree.insert("", "end", values=(type_data['name'], values_text))

        self.types_tree.pack(fill="both", expand=True, pady=(0, 15))
        
        # Двойной клик для выбора
        self.types_tree.bind("<Double-1>", self.on_type_select)

        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(
            button_frame, 
            text="Select", 
            command=self.on_select,
            fg_color=self.app.colors["success"]
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Cancel", 
            command=self.destroy
        ).pack(side="right", padx=5)

    def on_type_select(self, event):
        """Обработка выбора типа двойным кликом"""
        self.on_select()

    def on_select(self):
        """Обработка выбора типа"""
        selection = self.types_tree.selection()
        if selection:
            item = self.types_tree.item(selection[0])
            self.selected_type = item['values'][0]
            self.destroy()