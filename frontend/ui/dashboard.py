import customtkinter as ctk


class Dashboard:
    def __init__(self, parent, app):
        self.app = app
        self.setup_ui(parent)

    def setup_ui(self, parent):
        """Создание главной страницы с тремя кнопками"""
        dashboard_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dashboard_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_frame = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 40))

        ctk.CTkLabel(title_frame, text="DDoS Attack Manager",
                     font=ctk.CTkFont(size=32, weight="bold")).pack()

        ctk.CTkLabel(title_frame, text="Manage and monitor DDoS attacks",
                     font=ctk.CTkFont(size=16),
                     text_color=self.app.colors["text_muted"]).pack(pady=(10, 0))

        # Карточки с действиями
        actions_frame = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        actions_frame.pack(fill="both", expand=True)

        # Создаем 3 колонки
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)
        actions_frame.columnconfigure(2, weight=1)
        actions_frame.rowconfigure(0, weight=1)

        self.create_action_card(actions_frame, 0, 0, "📊", "Initialize Database",
                                "Create necessary tables in the database",
                                self.initialize_database)
        # Карточка 2: Добавление атаки
        self.create_action_card(actions_frame, 0, 1, "➕", "Add New Attack",
                                "Create and register a new DDoS attack",
                                self.app.show_attack_form)

        # Карточка 3: Просмотр таблицы
        self.create_action_card(actions_frame, 0, 2, "📋", "View Attacks",
                                "Browse and manage all registered attacks",
                                self.app.show_attacks_list)

    def create_action_card(self, parent, row, col, emoji, title, description, command):
        """Создание карточки действия"""
        card = ctk.CTkFrame(parent, fg_color=self.app.colors["card_bg"],
                            corner_radius=12, height=200)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=25)

        # Эмодзи
        ctk.CTkLabel(content, text=emoji, font=ctk.CTkFont(size=40)).pack(pady=(0, 15))

        ctk.CTkLabel(content, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack()

        desc_label = ctk.CTkLabel(content, text=description,
                                  text_color=self.app.colors["text_muted"],
                                  wraplength=200, justify="center")
        desc_label.pack(pady=10)

        ctk.CTkButton(content, text="Open", command=command,
                      fg_color=self.app.colors["primary"]).pack(side="bottom", pady=(15, 0))

    def initialize_database(self):
        """Инициализация базы данных"""
        import threading
        def init_thread():
            try:
                print("Starting database initialization...")  
                result = self.app.api_client.initialize_database()
                print(f"Initialization result: {result}")
                self.app.window.after(0, lambda: self.app.show_success("Database initialized successfully!"))
            except Exception as e:
                print(f"Initialization error: {e}") 
                self.app.window.after(0, lambda: self.app.show_error(f"Failed to initialize database: {e}"))

        thread = threading.Thread(target=init_thread)
        thread.daemon = True
        thread.start()