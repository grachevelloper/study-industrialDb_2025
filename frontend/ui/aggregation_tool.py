import customtkinter as ctk
from tkinter import ttk, messagebox

class AggregationTool:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.aggregate_functions = []
        self.group_by_columns = []
        self.having_conditions = []
        
        self.table_combo = None
        self.agg_column_combo = None
        self.group_column_combo = None
        
        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            main_frame,
            text="📊 Advanced Aggregation Tool",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        self.create_query_settings(main_frame)
        self.create_aggregation_section(main_frame)
        self.create_grouping_section(main_frame)
        self.create_having_section(main_frame)
        self.create_action_buttons(main_frame)
        self.create_results_section(main_frame)

    def load_initial_data(self):
        try:
            if self.table_combo:
                self.table_combo.set("attacks")
                self.on_table_selected("attacks")
        except Exception as e:
            print(f"Error loading initial data: {e}")

    def create_query_settings(self, parent):
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(settings_frame, text="Query Settings", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        table_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        table_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(table_frame, text="Table:").pack(side="left")
        self.table_combo = ctk.CTkComboBox(table_frame, 
                                         values=self.get_available_tables(),
                                         width=200,
                                         command=self.on_table_selected)
        self.table_combo.pack(side="left", padx=(10, 20))

    def create_aggregation_section(self, parent):
        agg_frame = ctk.CTkFrame(parent)
        agg_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(agg_frame, text="Aggregate Functions", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        controls_frame = ctk.CTkFrame(agg_frame, fg_color="transparent")
        controls_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(controls_frame, text="Function:").pack(side="left")
        self.function_combo = ctk.CTkComboBox(controls_frame, 
                                            values=["COUNT", "SUM", "AVG", "MIN", "MAX"],
                                            width=120)
        self.function_combo.pack(side="left", padx=(10, 5))
        self.function_combo.set("COUNT")

        ctk.CTkLabel(controls_frame, text="Column:").pack(side="left")
        self.agg_column_combo = ctk.CTkComboBox(controls_frame, values=[], width=150)
        self.agg_column_combo.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(controls_frame, text="Alias:").pack(side="left")
        self.alias_entry = ctk.CTkEntry(controls_frame, placeholder_text="result_name", width=120)
        self.alias_entry.pack(side="left", padx=(10, 5))

        ctk.CTkButton(controls_frame, text="Add Function", 
                     command=self.add_aggregate_function).pack(side="left", padx=(10, 0))

        self.agg_list_frame = ctk.CTkScrollableFrame(agg_frame, height=80)
        self.agg_list_frame.pack(fill="x", padx=15, pady=(0, 10))

    def create_grouping_section(self, parent):
        group_frame = ctk.CTkFrame(parent)
        group_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(group_frame, text="GROUP BY", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        controls_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
        controls_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(controls_frame, text="Group by column:").pack(side="left")
        self.group_column_combo = ctk.CTkComboBox(controls_frame, values=[], width=200)
        self.group_column_combo.pack(side="left", padx=(10, 5))

        ctk.CTkButton(controls_frame, text="Add Grouping", 
                     command=self.add_group_column).pack(side="left", padx=(10, 0))

        self.group_list_frame = ctk.CTkScrollableFrame(group_frame, height=60)
        self.group_list_frame.pack(fill="x", padx=15, pady=(0, 10))

    def create_having_section(self, parent):
        having_frame = ctk.CTkFrame(parent)
        having_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(having_frame, text="HAVING Conditions", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        controls_frame = ctk.CTkFrame(having_frame, fg_color="transparent")
        controls_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(controls_frame, text="Condition:").pack(side="left")
        self.having_condition = ctk.CTkEntry(controls_frame, 
                                           placeholder_text="COUNT(*) > 5",
                                           width=200)
        self.having_condition.pack(side="left", padx=(10, 5))

        ctk.CTkButton(controls_frame, text="Add HAVING", 
                     command=self.add_having_condition).pack(side="left", padx=(10, 0))

        self.having_list_frame = ctk.CTkScrollableFrame(having_frame, height=60)
        self.having_list_frame.pack(fill="x", padx=15, pady=(0, 10))

    def create_action_buttons(self, parent):
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=15)

        ctk.CTkButton(
            button_frame,
            text="🚀 Execute Query",
            command=self.execute_aggregation,
            fg_color=self.app.colors["success"],
            width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="📝 Show SQL",
            command=self.show_sql,
            fg_color=self.app.colors["primary"],
            width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="🗑️ Clear All",
            command=self.clear_all,
            fg_color=self.app.colors["danger"],
            width=120
        ).pack(side="left", padx=5)

    def create_results_section(self, parent):
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(results_frame, text="Aggregation Results", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        self.results_tree = ttk.Treeview(results_frame, height=12)
        
        v_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        h_scroll = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.results_tree.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        v_scroll.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))
        h_scroll.pack(side="bottom", fill="x", padx=(15, 15), pady=(0, 0))

    def get_available_tables(self):
        try:
            return self.app.api_client.get_all_tables()
        except:
            return ["attacks", "targets"]

    def on_table_selected(self, choice):
        try:
            schema = self.app.api_client.get_table_schema(choice)
            columns = [col['name'] for col in schema]
            
            if hasattr(self, 'agg_column_combo') and self.agg_column_combo:
                self.agg_column_combo.configure(values=columns)
                if columns:
                    self.agg_column_combo.set(columns[0])
            
            if hasattr(self, 'group_column_combo') and self.group_column_combo:
                self.group_column_combo.configure(values=columns)
                if columns:
                    self.group_column_combo.set(columns[0])
                    
        except Exception as e:
            print(f"Error loading columns: {e}")

    def add_aggregate_function(self):
        func = self.function_combo.get()
        column = self.agg_column_combo.get()
        alias = self.alias_entry.get().strip() or f"{func.lower()}_{column}"

        if not column:
            messagebox.showwarning("Warning", "Please select a column")
            return

        agg_func = {
            'function': func,
            'column': column,
            'alias': alias
        }

        self.aggregate_functions.append(agg_func)
        self.update_aggregate_list()

    def add_group_column(self):
        column = self.group_column_combo.get()
        
        if not column:
            messagebox.showwarning("Warning", "Please select a column")
            return

        if column not in self.group_by_columns:
            self.group_by_columns.append(column)
            self.update_group_list()

    def add_having_condition(self):
        condition = self.having_condition.get().strip()
        
        if not condition:
            messagebox.showwarning("Warning", "Please enter a HAVING condition")
            return

        self.having_conditions.append(condition)
        self.update_having_list()

    def update_aggregate_list(self):
        for widget in self.agg_list_frame.winfo_children():
            widget.destroy()

        for i, agg in enumerate(self.aggregate_functions):
            frame = ctk.CTkFrame(self.agg_list_frame, height=25)
            frame.pack(fill="x", pady=1)

            text = f"{agg['function']}({agg['column']}) AS {agg['alias']}"
            ctk.CTkLabel(frame, text=text).pack(side="left", padx=5)

            ctk.CTkButton(
                frame, text="❌", width=30, height=20,
                command=lambda idx=i: self.remove_aggregate_function(idx)
            ).pack(side="right", padx=2)

    def update_group_list(self):
        for widget in self.group_list_frame.winfo_children():
            widget.destroy()

        for i, col in enumerate(self.group_by_columns):
            frame = ctk.CTkFrame(self.group_list_frame, height=25)
            frame.pack(fill="x", pady=1)

            ctk.CTkLabel(frame, text=col).pack(side="left", padx=5)

            ctk.CTkButton(
                frame, text="❌", width=30, height=20,
                command=lambda idx=i: self.remove_group_column(idx)
            ).pack(side="right", padx=2)

    def update_having_list(self):
        for widget in self.having_list_frame.winfo_children():
            widget.destroy()

        for i, condition in enumerate(self.having_conditions):
            frame = ctk.CTkFrame(self.having_list_frame, height=25)
            frame.pack(fill="x", pady=1)

            ctk.CTkLabel(frame, text=condition).pack(side="left", padx=5)

            ctk.CTkButton(
                frame, text="❌", width=30, height=20,
                command=lambda idx=i: self.remove_having_condition(idx)
            ).pack(side="right", padx=2)

    def remove_aggregate_function(self, index):
        self.aggregate_functions.pop(index)
        self.update_aggregate_list()

    def remove_group_column(self, index):
        self.group_by_columns.pop(index)
        self.update_group_list()

    def remove_having_condition(self, index):
        self.having_conditions.pop(index)
        self.update_having_list()

    def build_sql_query(self):
        table = self.table_combo.get()

        if not self.aggregate_functions:
            return None

        select_parts = []
        for agg in self.aggregate_functions:
            if agg['function'] == 'COUNT' and agg['column'] == '*':
                select_parts.append(f"COUNT(*) AS {agg['alias']}")
            else:
                select_parts.append(f"{agg['function']}({agg['column']}) AS {agg['alias']}")

        for col in self.group_by_columns:
            select_parts.append(col)

        select_clause = ", ".join(select_parts)

        group_clause = ""
        if self.group_by_columns:
            group_clause = f"GROUP BY {', '.join(self.group_by_columns)}"

        having_clause = ""
        if self.having_conditions:
            having_clause = f"HAVING {' AND '.join(self.having_conditions)}"

        sql = f"SELECT {select_clause} FROM {table}"
        if group_clause:
            sql += f" {group_clause}"
        if having_clause:
            sql += f" {having_clause}"

        return sql

    def execute_aggregation(self):
        sql = self.build_sql_query()
        
        if not sql:
            messagebox.showwarning("Warning", "Please add at least one aggregate function")
            return

        try:
            results = self.app.api_client.execute_custom_query(sql)
            self.display_results(results)
            
        except Exception as e:
            messagebox.showerror("Error", f"Aggregation failed: {e}")

    def show_sql(self):
        sql = self.build_sql_query()
        
        if not sql:
            messagebox.showwarning("Warning", "No query to show")
            return

        sql_dialog = ctk.CTkToplevel(self.parent)
        sql_dialog.title("Generated SQL Query")
        sql_dialog.geometry("600x200")
        
        ctk.CTkLabel(sql_dialog, text="SQL Query:", 
                    font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        sql_text = ctk.CTkTextbox(sql_dialog, width=580, height=120)
        sql_text.pack(padx=10, pady=10)
        sql_text.insert("1.0", sql)
        sql_text.configure(state="disabled")

    def clear_all(self):
        self.aggregate_functions = []
        self.group_by_columns = []
        self.having_conditions = []
        
        self.update_aggregate_list()
        self.update_group_list()
        self.update_having_list()
        
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def display_results(self, results):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        if not results:
            messagebox.showinfo("Info", "No results found")
            return

        columns = list(results[0].keys())
        self.results_tree["columns"] = columns
        self.results_tree["show"] = "headings"

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)

        for row in results:
            values = [str(row[col]) for col in columns]
            self.results_tree.insert("", "end", values=values)