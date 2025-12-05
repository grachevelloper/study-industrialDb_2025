# api/cte_api.py
"""
API модуль для работы с Common Table Expressions (CTE).
Обеспечивает создание, выполнение и анализ запросов с CTE.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from datetime import datetime
from enum import Enum


class CTEType(Enum):
    """Типы CTE"""
    REGULAR = "REGULAR"          # Обычное CTE
    RECURSIVE = "RECURSIVE"      # Рекурсивное CTE
    MULTIPLE = "MULTIPLE"        # Множественные CTE


class CTEQueryBuilder:
    """Класс для построения и анализа CTE запросов"""
    
    def __init__(self, db_manager):
        """
        Инициализация построителя CTE запросов
        
        Args:
            db_manager: Экземпляр DBManager для работы с БД
        """
        self.db_manager = db_manager
        self.db_type = db_manager.db_type if hasattr(db_manager, 'db_type') else 'sqlite'
        
        # Инициализация таблиц для хранения CTE определений
        self._init_cte_tables()
    
    def _init_cte_tables(self):
        """Инициализация таблиц для хранения CTE определений"""
        try:
            # Таблица сохраненных CTE
            cte_sql = """
            CREATE TABLE IF NOT EXISTS cte_definitions (
                cte_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                display_name TEXT,
                description TEXT,
                query TEXT NOT NULL,
                cte_type TEXT DEFAULT 'REGULAR',
                is_recursive BOOLEAN DEFAULT FALSE,
                columns TEXT,  -- JSON массив имен столбцов
                dependencies TEXT,  -- JSON массив зависимостей
                parameters TEXT,  -- JSON объект параметров
                tags TEXT,  -- JSON массив тегов
                usage_count INTEGER DEFAULT 0,
                avg_execution_time_ms INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                is_favorite BOOLEAN DEFAULT FALSE,
                is_template BOOLEAN DEFAULT FALSE,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name)
            )
            """
            self.db_manager.execute_query(cte_sql)
            
            # Таблица истории выполнения CTE
            history_sql = """
            CREATE TABLE IF NOT EXISTS cte_execution_history (
                execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cte_name TEXT,
                full_query TEXT,
                execution_time_ms INTEGER,
                row_count INTEGER,
                success BOOLEAN,
                error_message TEXT,
                executed_by TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cte_name) REFERENCES cte_definitions(name) ON DELETE SET NULL
            )
            """
            self.db_manager.execute_query(history_sql)
            
            # Таблица зависимостей между CTE
            dependencies_sql = """
            CREATE TABLE IF NOT EXISTS cte_dependencies (
                parent_cte TEXT,
                child_cte TEXT,
                dependency_type TEXT,  -- DIRECT, INDIRECT
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (parent_cte, child_cte),
                FOREIGN KEY (parent_cte) REFERENCES cte_definitions(name) ON DELETE CASCADE,
                FOREIGN KEY (child_cte) REFERENCES cte_definitions(name) ON DELETE CASCADE
            )
            """
            self.db_manager.execute_query(dependencies_sql)
            
        except Exception as e:
            print(f"Warning: Could not initialize CTE tables: {e}")
    
    def save_cte_definition(
        self,
        name: str,
        query: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        cte_type: Union[CTEType, str] = CTEType.REGULAR,
        columns: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_template: bool = False,
        created_by: Optional[str] = None,
        replace_if_exists: bool = False
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Сохранение определения CTE
        
        Args:
            name: Уникальное имя CTE
            query: SQL запрос CTE
            display_name: Отображаемое имя
            description: Описание
            cte_type: Тип CTE
            columns: Список столбцов
            parameters: Параметры запроса
            tags: Теги для поиска
            is_template: Является ли шаблоном
            created_by: Создатель
            replace_if_exists: Заменить если существует
            
        Returns:
            Кортеж (успех, сообщение, ID CTE)
        """
        try:
            # Валидация имени
            if not self._validate_cte_name(name):
                return False, "Invalid CTE name. Use letters, numbers and underscores only.", None
            
            # Проверка существования
            if not replace_if_exists and self._cte_exists(name):
                return False, f"CTE with name '{name}' already exists", None
            
            # Валидация запроса
            is_valid, error_msg = self._validate_cte_query(query)
            if not is_valid:
                return False, f"Invalid CTE query: {error_msg}", None
            
            # Определение типа CTE
            if isinstance(cte_type, CTEType):
                cte_type = cte_type.value
            
            is_recursive = self._is_recursive_query(query)
            if is_recursive:
                cte_type = CTEType.RECURSIVE.value
            
            # Автоматическое определение столбцов, если не указаны
            if not columns:
                columns = self._extract_columns_from_query(query)
            
            # Определение зависимостей
            dependencies = self._extract_cte_dependencies(query)
            
            # Подготовка данных для сохранения
            columns_json = json.dumps(columns, ensure_ascii=False) if columns else '[]'
            dependencies_json = json.dumps(dependencies, ensure_ascii=False) if dependencies else '[]'
            parameters_json = json.dumps(parameters, ensure_ascii=False) if parameters else '{}'
            tags_json = json.dumps(tags, ensure_ascii=False) if tags else '[]'
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if replace_if_exists and self._cte_exists(name):
                # Обновление существующего CTE
                query_sql = """
                UPDATE cte_definitions 
                SET display_name = ?,
                    description = ?,
                    query = ?,
                    cte_type = ?,
                    is_recursive = ?,
                    columns = ?,
                    dependencies = ?,
                    parameters = ?,
                    tags = ?,
                    is_template = ?,
                    updated_at = ?
                WHERE name = ?
                """
                
                params = (
                    display_name or name,
                    description or '',
                    query,
                    cte_type,
                    is_recursive,
                    columns_json,
                    dependencies_json,
                    parameters_json,
                    tags_json,
                    is_template,
                    now,
                    name
                )
                
                self.db_manager.execute_query(query_sql, params)
                
                # Получаем ID
                id_query = "SELECT cte_id FROM cte_definitions WHERE name = ?"
                result = self.db_manager.execute_query(id_query, (name,))
                cte_id = result[0][0] if result else None
                
                message = f"CTE '{name}' updated successfully"
                
            else:
                # Вставка нового CTE
                query_sql = """
                INSERT INTO cte_definitions 
                (name, display_name, description, query, cte_type, is_recursive, 
                 columns, dependencies, parameters, tags, is_template, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    name,
                    display_name or name,
                    description or '',
                    query,
                    cte_type,
                    is_recursive,
                    columns_json,
                    dependencies_json,
                    parameters_json,
                    tags_json,
                    is_template,
                    created_by,
                    now
                )
                
                self.db_manager.execute_query(query_sql, params)
                
                # Получаем ID созданного CTE
                cte_id = self.db_manager.execute_query("SELECT last_insert_rowid()")[0][0]
                
                message = f"CTE '{name}' saved successfully"
            
            # Обновление зависимостей
            if dependencies:
                self._update_cte_dependencies(name, dependencies)
            
            return True, message, cte_id
            
        except Exception as e:
            return False, f"Error saving CTE: {str(e)}", None
    
    def get_cte_definition(self, name_or_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Получение определения CTE по имени или ID
        
        Args:
            name_or_id: Имя или ID CTE
            
        Returns:
            Словарь с определением CTE или None
        """
        try:
            # Определяем, что передано: имя или ID
            if isinstance(name_or_id, int):
                query = "SELECT * FROM cte_definitions WHERE cte_id = ?"
                params = (name_or_id,)
            else:
                query = "SELECT * FROM cte_definitions WHERE name = ?"
                params = (name_or_id,)
            
            results = self.db_manager.execute_query(query, params)
            
            if not results:
                return None
            
            row = results[0]
            
            # Парсим JSON поля
            columns = json.loads(row[7]) if row[7] else []
            dependencies = json.loads(row[8]) if row[8] else []
            parameters = json.loads(row[9]) if row[9] else {}
            tags = json.loads(row[10]) if row[10] else []
            
            cte_info = {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'query': row[4],
                'type': row[5],
                'is_recursive': bool(row[6]),
                'columns': columns,
                'dependencies': dependencies,
                'parameters': parameters,
                'tags': tags,
                'usage_count': row[11],
                'avg_execution_time_ms': row[12],
                'last_used': row[13],
                'is_favorite': bool(row[14]),
                'is_template': bool(row[15]),
                'created_by': row[16],
                'created_at': row[17],
                'updated_at': row[18]
            }
            
            # Добавляем информацию о производительности
            cte_info['performance_stats'] = self._get_cte_performance_stats(row[1])
            
            # Добавляем примеры использования
            cte_info['usage_examples'] = self._get_cte_usage_examples(row[1])
            
            return cte_info
            
        except Exception as e:
            print(f"Error getting CTE definition: {e}")
            return None
    
    def get_all_cte_definitions(
        self,
        filter_type: Optional[str] = None,
        search_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        only_templates: bool = False,
        only_favorites: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получение всех сохраненных CTE определений
        
        Args:
            filter_type: Фильтр по типу
            search_text: Поиск по имени и описанию
            tags: Фильтр по тегам
            only_templates: Только шаблоны
            only_favorites: Только избранные
            limit: Ограничение количества
            offset: Смещение
            
        Returns:
            Список CTE определений
        """
        try:
            query_parts = ["SELECT * FROM cte_definitions WHERE 1=1"]
            params = []
            
            if filter_type:
                query_parts.append("AND cte_type = ?")
                params.append(filter_type)
            
            if search_text:
                query_parts.append("AND (name LIKE ? OR display_name LIKE ? OR description LIKE ?)")
                search_pattern = f"%{search_text}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if tags:
                for tag in tags:
                    query_parts.append("AND tags LIKE ?")
                    params.append(f'%"{tag}"%')
            
            if only_templates:
                query_parts.append("AND is_template = TRUE")
            
            if only_favorites:
                query_parts.append("AND is_favorite = TRUE")
            
            query_parts.append("ORDER BY updated_at DESC, usage_count DESC")
            
            if limit is not None:
                query_parts.append("LIMIT ? OFFSET ?")
                params.extend([limit, offset])
            
            query = " ".join(query_parts)
            results = self.db_manager.execute_query(query, tuple(params))
            
            cte_list = []
            for row in results:
                # Парсим JSON поля
                columns = json.loads(row[7]) if row[7] else []
                dependencies = json.loads(row[8]) if row[8] else []
                parameters = json.loads(row[9]) if row[9] else {}
                tags = json.loads(row[10]) if row[10] else []
                
                cte_info = {
                    'id': row[0],
                    'name': row[1],
                    'display_name': row[2],
                    'description': row[3],
                    'query': row[4],
                    'type': row[5],
                    'is_recursive': bool(row[6]),
                    'columns': columns,
                    'dependencies': dependencies,
                    'parameters': parameters,
                    'tags': tags,
                    'usage_count': row[11],
                    'avg_execution_time_ms': row[12],
                    'last_used': row[13],
                    'is_favorite': bool(row[14]),
                    'is_template': bool(row[15]),
                    'created_by': row[16],
                    'created_at': row[17],
                    'updated_at': row[18]
                }
                
                cte_list.append(cte_info)
            
            return cte_list
            
        except Exception as e:
            print(f"Error getting all CTE definitions: {e}")
            return []
    
    def delete_cte_definition(self, name: str, cascade: bool = True) -> Tuple[bool, str]:
        """
        Удаление определения CTE
        
        Args:
            name: Имя CTE
            cascade: Удалить зависимости
            
        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            # Проверка существования
            if not self._cte_exists(name):
                return False, f"CTE '{name}' does not exist"
            
            # Проверка зависимостей
            if not cascade:
                dependencies = self.get_cte_dependents(name)
                if dependencies:
                    dep_names = [d['name'] for d in dependencies]
                    return False, f"Cannot delete '{name}'. It is referenced by: {', '.join(dep_names)}"
            
            # Удаление зависимостей
            self._delete_cte_dependencies(name)
            
            # Удаление истории выполнения
            self._delete_execution_history(name)
            
            # Удаление CTE
            query = "DELETE FROM cte_definitions WHERE name = ?"
            self.db_manager.execute_query(query, (name,))
            
            return True, f"CTE '{name}' deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting CTE: {str(e)}"
    
    def execute_cte_query(
        self,
        cte_definitions: List[Dict[str, str]],
        main_query: str,
        parameters: Optional[Dict[str, Any]] = None,
        explain: bool = False,
        limit: Optional[int] = None,
        timeout_ms: Optional[int] = None,
        executed_by: Optional[str] = None
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
        """
        Выполнение запроса с CTE
        
        Args:
            cte_definitions: Список определений CTE
            main_query: Основной запрос
            parameters: Параметры для подстановки
            explain: Выполнить EXPLAIN вместо SELECT
            limit: Ограничение количества строк
            timeout_ms: Таймаут выполнения
            executed_by: Идентификатор исполнителя
            
        Returns:
            Кортеж (успех, сообщение, данные, статистика)
        """
        start_time = datetime.now()
        
        try:
            # Валидация входных данных
            if not cte_definitions:
                return False, "No CTE definitions provided", None, None
            
            if not main_query.strip():
                return False, "Main query is empty", None, None
            
            # Построение полного запроса
            full_query = self._build_full_cte_query(cte_definitions, main_query, limit)
            
            # Подстановка параметров
            if parameters:
                full_query = self._substitute_parameters(full_query, parameters)
            
            # Добавление EXPLAIN, если нужно
            if explain:
                if self.db_type == "sqlite":
                    full_query = f"EXPLAIN QUERY PLAN {full_query}"
                elif self.db_type == "postgresql":
                    full_query = f"EXPLAIN (FORMAT JSON, ANALYZE) {full_query}"
                else:
                    full_query = f"EXPLAIN {full_query}"
            
            # Установка таймаута, если поддерживается
            if timeout_ms and self.db_type == "sqlite":
                self.db_manager.execute_query(f"PRAGMA busy_timeout = {timeout_ms}")
            
            # Выполнение запроса
            results = self.db_manager.execute_query(full_query)
            
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Форматирование результатов
            formatted_results = None
            if not explain and results:
                # Получаем информацию о столбцах
                column_names = self._get_column_names_from_results(results)
                
                # Форматируем результаты
                formatted_results = []
                for row in results:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(column_names):
                            row_dict[column_names[i]] = value
                        else:
                            row_dict[f'column_{i}'] = value
                    formatted_results.append(row_dict)
            
            # Статистика выполнения
            stats = {
                'execution_time_ms': execution_time_ms,
                'row_count': len(results) if results else 0,
                'query_length': len(full_query),
                'cte_count': len(cte_definitions),
                'is_explain': explain,
                'timestamp': end_time.isoformat()
            }
            
            # Сохранение в историю
            self._save_execution_history(
                cte_name=cte_definitions[-1]['name'] if cte_definitions else 'custom',
                full_query=full_query,
                execution_time_ms=execution_time_ms,
                row_count=len(results) if results else 0,
                success=True,
                executed_by=executed_by
            )
            
            # Обновление счетчика использования для CTE
            for cte in cte_definitions:
                if 'name' in cte:
                    self._increment_usage_count(cte['name'], execution_time_ms)
            
            success_message = "Query executed successfully"
            if explain:
                success_message = "Query plan generated successfully"
            
            return True, success_message, formatted_results, stats
            
        except Exception as e:
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Сохранение ошибки в историю
            error_msg = str(e)
            self._save_execution_history(
                cte_name=cte_definitions[-1]['name'] if cte_definitions else 'custom',
                full_query="",
                execution_time_ms=execution_time_ms,
                row_count=0,
                success=False,
                error_message=error_msg[:500],
                executed_by=executed_by
            )
            
            return False, f"Execution error: {error_msg}", None, None
    
    def validate_cte_chain(
        self,
        cte_definitions: List[Dict[str, str]]
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Валидация цепочки CTE (проверка зависимостей и циклов)
        
        Args:
            cte_definitions: Список определений CTE
            
        Returns:
            Кортеж (успех, сообщение, список проблем)
        """
        try:
            problems = []
            
            # Проверка уникальности имен
            cte_names = [cte.get('name', '') for cte in cte_definitions]
            unique_names = set()
            duplicate_names = set()
            
            for name in cte_names:
                if name in unique_names:
                    duplicate_names.add(name)
                else:
                    unique_names.add(name)
            
            if duplicate_names:
                problems.append({
                    'type': 'DUPLICATE_NAME',
                    'severity': 'ERROR',
                    'message': f"Duplicate CTE names: {', '.join(duplicate_names)}",
                    'cte_names': list(duplicate_names)
                })
            
            # Проверка зависимостей
            dependency_graph = {}
            
            for i, cte in enumerate(cte_definitions):
                name = cte.get('name', f'cte_{i+1}')
                query = cte.get('query', '')
                
                # Извлекаем зависимости
                dependencies = self._extract_cte_dependencies_from_query(query)
                
                # Фильтруем зависимости, которые определены позже
                valid_dependencies = []
                for dep in dependencies:
                    if dep in cte_names[i+1:]:  # Зависимость определена позже
                        problems.append({
                            'type': 'FORWARD_REFERENCE',
                            'severity': 'ERROR',
                            'message': f"CTE '{name}' references '{dep}' which is defined later",
                            'cte_name': name,
                            'dependency': dep
                        })
                    elif dep in cte_names[:i]:  # Зависимость определена ранее - OK
                        valid_dependencies.append(dep)
                    else:
                        # Зависимость не определена в цепочке CTE
                        problems.append({
                            'type': 'UNDEFINED_DEPENDENCY',
                            'severity': 'WARNING',
                            'message': f"CTE '{name}' references undefined CTE '{dep}'",
                            'cte_name': name,
                            'dependency': dep
                        })
                
                dependency_graph[name] = valid_dependencies
            
            # Проверка циклических зависимостей
            cycles = self._find_cycles_in_dependency_graph(dependency_graph)
            if cycles:
                for cycle in cycles:
                    problems.append({
                        'type': 'CYCLE_DETECTED',
                        'severity': 'ERROR',
                        'message': f"Circular dependency detected: {' -> '.join(cycle)}",
                        'cycle': cycle
                    })
            
            # Проверка рекурсивных CTE
            for i, cte in enumerate(cte_definitions):
                name = cte.get('name', f'cte_{i+1}')
                query = cte.get('query', '')
                
                if self._is_recursive_query(query):
                    # Проверяем, что рекурсивное CTE первое в цепочке
                    if i != 0:
                        problems.append({
                            'type': 'RECURSIVE_NOT_FIRST',
                            'severity': 'ERROR',
                            'message': f"Recursive CTE '{name}' must be the first CTE in the chain",
                            'cte_name': name,
                            'position': i + 1
                        })
                    
                    # Проверяем структуру рекурсивного CTE
                    recursive_problems = self._validate_recursive_cte(query, name)
                    problems.extend(recursive_problems)
            
            # Сортировка проблем по серьезности
            severity_order = {'ERROR': 0, 'WARNING': 1, 'INFO': 2}
            problems.sort(key=lambda x: severity_order.get(x['severity'], 3))
            
            if any(p['severity'] == 'ERROR' for p in problems):
                return False, "CTE chain validation failed", problems
            elif problems:
                return True, "CTE chain has warnings", problems
            else:
                return True, "CTE chain is valid", None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", None
    
    def analyze_cte_query(
        self,
        query: str,
        analyze_dependencies: bool = True,
        analyze_performance: bool = False
    ) -> Dict[str, Any]:
        """
        Анализ CTE запроса
        
        Args:
            query: SQL запрос с CTE
            analyze_dependencies: Анализировать зависимости
            analyze_performance: Анализировать производительность
            
        Returns:
            Словарь с результатами анализа
        """
        try:
            analysis = {
                'cte_count': 0,
                'is_recursive': False,
                'cte_names': [],
                'estimated_cost': 0,
                'warnings': [],
                'recommendations': []
            }
            
            # Извлечение CTE из запроса
            cte_matches = re.finditer(r'WITH\s+(?:RECURSIVE\s+)?(.+?)\)\s*,\s*', query, re.IGNORECASE | re.DOTALL)
            cte_definitions = []
            
            for match in cte_matches:
                cte_text = match.group(1)
                # Парсим имя и запрос CTE
                name_match = re.search(r'(\w+)\s+AS\s*\(', cte_text, re.IGNORECASE)
                if name_match:
                    cte_name = name_match.group(1)
                    analysis['cte_names'].append(cte_name)
                    
                    # Извлекаем запрос CTE
                    query_start = name_match.end()
                    query_end = cte_text.rfind(')')
                    if query_end > query_start:
                        cte_query = cte_text[query_start:query_end].strip()
                        cte_definitions.append({
                            'name': cte_name,
                            'query': cte_query
                        })
            
            analysis['cte_count'] = len(cte_definitions)
            
            # Проверка на рекурсивность
            if 'RECURSIVE' in query.upper():
                analysis['is_recursive'] = True
            
            # Анализ зависимостей
            if analyze_dependencies and cte_definitions:
                dependencies = {}
                for cte in cte_definitions:
                    deps = self._extract_cte_dependencies_from_query(cte['query'])
                    dependencies[cte['name']] = deps
                
                analysis['dependencies'] = dependencies
                
                # Проверка на циклические зависимости
                cycles = self._find_cycles_in_dependency_graph(dependencies)
                if cycles:
                    analysis['warnings'].append({
                        'type': 'CYCLE_WARNING',
                        'message': 'Potential circular dependencies detected',
                        'cycles': cycles
                    })
            
            # Анализ производительности
            if analyze_performance:
                # Оценка сложности запроса
                complexity_score = self._estimate_query_complexity(query)
                analysis['complexity_score'] = complexity_score
                
                if complexity_score > 100:
                    analysis['recommendations'].append({
                        'type': 'PERFORMANCE',
                        'message': 'Query appears complex. Consider breaking it down or adding indexes.',
                        'priority': 'MEDIUM'
                    })
                
                # Проверка на отсутствие LIMIT в основном запросе
                main_query = query.upper().split(')')[-1] if ')' in query else query.upper()
                if 'SELECT' in main_query and 'LIMIT' not in main_query:
                    analysis['recommendations'].append({
                        'type': 'PERFORMANCE',
                        'message': 'Main query does not have LIMIT clause. Consider adding LIMIT for large result sets.',
                        'priority': 'LOW'
                    })
            
            # Проверка лучших практик
            if analysis['cte_count'] > 5:
                analysis['warnings'].append({
                    'type': 'BEST_PRACTICE',
                    'message': f"Query has {analysis['cte_count']} CTEs. Consider simplifying or breaking into multiple queries.",
                    'priority': 'LOW'
                })
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing CTE query: {e}")
            return {
                'error': str(e),
                'cte_count': 0,
                'is_recursive': False,
                'cte_names': []
            }
    
    def generate_cte_from_template(
        self,
        template_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Генерация CTE запроса из шаблона
        
        Args:
            template_name: Имя шаблона
            parameters: Параметры для подстановки
            
        Returns:
            Кортеж (успех, сообщение, сгенерированный CTE)
        """
        try:
            # Получаем шаблон
            template = self.get_cte_definition(template_name)
            if not template:
                return False, f"Template '{template_name}' not found", None
            
            if not template.get('is_template'):
                return False, f"'{template_name}' is not a template", None
            
            # Получаем запрос и параметры шаблона
            query = template['query']
            template_params = template.get('parameters', {})
            
            # Объединяем параметры
            all_params = {**template_params, **(parameters or {})}
            
            # Подставляем параметры
            generated_query = self._substitute_parameters(query, all_params)
            
            # Генерируем уникальное имя для CTE
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            generated_name = f"{template_name}_{timestamp}"
            
            generated_cte = {
                'name': generated_name,
                'display_name': f"{template['display_name']} ({timestamp})",
                'query': generated_query,
                'type': template['type'],
                'columns': template['columns'],
                'parameters': all_params,
                'template_source': template_name
            }
            
            return True, f"CTE generated from template '{template_name}'", generated_cte
            
        except Exception as e:
            return False, f"Error generating CTE from template: {str(e)}", None
    
    def get_cte_dependents(self, cte_name: str) -> List[Dict[str, Any]]:
        """
        Получение CTE, которые зависят от указанного CTE
        
        Args:
            cte_name: Имя CTE
            
        Returns:
            Список зависимых CTE
        """
        try:
            query = """
            SELECT cd.* 
            FROM cte_definitions cd
            WHERE cd.dependencies LIKE ?
            ORDER BY cd.name
            """
            
            pattern = f'%"{cte_name}"%'
            results = self.db_manager.execute_query(query, (pattern,))
            
            dependents = []
            for row in results:
                dependent = {
                    'id': row[0],
                    'name': row[1],
                    'display_name': row[2],
                    'description': row[3],
                    'type': row[5],
                    'usage_count': row[11]
                }
                dependents.append(dependent)
            
            return dependents
            
        except Exception as e:
            print(f"Error getting CTE dependents: {e}")
            return []
    
    def get_execution_history(
        self,
        cte_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получение истории выполнения CTE
        
        Args:
            cte_name: Имя CTE (None для всех)
            limit: Ограничение количества
            offset: Смещение
            
        Returns:
            Список записей истории
        """
        try:
            if cte_name:
                query = """
                SELECT * FROM cte_execution_history 
                WHERE cte_name = ?
                ORDER BY executed_at DESC
                LIMIT ? OFFSET ?
                """
                params = (cte_name, limit, offset)
            else:
                query = """
                SELECT * FROM cte_execution_history 
                ORDER BY executed_at DESC
                LIMIT ? OFFSET ?
                """
                params = (limit, offset)
            
            results = self.db_manager.execute_query(query, params)
            
            history = []
            for row in results:
                record = {
                    'id': row[0],
                    'cte_name': row[1],
                    'full_query': row[2][:500] + '...' if len(row[2]) > 500 else row[2],
                    'execution_time_ms': row[3],
                    'row_count': row[4],
                    'success': bool(row[5]),
                    'error_message': row[6],
                    'executed_by': row[7],
                    'executed_at': row[8]
                }
                history.append(record)
            
            return history
            
        except Exception as e:
            print(f"Error getting execution history: {e}")
            return []
    
    def export_cte_definitions(
        self,
        format: str = "json",
        include_history: bool = False,
        cte_names: Optional[List[str]] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Экспорт определений CTE
        
        Args:
            format: Формат экспорта (json, sql)
            include_history: Включить историю выполнения
            cte_names: Список CTE для экспорта (None для всех)
            
        Returns:
            Кортеж (успех, сообщение, данные)
        """
        try:
            # Получаем CTE для экспорта
            if cte_names:
                cte_list = []
                for name in cte_names:
                    cte = self.get_cte_definition(name)
                    if cte:
                        cte_list.append(cte)
            else:
                cte_list = self.get_all_cte_definitions()
            
            export_data = None
            
            if format == "json":
                export_dict = {
                    'export_date': datetime.now().isoformat(),
                    'cte_count': len(cte_list),
                    'cte_definitions': cte_list
                }
                
                if include_history:
                    export_dict['execution_history'] = self.get_execution_history(limit=1000)
                
                export_data = json.dumps(export_dict, indent=2, default=str, ensure_ascii=False)
            
            elif format == "sql":
                sql_lines = []
                sql_lines.append(f"-- CTE Definitions Export")
                sql_lines.append(f"-- Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                sql_lines.append(f"-- CTE Count: {len(cte_list)}")
                sql_lines.append("")
                
                for cte in cte_list:
                    sql_lines.append(f"-- CTE: {cte['name']}")
                    sql_lines.append(f"-- Type: {cte['type']}")
                    sql_lines.append(f"-- Created: {cte['created_at']}")
                    sql_lines.append(f"-- Columns: {', '.join(cte['columns'])}")
                    sql_lines.append("")
                    sql_lines.append(f"WITH {cte['name']} AS (")
                    sql_lines.append(f"    {cte['query']}")
                    sql_lines.append(")")
                    sql_lines.append("SELECT * FROM {cte['name']};")
                    sql_lines.append("")
                    sql_lines.append("")
                
                export_data = "\n".join(sql_lines)
            
            else:
                return False, f"Unsupported format: {format}", None
            
            return True, "Export successful", export_data
            
        except Exception as e:
            return False, f"Error exporting CTE definitions: {str(e)}", None
    
    def import_cte_definitions(
        self,
        import_data: str,
        format: str = "json",
        replace_existing: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Импорт определений CTE
        
        Args:
            import_data: Данные для импорта
            format: Формат импорта (json, sql)
            replace_existing: Заменить существующие CTE
            
        Returns:
            Кортеж (успех, сообщение, статистика импорта)
        """
        try:
            stats = {
                'total': 0,
                'imported': 0,
                'skipped': 0,
                'failed': 0,
                'errors': []
            }
            
            if format == "json":
                import_dict = json.loads(import_data)
                cte_definitions = import_dict.get('cte_definitions', [])
            
            elif format == "sql":
                # Парсинг SQL (упрощенный)
                cte_definitions = self._parse_cte_from_sql(import_data)
            
            else:
                return False, f"Unsupported format: {format}", stats
            
            stats['total'] = len(cte_definitions)
            
            for cte_data in cte_definitions:
                try:
                    name = cte_data.get('name')
                    if not name:
                        stats['failed'] += 1
                        stats['errors'].append(f"CTE without name: {cte_data}")
                        continue
                    
                    # Проверка существования
                    if not replace_existing and self._cte_exists(name):
                        stats['skipped'] += 1
                        continue
                    
                    # Импорт CTE
                    success, message, cte_id = self.save_cte_definition(
                        name=name,
                        query=cte_data.get('query', ''),
                        display_name=cte_data.get('display_name', name),
                        description=cte_data.get('description', ''),
                        cte_type=cte_data.get('type', 'REGULAR'),
                        columns=cte_data.get('columns', []),
                        parameters=cte_data.get('parameters', {}),
                        tags=cte_data.get('tags', []),
                        is_template=cte_data.get('is_template', False),
                        replace_if_exists=replace_existing
                    )
                    
                    if success:
                        stats['imported'] += 1
                    else:
                        stats['failed'] += 1
                        stats['errors'].append(f"{name}: {message}")
                        
                except Exception as e:
                    stats['failed'] += 1
                    stats['errors'].append(f"Error importing CTE: {str(e)}")
            
            message = f"Import completed: {stats['imported']} imported, {stats['skipped']} skipped, {stats['failed']} failed"
            return True, message, stats
            
        except Exception as e:
            return False, f"Error importing CTE definitions: {str(e)}", stats
    
    # Вспомогательные методы
    
    def _validate_cte_name(self, name: str) -> bool:
        """Валидация имени CTE"""
        if not name or not name.strip():
            return False
        
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, name))
    
    def _validate_cte_query(self, query: str) -> Tuple[bool, str]:
        """Валидация CTE запроса"""
        if not query or not query.strip():
            return False, "Query is empty"
        
        query_upper = query.strip().upper()
        
        # Проверяем, что это SELECT запрос
        if not query_upper.startswith("SELECT"):
            return False, "CTE must be a SELECT query"
        
        # Проверяем на наличие запрещенных операций
        forbidden = [
            "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER",
            "TRUNCATE", "COMMIT", "ROLLBACK", "SAVEPOINT", "GRANT", "REVOKE"
        ]
        
        for forbidden_op in forbidden:
            if forbidden_op in query_upper:
                return False, f"Query cannot contain {forbidden_op} operations"
        
        return True, "Query is valid"
    
    def _cte_exists(self, name: str) -> bool:
        """Проверка существования CTE"""
        try:
            query = "SELECT 1 FROM cte_definitions WHERE name = ?"
            results = self.db_manager.execute_query(query, (name,))
            return bool(results)
        except:
            return False
    
    def _is_recursive_query(self, query: str) -> bool:
        """Проверка, является ли запрос рекурсивным"""
        query_upper = query.upper()
        
        # Ищем UNION ALL или UNION в сочетании с рекурсивной ссылкой
        if 'UNION' in query_upper:
            # Проверяем, есть ли ссылка на саму себя
            lines = query_upper.split('\n')
            for line in lines:
                if 'FROM' in line or 'JOIN' in line:
                    # Ищем имя CTE в запросе (упрощенная проверка)
                    if any(word in line for word in ['CTE_', '_CTE', 'RECURSIVE']):
                        return True
        
        return False
    
    def _extract_columns_from_query(self, query: str) -> List[str]:
        """Извлечение столбцов из SQL запроса"""
        try:
            columns = []
            
            # Ищем SELECT ... FROM
            select_match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_clause = select_match.group(1)
                
                # Разбиваем по запятым, но игнорируем запятые внутри скобок
                parts = [p.strip() for p in re.split(r',\s*(?![^()]*\))', select_clause)]
                
                for part in parts:
                    # Извлекаем имя столбца или алиас
                    as_match = re.search(r'(?:AS\s+)?([\w]+)$', part, re.IGNORECASE)
                    if as_match:
                        column_name = as_match.group(1)
                        if column_name.upper() not in ['SELECT', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING']:
                            columns.append(column_name)
                    else:
                        # Берем последнее слово
                        words = re.findall(r'\b(\w+)\b', part)
                        if words:
                            last_word = words[-1]
                            if last_word.upper() not in ['SELECT', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING']:
                                columns.append(last_word)
            
            # Если SELECT * FROM
            if not columns and re.search(r'SELECT\s*\*\s+FROM', query, re.IGNORECASE):
                # Пытаемся определить таблицу
                table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
                if table_match:
                    table_name = table_match.group(1)
                    # Попробуем получить столбцы таблицы
                    try:
                        if self.db_type == "sqlite":
                            pragma_query = f"PRAGMA table_info({table_name})"
                            results = self.db_manager.execute_query(pragma_query)
                            if results:
                                columns = [row[1] for row in results]
                    except:
                        pass
            
            return columns
            
        except:
            return []
    
    def _extract_cte_dependencies(self, query: str) -> List[str]:
        """Извлечение зависимостей CTE из запроса"""
        try:
            dependencies = set()
            
            # Ищем ссылки на другие CTE в запросе
            # Паттерн: FROM cte_name, JOIN cte_name
            patterns = [
                r'FROM\s+(\w+)(?:\s+|$)',
                r'JOIN\s+(\w+)(?:\s+|$)',
                r'\,\s*(\w+)(?:\s+|$)'  # Старый стиль JOIN через запятую
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    dependency = match.group(1)
                    # Проверяем, что это не ключевое слово SQL
                    if dependency.upper() not in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'GROUP', 'ORDER', 'HAVING']:
                        dependencies.add(dependency)
            
            return list(dependencies)
            
        except:
            return []
    
    def _extract_cte_dependencies_from_query(self, query: str) -> List[str]:
        """Извлечение зависимостей CTE из запроса (специализированный метод)"""
        return self._extract_cte_dependencies(query)
    
    def _update_cte_dependencies(self, cte_name: str, dependencies: List[str]):
        """Обновление зависимостей CTE"""
        try:
            # Удаляем старые зависимости
            delete_query = "DELETE FROM cte_dependencies WHERE parent_cte = ? OR child_cte = ?"
            self.db_manager.execute_query(delete_query, (cte_name, cte_name))
            
            # Добавляем новые зависимости
            for dep in dependencies:
                insert_query = """
                INSERT OR REPLACE INTO cte_dependencies (parent_cte, child_cte, dependency_type)
                VALUES (?, ?, 'DIRECT')
                """
                self.db_manager.execute_query(insert_query, (cte_name, dep))
                
        except Exception as e:
            print(f"Error updating CTE dependencies: {e}")
    
    def _delete_cte_dependencies(self, cte_name: str):
        """Удаление зависимостей CTE"""
        try:
            query = "DELETE FROM cte_dependencies WHERE parent_cte = ? OR child_cte = ?"
            self.db_manager.execute_query(query, (cte_name, cte_name))
        except:
            pass
    
    def _delete_execution_history(self, cte_name: str):
        """Удаление истории выполнения CTE"""
        try:
            query = "DELETE FROM cte_execution_history WHERE cte_name = ?"
            self.db_manager.execute_query(query, (cte_name,))
        except:
            pass
    
    def _build_full_cte_query(
        self,
        cte_definitions: List[Dict[str, str]],
        main_query: str,
        limit: Optional[int] = None
    ) -> str:
        """Построение полного CTE запроса"""
        # Удаляем точку с запятой из основного запроса, если есть
        main_query = main_query.strip()
        if main_query.endswith(';'):
            main_query = main_query[:-1]
        
        # Проверяем, есть ли рекурсивные CTE
        has_recursive = any(self._is_recursive_query(cte.get('query', '')) for cte in cte_definitions)
        
        # Начинаем построение запроса
        query_parts = ["WITH"]
        
        if has_recursive:
            query_parts.append("RECURSIVE")
        
        # Добавляем CTE определения
        cte_parts = []
        for i, cte in enumerate(cte_definitions):
            name = cte.get('name', f'cte_{i+1}')
            cte_query = cte.get('query', '').strip()
            
            # Удаляем точку с запятой из CTE запроса
            if cte_query.endswith(';'):
                cte_query = cte_query[:-1]
            
            cte_part = f"  {name} AS (\n    {cte_query}\n  )"
            
            if i < len(cte_definitions) - 1:
                cte_part += ","
            
            cte_parts.append(cte_part)
        
        query_parts.append("\n".join(cte_parts))
        query_parts.append("\n")
        query_parts.append(main_query)
        
        # Добавляем LIMIT, если указан
        if limit is not None:
            query_parts.append(f" LIMIT {limit}")
        
        query_parts.append(";")
        
        return "\n".join(query_parts)
    
    def _substitute_parameters(self, query: str, parameters: Dict[str, Any]) -> str:
        """Подстановка параметров в запрос"""
        if not parameters:
            return query
        
        result = query
        
        for key, value in parameters.items():
            placeholder = f"{{{{{key}}}}}"  # Двойные фигурные скобки для параметров
            if placeholder in result:
                # Экранирование значений в зависимости от типа
                if value is None:
                    substituted_value = "NULL"
                elif isinstance(value, str):
                    # Экранируем кавычки
                    escaped_value = value.replace("'", "''")
                    substituted_value = f"'{escaped_value}'"
                elif isinstance(value, bool):
                    substituted_value = "1" if value else "0" if self.db_type == "sqlite" else str(value).upper()
                elif isinstance(value, (int, float)):
                    substituted_value = str(value)
                elif isinstance(value, datetime):
                    substituted_value = f"'{value.isoformat()}'"
                else:
                    substituted_value = f"'{str(value)}'"
                
                result = result.replace(placeholder, substituted_value)
        
        return result
    
    def _get_column_names_from_results(self, results: List[tuple]) -> List[str]:
        """Получение имен столбцов из результатов запроса"""
        # В SQLite нет простого способа получить имена столбцов из cursor.description
        # как в других БД, поэтому используем эвристику
        
        if not results:
            return []
        
        # Если это результаты EXPLAIN QUERY PLAN
        if len(results[0]) == 4 and self.db_type == "sqlite":
            return ['id', 'parent', 'notused', 'detail']
        
        # Для обычных запросов генерируем имена column_0, column_1, ...
        return [f'column_{i}' for i in range(len(results[0]))]
    
    def _save_execution_history(
        self,
        cte_name: str,
        full_query: str,
        execution_time_ms: int,
        row_count: int,
        success: bool,
        error_message: Optional[str] = None,
        executed_by: Optional[str] = None
    ):
        """Сохранение истории выполнения"""
        try:
            query = """
            INSERT INTO cte_execution_history 
            (cte_name, full_query, execution_time_ms, row_count, success, error_message, executed_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db_manager.execute_query(
                query,
                (cte_name, full_query[:2000], execution_time_ms, row_count, success, error_message, executed_by)
            )
        except Exception as e:
            print(f"Error saving execution history: {e}")
    
    def _increment_usage_count(self, cte_name: str, execution_time_ms: int):
        """Увеличение счетчика использования CTE"""
        try:
            # Получаем текущую статистику
            query = """
            SELECT usage_count, avg_execution_time_ms 
            FROM cte_definitions 
            WHERE name = ?
            """
            
            results = self.db_manager.execute_query(query, (cte_name,))
            
            if results:
                current_count = results[0][0]
                current_avg_time = results[0][1] or 0
                
                new_count = current_count + 1
                new_avg_time = ((current_avg_time * current_count) + execution_time_ms) // new_count
                
                # Обновляем
                update_query = """
                UPDATE cte_definitions 
                SET usage_count = ?, 
                    avg_execution_time_ms = ?,
                    last_used = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
                """
                
                self.db_manager.execute_query(
                    update_query,
                    (new_count, new_avg_time, cte_name)
                )
        except Exception as e:
            print(f"Error incrementing usage count: {e}")
    
    def _get_cte_performance_stats(self, cte_name: str) -> Dict[str, Any]:
        """Получение статистики производительности CTE"""
        try:
            query = """
            SELECT 
                AVG(execution_time_ms) as avg_time,
                MIN(execution_time_ms) as min_time,
                MAX(execution_time_ms) as max_time,
                COUNT(*) as execution_count,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
            FROM cte_execution_history
            WHERE cte_name = ?
            GROUP BY cte_name
            """
            
            results = self.db_manager.execute_query(query, (cte_name,))
            
            if results and results[0][0]:
                row = results[0]
                return {
                    'avg_execution_time_ms': row[0],
                    'min_execution_time_ms': row[1],
                    'max_execution_time_ms': row[2],
                    'execution_count': row[3],
                    'success_rate': (row[4] / row[3] * 100) if row[3] > 0 else 0
                }
            
            return {}
            
        except Exception as e:
            print(f"Error getting CTE performance stats: {e}")
            return {}
    
    def _get_cte_usage_examples(self, cte_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Получение примеров использования CTE"""
        try:
            query = """
            SELECT full_query, executed_at, execution_time_ms, row_count
            FROM cte_execution_history
            WHERE cte_name = ? AND success = TRUE
            ORDER BY executed_at DESC
            LIMIT ?
            """
            
            results = self.db_manager.execute_query(query, (cte_name, limit))
            
            examples = []
            for row in results:
                example = {
                    'query_preview': row[0][:200] + '...' if len(row[0]) > 200 else row[0],
                    'executed_at': row[1],
                    'execution_time_ms': row[2],
                    'row_count': row[3]
                }
                examples.append(example)
            
            return examples
            
        except Exception as e:
            print(f"Error getting CTE usage examples: {e}")
            return []
    
    def _find_cycles_in_dependency_graph(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Поиск циклов в графе зависимостей"""
        def dfs(node, visited, stack):
            visited.add(node)
            stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, visited, stack):
                        return True
                elif neighbor in stack:
                    # Найден цикл
                    cycle_start = list(stack).index(neighbor)
                    cycle = list(stack)[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            stack.remove(node)
            return False
        
        visited = set()
        stack = set()
        cycles = []
        
        for node in graph:
            if node not in visited:
                dfs(node, visited, stack)
        
        return cycles
    
    def _validate_recursive_cte(self, query: str, cte_name: str) -> List[Dict[str, Any]]:
        """Валидация рекурсивного CTE"""
        problems = []
        
        # Проверяем наличие UNION ALL
        if 'UNION ALL' not in query.upper():
            problems.append({
                'type': 'RECURSIVE_NO_UNION_ALL',
                'severity': 'ERROR',
                'message': f"Recursive CTE '{cte_name}' must use UNION ALL (not UNION)",
                'cte_name': cte_name
            })
        
        # Проверяем наличие анкерной и рекурсивной частей
        query_upper = query.upper()
        union_index = query_upper.find('UNION ALL')
        
        if union_index > 0:
            anchor_part = query[:union_index].strip()
            recursive_part = query[union_index + len('UNION ALL'):].strip()
            
            # Проверяем, что рекурсивная часть ссылается на CTE
            if cte_name.upper() not in recursive_part.upper():
                problems.append({
                    'type': 'RECURSIVE_NO_SELF_REFERENCE',
                    'severity': 'ERROR',
                    'message': f"Recursive part of CTE '{cte_name}' must reference the CTE itself",
                    'cte_name': cte_name
                })
        
        return problems
    
    def _estimate_query_complexity(self, query: str) -> int:
        """Оценка сложности запроса"""
        complexity = 0
        
        # Ключевые слова, увеличивающие сложность
        complexity_keywords = {
            'JOIN': 10,
            'UNION': 15,
            'GROUP BY': 5,
            'ORDER BY': 3,
            'WHERE': 2,
            'HAVING': 5,
            'SUBQUERY': 20,
            'CASE': 5,
            'WINDOW': 15
        }
        
        query_upper = query.upper()
        
        for keyword, weight in complexity_keywords.items():
            if keyword in query_upper:
                complexity += weight
        
        # Количество CTE
        cte_count = len(re.findall(r'WITH', query_upper, re.IGNORECASE))
        complexity += cte_count * 5
        
        # Длина запроса
        complexity += len(query) // 100  # 1 балл за каждые 100 символов
        
        return complexity
    
    def _parse_cte_from_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Парсинг CTE из SQL строки"""
        cte_definitions = []
        
        # Ищем блок WITH
        with_pattern = r'WITH\s+(?:RECURSIVE\s+)?(.+?)\)\s*(?:,|SELECT)'
        match = re.search(with_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if match:
            cte_block = match.group(1)
            
            # Разбиваем на отдельные CTE
            cte_pattern = r'(\w+)\s+AS\s*\(([^)]+)\)'
            cte_matches = re.finditer(cte_pattern, cte_block, re.IGNORECASE | re.DOTALL)
            
            for cte_match in cte_matches:
                name = cte_match.group(1)
                query = cte_match.group(2).strip()
                
                cte_def = {
                    'name': name,
                    'query': query,
                    'type': 'REGULAR',
                    'columns': self._extract_columns_from_query(query)
                }
                
                # Проверяем на рекурсивность
                if self._is_recursive_query(query):
                    cte_def['type'] = 'RECURSIVE'
                
                cte_definitions.append(cte_def)
        
        return cte_definitions


# Вспомогательные функции
def create_cte_api(db_manager) -> CTEQueryBuilder:
    """
    Создание экземпляра CTEQueryBuilder
    
    Args:
        db_manager: Экземпляр DBManager
        
    Returns:
        Экземпляр CTEQueryBuilder
    """
    return CTEQueryBuilder(db_manager)


if __name__ == "__main__":
    # Демонстрация работы API
    print("=== CTE API Demo ===\n")
    
    # Пример использования
    try:
        from db_manager import DBManager
        
        # Создаем подключение к БД в памяти
        db_manager = DBManager(":memory:")
        
        # Создаем API
        cte_api = CTEQueryBuilder(db_manager)
        
        # Создаем тестовую таблицу
        db_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS attacks (
                id INTEGER PRIMARY KEY,
                name TEXT,
                attack_type TEXT,
                severity TEXT,
                danger INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Добавляем тестовые данные
        db_manager.execute_query("""
            INSERT INTO attacks (name, attack_type, severity, danger) VALUES
            ('SQL Injection', 'Web', 'HIGH', 9),
            ('XSS', 'Web', 'MEDIUM', 7),
            ('Brute Force', 'Network', 'MEDIUM', 5),
            ('Phishing', 'Social', 'HIGH', 8),
            ('DDoS', 'Network', 'HIGH', 9)
        """)
        
        print("1. Saving CTE definition...")
        success, message, cte_id = cte_api.save_cte_definition(
            name="high_danger_attacks",
            query="SELECT * FROM attacks WHERE danger > 7",
            display_name="High Danger Attacks",
            description="Attacks with danger level greater than 7",
            tags=["attacks", "high-danger", "security"]
        )
        print(f"   Result: {message}")
        if success:
            print(f"   CTE ID: {cte_id}")
        
        print("\n2. Getting CTE definition...")
        cte_def = cte_api.get_cte_definition("high_danger_attacks")
        if cte_def:
            print(f"   Name: {cte_def['name']}")
            print(f"   Description: {cte_def['description']}")
            print(f"   Columns: {', '.join(cte_def['columns'])}")
        
        print("\n3. Executing CTE query...")
        cte_definitions = [
            {
                'name': 'high_danger',
                'query': 'SELECT * FROM attacks WHERE danger > 7'
            },
            {
                'name': 'attack_summary',
                'query': 'SELECT attack_type, COUNT(*) as count FROM high_danger GROUP BY attack_type'
            }
        ]
        
        success, message, results, stats = cte_api.execute_cte_query(
            cte_definitions=cte_definitions,
            main_query="SELECT * FROM attack_summary ORDER BY count DESC",
            limit=10
        )
        
        print(f"   Result: {message}")
        if success and results:
            print(f"   Returned {len(results)} rows")
            for row in results[:3]:  # Показать первые 3 результата
                print(f"   - {row}")
        
        print("\n4. Validating CTE chain...")
        is_valid, validation_message, problems = cte_api.validate_cte_chain(cte_definitions)
        print(f"   Validation: {validation_message}")
        if problems:
            for problem in problems[:2]:  # Показать первые 2 проблемы
                print(f"   - {problem['message']}")
        
        print("\n5. Analyzing CTE query...")
        query_with_cte = """
        WITH high_danger AS (
            SELECT * FROM attacks WHERE danger > 7
        ),
        attack_summary AS (
            SELECT attack_type, COUNT(*) as count FROM high_danger GROUP BY attack_type
        )
        SELECT * FROM attack_summary ORDER BY count DESC
        """
        
        analysis = cte_api.analyze_cte_query(query_with_cte)
        print(f"   CTE Count: {analysis['cte_count']}")
        print(f"   Is Recursive: {analysis['is_recursive']}")
        print(f"   CTE Names: {', '.join(analysis['cte_names'])}")
        
        print("\n6. Getting execution history...")
        history = cte_api.get_execution_history(limit=3)
        print(f"   Found {len(history)} history records")
        for record in history:
            print(f"   - {record['cte_name']}: {record['execution_time_ms']} ms, {record['row_count']} rows")
        
        print("\n7. Exporting CTE definitions...")
        success, message, export_data = cte_api.export_cte_definitions(
            format="json",
            include_history=False
        )
        if success:
            print(f"   Export successful ({len(export_data)} chars)")
        
        db_manager.close_connection()
        
        print("\n=== Demo completed ===")
        
    except ImportError:
        print("DBManager not available for demo")
    except Exception as e:
        print(f"Demo error: {e}")