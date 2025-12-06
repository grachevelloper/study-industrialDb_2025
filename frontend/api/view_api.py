from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

class ViewAPI:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_all_views(self) -> List[Dict[str, Any]]:
        """Получение всех представлений"""
        return self.db.get_all_views()
    
    def create_view(self, view_name: str, query: str, **kwargs) -> Tuple[bool, str]:
        """Создание представления"""
        try:
            success = self.db.create_view(
                view_name=view_name,
                query=query,
                view_type=kwargs.get('view_type', 'REGULAR'),
                is_materialized=kwargs.get('is_materialized', False),
                refresh_option=kwargs.get('refresh_option'),
                description=kwargs.get('description'),
                tags=kwargs.get('tags')
            )
            if success:
                return True, f"View '{view_name}' created successfully"
            else:
                return False, f"Failed to create view '{view_name}'"
        except Exception as e:
            return False, f"Error creating view: {str(e)}"
    
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
    
    def _is_materialized_view(self, view_name: str) -> bool:
        """Проверка, является ли представление материализованным"""
        try:
            views = self.db.get_all_views()
            for view in views:
                if view.get('name') == view_name:
                    return view.get('is_materialized', False)
            return False
        except:
            return False
    
    def refresh_materialized_view(self, view_name: str) -> Tuple[bool, str]:
        """Обновление материализованного представления"""
        try:
            # Для SQLite просто пересоздаем представление
            # Получаем определение представления
            query = "SELECT sql FROM sqlite_master WHERE type='view' AND name=?"
            result = self.db.execute_custom_query(query, (view_name,))
            
            if not result:
                return False, f"View '{view_name}' not found"
            
            sql_definition = result[0][0]
            
            # Удаляем и пересоздаем представление
            drop_sql = f"DROP VIEW IF EXISTS `{view_name}`"
            self.db.execute_custom_query(drop_sql)
            
            self.db.execute_custom_query(sql_definition)
            
            # Обновляем статистику
            if hasattr(self.db, 'update_mv_refresh_stats'):
                self.db.update_mv_refresh_stats(view_name, 0)
            
            return True, f"Materialized view '{view_name}' refreshed successfully"
        except Exception as e:
            return False, f"Error refreshing view: {str(e)}"
    
    def export_view_definition(self, view_name: str, format: str = "sql") -> Tuple[bool, str, Optional[str]]:
        """Экспорт определения представления"""
        try:
            # Получаем SQL определение
            query = "SELECT sql FROM sqlite_master WHERE type='view' AND name=?"
            result = self.db.execute_custom_query(query, (view_name,))
            
            if not result:
                return False, f"View '{view_name}' not found", None
            
            sql_definition = result[0][0]
            
            if format == "sql":
                return True, f"Definition exported successfully", sql_definition
            elif format == "json":
                definition_json = json.dumps({
                    "view_name": view_name,
                    "sql_definition": sql_definition,
                    "exported_at": datetime.now().isoformat()
                }, indent=2)
                return True, f"Definition exported successfully", definition_json
            else:
                return False, f"Unsupported format: {format}", None
                
        except Exception as e:
            return False, f"Error exporting view definition: {str(e)}", None
    
    def drop_view(self, view_name: str) -> Tuple[bool, str]:
        """Удаление представления"""
        try:
            success = self.db.drop_view(view_name)
            if success:
                return True, f"View '{view_name}' dropped successfully"
            else:
                return False, f"Failed to drop view '{view_name}'"
        except Exception as e:
            return False, f"Error dropping view: {str(e)}"