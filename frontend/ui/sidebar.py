import customtkinter as ctk
from datetime import datetime


class Sidebar:
    def __init__(self, parent, app):
        self.app = app
        self.setup_ui(parent)

    def setup_ui(self, parent):
        """Создание боковой панели"""
        sidebar = ctk.CTkFrame(parent, width=250, fg_color=self.app.colors["card_bg"],
                               corner_radius=0)
        sidebar.pack(side="left", fill="y", padx=(0, 5), pady=0)
        sidebar.pack_propagate(False)

        # Логотип
        self.create_logo_section(sidebar)

        # Навигация
        self.create_navigation_section(sidebar)

        # Статистика
        self.create_stats_section(sidebar)

    def create_logo_section(self, parent):
        """Создание секции с логотипом"""
        logo_frame = ctk.CTkFrame(parent, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(logo_frame, text="🛡️", font=ctk.CTkFont(size=24)).pack()
        ctk.CTkLabel(logo_frame, text="DDoS Manager",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.app.colors["text_light"]).pack(pady=(5, 0))

    def create_navigation_section(self, parent):
        """Создание секции навигации"""
        nav_frame = ctk.CTkFrame(parent, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15, pady=20)

        main_nav_buttons = [
            ("🏠 Main Dashboard", self.app.show_dashboard),
            ("➕ Add Attack", self.app.show_attack_form),
            ("📋 View Table", self.app.show_attacks_list),
        ]

        for text, command in main_nav_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=14),
                                height=40)
            btn.pack(fill="x", pady=2)

        separator = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator.pack(fill="x", pady=10)

        advanced_nav_buttons = [
            ("🔧 DB Structure", self.app.show_alter_table_manager),
            ("🔍 Query Builder", self.app.show_advanced_query_builder),
            ("📖 Text Search", self.app.show_text_search_tool),
            ("🔄 String Functions", self.app.show_string_functions_tool),
            ("🔗 JOIN Wizard", self.app.show_join_wizard),
            # ⭐⭐⭐ ДОБАВЬТЕ ЭТИ ДВЕ НОВЫЕ КНОПКИ ⭐⭐⭐
            ("🔍 Regex Search", self.app.show_regex_search_tool),
            ("📊 Aggregation", self.app.show_aggregation_tool),
        ]

        for text, command in advanced_nav_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=14),
                                height=40)
            btn.pack(fill="x", pady=2)

        separator2 = ctk.CTkFrame(nav_frame, height=1, fg_color="#3a3a5a")
        separator2.pack(fill="x", pady=10)

        new_nav_buttons = [
            ("🎛️ Subquery Filters", self.app.show_subquery_filters),
            ("🎨 Custom Types", self.app.show_custom_types_manager),
        ]

        for text, command in new_nav_buttons:
            btn = ctk.CTkButton(nav_frame, text=text, command=command,
                                fg_color="transparent", hover_color="#2a2a4a",
                                anchor="w", font=ctk.CTkFont(size=14),
                                height=40)
            btn.pack(fill="x", pady=2)

    def create_stats_section(self, parent):
        """Создание секции статистики"""
        stats_frame = ctk.CTkFrame(parent, fg_color="#2a2a4a", corner_radius=8)
        stats_frame.pack(fill="x", padx=15, pady=20)

        ctk.CTkLabel(stats_frame, text="Quick Stats",
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        self.stats_label = ctk.CTkLabel(stats_frame, text="Loading...", justify="left",
                                        font=ctk.CTkFont(size=12))
        self.stats_label.pack(anchor="w", padx=15, pady=(0, 10))
        
    def update_stats(self):
        """Обновление статистики"""
        total_attacks = len(self.app.attacks)
        critical_attacks = len([a for a in self.app.attacks if str(a.get("danger", "")).lower() == "critical"])
        high_freq_attacks = len(
            [a for a in self.app.attacks if str(a.get("frequency", "")).lower() in ["high", "very_high", "continuous"]])

        current_time = datetime.now().strftime("%H:%M")

        stats_text = f"""Total Attacks: {total_attacks}
Critical: {critical_attacks}
High Frequency: {high_freq_attacks}
Updated: {current_time}"""

        self.stats_label.configure(text=stats_text)