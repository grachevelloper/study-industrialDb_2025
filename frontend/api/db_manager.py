import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from .db_config import db_config


class DatabaseManager:
    def __init__(self, config=None):
        self.config = config or db_config
        self.db_path = Path(__file__).parent.parent / self.config.database
        self.db_type = "sqlite"  # Для совместимости с query_builder

    def get_connection(self):
        """Получение соединения с SQLite"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query: str, params: tuple = (), return_cursor: bool = False):
        """Выполнение SQL запроса"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            
            if return_cursor:
                return cursor
            else:
                return cursor.fetchall()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn and not return_cursor:
                conn.close()

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

            # Существующие таблицы
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

            # НОВЫЕ ТАБЛИЦЫ ДЛЯ РАСШИРЕННЫХ ФУНКЦИЙ
            
            # Таблица для хранения представлений (VIEW)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS view_definitions (
                    view_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    query TEXT NOT NULL,
                    view_type TEXT DEFAULT 'REGULAR',
                    is_materialized BOOLEAN DEFAULT FALSE,
                    refresh_option TEXT,
                    columns TEXT,
                    dependencies TEXT,
                    description TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    usage_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            # Таблица для хранения CTE определений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cte_definitions (
                    cte_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    description TEXT,
                    query TEXT NOT NULL,
                    cte_type TEXT DEFAULT 'REGULAR',
                    is_recursive BOOLEAN DEFAULT FALSE,
                    columns TEXT,
                    dependencies TEXT,
                    parameters TEXT,
                    tags TEXT,
                    usage_count INTEGER DEFAULT 0,
                    avg_execution_time_ms INTEGER DEFAULT 0,
                    last_used TIMESTAMP,
                    is_favorite BOOLEAN DEFAULT FALSE,
                    is_template BOOLEAN DEFAULT FALSE,
                    created_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица истории выполнения запросов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_execution_history (
                    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_type TEXT,
                    query_text TEXT,
                    parameters TEXT,
                    execution_time_ms INTEGER,
                    row_count INTEGER,
                    success BOOLEAN,
                    error_message TEXT,
                    executed_by TEXT,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица для хранения материализованных представлений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS materialized_views_metadata (
                    mv_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    view_name TEXT UNIQUE NOT NULL,
                    original_name TEXT,
                    is_materialized BOOLEAN DEFAULT TRUE,
                    build_option TEXT DEFAULT 'IMMEDIATE',
                    refresh_option TEXT DEFAULT 'ON DEMAND',
                    incremental_column TEXT,
                    last_full_refresh TIMESTAMP,
                    last_incremental_refresh TIMESTAMP,
                    next_scheduled_refresh TIMESTAMP,
                    refresh_count INTEGER DEFAULT 0,
                    total_refresh_time_ms INTEGER DEFAULT 0,
                    avg_refresh_time_ms INTEGER DEFAULT 0,
                    estimated_size_kb INTEGER DEFAULT 0,
                    row_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица расписаний обновления
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mv_refresh_schedules (
                    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    view_name TEXT,
                    schedule_type TEXT,
                    schedule_interval TEXT,
                    schedule_time TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (view_name) REFERENCES materialized_views_metadata(view_name) ON DELETE CASCADE
                )
            """)

            # Таблица индексов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mv_indexes (
                    index_name TEXT PRIMARY KEY,
                    view_name TEXT,
                    columns TEXT,
                    is_unique BOOLEAN DEFAULT FALSE,
                    index_type TEXT DEFAULT 'BTREE',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (view_name) REFERENCES materialized_views_metadata(view_name) ON DELETE CASCADE
                )
            """)

            conn.commit()
            return {"success": True, "message": "Database tables created successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if conn is not None:
                conn.close()

    # СУЩЕСТВУЮЩИЕ МЕТОДЫ (остаются без изменений)
    # ==============================================
    
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
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM attacks ORDER BY created_at DESC")
            attacks_data = cursor.fetchall()

            attacks = []
            for attack_row in attacks_data:
                attack = dict(attack_row)

                attack["source_ips"] = self._parse_json_field(attack["source_ips"])
                attack["affected_ports"] = self._parse_json_field(attack["affected_ports"])
                attack["mitigation_strategies"] = self._parse_json_field(attack["mitigation_strategies"])

                cursor.execute("SELECT * FROM targets WHERE attack_id = ?", (attack["id"],))
                targets_data = cursor.fetchall()

                targets = []
                for target_row in targets_data:
                    target = dict(target_row)
                    target["tags"] = self._parse_json_field(target["tags"])
                    if "id" in target:
                        del target["id"]
                    if "attack_id" in target:
                        del target["attack_id"]
                    targets.append(target)

                attack["targets"] = targets
                attacks.append(attack)

            return attacks

        except Exception as e:
            print(f"Error in get_all_attacks: {e}")
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

            cursor.execute("SELECT * FROM attacks WHERE id = ?", (attack_id,))
            attack_row = cursor.fetchone()

            if not attack_row:
                return None

            attack = dict(attack_row)
            attack["source_ips"] = self._parse_json_field(attack["source_ips"])
            attack["affected_ports"] = self._parse_json_field(attack["affected_ports"])
            attack["mitigation_strategies"] = self._parse_json_field(attack["mitigation_strategies"])

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

            attack_id = attack_data.get("id")
            if not attack_id:
                import uuid
                attack_id = str(uuid.uuid4())

            current_time = datetime.now().isoformat()

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

            cursor.execute("SELECT id FROM attacks WHERE id = ?", (attack_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Attack {attack_id} not found"
                }

            current_time = datetime.now().isoformat()

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

            cursor.execute("SELECT id FROM attacks WHERE id = ?", (attack_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Attack {attack_id} not found"
                }

            current_time = datetime.now().isoformat()

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

            cursor.execute("DELETE FROM targets WHERE attack_id = ?", (attack_id,))

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

            cursor.execute("SELECT id FROM attacks WHERE id = ?", (attack_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Attack {attack_id} not found"
                }

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

            query = """
                SELECT DISTINCT a.* FROM attacks a
                WHERE 1=1
            """
            params = []

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

            cursor.execute("DROP TABLE IF EXISTS targets")
            cursor.execute("DROP TABLE IF EXISTS attacks")

            conn.commit()

            return self.initialize_database()

        except Exception as e:
            return {
                "success": False,
                "error": f"Database reset failed: {e}"
            }
        finally:
            if conn is not None:
                conn.close()

    # НОВЫЕ МЕТОДЫ ДЛЯ РАСШИРЕННЫХ ФУНКЦИЙ
    # ====================================

    def get_database_info(self) -> Dict[str, Any]:
        """Получение информации о базе данных"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Размер файла БД
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024)
            
            # Количество таблиц
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # Количество представлений
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")
            view_count = cursor.fetchone()[0]
            
            # Количество записей в таблицах
            cursor.execute("SELECT COUNT(*) FROM attacks")
            attack_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM targets")
            target_count = cursor.fetchone()[0]
            
            # Количество материализованных представлений
            cursor.execute("SELECT COUNT(*) FROM materialized_views_metadata WHERE is_active = TRUE")
            mv_count = cursor.fetchone()[0]
            
            # Количество CTE определений
            cursor.execute("SELECT COUNT(*) FROM cte_definitions")
            cte_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'name': self.db_path.name,
                'path': str(self.db_path),
                'size_mb': round(db_size_mb, 2),
                'table_count': table_count,
                'view_count': view_count,
                'materialized_view_count': mv_count,
                'cte_count': cte_count,
                'attack_count': attack_count,
                'target_count': target_count,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'name': 'Ошибка получения информации',
                'size_mb': 0,
                'table_count': 0,
                'view_count': 0,
                'materialized_view_count': 0,
                'cte_count': 0,
                'attack_count': 0,
                'target_count': 0,
                'error': str(e)
            }

    def execute_custom_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Выполнение пользовательского SQL запроса"""
        return self.execute_query(query, params)

    def save_query_execution(self, query_type: str, query_text: str, execution_time_ms: int, 
                            row_count: int, success: bool, error_message: str = None, 
                            executed_by: str = None, parameters: Dict = None):
        """Сохранение истории выполнения запроса"""
        try:
            query = """
                INSERT INTO query_execution_history 
                (query_type, query_text, parameters, execution_time_ms, row_count, success, error_message, executed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                query_type,
                query_text[:1000],  # Ограничиваем длину
                json.dumps(parameters) if parameters else None,
                execution_time_ms,
                row_count,
                success,
                error_message,
                executed_by
            )
            
            self.execute_query(query, params)
            
        except Exception as e:
            print(f"Error saving query execution: {e}")

    def get_query_execution_stats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение статистики выполнения запросов"""
        try:
            query = """
                SELECT 
                    query_type,
                    COUNT(*) as execution_count,
                    AVG(execution_time_ms) as avg_time_ms,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                    SUM(row_count) as total_rows
                FROM query_execution_history
                GROUP BY query_type
                ORDER BY execution_count DESC
                LIMIT ?
            """
            
            results = self.execute_query(query, (limit,))
            
            stats = []
            for row in results:
                stats.append({
                    'query_type': row[0],
                    'execution_count': row[1],
                    'avg_time_ms': round(row[2] or 0, 2),
                    'success_rate': round((row[3] / row[1] * 100) if row[1] > 0 else 0, 1),
                    'total_rows': row[4]
                })
            
            return stats
            
        except Exception as e:
            print(f"Error getting query execution stats: {e}")
            return []

    def create_view(self, view_name: str, query: str, view_type: str = 'REGULAR', 
                   is_materialized: bool = False, refresh_option: str = None,
                   description: str = None, tags: List[str] = None) -> bool:
        """Создание представления"""
        try:
            # Сначала создаем VIEW в базе данных
            if is_materialized:
                # Для SQLite эмулируем материализованные представления через обычные
                create_sql = f"CREATE VIEW mv_{view_name} AS {query}"
            else:
                create_sql = f"CREATE VIEW {view_name} AS {query}"
            
            self.execute_query(create_sql)
            
            # Сохраняем метаданные
            metadata_query = """
                INSERT OR REPLACE INTO view_definitions 
                (name, display_name, query, view_type, is_materialized, refresh_option, description, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                view_name,
                view_name,
                query,
                view_type,
                is_materialized,
                refresh_option,
                description or '',
                json.dumps(tags or []),
                datetime.now().isoformat()
            )
            
            self.execute_query(metadata_query, params)
            return True
            
        except Exception as e:
            print(f"Error creating view: {e}")
            return False

    def get_all_views(self) -> List[Dict[str, Any]]:
        """Получение всех представлений"""
        try:
            # Получаем из системных таблиц
            query = """
                SELECT name, type, tbl_name, sql 
                FROM sqlite_master 
                WHERE type = 'view'
                ORDER BY name
            """
            
            results = self.execute_query(query)
            
            views = []
            for row in results:
                view_name = row[0]
                
                # Получаем дополнительные метаданные
                metadata_query = "SELECT * FROM view_definitions WHERE name = ?"
                metadata_results = self.execute_query(metadata_query, (view_name,))
                
                if metadata_results:
                    metadata = dict(metadata_results[0])
                    metadata['sql_definition'] = row[3]
                    views.append(metadata)
                else:
                    views.append({
                        'name': view_name,
                        'type': row[1],
                        'base_table': row[2],
                        'sql_definition': row[3],
                        'view_type': 'REGULAR',
                        'is_materialized': False
                    })
            
            return views
            
        except Exception as e:
            print(f"Error getting views: {e}")
            return []

    def drop_view(self, view_name: str) -> bool:
        """Удаление представления"""
        try:
            # Удаляем VIEW из базы данных
            drop_sql = f"DROP VIEW IF EXISTS {view_name}"
            self.execute_query(drop_sql)
            
            # Также проверяем материализованное представление
            drop_mv_sql = f"DROP VIEW IF EXISTS mv_{view_name}"
            self.execute_query(drop_mv_sql)
            
            # Удаляем метаданные
            delete_metadata_sql = "DELETE FROM view_definitions WHERE name = ?"
            self.execute_query(delete_metadata_sql, (view_name,))
            
            return True
            
        except Exception as e:
            print(f"Error dropping view: {e}")
            return False

    def save_cte_definition(self, name: str, query: str, cte_type: str = 'REGULAR',
                           description: str = None, tags: List[str] = None) -> bool:
        """Сохранение определения CTE"""
        try:
            query_sql = """
                INSERT OR REPLACE INTO cte_definitions 
                (name, display_name, description, query, cte_type, tags, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                name,
                name,
                description or '',
                query,
                cte_type,
                json.dumps(tags or []),
                datetime.now().isoformat()
            )
            
            self.execute_query(query_sql, params)
            return True
            
        except Exception as e:
            print(f"Error saving CTE definition: {e}")
            return False

    def get_all_cte_definitions(self) -> List[Dict[str, Any]]:
        """Получение всех CTE определений"""
        try:
            query = "SELECT * FROM cte_definitions ORDER BY updated_at DESC"
            results = self.execute_query(query)
            
            cte_list = []
            for row in results:
                cte = dict(row)
                # Парсим JSON поля
                cte['tags'] = self._parse_json_field(cte['tags'])
                cte_list.append(cte)
            
            return cte_list
            
        except Exception as e:
            print(f"Error getting CTE definitions: {e}")
            return []

    def close_connection(self):
        """Закрытие соединения (заглушка для совместимости)"""
        pass

    # МЕТОДЫ ДЛЯ ГРУППИРОВКИ ДАННЫХ
    # ==============================
    
    def get_table_columns(self, table_name: str = "attacks") -> List[str]:
        """Получение списка столбцов таблицы"""
        try:
            if table_name == "attacks":
                # Для таблицы attacks возвращаем фиксированный список
                return ["id", "name", "frequency", "danger", "attack_type", 
                        "source_ips", "affected_ports", "mitigation_strategies", 
                        "created_at", "updated_at"]
            else:
                # Для других таблиц используем PRAGMA
                query = f"PRAGMA table_info({table_name})"
                results = self.execute_query(query)
                return [row[1] for row in results]
        except:
            return []

    def execute_grouping_query(self, query: str) -> List[Dict[str, Any]]:
        """Выполнение запроса с группировкой"""
        try:
            results = self.execute_query(query)
            
            # Преобразуем в список словарей
            formatted_results = []
            for row in results:
                if isinstance(row, tuple):
                    formatted_results.append(dict(enumerate(row)))
                else:
                    formatted_results.append(dict(row))
            
            return formatted_results
            
        except Exception as e:
            print(f"Error executing grouping query: {e}")
            return []

    def create_materialized_view_metadata(self, view_name: str, original_name: str, 
                                         build_option: str = 'IMMEDIATE', 
                                         refresh_option: str = 'ON DEMAND') -> bool:
        """Создание метаданных материализованного представления"""
        try:
            query = """
                INSERT INTO materialized_views_metadata 
                (view_name, original_name, build_option, refresh_option, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now().isoformat()
            params = (view_name, original_name, build_option, refresh_option, now, now)
            
            self.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"Error creating MV metadata: {e}")
            return False

    def get_materialized_views(self) -> List[Dict[str, Any]]:
        """Получение списка материализованных представлений"""
        try:
            query = """
                SELECT * FROM materialized_views_metadata 
                WHERE is_active = TRUE
                ORDER BY view_name
            """
            
            results = self.execute_query(query)
            
            mvs = []
            for row in results:
                mv = dict(row)
                mvs.append(mv)
            
            return mvs
            
        except Exception as e:
            print(f"Error getting materialized views: {e}")
            return []

    def update_mv_refresh_stats(self, view_name: str, refresh_time_ms: int):
        """Обновление статистики обновления материализованного представления"""
        try:
            query = """
                UPDATE materialized_views_metadata 
                SET last_full_refresh = ?,
                    refresh_count = refresh_count + 1,
                    total_refresh_time_ms = total_refresh_time_ms + ?,
                    avg_refresh_time_ms = (total_refresh_time_ms + ?) / (refresh_count + 1),
                    updated_at = ?
                WHERE view_name = ?
            """
            
            now = datetime.now().isoformat()
            params = (now, refresh_time_ms, refresh_time_ms, now, view_name)
            
            self.execute_query(query, params)
            
        except Exception as e:
            print(f"Error updating MV refresh stats: {e}")

    # УТИЛИТНЫЕ МЕТОДЫ
    # ================
    
    def table_exists(self, table_name: str) -> bool:
        """Проверка существования таблицы"""
        try:
            query = "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
        except:
            return False

    def view_exists(self, view_name: str) -> bool:
        """Проверка существования представления"""
        try:
            query = "SELECT 1 FROM sqlite_master WHERE type='view' AND name=?"
            result = self.execute_query(query, (view_name,))
            return len(result) > 0
        except:
            return False

    def get_table_row_count(self, table_name: str) -> int:
        """Получение количества строк в таблице"""
        try:
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = self.execute_query(query)
            return result[0][0] if result else 0
        except:
            return 0