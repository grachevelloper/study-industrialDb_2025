import customtkinter as ctk
from datetime import datetime


class Sidebar:
    def __init__(self, parent, app):
        self.app = app
        self.setup_ui(parent)

    def setup_ui(self, parent):
        """Create sidebar with scroll"""
        # Main container for sidebar
        sidebar_container = ctk.CTkFrame(parent, width=280, fg_color="transparent")
        sidebar_container.pack(side="left", fill="y", padx=(0, 5), pady=0)
        sidebar_container.pack_propagate(False)

        # Canvas for scrolling
        canvas = ctk.CTkCanvas(sidebar_container, bg=self.app.colors["card_bg"], 
                              highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(sidebar_container, orientation="vertical", 
                                    command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color=self.app.colors["card_bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Function for mouse wheel scrolling
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        # Create sidebar content inside scrollable_frame
        self.create_sidebar_content(scrollable_frame)

    def create_sidebar_content(self, parent):
        """Create sidebar content"""
        # Logo
        self.create_logo_section(parent)

        # Navigation
        self.create_navigation_section(parent)

        # Statistics
        self.create_stats_section(parent)

    def create_logo_section(self, parent):
        """Create logo section"""
        logo_frame = ctk.CTkFrame(parent, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(logo_frame, text="🛡️", font=ctk.CTkFont(size=24)).pack()
        ctk.CTkLabel(logo_frame, text="DDoS Attack Manager",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.app.colors["text_light"]).pack(pady=(5, 0))
        
        # Version and status
        ctk.CTkLabel(logo_frame, text="Advanced SQL Edition",
                     font=ctk.CTkFont(size=10, slant="italic"),
                     text_color=self.app.colors["text_muted"]).pack(pady=(2, 0))

    def create_navigation_section(self, parent):
        """Create navigation section - SIMPLIFIED VERSION"""
        nav_frame = ctk.CTkFrame(parent, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15, pady=(0, 20))

        # Main navigation
        ctk.CTkLabel(nav_frame, text="Main Functions",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        main_nav_buttons = [
            ("🏠 Dashboard", self.app.show_dashboard),
            ("➕ Add Attack", self.app.show_attack_form),
            ("📋 View Data", self.app.show_attacks_list),
        ]

        for text, command in main_nav_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

        separator = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator.pack(fill="x", pady=12)

        # Advanced SQL functions - GROUPED
        ctk.CTkLabel(nav_frame, text="SQL Analysis",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        sql_analysis_buttons = [
            ("📊 Grouping", self.app.show_grouping_tool),
            ("📈 Aggregations", self.app.show_aggregation_tool),
            ("👁️ Views", self.app.show_view_manager),
            ("💾 Materialized Views", self.app.show_materialized_view_manager),
            ("🔄 CTE", self.app.show_cte_builder),
        ]

        for text, command in sql_analysis_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

        separator2 = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator2.pack(fill="x", pady=12)

        # Search and filtering
        ctk.CTkLabel(nav_frame, text="Search & Filtering",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        search_buttons = [
            ("🔍 Text Search", self.app.show_text_search_tool),
            ("🎛️ Filters", self.app.show_subquery_filters),
            ("🔄 Regex Search", self.app.show_regex_search_tool),
            ("🔍 Query Builder", self.app.show_advanced_query_builder),
        ]

        for text, command in search_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

        separator3 = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator3.pack(fill="x", pady=12)

        # Advanced functions
        ctk.CTkLabel(nav_frame, text="Advanced Functions",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        advanced_buttons = [
            ("🔗 JOIN Wizard", self.app.show_join_wizard),
            ("📖 String Functions", self.app.show_string_functions_tool),
            ("🎨 Custom Types", self.app.show_custom_types_manager),
            ("🔧 Database Structure", self.app.show_alter_table_manager),
        ]

        for text, command in advanced_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

        separator4 = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator4.pack(fill="x", pady=12)

        # System
        ctk.CTkLabel(nav_frame, text="System",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 10))

        system_buttons = [
            ("🛠️ Create Schema", self.app.create_schema),
            ("📊 Statistics", self.app.show_database_stats),
            ("📝 Logs", self.app.show_logs),
            ("⚙️ Settings", self.app.show_settings),
        ]

        for text, command in system_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=13),
                                height=35)
            btn.pack(fill="x", pady=2)

    def create_stats_section(self, parent):
        """Create statistics section"""
        stats_frame = ctk.CTkFrame(parent, fg_color="#2a2a4a", corner_radius=8)
        stats_frame.pack(fill="x", padx=15, pady=(0, 20))

        ctk.CTkLabel(stats_frame, text="Statistics",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # Dynamic statistics
        self.stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=15, pady=(0, 10))
        
        self.update_stats()

    def update_stats(self):
        """Update statistics"""
        # Clear old statistics
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        try:
            # Simplified statistics
            stats_items = [
                ("📊 Attacks:", str(len(self.app.attacks)) if hasattr(self.app, 'attacks') else "0"),
                ("⏱️ Time:", datetime.now().strftime("%H:%M")),
                ("🔄 Version:", "SQL Edition"),
            ]
            
            for icon_text, value in stats_items:
                stat_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent", height=25)
                stat_frame.pack(fill="x", pady=2)
                stat_frame.pack_propagate(False)
                
                ctk.CTkLabel(stat_frame, text=icon_text, 
                        font=ctk.CTkFont(size=11),
                        width=80, anchor="w").pack(side="left")
                ctk.CTkLabel(stat_frame, text=value, 
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=self.app.colors["text_light"]).pack(side="right")
                    
        except Exception as e:
            # If error occurred
            error_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            error_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(error_frame, text="Loading error",
                    font=ctk.CTkFont(size=11)).pack(anchor="w")