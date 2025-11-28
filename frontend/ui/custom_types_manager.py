import customtkinter as ctk
from tkinter import messagebox
import json

class CustomTypesManager:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса менеджера типов"""
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Custom Data Types Manager",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Кнопки создания типов
        self.create_type_buttons(main_frame)

        # Список существующих типов
        self.create_types_list(main_frame)

        # Загрузка существующих типов
        self.load_custom_types()

    def create_type_buttons(self, parent):
        """Создание кнопок для создания типов"""
        buttons_frame = ctk.CTkFrame(parent)
        buttons_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(buttons_frame, text="Create New Type",
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        button_subframe = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        button_subframe.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(button_subframe, text="Create ENUM Type",
                     command=self.create_enum_type,
                     fg_color=self.app.colors["success"]).pack(side="left", padx=5)

        ctk.CTkButton(button_subframe, text="Create Composite Type",
                     command=self.create_composite_type,
                     fg_color=self.app.colors["primary"]).pack(side="left", padx=5)

        ctk.CTkButton(button_subframe, text="Refresh Types",
                     command=self.load_custom_types,
                     fg_color=self.app.colors["warning"]).pack(side="left", padx=5)

    def create_types_list(self, parent):
        """Создание списка существующих типов"""
        list_frame = ctk.CTkFrame(parent)
        list_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(list_frame, text="Existing Custom Types",
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        # Таблица типов
        columns = ["Name", "Type", "Values/Fields", "Actions"]
        self.types_tree = ctk.CTkFrame(list_frame)
        self.types_tree.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Заголовки колонок
        header_frame = ctk.CTkFrame(self.types_tree)
        header_frame.pack(fill="x")
        
        for i, col in enumerate(columns):
            label = ctk.CTkLabel(header_frame, text=col, font=ctk.CTkFont(weight="bold"))
            label.pack(side="left", padx=2, fill="x", expand=True)

        # Контейнер для данных
        self.types_container = ctk.CTkScrollableFrame(self.types_tree, height=200)
        self.types_container.pack(fill="both", expand=True)

    def create_enum_type(self):
        """Создание ENUM типа"""
        dialog = EnumTypeDialog(self.parent, self.app)
        self.app.window.wait_window(dialog)
        
        if dialog.result:
            try:
                result = self.app.api_client.create_custom_type(
                    dialog.result['name'], 'ENUM', dialog.result['values']
                )
                if result.get('success'):
                    messagebox.showinfo("Success", f"ENUM type '{dialog.result['name']}' created successfully!")
                    self.load_custom_types()
                else:
                    messagebox.showerror("Error", f"Failed to create type: {result.get('error')}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create ENUM type: {e}")

    def create_composite_type(self):
        """Создание составного типа"""
        dialog = CompositeTypeDialog(self.parent, self.app)
        
        self.app.window.wait_window(dialog)
        
        if dialog.result:
            try:
                result = self.app.api_client.create_custom_type(
                    dialog.result['name'], 'COMPOSITE', dialog.result['fields']
                )
                if result.get('success'):
                    messagebox.showinfo("Success", f"Composite type '{dialog.result['name']}' created successfully!")
                    self.load_custom_types()
                else:
                    messagebox.showerror("Error", f"Failed to create type: {result.get('error')}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create composite type: {e}")

    def load_custom_types(self):
        """Загрузка пользовательских типов из БД"""
        try:
            # Очищаем контейнер
            for widget in self.types_container.winfo_children():
                widget.destroy()

            # Получаем типы из БД
            types = self.app.api_client.get_custom_types()
            
            if not types:
                no_data_label = ctk.CTkLabel(self.types_container, text="No custom types found")
                no_data_label.pack(pady=20)
                return

            # Отображаем типы
            for type_data in types:
                self.add_type_to_list(type_data)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load custom types: {e}")

    def add_type_to_list(self, type_data):
        """Добавление типа в список"""
        row_frame = ctk.CTkFrame(self.types_container)
        row_frame.pack(fill="x", pady=2)

        # Название
        name_label = ctk.CTkLabel(row_frame, text=type_data['name'])
        name_label.pack(side="left", padx=2, fill="x", expand=True)

        # Тип
        type_label = ctk.CTkLabel(row_frame, text=type_data['type'])
        type_label.pack(side="left", padx=2, fill="x", expand=True)

        # Значения/Поля
        values_text = json.dumps(type_data['values']) if isinstance(type_data['values'], (list, dict)) else str(type_data['values'])
        values_label = ctk.CTkLabel(row_frame, text=values_text[:50] + "..." if len(values_text) > 50 else values_text)
        values_label.pack(side="left", padx=2, fill="x", expand=True)

        # Кнопки действий
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.pack(side="left", padx=2)

        ctk.CTkButton(actions_frame, text="Delete", width=60,
                     command=lambda: self.delete_type(type_data['id']),
                     fg_color=self.app.colors["danger"]).pack(side="left", padx=1)

    def delete_type(self, type_id):
        """Удаление типа"""
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this type?"):
            try:
                result = self.app.api_client.delete_custom_type(type_id)
                if result.get('success'):
                    messagebox.showinfo("Success", "Type deleted successfully!")
                    self.load_custom_types()
                else:
                    messagebox.showerror("Error", f"Failed to delete type: {result.get('error')}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete type: {e}")

class EnumTypeDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.result = None
        self.title("Create ENUM Type")
        self.geometry("400x300")
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="ENUM Type Name:").pack(anchor="w", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="e.g., attack_status")
        self.name_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(main_frame, text="ENUM Values (one per line):").pack(anchor="w", pady=(0, 5))
        self.values_text = ctk.CTkTextbox(main_frame, height=120)
        self.values_text.pack(fill="both", expand=True, pady=(0, 15))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(button_frame, text="Create", command=self.on_create).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)

    def on_create(self):
        """Обработка создания ENUM типа"""
        
        name = self.name_entry.get().strip()
        values_text = self.values_text.get("1.0", "end-1c").strip()

        if not name:
            messagebox.showerror("Error", "Please enter a name for the ENUM type")
            return

        if not values_text:
            messagebox.showerror("Error", "Please enter at least one value for the ENUM")
            return

        values = [v.strip() for v in values_text.split('\n') if v.strip()]
        
        self.result = {
            'name': name,
            'values': values
        }
        self.destroy()

class CompositeTypeDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.result = None
        self.title("Create Composite Type")
        self.geometry("500x400")
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Composite Type Name:").pack(anchor="w", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="e.g., network_address")
        self.name_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(main_frame, text="Fields (field_name:field_type, one per line):").pack(anchor="w", pady=(0, 5))
        help_label = ctk.CTkLabel(main_frame, 
                                text="Example:\nip_address:text\nport:integer\nprotocol:varchar(10)",
                                text_color="gray", font=ctk.CTkFont(size=12))
        help_label.pack(anchor="w", pady=(0, 5))

        self.fields_text = ctk.CTkTextbox(main_frame, height=150)
        self.fields_text.pack(fill="both", expand=True, pady=(0, 15))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(button_frame, text="Create", command=self.on_create).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)

    def on_create(self):
        """Обработка создания составного типа"""
        name = self.name_entry.get().strip()
        fields_text = self.fields_text.get("1.0", "end-1c").strip()

        if not name:
            messagebox.showerror("Error", "Please enter a name for the composite type")
            return

        if not fields_text:
            messagebox.showerror("Error", "Please enter at least one field for the composite type")
            return

        fields = {}
        for line in fields_text.split('\n'):
            line = line.strip()
            if ':' in line:
                field_name, field_type = line.split(':', 1)
                fields[field_name.strip()] = field_type.strip()

        if not fields:
            messagebox.showerror("Error", "Please enter valid fields in format: field_name:field_type")
            return

        self.result = {
            'name': name,
            'fields': fields
        }
        self.destroy()