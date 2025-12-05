import customtkinter as ctk
import threading
from dataclasses import dataclass, field
from typing import List
import re


# Временный класс Target прямо в forms.py
@dataclass
class Target:
    target_ip: str = ""
    target_domain: str = ""
    port: int = 80
    protocol: str = "tcp"
    tags: List[str] = field(default_factory=list)


class AttackForm:
    def __init__(self, parent, app):
        self.app = app
        self.target_fields = []
        self.additional_fields = {}  # Словарь для хранения дополнительных полей
        self.setup_ui(parent)
        self.load_additional_columns()  # Загружаем дополнительные колонки

    def setup_ui(self, parent):
        """Создание формы ввода"""
        form_container = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_basic_info_section(form_container)

        # Источники и порты
        self.create_source_section(form_container)

        # Цели
        self.create_targets_section(form_container)

        # Стратегии защиты
        self.create_mitigation_section(form_container)

        # Дополнительные поля (будут созданы динамически)
        self.additional_fields_container = ctk.CTkFrame(form_container, fg_color="transparent")
        self.additional_fields_container.pack(fill="x", padx=5, pady=8)

        # Кнопка создания
        self.create_action_button(form_container)

        # Добавляем первую цель по умолчанию
        self.add_target_field()

    def load_additional_columns(self):
        """Загрузка дополнительных колонок из структуры таблицы"""
        try:
            conn = self.app.api_client.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(attacks)")
            columns_info = cursor.fetchall()
            conn.close()
            
            base_columns_set = {
                'id', 'name', 'frequency', 'danger', 'attack_type', 
                'source_ips', 'affected_ports', 'targets', 'created_at',
                'mitigation_strategies', "updated_at"
            }
            
            # Ищем дополнительные колонки
            additional_columns = []
            for col_info in columns_info:
                col_name = col_info[1]
                col_type = col_info[2].upper()
                if col_name not in base_columns_set:
                    additional_columns.append((col_name, col_type))
            
            # Создаем поля для дополнительных колонок
            self.create_additional_fields(additional_columns)
            
        except Exception as e:
            print(f"Error loading additional columns: {e}")

    def create_additional_fields(self, additional_columns):
        """Создание полей для дополнительных колонок"""
        if not additional_columns:
            return

        # Создаем карточку для дополнительных полей
        card = self.create_card(self.additional_fields_container, "📊 Additional Fields")
        
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=15)

        self.additional_fields = {}  # Очищаем словарь

        for i, (col_name, col_type) in enumerate(additional_columns):
            row = i % 3  # 3 колонки в ряду
            col = i // 3

            # Создаем фрейм для поля если нужно
            if row == 0:
                field_row = ctk.CTkFrame(grid, fg_color="transparent")
                field_row.pack(fill="x", pady=5)

            # Название поля
            label = ctk.CTkLabel(field_row, text=f"{col_name}:", font=ctk.CTkFont(weight="bold"))
            label.pack(side="left", padx=(20 if row > 0 else 0, 5), pady=5)

            # Создаем поле ввода в зависимости от типа
            field = self.create_field_by_type(field_row, col_type, col_name)
            field.pack(side="left", padx=5, pady=5, fill="x", expand=True)

            # Сохраняем поле в словарь
            self.additional_fields[col_name] = {
                'widget': field,
                'type': col_type,
                'label': label
            }

    def create_field_by_type(self, parent, col_type, col_name):
        """Создание поля ввода в зависимости от типа колонки"""
        col_type_upper = col_type.upper()
        
        # Определяем тип поля по типу колонки в БД
        if any(text_type in col_type_upper for text_type in ['VARCHAR', 'TEXT', 'CHAR']):
            # Текстовые поля
            if '255' in col_type or 'TEXT' in col_type_upper:
                return ctk.CTkEntry(parent, placeholder_text=f"Enter {col_name}...", width=200)
            else:
                return ctk.CTkEntry(parent, placeholder_text=f"Enter {col_name}...", width=200)
                
        elif any(num_type in col_type_upper for num_type in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT']):
            # Числовые поля
            return ctk.CTkEntry(parent, placeholder_text=f"Enter number...", width=120)
            
        elif 'BOOLEAN' in col_type_upper or 'BOOL' in col_type_upper:
            # Булевы значения
            var = ctk.BooleanVar()
            return ctk.CTkCheckBox(parent, text="", variable=var, width=30)
            
        elif any(float_type in col_type_upper for float_type in ['FLOAT', 'DOUBLE', 'DECIMAL', 'REAL']):
            # Числа с плавающей точкой
            return ctk.CTkEntry(parent, placeholder_text=f"Enter decimal...", width=120)
            
        elif 'JSON' in col_type_upper:
            # JSON поля
            return ctk.CTkEntry(parent, placeholder_text='{"key": "value"}', width=200)
            
        elif 'DATE' in col_type_upper or 'TIME' in col_type_upper:
            # Дата/время
            return ctk.CTkEntry(parent, placeholder_text="YYYY-MM-DD", width=120)
            
        else:
            # По умолчанию текстовое поле
            return ctk.CTkEntry(parent, placeholder_text=f"Enter {col_name}...", width=200)

    def create_basic_info_section(self, parent):
        """Секция основной информации с ограниченными типами"""
        card = self.create_card(parent, "🎯 Basic Information")

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=15)

        # Название атаки
        ctk.CTkLabel(grid, text="Attack Name:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=8,
                                                                                      sticky="w")
        self.name_entry = ctk.CTkEntry(grid, width=300, placeholder_text="Enter attack name (max 30 chars)...")
        self.name_entry.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        # Добавляем валидацию для имени
        self.name_entry.bind('<KeyRelease>', self.validate_name_field)

        # Частота
        ctk.CTkLabel(grid, text="Frequency:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=20, pady=8,
                                                                                    sticky="w")
        self.frequency_combo = ctk.CTkComboBox(grid, values=self.app.frequency_levels, width=140)
        self.frequency_combo.grid(row=0, column=3, padx=5, pady=8, sticky="w")
        self.frequency_combo.set("high")

        # Уровень опасности (только разрешенные значения)
        ctk.CTkLabel(grid, text="Danger Level:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=5, pady=8,
                                                                                       sticky="w")
        self.danger_combo = ctk.CTkComboBox(grid, values=self.app.danger_levels, width=140)
        self.danger_combo.grid(row=1, column=1, padx=5, pady=8, sticky="w")
        self.danger_combo.set("high")

        # Тип атаки (только разрешенные значения)
        ctk.CTkLabel(grid, text="Attack Type:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=2, padx=20, pady=8,
                                                                                      sticky="w")
        self.attack_type_combo = ctk.CTkComboBox(grid, values=self.app.attack_types, width=140)
        self.attack_type_combo.grid(row=1, column=3, padx=5, pady=8, sticky="w")
        self.attack_type_combo.set("amplification")  # Значение по умолчанию из разрешенных

    def create_source_section(self, parent):
        """Секция источников"""
        card = self.create_card(parent, "🌐 Source Configuration")

        columns = ctk.CTkFrame(card, fg_color="transparent")
        columns.pack(fill="x", padx=15, pady=15)

        # Source IPs
        left_col = ctk.CTkFrame(columns, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_col, text="Source IP Addresses:", font=ctk.CTkFont(weight="bold")).pack(anchor="w",
                                                                                                  pady=(0, 5))
        ctk.CTkLabel(left_col, text="One IP address per line", font=ctk.CTkFont(size=12),
                     text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 8))

        self.source_ips_text = ctk.CTkTextbox(left_col, height=100, border_width=1, fg_color="#2a2a3a")
        self.source_ips_text.pack(fill="x", pady=5)
        self.source_ips_text.insert("1.0", "8.8.8.8\n1.1.1.1\n9.9.9.9")

        # Ports
        right_col = ctk.CTkFrame(columns, fg_color="transparent")
        right_col.pack(side="right", fill="x", expand=True, padx=(10, 0))

        ctk.CTkLabel(right_col, text="Affected Ports:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(right_col, text="Comma-separated port numbers (1-65535)", font=ctk.CTkFont(size=12),
                     text_color=self.app.colors["text_muted"]).pack(anchor="w", pady=(0, 8))

        self.ports_entry = ctk.CTkEntry(right_col, placeholder_text="53, 80, 443, 8080")
        self.ports_entry.pack(fill="x", pady=5)
        self.ports_entry.insert(0, "53, 443, 80")
        # Добавляем валидацию для портов
        self.ports_entry.bind('<KeyRelease>', self.validate_ports_field)

    def create_targets_section(self, parent):
        """Секция целей (оригинальный интерфейс)"""
        card = self.create_card(parent, "🎯 Attack Targets")

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(header, text="Target Servers & Services", font=ctk.CTkFont(weight="bold")).pack(side="left")

        # Кнопка добавления цели
        add_btn = ctk.CTkButton(header, text="+ Add Target", width=100, height=32,
                                command=self.add_target_field)
        add_btn.pack(side="right")

        self.targets_container = ctk.CTkFrame(card, fg_color="transparent")
        self.targets_container.pack(fill="x", padx=15, pady=(0, 15))

    def create_mitigation_section(self, parent):
        """Секция стратегий защиты"""
        card = self.create_card(parent, "🛡️ Mitigation Strategies")

        ctk.CTkLabel(card, text="Defense Mechanisms", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15,
                                                                                            pady=(15, 5))
        ctk.CTkLabel(card, text="One strategy per line", font=ctk.CTkFont(size=12),
                     text_color=self.app.colors["text_muted"]).pack(anchor="w", padx=15, pady=(0, 8))

        self.mitigation_text = ctk.CTkTextbox(card, height=120, border_width=1, fg_color="#2a2a3a")
        self.mitigation_text.pack(fill="x", padx=15, pady=(0, 15))
        self.mitigation_text.insert("1.0",
                                    "DNS Response Rate Limiting\nAnycast DNS Implementation\nSource IP Validation\nTraffic Filtering")

    def create_action_button(self, parent):
        """Кнопка создания атаки"""
        card = self.create_card(parent, "")

        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=15)

        self.create_button = ctk.CTkButton(button_frame, text="🚀 Create Attack",
                                           command=self.create_attack, height=40,
                                           fg_color=self.app.colors["success"],
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self.create_button.pack(side="left", padx=5)

    def create_card(self, parent, title):
        """Создание карточки"""
        card = ctk.CTkFrame(parent, fg_color=self.app.colors["card_bg"], corner_radius=12)
        card.pack(fill="x", padx=5, pady=8)

        if title:
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=15, pady=15)
            ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")

            separator = ctk.CTkFrame(card, height=1, fg_color="#3a3a5a")
            separator.pack(fill="x", padx=15)

        return card

    def add_target_field(self):
        """Добавление поля для ввода target (оригинальная реализация)"""
        target_card = ctk.CTkFrame(self.targets_container, fg_color="#2a2a4a", corner_radius=8)
        target_card.pack(fill="x", pady=8)

        target_index = len(self.target_fields)

        # Заголовок target с кнопкой удаления
        target_header = ctk.CTkFrame(target_card, fg_color="transparent")
        target_header.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(target_header, text=f"🎯 Target #{target_index + 1}",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")

        # Кнопка удаления (показываем для всех целей)
        remove_btn = ctk.CTkButton(target_header, text="🗑️ Remove", width=80, height=24,
                                   command=lambda idx=target_card: self.remove_target_field(idx),
                                   fg_color=self.app.colors["danger"], hover_color="#e55a5a")
        remove_btn.pack(side="right")

        # Поля для target
        fields_frame = ctk.CTkFrame(target_card, fg_color="transparent")
        fields_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Target IP
        ctk.CTkLabel(fields_frame, text="Target IP:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        target_ip_entry = ctk.CTkEntry(fields_frame, placeholder_text="192.168.1.1 (max 255 chars)", width=180)
        target_ip_entry.grid(row=0, column=1, padx=5, pady=5)
        # Валидация IP в реальном времени
        target_ip_entry.bind('<KeyRelease>', lambda e, field=target_ip_entry: self.validate_target_ip_field(field))

        # Target Domain
        ctk.CTkLabel(fields_frame, text="Domain:").grid(row=0, column=2, padx=15, pady=5, sticky="w")
        target_domain_entry = ctk.CTkEntry(fields_frame, placeholder_text="example.com (max 255 chars)", width=180)
        target_domain_entry.grid(row=0, column=3, padx=5, pady=5)
        # Валидация домена в реальном времени
        target_domain_entry.bind('<KeyRelease>',
                                 lambda e, field=target_domain_entry: self.validate_target_domain_field(field))

        # Port
        ctk.CTkLabel(fields_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        port_entry = ctk.CTkEntry(fields_frame, placeholder_text="80 (1-65535)", width=80)
        port_entry.grid(row=1, column=1, padx=5, pady=5)
        port_entry.insert(0, "80")
        # Валидация порта в реальном времени
        port_entry.bind('<KeyRelease>', lambda e, field=port_entry: self.validate_target_port_field(field))

        # Protocol
        ctk.CTkLabel(fields_frame, text="Protocol:").grid(row=1, column=2, padx=15, pady=5, sticky="w")
        protocol_combo = ctk.CTkComboBox(fields_frame, values=self.app.protocols, width=120)
        protocol_combo.grid(row=1, column=3, padx=5, pady=5)
        protocol_combo.set("tcp")

        # Tags
        ctk.CTkLabel(fields_frame, text="Tags:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        tags_entry = ctk.CTkEntry(fields_frame, placeholder_text="web-server,critical,production", width=300)
        tags_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        target_data = {
            'frame': target_card,
            'target_ip': target_ip_entry,
            'target_domain': target_domain_entry,
            'port': port_entry,
            'protocol': protocol_combo,
            'tags': tags_entry
        }

        self.target_fields.append(target_data)

    def get_additional_fields_data(self):
        """Получение данных из дополнительных полей"""
        additional_data = {}
        
        for col_name, field_info in self.additional_fields.items():
            widget = field_info['widget']
            field_type = field_info['type'].upper()
            
            if isinstance(widget, ctk.CTkEntry):
                value = widget.get().strip()
                
                
                if not value:
                    continue  
                if any(num_type in field_type for num_type in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT']):
                    if value.isdigit():
                        additional_data[col_name] = int(value)
                    elif value:
                        additional_data[col_name] = 0  # Значение по умолчанию для чисел
                    else:
                        additional_data[col_name] = None
                        
                elif any(float_type in field_type for float_type in ['FLOAT', 'DOUBLE', 'DECIMAL', 'REAL']):
                    try:
                        additional_data[col_name] = float(value) if value else None
                    except ValueError:
                        additional_data[col_name] = 0.0
                        
                elif 'BOOLEAN' in field_type or 'BOOL' in field_type:
                    additional_data[col_name] = bool(value) if value else False
                    
                else:
                    # Текстовые и другие типы
                    additional_data[col_name] = value if value else None
                    
            elif isinstance(widget, ctk.CTkCheckBox):
                # Для чекбоксов получаем значение переменной
                additional_data[col_name] = widget.get()
                
        return additional_data

    def validate_name_field(self, event):
        """Валидация поля имени в реальном времени"""
        name = self.name_entry.get().strip()
        if len(name) > 30:
            self.name_entry.configure(border_color="red")
        else:
            self.name_entry.configure(border_color=self.app.colors["primary"])

    def validate_ports_field(self, event):
        """Валидация поля портов в реальном времени"""
        ports_text = self.ports_entry.get().strip()
        if ports_text:
            ports_list = [port.strip() for port in ports_text.split(",") if port.strip()]
            for port_str in ports_list:
                if port_str and (not port_str.isdigit() or int(port_str) < 1 or int(port_str) > 65535):
                    self.ports_entry.configure(border_color="red")
                    return
        self.ports_entry.configure(border_color=self.app.colors["primary"])

    def validate_target_ip_field(self, field):
        """Валидация поля IP таргета в реальном времени"""
        ip = field.get().strip()
        if ip and len(ip) > 255:
            field.configure(border_color="red")
        else:
            field.configure(border_color=self.app.colors["primary"])

    def validate_target_domain_field(self, field):
        """Валидация поля домена таргета в реальном времени"""
        domain = field.get().strip()
        if domain and len(domain) > 255:
            field.configure(border_color="red")
        else:
            field.configure(border_color=self.app.colors["primary"])

    def validate_target_port_field(self, field):
        """Валидация поля порта таргета в реальном времени"""
        port = field.get().strip()
        if port:
            if not port.isdigit() or int(port) < 1 or int(port) > 65535:
                field.configure(border_color="red")
            else:
                field.configure(border_color=self.app.colors["primary"])
        else:
            field.configure(border_color=self.app.colors["primary"])

    def remove_target_field(self, target_frame):
        """Удаление поля target"""
        if len(self.target_fields) > 0:
            for i, target_data in enumerate(self.target_fields):
                if target_data['frame'] == target_frame:
                    self.target_fields.pop(i)
                    target_frame.destroy()
                    break

            # Renumber remaining targets
            for i, target_data in enumerate(self.target_fields):
                header_frame = target_data['frame'].winfo_children()[0]
                header_label = header_frame.winfo_children()[0]
                header_label.configure(text=f"🎯 Target #{i + 1}")

    def validate_form(self):
        """Валидация всех полей формы"""
        # Валидация имени атаки
        name = self.name_entry.get().strip()
        if not name:
            self.app.show_error("Please enter attack name!")
            return False
        if len(name) > 30:
            self.app.show_error("Attack name must be less than 30 characters!")
            return False

        # Валидация портов
        ports_text = self.ports_entry.get().strip()
        if ports_text:
            ports_list = [port.strip() for port in ports_text.split(",") if port.strip()]
            for port_str in ports_list:
                if not port_str.isdigit():
                    self.app.show_error(f"Port '{port_str}' must be a valid number!")
                    return False
                port_num = int(port_str)
                if port_num < 1 or port_num > 65535:
                    self.app.show_error(f"Port '{port_str}' must be between 1 and 65535!")
                    return False

        # Валидация целей
        targets = self.get_targets_data()
        if not targets:
            self.app.show_error("Please add at least one target!")
            return False

        for i, target in enumerate(targets):
            # Валидация IP
            if target.target_ip and len(target.target_ip) > 255:
                self.app.show_error(f"Target #{i + 1} IP address must be less than 255 characters!")
                return False

            # Валидация домена
            if target.target_domain and len(target.target_domain) > 255:
                self.app.show_error(f"Target #{i + 1} domain must be less than 255 characters!")
                return False

            # Валидация порта
            if target.port < 1 or target.port > 65535:
                self.app.show_error(f"Target #{i + 1} port must be between 1 and 65535!")
                return False

            # Проверка что указан хотя бы IP или домен
            if not target.target_ip and not target.target_domain:
                self.app.show_error(f"Target #{i + 1} must have either IP address or domain!")
                return False

        # Валидация source IPs
        source_ips = [ip.strip() for ip in self.source_ips_text.get("1.0", "end-1c").split("\n") if ip.strip()]
        if not source_ips:
            self.app.show_error("Please add at least one source IP!")
            return False

        return True

    def get_targets_data(self):
        """Получение данных о targets из формы"""
        targets = []
        for target_data in self.target_fields:
            target_ip = target_data['target_ip'].get().strip()
            target_domain = target_data['target_domain'].get().strip()
            port = target_data['port'].get().strip()
            protocol = target_data['protocol'].get()
            tags_str = target_data['tags'].get().strip()

            # Создаем target если есть хотя бы IP или домен
            if target_ip or target_domain:
                # Валидация порта перед созданием target
                port_num = 80
                if port:
                    if port.isdigit():
                        port_num = int(port)
                    else:
                        # Если порт невалидный, используем значение по умолчанию
                        port_num = 80

                target = Target(
                    target_ip=target_ip,
                    target_domain=target_domain,
                    port=port_num,
                    protocol=protocol,
                    tags=[tag.strip() for tag in tags_str.split(",") if tag.strip()]
                )
                targets.append(target)

        return targets

    def create_attack(self):
        """Создание атаки через API"""
        # Валидация формы перед отправкой
        if not self.validate_form():
            return

        name = self.name_entry.get().strip()

        def create_attack_thread():
            try:
                # Сбор данных из формы
                source_ips = [ip.strip() for ip in self.source_ips_text.get("1.0", "end-1c").split("\n") if ip.strip()]
                ports = [int(port.strip()) for port in self.ports_entry.get().split(",") if port.strip().isdigit()]
                mitigation_strategies = [strat.strip() for strat in
                                         self.mitigation_text.get("1.0", "end-1c").split("\n") if strat.strip()]
                targets = self.get_targets_data()
                
                # Получаем данные из дополнительных полей
                additional_data = self.get_additional_fields_data()

                # Подготовка данных для API
                attack_data = {
                    "name": name,
                    "frequency": self.frequency_combo.get(),
                    "danger": self.danger_combo.get(),
                    "attack_type": self.attack_type_combo.get(),
                    "source_ips": source_ips,
                    "affected_ports": ports,
                    "mitigation_strategies": mitigation_strategies,
                    "targets": [target.__dict__ for target in targets]
                }
                
                # Добавляем данные из дополнительных полей
                attack_data.update(additional_data)

                # Отправка на сервер
                result = self.app.api_client.create_attack(attack_data)
                self.app.window.after(0, lambda attack_name=name: self.on_attack_created(attack_name))

            except ValueError as e:
                error_msg = str(e)
                self.app.window.after(0, lambda msg=error_msg: self.app.show_error(f"Invalid input: {msg}"))
            except Exception as e:
                error_msg = str(e)
                self.app.window.after(0, lambda msg=error_msg: self.app.show_error(f"Failed to create attack: {msg}"))

        thread = threading.Thread(target=create_attack_thread)
        thread.daemon = True
        thread.start()

    def on_attack_created(self, name):
        """Обработка успешного создания"""
        self.app.show_success(f"Attack '{name}' created successfully!")
        self.clear_form()
        self.app.refresh_attacks()

    def clear_form(self):
        """Очистка формы"""
        self.name_entry.delete(0, "end")
        self.name_entry.configure(border_color=self.app.colors["primary"])

        self.frequency_combo.set("high")
        self.danger_combo.set("high")
        self.attack_type_combo.set("amplification")

        self.source_ips_text.delete("1.0", "end")
        self.source_ips_text.insert("1.0", "8.8.8.8\n1.1.1.1\n9.9.9.9")

        self.ports_entry.delete(0, "end")
        self.ports_entry.insert(0, "53, 443, 80")
        self.ports_entry.configure(border_color=self.app.colors["primary"])

        self.mitigation_text.delete("1.0", "end")
        self.mitigation_text.insert("1.0",
                                    "DNS Response Rate Limiting\nAnycast DNS Implementation\nSource IP Validation\nTraffic Filtering")

        # Очистка targets (оставляем один пустой)
        for target_data in self.target_fields:
            target_data['frame'].destroy()
        self.target_fields = []
        self.add_target_field()
        
        for field_info in self.additional_fields.values():
            widget = field_info['widget']
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
            elif isinstance(widget, ctk.CTkCheckBox):
                widget.deselect()