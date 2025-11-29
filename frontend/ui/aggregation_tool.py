import customtkinter as ctk
from tkinter import ttk, messagebox


class AggregationTool:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.aggregate_functions = []
        self.group_by_columns = []
        self.having_conditions = []
        self.case_expressions = []
        self.null_functions = []

        self.table_combo = None
        self.agg_column_combo = None
        self.group_column_combo = None

        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        # Main scrollable frame
        main_scrollable = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        main_scrollable.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            main_scrollable,
            text="📊 Advanced Aggregation Tool",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        self.create_query_settings(main_scrollable)
        self.create_case_section(main_scrollable)
        self.create_null_functions_section(main_scrollable)
        self.create_aggregation_section(main_scrollable)
        self.create_grouping_section(main_scrollable)
        self.create_having_section(main_scrollable)
        self.create_action_buttons(main_scrollable)
        self.create_results_section(main_scrollable)

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

    def create_case_section(self, parent):
        case_frame = ctk.CTkFrame(parent)
        case_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(case_frame, text="CASE Expression Builder",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        # Первая строка - основные элементы
        row1_frame = ctk.CTkFrame(case_frame, fg_color="transparent")
        row1_frame.pack(fill="x", padx=15, pady=5)

        # Column selection
        ctk.CTkLabel(row1_frame, text="Column:").pack(side="left")
        self.case_column_combo = ctk.CTkComboBox(row1_frame, values=[], width=120)
        self.case_column_combo.pack(side="left", padx=(10, 5))

        # Operator selection
        ctk.CTkLabel(row1_frame, text="Operator:").pack(side="left")
        self.case_operator_combo = ctk.CTkComboBox(row1_frame,
                                                   values=["=", "!=", ">", "<", ">=", "<=", "IS NULL", "IS NOT NULL"],
                                                   width=100)
        self.case_operator_combo.pack(side="left", padx=(10, 5))
        self.case_operator_combo.set("=")

        # Value entry
        ctk.CTkLabel(row1_frame, text="Value:").pack(side="left")
        self.case_value_entry = ctk.CTkEntry(row1_frame, placeholder_text="value", width=100)
        self.case_value_entry.pack(side="left", padx=(10, 5))

        # THEN value
        ctk.CTkLabel(row1_frame, text="THEN:").pack(side="left")
        self.case_then_entry = ctk.CTkEntry(row1_frame, placeholder_text="then_value", width=100)
        self.case_then_entry.pack(side="left", padx=(10, 5))

        # Add WHEN button
        ctk.CTkButton(row1_frame, text="Add WHEN",
                      command=self.add_when_condition).pack(side="left", padx=(10, 5))

        # Вторая строка - алиас и ELSE
        row2_frame = ctk.CTkFrame(case_frame, fg_color="transparent")
        row2_frame.pack(fill="x", padx=15, pady=5)

        # Alias
        ctk.CTkLabel(row2_frame, text="Alias:").pack(side="left")
        self.case_alias_entry = ctk.CTkEntry(row2_frame, placeholder_text="case_result", width=100)
        self.case_alias_entry.pack(side="left", padx=(10, 5))

        # ELSE value
        ctk.CTkLabel(row2_frame, text="ELSE:").pack(side="left")
        self.case_else_entry = ctk.CTkEntry(row2_frame, placeholder_text="else_value", width=100)
        self.case_else_entry.pack(side="left", padx=(10, 5))

        # Finalize CASE button
        ctk.CTkButton(row2_frame, text="Create CASE",
                      command=self.finalize_case_expression).pack(side="left", padx=(10, 0))

        # CASE conditions list
        ctk.CTkLabel(case_frame, text="Current WHEN Conditions:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        self.case_conditions_frame = ctk.CTkScrollableFrame(case_frame, height=80)
        self.case_conditions_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Final CASE expressions list
        ctk.CTkLabel(case_frame, text="Created CASE Expressions:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        self.case_list_frame = ctk.CTkScrollableFrame(case_frame, height=100)
        self.case_list_frame.pack(fill="x", padx=15, pady=(0, 10))

    def create_null_functions_section(self, parent):
        null_frame = ctk.CTkFrame(parent)
        null_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(null_frame, text="NULL Functions",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        # COALESCE row
        coalesce_frame = ctk.CTkFrame(null_frame, fg_color="transparent")
        coalesce_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(coalesce_frame, text="COALESCE:").pack(side="left")
        self.coalesce_column_combo = ctk.CTkComboBox(coalesce_frame, values=[], width=120)
        self.coalesce_column_combo.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(coalesce_frame, text="Default:").pack(side="left")
        self.coalesce_default_entry = ctk.CTkEntry(coalesce_frame, placeholder_text="default_value", width=100)
        self.coalesce_default_entry.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(coalesce_frame, text="Alias:").pack(side="left")
        self.coalesce_alias_entry = ctk.CTkEntry(coalesce_frame, placeholder_text="coalesce_result", width=100)
        self.coalesce_alias_entry.pack(side="left", padx=(10, 5))

        ctk.CTkButton(coalesce_frame, text="Add COALESCE",
                      command=self.add_coalesce_function).pack(side="left", padx=(10, 5))

        # NULLIF row
        nullif_frame = ctk.CTkFrame(null_frame, fg_color="transparent")
        nullif_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(nullif_frame, text="NULLIF:").pack(side="left")
        self.nullif_column_combo = ctk.CTkComboBox(nullif_frame, values=[], width=120)
        self.nullif_column_combo.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(nullif_frame, text="Compare:").pack(side="left")
        self.nullif_compare_entry = ctk.CTkEntry(nullif_frame, placeholder_text="value_to_null", width=100)
        self.nullif_compare_entry.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(nullif_frame, text="Alias:").pack(side="left")
        self.nullif_alias_entry = ctk.CTkEntry(nullif_frame, placeholder_text="nullif_result", width=100)
        self.nullif_alias_entry.pack(side="left", padx=(10, 5))

        ctk.CTkButton(nullif_frame, text="Add NULLIF",
                      command=self.add_nullif_function).pack(side="left", padx=(10, 0))

        # NULL functions list
        ctk.CTkLabel(null_frame, text="NULL Functions:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        self.null_list_frame = ctk.CTkScrollableFrame(null_frame, height=80)
        self.null_list_frame.pack(fill="x", padx=15, pady=(0, 10))

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

        self.agg_list_frame = ctk.CTkScrollableFrame(agg_frame, height=100)
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

        self.group_list_frame = ctk.CTkScrollableFrame(group_frame, height=80)
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

        self.having_list_frame = ctk.CTkScrollableFrame(having_frame, height=80)
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

        # Create a frame for treeview with scrollbars
        tree_frame = ctk.CTkFrame(results_frame)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.results_tree = ttk.Treeview(tree_frame, height=12)

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.results_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.results_tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

    def get_available_tables(self):
        try:
            return self.app.api_client.get_all_tables()
        except:
            return ["attacks", "targets"]

    def on_table_selected(self, choice):
        try:
            schema = self.app.api_client.get_table_schema(choice)
            columns = [col['name'] for col in schema]

            # Update all column comboboxes
            for combo_attr in ['agg_column_combo', 'group_column_combo', 'case_column_combo',
                               'coalesce_column_combo', 'nullif_column_combo']:
                combo = getattr(self, combo_attr, None)
                if combo:
                    combo.configure(values=columns)
                    if columns:
                        combo.set(columns[0])

        except Exception as e:
            print(f"Error loading columns: {e}")

    # CASE Expression Methods
    def add_when_condition(self):
        column = self.case_column_combo.get()
        operator = self.case_operator_combo.get()
        value = self.case_value_entry.get().strip()
        then_value = self.case_then_entry.get().strip()

        if not column or not then_value:
            messagebox.showwarning("Warning", "Please fill column and THEN value")
            return

        # For IS NULL/IS NOT NULL, don't require value
        if operator in ["IS NULL", "IS NOT NULL"]:
            condition = f"{column} {operator}"
        else:
            if not value:
                messagebox.showwarning("Warning", "Please enter a value for comparison")
                return
            # Add quotes for string values (simple heuristic)
            if not value.replace('.', '').isdigit():
                value = f"'{value}'"
            condition = f"{column} {operator} {value}"

        # Add quotes for THEN value if it's not a number
        if not then_value.replace('.', '').isdigit() and then_value.upper() != 'NULL':
            then_value = f"'{then_value}'"

        # Store condition temporarily
        if not hasattr(self, 'current_case_conditions'):
            self.current_case_conditions = []

        self.current_case_conditions.append({
            'condition': condition,
            'then_value': then_value
        })

        self.update_case_conditions_list()

        # Clear input fields
        self.case_value_entry.delete(0, 'end')
        self.case_then_entry.delete(0, 'end')

    def finalize_case_expression(self):
        if not hasattr(self, 'current_case_conditions') or not self.current_case_conditions:
            messagebox.showwarning("Warning", "Please add at least one WHEN condition")
            return

        alias = self.case_alias_entry.get().strip() or "case_result"
        else_value = self.case_else_entry.get().strip() or "NULL"

        # Add quotes for ELSE value if it's not a number
        if else_value.upper() != 'NULL' and not else_value.replace('.', '').isdigit():
            else_value = f"'{else_value}'"

        case_expr = {
            'type': 'CASE',
            'conditions': self.current_case_conditions.copy(),
            'else_value': else_value,
            'alias': alias
        }

        self.case_expressions.append(case_expr)
        self.update_case_list()

        # Reset current conditions
        self.current_case_conditions = []
        for widget in self.case_conditions_frame.winfo_children():
            widget.destroy()

        # Clear input fields
        self.case_alias_entry.delete(0, 'end')
        self.case_else_entry.delete(0, 'end')

    def update_case_conditions_list(self):
        for widget in self.case_conditions_frame.winfo_children():
            widget.destroy()

        if hasattr(self, 'current_case_conditions'):
            for i, cond in enumerate(self.current_case_conditions):
                frame = ctk.CTkFrame(self.case_conditions_frame, height=25)
                frame.pack(fill="x", pady=1)

                text = f"WHEN {cond['condition']} THEN {cond['then_value']}"
                ctk.CTkLabel(frame, text=text).pack(side="left", padx=5)

                ctk.CTkButton(
                    frame, text="❌", width=30, height=20,
                    command=lambda idx=i: self.remove_case_condition(idx)
                ).pack(side="right", padx=2)

    def update_case_list(self):
        for widget in self.case_list_frame.winfo_children():
            widget.destroy()

        for i, case in enumerate(self.case_expressions):
            frame = ctk.CTkFrame(self.case_list_frame, height=25)
            frame.pack(fill="x", pady=1)

            # Create shortened display text
            conditions_count = len(case['conditions'])
            display_text = f"CASE ({conditions_count} conditions) AS {case['alias']}"

            ctk.CTkLabel(frame, text=display_text, cursor="hand2").pack(side="left", padx=5)

            # Add tooltip on hover
            def make_tooltip(case_obj):
                full_text = "CASE "
                for cond in case_obj['conditions']:
                    full_text += f"WHEN {cond['condition']} THEN {cond['then_value']} "
                full_text += f"ELSE {case_obj['else_value']} END AS {case_obj['alias']}"
                return full_text

            # Bind hover event to show full SQL
            def on_enter(event, text=make_tooltip(case)):
                tooltip = ctk.CTkToplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
                label = ctk.CTkLabel(tooltip, text=text, justify="left")
                label.pack(padx=5, pady=5)
                tooltip.tooltip = tooltip  # Keep reference

            def on_leave(event):
                if hasattr(event.widget, 'tooltip') and event.widget.tooltip:
                    event.widget.tooltip.destroy()

            frame.bind("<Enter>", lambda e, c=case: on_enter(e))
            frame.bind("<Leave>", on_leave)

            ctk.CTkButton(
                frame, text="❌", width=30, height=20,
                command=lambda idx=i: self.remove_case_expression(idx)
            ).pack(side="right", padx=2)

    def remove_case_condition(self, index):
        if hasattr(self, 'current_case_conditions'):
            self.current_case_conditions.pop(index)
            self.update_case_conditions_list()

    def remove_case_expression(self, index):
        self.case_expressions.pop(index)
        self.update_case_list()

    # NULL Functions Methods
    def add_coalesce_function(self):
        column = self.coalesce_column_combo.get()
        default_value = self.coalesce_default_entry.get().strip()
        alias = self.coalesce_alias_entry.get().strip() or "coalesce_result"

        if not column or not default_value:
            messagebox.showwarning("Warning", "Please fill column and default value")
            return

        # Add quotes for string values
        if not default_value.replace('.', '').isdigit():
            default_value = f"'{default_value}'"

        null_func = {
            'type': 'COALESCE',
            'column': column,
            'default_value': default_value,
            'alias': alias
        }

        self.null_functions.append(null_func)
        self.update_null_list()

        # Clear input fields
        self.coalesce_default_entry.delete(0, 'end')
        self.coalesce_alias_entry.delete(0, 'end')

    def add_nullif_function(self):
        column = self.nullif_column_combo.get()
        compare_value = self.nullif_compare_entry.get().strip()
        alias = self.nullif_alias_entry.get().strip() or "nullif_result"

        if not column or not compare_value:
            messagebox.showwarning("Warning", "Please fill column and compare value")
            return

        # Add quotes for string values
        if not compare_value.replace('.', '').isdigit():
            compare_value = f"'{compare_value}'"

        null_func = {
            'type': 'NULLIF',
            'column': column,
            'compare_value': compare_value,
            'alias': alias
        }

        self.null_functions.append(null_func)
        self.update_null_list()

        # Clear input fields
        self.nullif_compare_entry.delete(0, 'end')
        self.nullif_alias_entry.delete(0, 'end')

    def update_null_list(self):
        for widget in self.null_list_frame.winfo_children():
            widget.destroy()

        for i, null_func in enumerate(self.null_functions):
            frame = ctk.CTkFrame(self.null_list_frame, height=25)
            frame.pack(fill="x", pady=1)

            if null_func['type'] == 'COALESCE':
                text = f"COALESCE({null_func['column']}, {null_func['default_value']}) AS {null_func['alias']}"
            else:
                text = f"NULLIF({null_func['column']}, {null_func['compare_value']}) AS {null_func['alias']}"

            ctk.CTkLabel(frame, text=text).pack(side="left", padx=5)

            ctk.CTkButton(
                frame, text="❌", width=30, height=20,
                command=lambda idx=i: self.remove_null_function(idx)
            ).pack(side="right", padx=2)

    def remove_null_function(self, index):
        self.null_functions.pop(index)
        self.update_null_list()

    # Existing methods with modifications for SQL building
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

        # Clear alias field
        self.alias_entry.delete(0, 'end')

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

        # Clear condition field
        self.having_condition.delete(0, 'end')

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

        if not self.aggregate_functions and not self.case_expressions and not self.null_functions and not self.group_by_columns:
            return None

        select_parts = []

        # Add CASE expressions
        for case in self.case_expressions:
            case_sql = "CASE "
            for cond in case['conditions']:
                case_sql += f"WHEN {cond['condition']} THEN {cond['then_value']} "
            case_sql += f"ELSE {case['else_value']} END AS {case['alias']}"
            select_parts.append(case_sql)

        # Add NULL functions
        for null_func in self.null_functions:
            if null_func['type'] == 'COALESCE':
                select_parts.append(
                    f"COALESCE({null_func['column']}, {null_func['default_value']}) AS {null_func['alias']}")
            else:
                select_parts.append(
                    f"NULLIF({null_func['column']}, {null_func['compare_value']}) AS {null_func['alias']}")

        # Add aggregate functions
        for agg in self.aggregate_functions:
            if agg['function'] == 'COUNT' and agg['column'] == '*':
                select_parts.append(f"COUNT(*) AS {agg['alias']}")
            else:
                select_parts.append(f"{agg['function']}({agg['column']}) AS {agg['alias']}")

        # Add GROUP BY columns
        for col in self.group_by_columns:
            select_parts.append(col)

        select_clause = ", ".join(select_parts) if select_parts else "*"

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
            messagebox.showwarning("Warning", "Please add at least one function or expression")
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
        self.case_expressions = []
        self.null_functions = []

        if hasattr(self, 'current_case_conditions'):
            self.current_case_conditions = []

        self.update_aggregate_list()
        self.update_group_list()
        self.update_having_list()
        self.update_case_list()
        self.update_null_list()

        # Clear conditions frame
        for widget in self.case_conditions_frame.winfo_children():
            widget.destroy()

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