import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from .db_config import db_config

class DatabaseManager:
    def __init__(self, config=None):
        self.config = config or db_config
        self.db_path = Path(__file__).parent.parent / self.config.database

    def get_connection(self):
        """Получение соединения с SQLite"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _parse_json_field(self, field_value):
        """Парсинг JSON полей из БД"""
        if isinstance(field_value, (list, dict)):
            return field_value
        elif field_value:
            try:
                return json.loads(field_value)
            except (json.JSONDecodeError, TypeError):
                return []
        else:
            return []

    def initialize_database(self) -> Dict[str, Any]:
        """Создание таблиц в SQLite"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Таблица атак
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attacks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    danger TEXT NOT NULL,
                    attack_type TEXT NOT NULL,
                    source_ips TEXT NOT NULL,
                    affected_ports TEXT NOT NULL,
                    mitigation_strategies TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Таблица целей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attack_id TEXT NOT NULL,
                    target_ip TEXT,
                    target_domain TEXT,
                    port INTEGER DEFAULT 80,
                    protocol TEXT DEFAULT 'tcp',
                    tags TEXT,
                    FOREIGN KEY (attack_id) REFERENCES attacks (id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_types (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE,
                    type TEXT,
                    enum_values TEXT,
                    created_at TEXT
                )
            """)


            conn.commit()
            return {"success": True, "message": "Database tables created successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if conn is not None:
                conn.close()

    def check_database_status(self) -> Dict[str, Any]:
        """Проверка статуса БД и существования таблиц"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('attacks', 'targets', 'custom_types')
            """)
            tables = cursor.fetchall()

            tables_exist = len(tables) == 3

            return {
                "success": True,
                "data": {
                    "tablesExist": tables_exist,
                    "database": str(self.db_path),
                    "tables": [table[0] for table in tables]
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {"tablesExist": False}
            }
        finally:
            if conn is not None:
                conn.close()

    def get_all_attacks(self) -> List[Dict[str, Any]]:
        """Получение всех атак с целями"""
        conn = None
        try:
            print("🔍 DEBUG: Connecting to database...")
            conn = self.get_connection()
            cursor = conn.cursor()

            # Получаем все атаки
            cursor.execute("SELECT * FROM attacks ORDER BY created_at DESC")
            attacks_data = cursor.fetchall()
            print(f"🔍 DEBUG: Found {len(attacks_data)} attacks")

            attacks = []
            for i, attack_row in enumerate(attacks_data):
                print(f"🔍 DEBUG: Processing attack {i+1}")
                try:
                    attack = dict(attack_row)
                    print(f"🔍 DEBUG: Attack keys: {list(attack.keys())}")

                    # Детально отлаживаем каждое поле
                    for key, value in attack.items():
                        print(f"🔍 DEBUG: Field {key}: type={type(value)}, value={repr(value)}")

                    # Парсим JSON поля
                    print("🔍 DEBUG: Parsing source_ips...")
                    attack["source_ips"] = self._parse_json_field(attack["source_ips"])
                    print("🔍 DEBUG: Parsing affected_ports...")
                    attack["affected_ports"] = self._parse_json_field(attack["affected_ports"])
                    print("🔍 DEBUG: Parsing mitigation_strategies...")
                    attack["mitigation_strategies"] = self._parse_json_field(attack["mitigation_strategies"])

                    # Получаем цели для этой атаки
                    cursor.execute("SELECT * FROM targets WHERE attack_id = ?", (attack["id"],))
                    targets_data = cursor.fetchall()
                    print(f"🔍 DEBUG: Found {len(targets_data)} targets for attack")

                    targets = []
                    for j, target_row in enumerate(targets_data):
                        print(f"🔍 DEBUG: Processing target {j+1}")
                        target = dict(target_row)
                        
                        target["tags"] = self._parse_json_field(target["tags"])
                        # Удаляем внутренний ID
                        if "id" in target:
                            del target["id"]
                        if "attack_id" in target:
                            del target["attack_id"]
                        targets.append(target)

                    attack["targets"] = targets
                    attacks.append(attack)
                    print(f"🔍 DEBUG: Successfully processed attack {i+1}")
                    
                except Exception as e:
                    print(f"❌ DEBUG: Error processing attack {i+1}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            print(f"🔍 DEBUG: Successfully processed {len(attacks)} attacks")
            return attacks

        except Exception as e:
            print(f"❌ DEBUG: Error in get_all_attacks: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if conn is not None:
                conn.close()
            
    def get_attack(self, attack_id: str) -> Optional[Dict[str, Any]]:
        """Получение конкретной атаки по ID"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Получаем атаку
            cursor.execute("SELECT * FROM attacks WHERE id = ?", (attack_id,))
            attack_row = cursor.fetchone()

            if not attack_row:
                return None

            attack = dict(attack_row)

            # Парсим JSON поля
            attack["source_ips"] = self._parse_json_field(attack["source_ips"])
            attack["affected_ports"] = self._parse_json_field(attack["affected_ports"])
            attack["mitigation_strategies"] = self._parse_json_field(attack["mitigation_strategies"])

            # Получаем цели
            cursor.execute("SELECT * FROM targets WHERE attack_id = ?", (attack_id,))
            targets_data = cursor.fetchall()

            targets = []
            for target_row in targets_data:
                target = dict(target_row)
                target["tags"] = self._parse_json_field(target["tags"])
                del target["id"]
                del target["attack_id"]
                targets.append(target)

            attack["targets"] = targets
            return attack

        except Exception as e:
            print(f"Error fetching attack {attack_id}: {e}")
            return None
        finally:
            if conn is not None:
                conn.close()

    def create_attack(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание новой атаки"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Подготавливаем данные для вставки
            attack_id = attack_data.get("id")
            if not attack_id:
                import uuid
                attack_id = str(uuid.uuid4())

            current_time = datetime.now().isoformat()

            # Вставляем атаку
            cursor.execute("""
                INSERT INTO attacks 
                (id, name, frequency, danger, attack_type, source_ips, affected_ports, mitigation_strategies, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attack_id,
                attack_data["name"],
                attack_data["frequency"],
                attack_data["danger"],
                attack_data["attack_type"],
                json.dumps(attack_data["source_ips"]),
                json.dumps(attack_data["affected_ports"]),
                json.dumps(attack_data["mitigation_strategies"]),
                current_time,
                current_time
            ))

            # Вставляем цели
            for target_data in attack_data.get("targets", []):
                cursor.execute("""
                    INSERT INTO targets 
                    (attack_id, target_ip, target_domain, port, protocol, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    attack_id,
                    target_data.get("target_ip", ""),
                    target_data.get("target_domain", ""),
                    target_data.get("port", 80),
                    target_data.get("protocol", "tcp"),
                    json.dumps(target_data.get("tags", []))
                ))

            conn.commit()

            return {
                "success": True,
                "data": self.get_attack(attack_id),
                "message": "Attack created successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create attack: {e}"
            }
        finally:
            if conn is not None:
                conn.close()

    def update_attack(self, attack_id: str, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление атаки"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Проверяем существование атаки
            cursor.execute("SELECT id FROM attacks WHERE id = ?", (attack_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Attack {attack_id} not found"
                }

            current_time = datetime.now().isoformat()

            # Обновляем атаку
            cursor.execute("""
                UPDATE attacks 
                SET name = ?, frequency = ?, danger = ?, attack_type = ?, 
                    source_ips = ?, affected_ports = ?, mitigation_strategies = ?, updated_at = ?
                WHERE id = ?
            """, (
                attack_data["name"],
                attack_data["frequency"],
                attack_data["danger"],
                attack_data["attack_type"],
                json.dumps(attack_data["source_ips"]),
                json.dumps(attack_data["affected_ports"]),
                json.dumps(attack_data["mitigation_strategies"]),
                current_time,
                attack_id
            ))

            conn.commit()

            return {
                "success": True,
                "data": self.get_attack(attack_id),
                "message": "Attack updated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update attack {attack_id}: {e}"
            }
        finally:
            if conn is not None:
                conn.close()

    def update_attack_with_targets(self, attack_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление атаки с целями"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Проверяем существование атаки
            cursor.execute("SELECT id FROM attacks WHERE id = ?", (attack_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Attack {attack_id} not found"
                }

            current_time = datetime.now().isoformat()

            # Обновляем атаку
            cursor.execute("""
                UPDATE attacks 
                SET name = ?, frequency = ?, danger = ?, attack_type = ?, 
                    source_ips = ?, affected_ports = ?, mitigation_strategies = ?, updated_at = ?
                WHERE id = ?
            """, (
                data["name"],
                data["frequency"],
                data["danger"],
                data["attack_type"],
                json.dumps(data["source_ips"]),
                json.dumps(data["affected_ports"]),
                json.dumps(data["mitigation_strategies"]),
                current_time,
                attack_id
            ))

            # Удаляем старые цели
            cursor.execute("DELETE FROM targets WHERE attack_id = ?", (attack_id,))

            # Добавляем новые цели
            for target_data in data.get("targets", []):
                cursor.execute("""
                    INSERT INTO targets 
                    (attack_id, target_ip, target_domain, port, protocol, tags)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    attack_id,
                    target_data.get("target_ip", ""),
                    target_data.get("target_domain", ""),
                    target_data.get("port", 80),
                    target_data.get("protocol", "tcp"),
                    json.dumps(target_data.get("tags", []))
                ))

            conn.commit()

            return {
                "success": True,
                "data": self.get_attack(attack_id),
                "message": "Attack with targets updated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update attack {attack_id} with targets: {e}"
            }
        finally:
            if conn is not None:
                conn.close()

    def delete_attack(self, attack_id: str) -> Dict[str, Any]:
        """Удаление атаки"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Проверяем существование атаки
            cursor.execute("SELECT id FROM attacks WHERE id = ?", (attack_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Attack {attack_id} not found"
                }

            # Удаляем атаку (цели удалятся каскадно)
            cursor.execute("DELETE FROM attacks WHERE id = ?", (attack_id,))
            conn.commit()

            return {
                "success": True,
                "message": f"Attack {attack_id} deleted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete attack {attack_id}: {e}"
            }
        finally:
            if conn is not None:
                conn.close()

    def filter_attacks(self, frequencies: List[str] = None, danger_levels: List[str] = None,
                       attack_types: List[str] = None, protocols: List[str] = None) -> List[Dict[str, Any]]:
        """Фильтрация атак по параметрам"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Базовый запрос
            query = """
                SELECT DISTINCT a.* FROM attacks a
                WHERE 1=1
            """
            params = []

            # Добавляем условия фильтрации
            if frequencies:
                placeholders = ",".join(["?"] * len(frequencies))
                query += f" AND a.frequency IN ({placeholders})"
                params.extend(frequencies)

            if danger_levels:
                placeholders = ",".join(["?"] * len(danger_levels))
                query += f" AND a.danger IN ({placeholders})"
                params.extend(danger_levels)

            if attack_types:
                placeholders = ",".join(["?"] * len(attack_types))
                query += f" AND a.attack_type IN ({placeholders})"
                params.extend(attack_types)

            # Фильтрация по протоколу требует JOIN с targets
            if protocols:
                query += """
                    AND EXISTS (
                        SELECT 1 FROM targets t 
                        WHERE t.attack_id = a.id AND t.protocol IN ({})
                    )
                """.format(",".join(["?"] * len(protocols)))
                params.extend(protocols)

            query += " ORDER BY a.created_at DESC"

            cursor.execute(query, params)
            attacks_data = cursor.fetchall()

            # Получаем полные данные для отфильтрованных атак
            attacks = []
            for attack_row in attacks_data:
                attack = self.get_attack(attack_row["id"])
                if attack:
                    attacks.append(attack)

            return attacks

        except Exception as e:
            print(f"Error filtering attacks: {e}")
            return []
        finally:
            if conn is not None:
                conn.close()

    def reset_database(self) -> Dict[str, Any]:
        """Сброс базы данных (удаление всех данных)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Удаляем таблицы
            cursor.execute("DROP TABLE IF EXISTS targets")
            cursor.execute("DROP TABLE IF EXISTS attacks")

            conn.commit()

            # Создаем заново
            return self.initialize_database()

        except Exception as e:
            return {
                "success": False,
                "error": f"Database reset failed: {e}"
            }
        finally:
            if conn is not None:
                conn.close()