import customtkinter as ctk
from ui.modal_windows import AddAttackModal, DataViewModal
from ui.grouping_tool import GroupingTool
from ui.view_manager import ViewManager
from ui.materialized_view_manager import MaterializedViewManager
from ui.cte_builder import CTEBuilder


class MainWindow:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.current_module = None
        self.setup_main_window()

    def setup_main_window(self):
        """Setup the main window with buttons"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="DDoS Attack Database Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 30))

        # Main container with navigation and content
        self.setup_main_container(main_frame)

    def setup_main_container(self, parent):
        """Setup main container with navigation and workspace"""
        # Main frame with navigation and workspace
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        # Split into navigation and workspace
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        
        # Navigation panel
        nav_frame = ctk.CTkFrame(container, width=200, corner_radius=0)
        nav_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        nav_frame.grid_propagate(False)
        
        # Workspace area
        self.workspace_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.workspace_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Setup navigation panel
        self.setup_navigation_panel(nav_frame)
        
        # Show main dashboard by default
        self.show_main_dashboard()

    def setup_navigation_panel(self, parent):
        """Setup navigation panel"""
        # Navigation title
        nav_label = ctk.CTkLabel(
            parent,
            text="Navigation",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        nav_label.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Main sections
        sections = [
            ("📊 Dashboard", self.show_main_dashboard, "primary"),
            ("➕ Add Attack", self.open_add_attack_modal, "success"),
            ("👁️ View Data", self.open_data_view_modal, "warning"),
            ("🔍 Advanced Search", self.show_advanced_search, "info"),
            ("📋 Subqueries", self.show_subqueries, "secondary")
        ]
        
        for text, command, color in sections:
            btn = ctk.CTkButton(
                parent,
                text=text,
                command=command,
                fg_color=self.app.colors.get(color, self.app.colors["primary"]),
                hover_color=self.app.colors.get(f"{color}_hover", self.app.colors["primary_hover"]),
                anchor="w",
                height=40
            )
            btn.pack(fill="x", padx=10, pady=2)
        
        # Separator
        separator = ctk.CTkFrame(parent, height=2, fg_color="gray30")
        separator.pack(fill="x", padx=20, pady=15)
        
        # Advanced features (new modules)
        advanced_label = ctk.CTkLabel(
            parent,
            text="Advanced Features",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        advanced_label.pack(pady=(0, 10), padx=20, anchor="w")
        
        advanced_sections = [
            ("📈 Data Grouping", self.show_grouping_tool, "primary"),
            ("👁️ Views", self.show_view_manager, "info"),
            ("💾 Materialized Views", self.show_materialized_view_manager, "success"),
            ("🔗 CTE Builder", self.show_cte_builder, "warning")
        ]
        
        for text, command, color in advanced_sections:
            btn = ctk.CTkButton(
                parent,
                text=text,
                command=command,
                fg_color=self.app.colors.get(color, self.app.colors["primary"]),
                hover_color=self.app.colors.get(f"{color}_hover", self.app.colors["primary_hover"]),
                anchor="w",
                height=35
            )
            btn.pack(fill="x", padx=10, pady=2)
        
        # Database management
        separator2 = ctk.CTkFrame(parent, height=2, fg_color="gray30")
        separator2.pack(fill="x", padx=20, pady=15)
        
        db_label = ctk.CTkLabel(
            parent,
            text="Database Management",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        db_label.pack(pady=(0, 10), padx=20, anchor="w")
        
        # Create schema button
        ctk.CTkButton(
            parent,
            text="🛠️ Create Database Schema",
            command=self.create_schema,
            fg_color=self.app.colors["primary"],
            hover_color=self.app.colors["primary_hover"],
            anchor="w",
            height=35
        ).pack(fill="x", padx=10, pady=2)
        
        # System information
        self.setup_system_info(parent)

    def setup_system_info(self, parent):
        """Setup system information"""
        separator = ctk.CTkFrame(parent, height=2, fg_color="gray30")
        separator.pack(fill="x", padx=20, pady=15)
        
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Database information
        try:
            db_info = self.app.api_client.get_database_info()
            db_name = db_info.get('name', 'Unknown')
            db_size = db_info.get('size_mb', 0)
            
            ctk.CTkLabel(
                info_frame,
                text=f"📁 Database: {db_name}",
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                info_frame,
                text=f"📊 Size: {db_size:.2f} MB",
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w", pady=2)
            
        except:
            ctk.CTkLabel(
                info_frame,
                text="📁 Database not connected",
                font=ctk.CTkFont(size=11, slant="italic")
            ).pack(anchor="w", pady=2)
        
        # Application version
        ctk.CTkLabel(
            info_frame,
            text=f"⚙️ Version: {self.app.version}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=2)

    def clear_workspace(self):
        """Clear workspace area"""
        for widget in self.workspace_frame.winfo_children():
            widget.destroy()
        self.current_module = None

    def show_main_dashboard(self):
        """Show main dashboard"""
        self.clear_workspace()
        
        # Title
        title_label = ctk.CTkLabel(
            self.workspace_frame,
            text="Main Control Panel",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Welcome message
        welcome_frame = ctk.CTkFrame(self.workspace_frame)
        welcome_frame.pack(fill="x", padx=20, pady=10)
        
        welcome_text = """
        Welcome to DDoS Attack Database Management System!
        
        Use the navigation panel on the left to access features:
        
        • Add Attack - add new attack records
        • View Data - display and filter data
        • Advanced Search - complex database queries
        • Subqueries - work with nested queries
        
        Advanced SQL Features:
        
        • Data Grouping - ROLLUP, CUBE, GROUPING SETS
        • Views - create and manage VIEWs
        • Materialized Views - query optimization
        • CTE Builder - build queries with WITH
        
        Start by creating database schema if not already done.
        """
        
        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text=welcome_text,
            font=ctk.CTkFont(size=13),
            justify="left"
        )
        welcome_label.pack(padx=20, pady=20)
        
        # Quick actions
        self.create_quick_actions()

    def create_quick_actions(self):
        """Create quick actions on main dashboard"""
        quick_frame = ctk.CTkFrame(self.workspace_frame)
        quick_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            quick_frame,
            text="Quick Actions:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        actions_frame = ctk.CTkFrame(quick_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        actions = [
            ("➕ Add Attack", self.open_add_attack_modal, "success"),
            ("👁️ View Data", self.open_data_view_modal, "warning"),
            ("🛠️ Create Schema", self.create_schema, "primary"),
            ("📊 Data Grouping", self.show_grouping_tool, "info")
        ]
        
        for i, (text, command, color) in enumerate(actions):
            btn = ctk.CTkButton(
                actions_frame,
                text=text,
                command=command,
                fg_color=self.app.colors[color],
                height=40,
                font=ctk.CTkFont(size=13)
            )
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
            actions_frame.grid_columnconfigure(i%2, weight=1)
        
        actions_frame.grid_rowconfigure(0, weight=1)
        actions_frame.grid_rowconfigure(1, weight=1)

    def show_grouping_tool(self):
        """Show data grouping tool"""
        self.clear_workspace()
        self.current_module = GroupingTool(self.workspace_frame, self.app)
        self.app.logger.log_info("Data grouping tool opened")

    def show_view_manager(self):
        """Show view manager"""
        self.clear_workspace()
        self.current_module = ViewManager(self.workspace_frame, self.app)
        self.app.logger.log_info("View manager opened")

    def show_materialized_view_manager(self):
        """Show materialized view manager"""
        self.clear_workspace()
        self.current_module = MaterializedViewManager(self.workspace_frame, self.app)
        self.app.logger.log_info("Materialized view manager opened")

    def show_cte_builder(self):
        """Show CTE builder"""
        self.clear_workspace()
        self.current_module = CTEBuilder(self.workspace_frame, self.app)
        self.app.logger.log_info("CTE builder opened")

    def show_advanced_search(self):
        """Show advanced search"""
        self.clear_workspace()
        # Placeholder for advanced search module
        placeholder_label = ctk.CTkLabel(
            self.workspace_frame,
            text="Advanced Search (to be implemented)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        placeholder_label.pack(pady=50)
        self.app.logger.log_info("Advanced search opened")

    def show_subqueries(self):
        """Show subqueries interface"""
        self.clear_workspace()
        # Placeholder for subqueries module
        placeholder_label = ctk.CTkLabel(
            self.workspace_frame,
            text="Subqueries (to be implemented)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        placeholder_label.pack(pady=50)
        self.app.logger.log_info("Subqueries opened")

    def create_schema(self):
        """Create database schema"""
        try:
            self.app.logger.log_info("Creating database schema...")
            result = self.app.api_client.initialize_database()

            if result.get('success') or result.get('status') == 'already_exists':
                self.app.logger.log_database_operation("CREATE_SCHEMA", True)
                if result.get('status') == 'already_exists':
                    self.app.show_success("Tables already exist in the database!")
                else:
                    self.app.show_success("Database schema created successfully!")
            else:
                self.app.logger.log_database_operation("CREATE_SCHEMA", False)
                self.app.show_error("Failed to create database schema")

        except Exception as e:
            # If tables already exist - not an error
            if "409" in str(e) or "already exists" in str(e).lower():
                self.app.logger.log_database_operation("CREATE_SCHEMA", True)
                self.app.show_success("Tables already exist in the database!")
            else:
                self.app.logger.log_error(f"Database schema creation error: {e}")
                self.app.logger.log_database_operation("CREATE_SCHEMA", False)
                self.app.show_error(f"Schema creation error: {e}")

    def open_add_attack_modal(self):
        """Open modal window for adding new attack"""
        self.app.logger.log_info("Opening add attack modal")
        AddAttackModal(self.parent, self.app)

    def open_data_view_modal(self):
        """Open modal window for viewing data"""
        self.app.logger.log_info("Opening data view modal")
        DataViewModal(self.parent, self.app)