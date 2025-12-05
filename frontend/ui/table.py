import customtkinter as ctk
from tkinter import ttk
import threading
from datetime import datetime


class AttackTable:
    def __init__(self, parent, app):
        self.app = app
        self.tree = None
        self.filtered_attacks = []
        self.current_filters = {
            "frequency": [],
            "danger": [],
            "attack_type": [],
            "protocol": []
        }
        self.setup_ui(parent)
        self.refresh_table()

    def setup_ui(self, parent):
        """Создание улучшенной таблицы с фильтрами"""
        main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Заголовок и статистика
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        # Заголовок
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x")

        ctk.CTkLabel(title_frame, text="📋 Attacks Overview",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        # Статистика
        self.stats_label = ctk.CTkLabel(title_frame, text="Loading...",
                                        font=ctk.CTkFont(size=12),
                                        text_color=self.app.colors["text_muted"])
        self.stats_label.pack(side="right")

        # Панель управления
        control_frame = ctk.CTkFrame(main_frame, fg_color=self.app.colors["card_bg"], corner_radius=12)
        control_frame.pack(fill="x", pady=(0, 15))

        control_content = ctk.CTkFrame(control_frame, fg_color="transparent")
        control_content.pack(fill="x", padx=20, pady=15)

        # Левая часть - кнопки действий
        left_controls = ctk.CTkFrame(control_content, fg_color="transparent")
        left_controls.pack(side="left")

        # Кнопка обновления
        refresh_btn = ctk.CTkButton(left_controls, text="🔄 Refresh Data",
                                    command=self.refresh_table,
                                    width=140, height=36,
                                    fg_color=self.app.colors["primary"],
                                    hover_color="#1f4a63",
                                    font=ctk.CTkFont(weight="bold"))
        refresh_btn.pack(side="left", padx=(0, 15))

        # Кнопка удаления выбранного
        self.delete_btn = ctk.CTkButton(left_controls, text="🗑️ Delete Selected",
                                        command=self.delete_selected_attack,
                                        width=140, height=36,
                                        fg_color=self.app.colors["danger"],
                                        hover_color="#e55a5a",
                                        font=ctk.CTkFont(weight="bold"),
                                        state="disabled")
        self.delete_btn.pack(side="left", padx=(0, 15))

        # Правая часть - фильтры
        right_controls = ctk.CTkFrame(control_content, fg_color="transparent")
        right_controls.pack(side="right")

        # Фильтры (API фильтрация)
        filters_frame = ctk.CTkFrame(right_controls, fg_color="transparent")
        filters_frame.pack(side="left")

        # Фильтр по частоте
        ctk.CTkLabel(filters_frame, text="📊 Freq:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        self.frequency_filter = ctk.CTkComboBox(filters_frame,
                                                values=["All", "low", "medium", "high", "very_high", "continuous"],
                                                width=120, height=36,
                                                command=self.on_frequency_filter_change)
        self.frequency_filter.pack(side="left", padx=(0, 10))
        self.frequency_filter.set("All")

        # Фильтр по опасности
        ctk.CTkLabel(filters_frame, text="🛡️ Danger:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        self.danger_filter = ctk.CTkComboBox(filters_frame,
                                             values=["All", "low", "medium", "high", "critical"],
                                             width=100, height=36,
                                             command=self.on_danger_filter_change)
        self.danger_filter.pack(side="left", padx=(0, 10))
        self.danger_filter.set("All")

        # Фильтр по типу атаки
        ctk.CTkLabel(filters_frame, text="🎯 Type:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        self.attack_type_filter = ctk.CTkComboBox(filters_frame,
                                                  values=["All", "volumetric", "protocol", "application",
                                                          "amplification"],
                                                  width=120, height=36,
                                                  command=self.on_attack_type_filter_change)
        self.attack_type_filter.pack(side="left", padx=(0, 10))
        self.attack_type_filter.set("All")

        # Фильтр по протоколу
        ctk.CTkLabel(filters_frame, text="🔗 Protocol:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        self.protocol_filter = ctk.CTkComboBox(filters_frame,
                                               values=["All", "tcp", "udp", "dns", "http", "https", "icmp"],
                                               width=100, height=36,
                                               command=self.on_protocol_filter_change)
        self.protocol_filter.pack(side="left", padx=(0, 10))
        self.protocol_filter.set("All")

        # Контейнер для таблицы
        table_container = ctk.CTkFrame(main_frame, fg_color=self.app.colors["card_bg"], corner_radius=12)
        table_container.pack(fill="both", expand=True)

        # Создание стилизованной таблицы
        self.create_table(table_container)

        # Статус бар
        self.status_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=30)
        self.status_frame.pack(fill="x", pady=(10, 0))
        self.status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready",
                                         text_color=self.app.colors["text_muted"],
                                         font=ctk.CTkFont(size=12))
        self.status_label.pack(side="left")

    def create_table(self, parent):
        """Создание стилизованной таблицы с динамическими колонками"""
        # Кастомный стиль для таблицы
        style = ttk.Style()
        style.theme_use("default")

        # Стиль для обычных строк
        style.configure("Custom.Treeview",
                        background=self.app.colors["card_bg"],
                        foreground=self.app.colors["text_light"],
                        fieldbackground=self.app.colors["card_bg"],
                        borderwidth=0,
                        rowheight=35,
                        font=('Segoe UI', 10))

        # Стиль для заголовков
        style.configure("Custom.Treeview.Heading",
                        background="#2a2a4a",
                        foreground=self.app.colors["text_light"],
                        relief="flat",
                        borderwidth=0,
                        font=('Segoe UI', 11, 'bold'))

        # Стиль для выделенной строки
        style.map("Custom.Treeview",
                  background=[('selected', '#1f6aa5')],
                  foreground=[('selected', 'white')])

        # Базовые колонки + динамические
        base_columns = ("Name", "Frequency", "Danger", "Type", "Source IPs", "Ports", "Targets", "Created")
        
        # Получаем дополнительные колонки из структуры таблицы
        additional_columns = self.get_additional_columns()
        
        # Объединяем все колонки
        all_columns = base_columns + additional_columns
        
        self.tree = ttk.Treeview(parent, columns=all_columns, show="headings", style="Custom.Treeview")

        # Настройка колонок с улучшенными заголовками
        column_config = {
            "Name": {"width": 200, "anchor": "w"},
            "Frequency": {"width": 100, "anchor": "center"},
            "Danger": {"width": 100, "anchor": "center"},
            "Type": {"width": 120, "anchor": "center"},
            "Source IPs": {"width": 180, "anchor": "w"},
            "Ports": {"width": 120, "anchor": "center"},
            "Targets": {"width": 90, "anchor": "center"},
            "Created": {"width": 110, "anchor": "center"}
        }

        # Добавляем конфигурацию для дополнительных колонок
        for col in additional_columns:
            column_config[col] = {"width": 120, "anchor": "center"}

        for col in all_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, **column_config[col])

        # Кастомный скроллбар
        scrollbar = ctk.CTkScrollbar(parent, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Размещение таблицы и скроллбара
        self.tree.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=15)

        # Привязка событий ТОЛЬКО для выбора строки
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    def get_additional_columns(self):
        """Получение списка дополнительных колонок из структуры таблицы"""
        try:
            # Получаем структуру таблицы attacks
            conn = self.app.api_client.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(attacks)")
            columns_info = cursor.fetchall()
            conn.close()
            
            # Базовые колонки, которые уже отображаются
            base_columns_set = {
                'id', 'name', 'frequency', 'danger', 'attack_type', 
                'source_ips', 'affected_ports', 'targets', 'created_at'
            }
            
            # Ищем дополнительные колонки
            additional_columns = []
            for col_info in columns_info:
                col_name = col_info[1]
                if col_name not in base_columns_set:
                    additional_columns.append(col_name)
            
            return tuple(additional_columns)
            
        except Exception as e:
            print(f"Error getting additional columns: {e}")
            return ()

    def on_frequency_filter_change(self, choice):
        """Обработка изменения фильтра по частоте"""
        if choice == "All":
            self.current_filters["frequency"] = []
        else:
            self.current_filters["frequency"] = [choice]

        self.apply_api_filters()

    def on_danger_filter_change(self, choice):
        """Обработка изменения фильтра по опасности"""
        if choice == "All":
            self.current_filters["danger"] = []
        else:
            self.current_filters["danger"] = [choice]

        self.apply_api_filters()

    def on_attack_type_filter_change(self, choice):
        """Обработка изменения фильтра по типу атаки"""
        if choice == "All":
            self.current_filters["attack_type"] = []
        else:
            self.current_filters["attack_type"] = [choice]

        self.apply_api_filters()

    def on_protocol_filter_change(self, choice):
        """Обработка изменения фильтра по протоколу"""
        if choice == "All":
            self.current_filters["protocol"] = []
        else:
            self.current_filters["protocol"] = [choice]

        self.apply_api_filters()

    def apply_api_filters(self):
        """Применение фильтров через API"""
        self.status_label.configure(text="🔄 Applying filters...")

        def filter_thread():
            try:
                # Получаем отфильтрованные данные с сервера
                frequencies = self.current_filters["frequency"]
                danger_levels = self.current_filters["danger"]
                attack_types = self.current_filters["attack_type"]
                protocols = self.current_filters["protocol"]

                if frequencies or danger_levels or attack_types or protocols:
                    # Используем API фильтрацию
                    filtered_attacks = self.app.api_client.filter_attacks_by_multiple(
                        frequencies=frequencies,
                        danger_levels=danger_levels,
                        attack_types=attack_types,
                        protocols=protocols
                    )
                else:
                    # Если фильтры пустые, загружаем все атаки
                    filtered_attacks = self.app.api_client.get_all_attacks()

                # Обновляем данные в основном потоке
                self.app.window.after(0, lambda: self.on_filters_applied(filtered_attacks))

            except Exception as e:
                self.app.window.after(0, lambda: self.show_error(f"Failed to apply filters: {e}"))

        thread = threading.Thread(target=filter_thread)
        thread.daemon = True
        thread.start()

    def on_filters_applied(self, filtered_attacks):
        """Обработка применения фильтров"""
        self.app.attacks = filtered_attacks
        self.update_table_content()
        self.status_label.configure(text=f"✅ Filters applied - {len(filtered_attacks)} attacks")

    def on_row_select(self, event):
        """Обработка выбора строки"""
        selection = self.tree.selection()
        if selection:
            self.delete_btn.configure(state="normal")
        else:
            self.delete_btn.configure(state="disabled")

    def delete_selected_attack(self):
        """Удаление выбранной атаки"""
        selection = self.tree.selection()
        if not selection:
            self.app.show_error("Please select an attack to delete!")
            return

        item = selection[0]
        attack_id = self.tree.item(item)["tags"][0] if self.tree.item(item)["tags"] else None
        attack_name = self.tree.item(item)["values"][0] if self.tree.item(item)["values"] else "Unknown"

        if attack_id:
            self.delete_attack(attack_id, attack_name)

    def refresh_table(self):
        """Обновление таблицы"""
        self.status_label.configure(text="🔄 Loading attacks...")

        def refresh_thread():
            try:
                # Загружаем все атаки (игнорируем текущие фильтры)
                attacks = self.app.api_client.get_all_attacks()
                self.app.window.after(0, lambda: self.on_data_loaded(attacks))
            except Exception as e:
                self.app.window.after(0, lambda: self.show_error(f"Failed to refresh: {e}"))

        thread = threading.Thread(target=refresh_thread)
        thread.daemon = True
        thread.start()

    def on_data_loaded(self, attacks):
        """Обработка загруженных данных"""
        self.app.attacks = attacks
        self.update_table_content()
        self.status_label.configure(text=f"✅ Loaded {len(attacks)} attacks")

    def update_table_content(self):
        """Обновление содержимого таблицы с учетом всех колонок"""
        if not self.tree:
            return

        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.filtered_attacks = self.app.attacks.copy()

        # Получаем список всех колонок
        all_columns = self.tree["columns"]
        base_columns_count = 8  # Количество базовых колонок

        # Заполняем данными с проверкой структуры
        for attack in self.filtered_attacks:
            try:
                # Проверяем что attack - это словарь
                if not isinstance(attack, dict):
                    print(f"Warning: Skipping non-dict attack: {attack}")
                    continue

                # Базовые данные
                name = attack.get("name", "Unknown")
                frequency = attack.get("frequency", "unknown")
                danger = attack.get("danger", "unknown")
                attack_type = attack.get("attack_type", "unknown")

                # Обработка source_ips - теперь это уже список из БД
                source_ips = attack.get("source_ips", [])
                if not isinstance(source_ips, list):
                    source_ips = []
                source_ips_preview = ", ".join(source_ips[:2])
                if len(source_ips) > 2:
                    source_ips_preview += "..."

                # Обработка affected_ports - теперь это уже список из БД
                affected_ports = attack.get("affected_ports", [])
                if not isinstance(affected_ports, list):
                    affected_ports = []
                ports_preview = ", ".join(map(str, affected_ports[:3]))
                if len(affected_ports) > 3:
                    ports_preview += "..."

                # Обработка targets
                targets = attack.get("targets", [])
                if not isinstance(targets, list):
                    targets = []
                targets_count = len(targets)

                created_date = "Unknown"
                created_at = attack.get("created_at", "")
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            if "T" in created_at:
                                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            else:
                                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                            created_date = dt.strftime("%m/%d/%Y")
                        else:
                            created_date = str(created_at)[:10] if created_at else "Unknown"
                    except Exception as date_error:
                        created_date = str(created_at)[:10] if created_at else "Unknown"

                row_values = [
                    name,
                    frequency.title(),
                    danger.title(),
                    attack_type.title(),
                    source_ips_preview,
                    ports_preview,
                    f"🎯 {targets_count}",
                    created_date
                ]

                additional_columns = all_columns[base_columns_count:]
                for col in additional_columns:
                    value = attack.get(col, "")
                    if isinstance(value, list):
                        value = ", ".join(map(str, value[:2])) + ("..." if len(value) > 2 else "")
                    elif isinstance(value, dict):
                        value = str(value)
                    elif value is None:
                        value = ""
                    row_values.append(str(value))

                item = self.tree.insert("", "end", values=tuple(row_values), 
                                      tags=(attack.get("id", ""),))

                danger_lower = str(danger).lower()
                if danger_lower == "critical":
                    self.tree.set(item, "Danger", "🔴 Critical")
                elif danger_lower == "high":
                    self.tree.set(item, "Danger", "🟠 High")
                elif danger_lower == "medium":
                    self.tree.set(item, "Danger", "🟡 Medium")
                elif danger_lower == "low":
                    self.tree.set(item, "Danger", "🟢 Low")

            except Exception as e:
                print(f"Error processing attack data: {e}")
                print(f"Problematic attack data: {attack}")
                continue

        self.update_stats()
        self.status_label.configure(text=f"✅ Loaded {len(self.filtered_attacks)} attacks")
        self.delete_btn.configure(state="disabled")

    def update_stats(self):
        """Обновление статистики"""
        total = len(self.app.attacks)
        critical = len([a for a in self.app.attacks if str(a.get("danger", "")).lower() == "critical"])
        high_freq = len([a for a in self.app.attacks if str(a.get("frequency", "")).lower() in ["high", "very_high"]])

        self.stats_label.configure(text=f"📊 Total: {total} | 🔴 Critical: {critical} | 🚀 High Freq: {high_freq}")

    def delete_attack(self, attack_id, attack_name):
        """Удаление атаки"""
        import tkinter.messagebox as mb

        # Диалог подтверждения с улучшенным дизайном
        result = mb.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the attack?\n\n"
            f"📛 Name: {attack_name}\n"
            f"⚠️ This action cannot be undone!",
            icon='warning'
        )

        if result:
            def delete_thread():
                try:
                    self.app.api_client.delete_attack(attack_id)
                    self.app.window.after(0, lambda: self.on_attack_deleted(attack_name))
                except Exception as e:
                    self.app.window.after(0, lambda: self.show_error(f"Failed to delete: {e}"))

            self.status_label.configure(text="🗑️ Deleting attack...")
            thread = threading.Thread(target=delete_thread)
            thread.daemon = True
            thread.start()

    def on_attack_deleted(self, attack_name):
        """Обработка успешного удаления"""
        self.app.show_success(f"Attack '{attack_name}' was successfully deleted!")

        # ОБНОВЛЯЕМ СТАТИСТИКУ В ДАШБОРДЕ И БОКОВОЙ ПАНЕЛИ
        self.app.refresh_attacks()  # Это обновит данные во всем приложении

        self.refresh_table()

    def show_error(self, message):
        """Показ ошибки"""
        self.status_label.configure(text="❌ Error")
        self.app.show_error(message)