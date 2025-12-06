from typing import List, Dict, Any, Optional, Tuple
import uuid
import json
from datetime import datetime
from .db_manager import DatabaseManager


class DDOSDatabaseClient:
    def __init__(self):
        self.db = DatabaseManager()

    def check_database_status(self) -> Dict[str, Any]:
        """Проверка статуса БД"""
        return self.db.check_database_status()

    def initialize_database(self) -> Dict[str, Any]:
        """Создание таблиц"""
        return self.db.initialize_database()

    def get_all_attacks(self) -> List[Dict[str, Any]]:
        """Получение всех атак"""
        return self.db.get_all_attacks()

    def get_attack(self, attack_id: str) -> Dict[str, Any]:
        """Получение конкретной атаки"""
        result = self.db.get_attack(attack_id)
        if result is None:
            raise Exception(f"Attack {attack_id} not found")
        return result

    def create_attack(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание новой атаки"""
        return self.db.create_attack(attack_data)

    def update_attack(self, attack_id: str, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление атаки"""
        return self.db.update_attack(attack_id, attack_data)

    def update_attack_with_targets(self, attack_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление атаки с целями"""
        return self.db.update_attack_with_targets(attack_id, data)

    def update_attack_targets(self, attack_id: str, targets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Обновление только целей атаки"""
        current_attack = self.db.get_attack(attack_id)
        if not current_attack:
            raise Exception(f"Attack {attack_id} not found")

        update_data = {
            "name": current_attack["name"],
            "frequency": current_attack["frequency"],
            "danger": current_attack["danger"],
            "attack_type": current_attack["attack_type"],
            "source_ips": current_attack["source_ips"],
            "affected_ports": current_attack["affected_ports"],
            "mitigation_strategies": current_attack["mitigation_strategies"],
            "targets": targets
        }

        return self.db.update_attack_with_targets(attack_id, update_data)

    def update_target(self, target_id: str, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление конкретной цели"""
        return self.db.update_target(int(target_id), target_data)

    def delete_attack(self, attack_id: str) -> Dict[str, Any]:
        """Удаление атаки"""
        return self.db.delete_attack(attack_id)

    def reset_database(self) -> Dict[str, Any]:
        """Сброс базы данных"""
        return self.db.reset_database()

    # Методы фильтрации
    def filter_attacks_by_frequency(self, frequencies: List[str]) -> List[Dict[str, Any]]:
        """Фильтрация атак по частоте"""
        if not frequencies:
            return self.get_all_attacks()
        return self.db.filter_attacks(frequencies=frequencies)

    def filter_attacks_by_danger(self, danger_levels: List[str]) -> List[Dict[str, Any]]:
        """Фильтрация атак по уровню опасности"""
        if not danger_levels:
            return self.get_all_attacks()
        return self.db.filter_attacks(danger_levels=danger_levels)

    def filter_attacks_by_attack_type(self, attack_types: List[str]) -> List[Dict[str, Any]]:
        """Фильтрация атак по типу атаки"""
        if not attack_types:
            return self.get_all_attacks()
        return self.db.filter_attacks(attack_types=attack_types)

    def filter_attacks_by_protocol(self, protocols: List[str]) -> List[Dict[str, Any]]:
        """Фильтрация атак по протоколу"""
        if not protocols:
            return self.get_all_attacks()
        return self.db.filter_attacks(protocols=protocols)

    def filter_attacks_by_multiple(self, frequencies: Optional[List[str]] = None,
                                   danger_levels: Optional[List[str]] = None,
                                   attack_types: Optional[List[str]] = None,
                                   protocols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Фильтрация атак по нескольким параметрам"""
        return self.db.filter_attacks(
            frequencies=frequencies,
            danger_levels=danger_levels,
            attack_types=attack_types,
            protocols=protocols
        )

    def _extract_attacks_data(self, data: Any) -> List[Dict[str, Any]]:
        """Совместимость со старым API клиентом"""
        if isinstance(data, dict) and 'data' in data:
            return data['data']
        elif isinstance(data, list):
            return data
        else:
            return []

    def create_custom_type(self, name: str, type_class: str, values: Any) -> Dict[str, Any]:
        """Создание пользовательского типа"""
        try:
            print(f"Creating custom type: {name}, {type_class}, {values}")
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = "INSERT INTO custom_types (id, name, type, enum_values, created_at) VALUES (?, ?, ?, ?, ?)"
            type_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            cursor.execute(query, (type_id, name, type_class, json.dumps(values), created_at))
            conn.commit()
            cursor.close()
            print(f"Type {name} created successfully") 
            return {"success": True, "message": f"Type {name} created successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_custom_types(self) -> List[Dict[str, Any]]:
        """Получение всех пользовательских типов"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM custom_types ORDER BY created_at DESC"
            cursor.execute(query)
            results = cursor.fetchall()
            
            types = []
            for row in results:
                types.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'values': json.loads(row[3]),
                    'created_at': row[4]
                })
            
            cursor.close()
            return types
        except Exception as e:
            print(f"Error getting custom types: {e}")
            return []

    def delete_custom_type(self, type_id: str) -> Dict[str, Any]:
        """Удаление пользовательского типа"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = "DELETE FROM custom_types WHERE id = ?"
            cursor.execute(query, (type_id,))
            conn.commit()
            cursor.close()
            
            return {"success": True, "message": "Type deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_custom_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Выполнение произвольного SQL запроса"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                # Получаем названия колонок
                column_names = [description[0] for description in cursor.description]
                # Конвертируем в список словарей
                formatted_results = []
                for row in results:
                    formatted_results.append(dict(zip(column_names, row)))
                cursor.close()
                return formatted_results
            else:
                conn.commit()
                cursor.close()
                return [{"message": "Query executed successfully", "rows_affected": cursor.rowcount}]
                
        except Exception as e:
            print(f"Error executing custom query: {e}")
            return [{"error": str(e)}]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Получение схемы таблицы"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            results = cursor.fetchall()
            
            schema = []
            for row in results:
                schema.append({
                    'cid': row[0],
                    'name': row[1],
                    'type': row[2],
                    'notnull': row[3],
                    'dflt_value': row[4],
                    'pk': row[5]
                })
            
            cursor.close()
            return schema
        except Exception as e:
            print(f"Error getting table schema: {e}")
            return []

    def get_all_tables(self) -> List[str]:
        """Получение списка всех таблиц в БД"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            cursor.execute(query)
            results = cursor.fetchall()
            
            tables = [row[0] for row in results]
            cursor.close()
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
        
    def get_database_info(self) -> Dict[str, Any]:
        """Получить информацию о базе данных"""
        try:
            # Используем метод из db_manager
            return self.db.get_database_info()
        except Exception as e:
            # Возвращаем базовую информацию при ошибке
            return {
                'name': 'attacks.db',
                'size_mb': 0,
                'table_count': 0,
                'view_count': 0,
                'materialized_view_count': 0,
                'cte_count': 0,
                'attack_count': 0,
                'target_count': 0,
                'last_updated': datetime.now().isoformat()
            }

    # НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ПРЕДСТАВЛЕНИЯМИ
    # =========================================

    def get_all_views(self) -> List[Dict[str, Any]]:
        """Получение всех представлений"""
        try:
            return self.db.get_all_views()
        except Exception as e:
            print(f"Error getting views: {e}")
            return []

    def create_view(self, view_name: str, query: str, **kwargs) -> bool:
        """Создание представления"""
        try:
            return self.db.create_view(
                view_name=view_name,
                query=query,
                view_type=kwargs.get('view_type', 'REGULAR'),
                is_materialized=kwargs.get('is_materialized', False),
                refresh_option=kwargs.get('refresh_option'),
                description=kwargs.get('description'),
                tags=kwargs.get('tags')
            )
        except Exception as e:
            print(f"Error creating view: {e}")
            return False

    def drop_view(self, view_name: str) -> bool:
        """Удаление представления"""
        try:
            return self.db.drop_view(view_name)
        except Exception as e:
            print(f"Error dropping view: {e}")
            return False

    def get_view_data(self, view_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение данных из представления"""
        try:
            query = f"SELECT * FROM `{view_name}` LIMIT {limit}"
            results = self.db.execute_custom_query(query)
            
            # Преобразуем в список словарей
            data = []
            for row in results:
                if hasattr(row, '_asdict'):
                    data.append(row._asdict())
                elif isinstance(row, tuple):
                    data.append({f"col_{i}": val for i, val in enumerate(row)})
                else:
                    data.append({"data": str(row)})
            return data
        except Exception as e:
            print(f"Error getting view data: {e}")
            return []

    def save_cte_definition(self, name: str, query: str, **kwargs) -> bool:
        """Сохранение определения CTE"""
        try:
            return self.db.save_cte_definition(
                name=name,
                query=query,
                cte_type=kwargs.get('cte_type', 'REGULAR'),
                description=kwargs.get('description'),
                tags=kwargs.get('tags')
            )
        except Exception as e:
            print(f"Error saving CTE definition: {e}")
            return False

    def get_all_cte_definitions(self) -> List[Dict[str, Any]]:
        """Получение всех CTE определений"""
        try:
            return self.db.get_all_cte_definitions()
        except Exception as e:
            print(f"Error getting CTE definitions: {e}")
            return []

    # Дополнительные методы для совместимости
    # ======================================

    def save_query_execution(self, query_type: str, query_text: str, 
                            execution_time_ms: int, row_count: int, 
                            success: bool, error_message: str = None, 
                            executed_by: str = None, parameters: Dict = None):
        """Сохранение истории выполнения запроса"""
        try:
            self.db.save_query_execution(
                query_type=query_type,
                query_text=query_text,
                execution_time_ms=execution_time_ms,
                row_count=row_count,
                success=success,
                error_message=error_message,
                executed_by=executed_by,
                parameters=parameters
            )
        except Exception as e:
            print(f"Error saving query execution: {e}")

    def get_query_execution_stats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение статистики выполнения запросов"""
        try:
            return self.db.get_query_execution_stats(limit)
        except Exception as e:
            print(f"Error getting query execution stats: {e}")
            return []

    def get_table_columns(self, table_name: str = "attacks") -> List[str]:
        """Получение списка столбцов таблицы"""
        try:
            return self.db.get_table_columns(table_name)
        except Exception as e:
            print(f"Error getting table columns: {e}")
            return []

    def execute_grouping_query(self, query: str) -> List[Dict[str, Any]]:
        """Выполнение запроса с группировкой"""
        try:
            return self.db.execute_grouping_query(query)
        except Exception as e:
            print(f"Error executing grouping query: {e}")
            return []