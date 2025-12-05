# api/materialized_view_api.py
"""
Специализированный API для работы с материализованными представлениями.
Расширяет функционал ViewAPI специфичными для материализованных представлений операциями.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum


class RefreshType(Enum):
    """Типы обновления материализованных представлений"""
    COMPLETE = "COMPLETE"      # Полное перестроение
    FAST = "FAST"              # Быстрое обновление (если поддерживается)
    FORCE = "FORCE"            # Принудительное обновление
    INCREMENTAL = "INCREMENTAL" # Инкрементальное обновление


class MVRefreshOption(Enum):
    """Опции обновления материализованных представлений"""
    ON_DEMAND = "ON DEMAND"    # По требованию
    ON_COMMIT = "ON COMMIT"    # При коммите
    NEVER = "NEVER"            # Никогда не обновлять автоматически


class BuildOption(Enum):
    """Опции построения материализованных представлений"""
    IMMEDIATE = "IMMEDIATE"    # Построить немедленно
    DEFERRED = "DEFERRED"      # Отложенное построение


class MaterializedViewAPI:
    """Специализированный API для материализованных представлений"""
    
    def __init__(self, db_manager):
        """
        Инициализация API материализованных представлений
        
        Args:
            db_manager: Экземпляр DBManager для работы с БД
        """
        self.db_manager = db_manager
        self.db_type = db_manager.db_type if hasattr(db_manager, 'db_type') else 'sqlite'
        
        # Инициализация таблиц метаданных
        self._init_metadata_tables()
    
    def _init_metadata_tables(self):
        """Инициализация таблиц метаданных для материализованных представлений"""
        try:
            # Основная таблица метаданных
            metadata_sql = """
            CREATE TABLE IF NOT EXISTS mv_system_metadata (
                view_name TEXT PRIMARY KEY,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.db_manager.execute_query(metadata_sql)
            
            # Таблица расписаний обновления
            schedule_sql = """
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (view_name) REFERENCES mv_system_metadata(view_name) ON DELETE CASCADE
            )
            """
            self.db_manager.execute_query(schedule_sql)
            
            # Таблица статистики использования
            usage_sql = """
            CREATE TABLE IF NOT EXISTS mv_usage_stats (
                view_name TEXT,
                query_date DATE DEFAULT CURRENT_DATE,
                query_count INTEGER DEFAULT 0,
                total_execution_time_ms INTEGER DEFAULT 0,
                avg_execution_time_ms INTEGER DEFAULT 0,
                cache_hits INTEGER DEFAULT 0,
                cache_misses INTEGER DEFAULT 0,
                PRIMARY KEY (view_name, query_date),
                FOREIGN KEY (view_name) REFERENCES mv_system_metadata(view_name) ON DELETE CASCADE
            )
            """
            self.db_manager.execute_query(usage_sql)
            
            # Таблица индексов материализованных представлений
            index_sql = """
            CREATE TABLE IF NOT EXISTS mv_indexes (
                index_name TEXT PRIMARY KEY,
                view_name TEXT,
                columns TEXT,
                is_unique BOOLEAN DEFAULT FALSE,
                index_type TEXT DEFAULT 'BTREE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (view_name) REFERENCES mv_system_metadata(view_name) ON DELETE CASCADE
            )
            """
            self.db_manager.execute_query(index_sql)
            
        except Exception as e:
            print(f"Warning: Could not initialize MV metadata tables: {e}")
    
    def get_all_materialized_views(self, only_active: bool = True) -> List[Dict[str, Any]]:
        """
        Получение списка всех материализованных представлений
        
        Args:
            only_active: Только активные представления
            
        Returns:
            Список материализованных представлений
        """
        try:
            mvs = []
            
            # Получаем представления из системной таблицы
            query = """
            SELECT 
                sm.view_name,
                sm.original_name,
                sm.is_materialized,
                sm.build_option,
                sm.refresh_option,
                sm.last_full_refresh,
                sm.next_scheduled_refresh,
                sm.refresh_count,
                sm.avg_refresh_time_ms,
                sm.estimated_size_kb,
                sm.row_count,
                sm.is_active
            FROM mv_system_metadata sm
            WHERE sm.is_materialized = TRUE
            """
            
            if only_active:
                query += " AND sm.is_active = TRUE"
            
            query += " ORDER BY sm.view_name"
            
            results = self.db_manager.execute_query(query)
            
            for row in results:
                mv_info = {
                    'name': row[0],
                    'original_name': row[1],
                    'is_materialized': bool(row[2]),
                    'build_option': row[3],
                    'refresh_option': row[4],
                    'last_refresh': row[5],
                    'next_scheduled_refresh': row[6],
                    'refresh_count': row[7],
                    'avg_refresh_time': row[8],
                    'size_kb': row[9],
                    'row_count': row[10],
                    'is_active': bool(row[11]),
                    'type': 'materialized view',
                    'status': self._get_mv_status(row[0], row[5], row[6])
                }
                
                # Получаем дополнительные данные
                mv_info['schedule'] = self.get_refresh_schedule(row[0])
                mv_info['indexes'] = self.get_mv_indexes(row[0])
                mv_info['performance_stats'] = self.get_performance_stats(row[0])
                
                mvs.append(mv_info)
            
            # Если в системной таблице нет записей, ищем представления с префиксом mv_
            if not mvs:
                all_views_query = "SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'mv_%'"
                view_results = self.db_manager.execute_query(all_views_query)
                
                for row in view_results:
                    mv_info = {
                        'name': row[0],
                        'original_name': row[0].replace('mv_', '', 1),
                        'is_materialized': True,
                        'build_option': 'IMMEDIATE',
                        'refresh_option': 'ON DEMAND',
                        'last_refresh': None,
                        'next_scheduled_refresh': None,
                        'refresh_count': 0,
                        'avg_refresh_time': 0,
                        'size_kb': self._estimate_mv_size(row[0]),
                        'row_count': self._get_mv_row_count(row[0]),
                        'is_active': True,
                        'type': 'materialized view',
                        'status': 'ACTIVE'
                    }
                    
                    # Добавляем в системную таблицу
                    self._add_to_metadata(mv_info)
                    mvs.append(mv_info)
            
            return mvs
            
        except Exception as e:
            print(f"Error getting materialized views: {e}")
            return []
    
    def create_materialized_view(
        self,
        view_name: str,
        query: str,
        build_option: Union[BuildOption, str] = BuildOption.IMMEDIATE,
        refresh_option: Union[MVRefreshOption, str] = MVRefreshOption.ON_DEMAND,
        incremental_column: Optional[str] = None,
        indexes: Optional[List[Dict[str, Any]]] = None,
        replace_if_exists: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Создание материализованного представления
        
        Args:
            view_name: Имя представления
            query: SELECT запрос
            build_option: Опция построения
            refresh_option: Опция обновления
            incremental_column: Колонка для инкрементального обновления
            indexes: Список индексов для создания
            replace_if_exists: Заменить если существует
            
        Returns:
            Кортеж (успех, сообщение, имя созданного представления)
        """
        try:
            # Преобразуем enum в строки
            if isinstance(build_option, BuildOption):
                build_option = build_option.value
            if isinstance(refresh_option, MVRefreshOption):
                refresh_option = refresh_option.value
            
            # Валидация имени
            if not self._validate_view_name(view_name):
                return False, "Invalid view name", None
            
            # Проверка существования
            if not replace_if_exists and self._mv_exists(view_name):
                return False, f"Materialized view '{view_name}' already exists", None
            
            # Валидация запроса
            is_valid, error_msg = self._validate_mv_query(query)
            if not is_valid:
                return False, error_msg, None
            
            # Формируем имя материализованного представления
            mv_name = f"mv_{view_name}" if self.db_type == "sqlite" else view_name
            
            # Удаляем старое представление, если нужно
            if replace_if_exists and self._mv_exists(view_name):
                success, message = self.drop_materialized_view(view_name, cascade=False)
                if not success:
                    return False, f"Cannot replace view: {message}", None
            
            # Создаем представление
            if self.db_type == "postgresql":
                # PostgreSQL поддерживает материализованные представления нативно
                sql = self._build_postgresql_mv_sql(
                    mv_name, query, build_option, refresh_option
                )
            else:
                # Для других БД используем обычные представления с префиксом
                sql = f"CREATE VIEW {mv_name} AS\n{query}"
            
            # Выполняем создание
            self.db_manager.execute_query(sql)
            
            # Создаем индексы, если указаны
            if indexes:
                for index in indexes:
                    self.create_mv_index(mv_name, index)
            
            # Добавляем метаданные
            metadata = {
                'view_name': mv_name,
                'original_name': view_name,
                'build_option': build_option,
                'refresh_option': refresh_option,
                'incremental_column': incremental_column,
                'row_count': self._get_mv_row_count(mv_name),
                'estimated_size_kb': self._estimate_mv_size(mv_name)
            }
            self._update_metadata(metadata)
            
            # Если опция BUILD DEFERRED, создаем задачу на построение
            if build_option == BuildOption.DEFERRED.value:
                self._schedule_deferred_build(mv_name)
            
            return True, f"Materialized view '{view_name}' created successfully", mv_name
            
        except Exception as e:
            return False, f"Error creating materialized view: {str(e)}", None
    
    def refresh_materialized_view(
        self,
        view_name: str,
        refresh_type: Union[RefreshType, str] = RefreshType.COMPLETE,
        with_data: bool = True,
        parallel: bool = False,
        max_workers: Optional[int] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Обновление материализованного представления
        
        Args:
            view_name: Имя материализованного представления
            refresh_type: Тип обновления
            with_data: С данными или без
            parallel: Параллельное обновление
            max_workers: Максимальное количество рабочих потоков
            
        Returns:
            Кортеж (успех, сообщение, статистика обновления)
        """
        try:
            start_time = datetime.now()
            
            # Преобразуем enum в строку
            if isinstance(refresh_type, RefreshType):
                refresh_type = refresh_type.value
            
            # Проверка существования
            if not self._mv_exists(view_name):
                return False, f"Materialized view '{view_name}' does not exist", None
            
            # Получаем информацию о представлении
            mv_info = self.get_mv_details(view_name)
            if not mv_info:
                return False, f"Cannot get information about '{view_name}'", None
            
            # Выполняем обновление в зависимости от типа БД
            if self.db_type == "postgresql":
                success, message = self._refresh_postgresql_mv(
                    view_name, refresh_type, with_data, parallel
                )
            else:
                success, message = self._refresh_generic_mv(
                    view_name, refresh_type, mv_info
                )
            
            if not success:
                return False, message, None
            
            # Вычисляем время обновления
            end_time = datetime.now()
            refresh_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Обновляем метаданные
            self._update_refresh_stats(view_name, refresh_time_ms)
            
            # Формируем статистику
            stats = {
                'view_name': view_name,
                'refresh_type': refresh_type,
                'refresh_time_ms': refresh_time_ms,
                'refresh_timestamp': end_time.isoformat(),
                'rows_affected': self._get_mv_row_count(view_name),
                'size_kb': self._estimate_mv_size(view_name)
            }
            
            return True, f"Materialized view '{view_name}' refreshed successfully", stats
            
        except Exception as e:
            return False, f"Error refreshing materialized view: {str(e)}", None
    
    def drop_materialized_view(
        self,
        view_name: str,
        cascade: bool = False,
        including_indexes: bool = True
    ) -> Tuple[bool, str]:
        """
        Удаление материализованного представления
        
        Args:
            view_name: Имя представления
            cascade: Удалить зависимости
            including_indexes: Удалить связанные индексы
            
        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            # Получаем фактическое имя представления
            mv_name = view_name
            if not view_name.startswith('mv_') and self.db_type == "sqlite":
                mv_name = f"mv_{view_name}"
            
            # Проверка существования
            if not self._view_exists(mv_name):
                return False, f"Materialized view '{view_name}' does not exist"
            
            # Удаляем индексы, если нужно
            if including_indexes:
                indexes = self.get_mv_indexes(mv_name)
                for index in indexes:
                    self.drop_mv_index(index['index_name'])
            
            # Удаляем расписания
            self._delete_refresh_schedules(mv_name)
            
            # Удаляем метаданные
            self._delete_metadata(mv_name)
            
            # Удаляем статистику использования
            self._delete_usage_stats(mv_name)
            
            # Удаляем представление
            if self.db_type == "postgresql":
                cascade_clause = " CASCADE" if cascade else ""
                sql = f"DROP MATERIALIZED VIEW {mv_name}{cascade_clause}"
            else:
                sql = f"DROP VIEW {mv_name}"
            
            self.db_manager.execute_query(sql)
            
            return True, f"Materialized view '{view_name}' dropped successfully"
            
        except Exception as e:
            return False, f"Error dropping materialized view: {str(e)}"
    
    def get_mv_details(self, view_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации о материализованном представлении
        
        Args:
            view_name: Имя представления
            
        Returns:
            Словарь с детальной информацией или None
        """
        try:
            # Получаем фактическое имя
            mv_name = view_name
            if not view_name.startswith('mv_') and self.db_type == "sqlite":
                mv_name = f"mv_{view_name}"
            
            # Получаем базовую информацию из метаданных
            query = """
            SELECT 
                view_name, original_name, build_option, refresh_option,
                incremental_column, last_full_refresh, last_incremental_refresh,
                next_scheduled_refresh, refresh_count, avg_refresh_time_ms,
                estimated_size_kb, row_count, is_active, created_at
            FROM mv_system_metadata
            WHERE view_name = ? OR original_name = ?
            """
            
            results = self.db_manager.execute_query(query, (mv_name, view_name))
            
            if not results:
                return None
            
            row = results[0]
            mv_info = {
                'name': row[0],
                'original_name': row[1],
                'build_option': row[2],
                'refresh_option': row[3],
                'incremental_column': row[4],
                'last_full_refresh': row[5],
                'last_incremental_refresh': row[6],
                'next_scheduled_refresh': row[7],
                'refresh_count': row[8],
                'avg_refresh_time_ms': row[9],
                'estimated_size_kb': row[10],
                'row_count': row[11],
                'is_active': bool(row[12]),
                'created_at': row[13],
                'type': 'materialized view',
                'status': self._get_mv_status(row[0], row[5], row[7])
            }
            
            # Получаем структуру
            mv_info['structure'] = self.get_mv_structure(mv_name)
            
            # Получаем зависимости
            mv_info['dependencies'] = self.get_mv_dependencies(mv_name)
            
            # Получаем индексы
            mv_info['indexes'] = self.get_mv_indexes(mv_name)
            
            # Получаем расписания
            mv_info['schedules'] = self.get_refresh_schedule(mv_name)
            
            # Получаем статистику производительности
            mv_info['performance'] = self.get_performance_stats(mv_name)
            
            # Получаем данные (первые 5 строк)
            mv_info['sample_data'] = self.get_mv_data(mv_name, limit=5)
            
            # Получаем определение
            mv_info['definition'] = self.get_mv_definition(mv_name)
            
            # Получаем рекомендации по оптимизации
            mv_info['recommendations'] = self.get_optimization_recommendations(mv_name)
            
            return mv_info
            
        except Exception as e:
            print(f"Error getting MV details: {e}")
            return None
    
    def get_mv_structure(self, view_name: str) -> List[Dict[str, Any]]:
        """
        Получение структуры материализованного представления
        
        Args:
            view_name: Имя представления
            
        Returns:
            Список словарей с информацией о столбцах
        """
        try:
            if self.db_type == "sqlite":
                query = f"PRAGMA table_info({view_name})"
                results = self.db_manager.execute_query(query)
                
                columns = []
                for row in results:
                    column_info = {
                        'cid': row[0],
                        'name': row[1],
                        'type': row[2],
                        'notnull': bool(row[3]),
                        'default_value': row[4],
                        'pk': bool(row[5])
                    }
                    columns.append(column_info)
                
                return columns
            else:
                # Для других БД используем общий подход
                return self._get_generic_structure(view_name)
                
        except Exception as e:
            print(f"Error getting MV structure: {e}")
            return []
    
    def get_mv_data(
        self,
        view_name: str,
        limit: int = 100,
        offset: int = 0,
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение данных из материализованного представления
        
        Args:
            view_name: Имя представления
            limit: Ограничение количества строк
            offset: Смещение
            columns: Список столбцов для выборки (None для всех)
            
        Returns:
            Список словарей с данными
        """
        try:
            # Формируем SELECT часть
            if columns:
                select_clause = ", ".join(columns)
            else:
                select_clause = "*"
            
            query = f"SELECT {select_clause} FROM {view_name} LIMIT {limit} OFFSET {offset}"
            results = self.db_manager.execute_query(query)
            
            # Получаем информацию о столбцах
            structure = self.get_mv_structure(view_name)
            column_names = [col['name'] for col in structure]
            
            # Если указаны конкретные столбцы, используем их
            if columns and len(columns) <= len(column_names):
                column_names = columns
            
            # Формируем результат
            data = []
            for row in results:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(column_names):
                        row_dict[column_names[i]] = value
                    else:
                        row_dict[f'column_{i}'] = value
                data.append(row_dict)
            
            return data
            
        except Exception as e:
            print(f"Error getting MV data: {e}")
            return []
    
    def create_mv_index(
        self,
        view_name: str,
        index_config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Создание индекса для материализованного представления
        
        Args:
            view_name: Имя представления
            index_config: Конфигурация индекса
            
        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            index_name = index_config.get('name', f"idx_{view_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            columns = index_config.get('columns', [])
            is_unique = index_config.get('unique', False)
            index_type = index_config.get('type', 'BTREE')
            where_clause = index_config.get('where_clause')
            
            if not columns:
                return False, "Index must have at least one column"
            
            # Формируем SQL для создания индекса
            unique_clause = "UNIQUE " if is_unique else ""
            columns_clause = ", ".join(columns)
            
            sql = f"CREATE {unique_clause}INDEX {index_name} ON {view_name}({columns_clause})"
            
            if where_clause and self.db_type in ["sqlite", "postgresql"]:
                sql += f" WHERE {where_clause}"
            
            # Выполняем создание индекса
            self.db_manager.execute_query(sql)
            
            # Сохраняем информацию об индексе в метаданные
            self._save_index_metadata(view_name, index_name, columns, is_unique, index_type)
            
            return True, f"Index '{index_name}' created successfully"
            
        except Exception as e:
            return False, f"Error creating index: {str(e)}"
    
    def get_mv_indexes(self, view_name: str) -> List[Dict[str, Any]]:
        """
        Получение списка индексов материализованного представления
        
        Args:
            view_name: Имя представления
            
        Returns:
            Список индексов
        """
        try:
            query = """
            SELECT 
                index_name, columns, is_unique, index_type, created_at
            FROM mv_indexes 
            WHERE view_name = ?
            ORDER BY created_at
            """
            
            results = self.db_manager.execute_query(query, (view_name,))
            
            indexes = []
            for row in results:
                index_info = {
                    'index_name': row[0],
                    'columns': row[1].split(',') if row[1] else [],
                    'is_unique': bool(row[2]),
                    'type': row[3],
                    'created_at': row[4]
                }
                
                # Получаем статистику использования индекса
                index_info['usage_stats'] = self._get_index_usage_stats(view_name, row[0])
                
                indexes.append(index_info)
            
            return indexes
            
        except Exception as e:
            print(f"Error getting MV indexes: {e}")
            return []
    
    def drop_mv_index(self, index_name: str) -> Tuple[bool, str]:
        """
        Удаление индекса материализованного представления
        
        Args:
            index_name: Имя индекса
            
        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            # Удаляем индекс из БД
            sql = f"DROP INDEX IF EXISTS {index_name}"
            self.db_manager.execute_query(sql)
            
            # Удаляем информацию из метаданных
            delete_sql = "DELETE FROM mv_indexes WHERE index_name = ?"
            self.db_manager.execute_query(delete_sql, (index_name,))
            
            return True, f"Index '{index_name}' dropped successfully"
            
        except Exception as e:
            return False, f"Error dropping index: {str(e)}"
    
    def add_refresh_schedule(
        self,
        view_name: str,
        schedule_type: str,
        schedule_time: Optional[str] = None,
        interval_minutes: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Добавление расписания обновления
        
        Args:
            view_name: Имя представления
            schedule_type: Тип расписания (HOURLY, DAILY, WEEKLY, MONTHLY, CUSTOM)
            schedule_time: Время запуска (для DAILY, WEEKLY, MONTHLY)
            interval_minutes: Интервал в минутах (для HOURLY, CUSTOM)
            start_date: Дата начала
            end_date: Дата окончания
            
        Returns:
            Кортеж (успех, сообщение, ID расписания)
        """
        try:
            # Получаем фактическое имя
            mv_name = view_name
            if not view_name.startswith('mv_') and self.db_type == "sqlite":
                mv_name = f"mv_{view_name}"
            
            # Проверяем существование представления
            if not self._mv_exists(view_name):
                return False, f"Materialized view '{view_name}' does not exist", None
            
            # Рассчитываем следующее время запуска
            next_run = self._calculate_next_run(
                schedule_type, schedule_time, interval_minutes
            )
            
            # Добавляем расписание в БД
            query = """
            INSERT INTO mv_refresh_schedules 
            (view_name, schedule_type, schedule_interval, schedule_time, next_run)
            VALUES (?, ?, ?, ?, ?)
            """
            
            schedule_interval = f"{interval_minutes} minutes" if interval_minutes else None
            
            self.db_manager.execute_query(
                query, 
                (mv_name, schedule_type, schedule_interval, schedule_time, next_run)
            )
            
            # Получаем ID созданного расписания
            schedule_id = self.db_manager.execute_query("SELECT last_insert_rowid()")[0][0]
            
            # Обновляем информацию о следующем запланированном обновлении в метаданных
            self._update_next_scheduled_refresh(mv_name)
            
            return True, f"Refresh schedule added for '{view_name}'", schedule_id
            
        except Exception as e:
            return False, f"Error adding refresh schedule: {str(e)}", None
    
    def get_refresh_schedule(self, view_name: str) -> List[Dict[str, Any]]:
        """
        Получение расписаний обновления представления
        
        Args:
            view_name: Имя представления
            
        Returns:
            Список расписаний
        """
        try:
            mv_name = view_name
            if not view_name.startswith('mv_') and self.db_type == "sqlite":
                mv_name = f"mv_{view_name}"
            
            query = """
            SELECT 
                schedule_id, schedule_type, schedule_interval, schedule_time,
                is_active, last_run, next_run, run_count, created_at
            FROM mv_refresh_schedules
            WHERE view_name = ?
            ORDER BY next_run
            """
            
            results = self.db_manager.execute_query(query, (mv_name,))
            
            schedules = []
            for row in results:
                schedule = {
                    'id': row[0],
                    'type': row[1],
                    'interval': row[2],
                    'time': row[3],
                    'is_active': bool(row[4]),
                    'last_run': row[5],
                    'next_run': row[6],
                    'run_count': row[7],
                    'created_at': row[8]
                }
                schedules.append(schedule)
            
            return schedules
            
        except Exception as e:
            print(f"Error getting refresh schedules: {e}")
            return []
    
    def remove_refresh_schedule(self, schedule_id: int) -> Tuple[bool, str]:
        """
        Удаление расписания обновления
        
        Args:
            schedule_id: ID расписания
            
        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            # Получаем информацию о расписании
            query = "SELECT view_name FROM mv_refresh_schedules WHERE schedule_id = ?"
            results = self.db_manager.execute_query(query, (schedule_id,))
            
            if not results:
                return False, f"Schedule with ID {schedule_id} does not exist"
            
            view_name = results[0][0]
            
            # Удаляем расписание
            delete_query = "DELETE FROM mv_refresh_schedules WHERE schedule_id = ?"
            self.db_manager.execute_query(delete_query, (schedule_id,))
            
            # Обновляем информацию о следующем запланированном обновлении
            self._update_next_scheduled_refresh(view_name)
            
            return True, f"Schedule {schedule_id} removed successfully"
            
        except Exception as e:
            return False, f"Error removing schedule: {str(e)}"
    
    def run_scheduled_refreshes(self) -> Dict[str, Any]:
        """
        Запуск запланированных обновлений
        
        Returns:
            Статистика выполнения
        """
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Находим расписания, которые нужно выполнить
            query = """
            SELECT 
                schedule_id, view_name, schedule_type
            FROM mv_refresh_schedules
            WHERE is_active = TRUE 
            AND (next_run <= ? OR next_run IS NULL)
            ORDER BY next_run
            """
            
            schedules = self.db_manager.execute_query(query, (now,))
            
            stats = {
                'total_scheduled': len(schedules),
                'successful': 0,
                'failed': 0,
                'total_time_ms': 0,
                'details': []
            }
            
            for schedule in schedules:
                schedule_id, view_name, schedule_type = schedule
                
                try:
                    # Запускаем обновление
                    start_time = datetime.now()
                    
                    success, message, refresh_stats = self.refresh_materialized_view(
                        view_name, 
                        refresh_type=RefreshType.COMPLETE
                    )
                    
                    end_time = datetime.now()
                    execution_time = int((end_time - start_time).total_seconds() * 1000)
                    
                    if success:
                        stats['successful'] += 1
                        # Обновляем информацию о расписании
                        self._update_schedule_after_run(schedule_id, True)
                        
                        detail = {
                            'view_name': view_name,
                            'schedule_id': schedule_id,
                            'status': 'SUCCESS',
                            'message': message,
                            'execution_time_ms': execution_time,
                            'refresh_stats': refresh_stats
                        }
                    else:
                        stats['failed'] += 1
                        self._update_schedule_after_run(schedule_id, False)
                        
                        detail = {
                            'view_name': view_name,
                            'schedule_id': schedule_id,
                            'status': 'FAILED',
                            'message': message,
                            'execution_time_ms': execution_time
                        }
                    
                    stats['details'].append(detail)
                    stats['total_time_ms'] += execution_time
                    
                except Exception as e:
                    stats['failed'] += 1
                    self._update_schedule_after_run(schedule_id, False)
                    
                    detail = {
                        'view_name': view_name,
                        'schedule_id': schedule_id,
                        'status': 'ERROR',
                        'message': str(e),
                        'execution_time_ms': 0
                    }
                    stats['details'].append(detail)
            
            return stats
            
        except Exception as e:
            return {
                'total_scheduled': 0,
                'successful': 0,
                'failed': 0,
                'total_time_ms': 0,
                'error': str(e),
                'details': []
            }
    
    def get_performance_stats(self, view_name: str) -> Dict[str, Any]:
        """
        Получение статистики производительности
        
        Args:
            view_name: Имя представления
            
        Returns:
            Словарь со статистикой
        """
        try:
            mv_name = view_name
            if not view_name.startswith('mv_') and self.db_type == "sqlite":
                mv_name = f"mv_{view_name}"
            
            # Статистика из метаданных
            query = """
            SELECT 
                refresh_count, avg_refresh_time_ms, estimated_size_kb, row_count
            FROM mv_system_metadata
            WHERE view_name = ?
            """
            
            results = self.db_manager.execute_query(query, (mv_name,))
            
            if not results:
                return {}
            
            row = results[0]
            stats = {
                'refresh_count': row[0],
                'avg_refresh_time_ms': row[1],
                'size_kb': row[2],
                'row_count': row[3],
                'avg_row_size_bytes': row[2] * 1024 // max(row[3], 1) if row[3] > 0 else 0
            }
            
            # Статистика использования
            usage_query = """
            SELECT 
                SUM(query_count) as total_queries,
                AVG(avg_execution_time_ms) as avg_query_time,
                SUM(cache_hits) as cache_hits,
                SUM(cache_misses) as cache_misses
            FROM mv_usage_stats
            WHERE view_name = ?
            GROUP BY view_name
            """
            
            usage_results = self.db_manager.execute_query(usage_query, (mv_name,))
            
            if usage_results and usage_results[0][0]:
                usage_row = usage_results[0]
                stats.update({
                    'total_queries': usage_row[0],
                    'avg_query_time_ms': usage_row[1],
                    'cache_hits': usage_row[2],
                    'cache_misses': usage_row[3],
                    'cache_hit_ratio': usage_row[2] / max(usage_row[2] + usage_row[3], 1) * 100
                })
            
            return stats
            
        except Exception as e:
            print(f"Error getting performance stats: {e}")
            return {}
    
    def get_optimization_recommendations(self, view_name: str) -> List[Dict[str, Any]]:
        """
        Получение рекомендаций по оптимизации
        
        Args:
            view_name: Имя представления
            
        Returns:
            Список рекомендаций
        """
        try:
            recommendations = []
            
            # Получаем информацию о представлении
            mv_info = self.get_mv_details(view_name)
            if not mv_info:
                return recommendations
            
            # Проверка на наличие индексов
            indexes = mv_info.get('indexes', [])
            if not indexes:
                recommendations.append({
                    'type': 'INDEX',
                    'priority': 'HIGH',
                    'description': 'No indexes found. Consider adding indexes for frequently queried columns.',
                    'suggestion': 'Analyze query patterns and create appropriate indexes.'
                })
            
            # Проверка размера
            size_kb = mv_info.get('estimated_size_kb', 0)
            if size_kb > 1024 * 100:  # Больше 100 MB
                recommendations.append({
                    'type': 'SIZE',
                    'priority': 'MEDIUM',
                    'description': f'Materialized view is large ({size_kb} KB).',
                    'suggestion': 'Consider partitioning or archiving old data.'
                })
            
            # Проверка частоты обновления
            refresh_count = mv_info.get('refresh_count', 0)
            last_refresh = mv_info.get('last_full_refresh')
            
            if last_refresh:
                last_refresh_date = datetime.fromisoformat(last_refresh.replace('Z', '+00:00'))
                days_since_refresh = (datetime.now() - last_refresh_date).days
                
                if days_since_refresh > 7 and refresh_count > 0:
                    recommendations.append({
                        'type': 'REFRESH',
                        'priority': 'LOW',
                        'description': f'Last refresh was {days_since_refresh} days ago.',
                        'suggestion': 'Consider more frequent refreshes if data changes often.'
                    })
            
            # Проверка эффективности
            performance = mv_info.get('performance', {})
            avg_refresh_time = performance.get('avg_refresh_time_ms', 0)
            
            if avg_refresh_time > 60000:  # Больше 60 секунд
                recommendations.append({
                    'type': 'PERFORMANCE',
                    'priority': 'HIGH',
                    'description': f'Average refresh time is {avg_refresh_time/1000:.1f} seconds.',
                    'suggestion': 'Consider incremental refreshes or optimizing the underlying query.'
                })
            
            return recommendations
            
        except Exception as e:
            print(f"Error getting optimization recommendations: {e}")
            return []
    
    def export_materialized_view(
        self,
        view_name: str,
        format: str = "sql",
        include_data: bool = False,
        data_limit: int = 1000
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Экспорт материализованного представления
        
        Args:
            view_name: Имя представления
            format: Формат экспорта (sql, json, csv)
            include_data: Включить данные
            data_limit: Ограничение на количество экспортируемых строк
            
        Returns:
            Кортеж (успех, сообщение, данные)
        """
        try:
            # Получаем информацию о представлении
            mv_info = self.get_mv_details(view_name)
            if not mv_info:
                return False, f"Materialized view '{view_name}' not found", None
            
            # Получаем определение
            definition = self.get_mv_definition(view_name)
            
            if format == "sql":
                # Экспорт в SQL формате
                export_data = f"-- Materialized View: {view_name}\n"
                export_data += f"-- Created: {mv_info.get('created_at', 'N/A')}\n"
                export_data += f"-- Last Refresh: {mv_info.get('last_full_refresh', 'Never')}\n"
                export_data += f"-- Row Count: {mv_info.get('row_count', 0)}\n"
                export_data += f"-- Size: {mv_info.get('estimated_size_kb', 0)} KB\n\n"
                
                export_data += definition + "\n\n"
                
                if include_data:
                    data = self.get_mv_data(view_name, limit=data_limit)
                    if data:
                        export_data += "-- Sample Data:\n"
                        columns = list(data[0].keys())
                        export_data += f"-- Columns: {', '.join(columns)}\n\n"
                        
                        for i, row in enumerate(data, 1):
                            values = []
                            for col in columns:
                                val = row.get(col)
                                if val is None:
                                    values.append("NULL")
                                elif isinstance(val, str):
                                    values.append(f"'{val.replace("'", "''")}'")
                                else:
                                    values.append(str(val))
                            
                            insert_sql = f"INSERT INTO {view_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                            export_data += insert_sql + "\n"
            
            elif format == "json":
                # Экспорт в JSON формате
                export_dict = {
                    'metadata': mv_info,
                    'definition': definition
                }
                
                if include_data:
                    data = self.get_mv_data(view_name, limit=data_limit)
                    export_dict['sample_data'] = data
                
                export_data = json.dumps(export_dict, indent=2, default=str, ensure_ascii=False)
            
            elif format == "csv":
                # Экспорт в CSV формате (только данные)
                if not include_data:
                    return False, "CSV export requires include_data=True", None
                
                data = self.get_mv_data(view_name, limit=data_limit)
                if not data:
                    return False, "No data to export", None
                
                columns = list(data[0].keys())
                csv_lines = [','.join(columns)]
                
                for row in data:
                    values = []
                    for col in columns:
                        val = row.get(col)
                        if val is None:
                            values.append('')
                        elif isinstance(val, str):
                            # Экранируем кавычки и запятые
                            escaped = str(val).replace('"', '""')
                            if ',' in escaped or '"' in escaped or '\n' in escaped:
                                values.append(f'"{escaped}"')
                            else:
                                values.append(escaped)
                        else:
                            values.append(str(val))
                    
                    csv_lines.append(','.join(values))
                
                export_data = '\n'.join(csv_lines)
            
            else:
                return False, f"Unsupported format: {format}", None
            
            return True, "Export successful", export_data
            
        except Exception as e:
            return False, f"Error exporting materialized view: {str(e)}", None
    
    def get_mv_definition(self, view_name: str) -> str:
        """
        Получение SQL определения материализованного представления
        
        Args:
            view_name: Имя представления
            
        Returns:
            SQL определение
        """
        try:
            if self.db_type == "sqlite":
                query = "SELECT sql FROM sqlite_master WHERE type='view' AND name=?"
                results = self.db_manager.execute_query(query, (view_name,))
                
                if results and results[0][0]:
                    return results[0][0]
            
            # Для других БД или если не нашли
            return f"-- Definition for {view_name} not available in system tables"
            
        except Exception as e:
            return f"-- Error getting definition: {str(e)}"
    
    def get_mv_dependencies(self, view_name: str) -> List[Dict[str, Any]]:
        """
        Получение зависимостей материализованного представления
        
        Args:
            view_name: Имя представления
            
        Returns:
            Список зависимостей
        """
        try:
            # Получаем определение
            definition = self.get_mv_definition(view_name)
            
            # Извлекаем таблицы из SQL
            tables = self._extract_table_references(definition)
            
            dependencies = []
            for table in tables:
                # Проверяем тип объекта
                if table.startswith('mv_'):
                    dep_type = 'materialized view'
                elif self._view_exists(table):
                    dep_type = 'view'
                elif self._table_exists(table):
                    dep_type = 'table'
                else:
                    dep_type = 'unknown'
                
                dependencies.append({
                    'name': table,
                    'type': dep_type,
                    'relation': 'source'
                })
            
            return dependencies
            
        except Exception as e:
            print(f"Error getting MV dependencies: {e}")
            return []
    
    # Вспомогательные методы
    
    def _validate_view_name(self, name: str) -> bool:
        """Валидация имени представления"""
        if not name or not name.strip():
            return False
        
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, name))
    
    def _validate_mv_query(self, query: str) -> Tuple[bool, str]:
        """Валидация запроса для материализованного представления"""
        if not query or not query.strip():
            return False, "Query is empty"
        
        query_upper = query.strip().upper()
        
        # Проверяем, что это SELECT запрос
        if not query_upper.startswith("SELECT"):
            return False, "Materialized view must be based on SELECT query"
        
        # Проверяем на наличие запрещенных операций
        forbidden = [
            "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER",
            "TRUNCATE", "COMMIT", "ROLLBACK", "SAVEPOINT"
        ]
        
        for forbidden_op in forbidden:
            if forbidden_op in query_upper:
                return False, f"Query cannot contain {forbidden_op} operations"
        
        return True, "Query is valid"
    
    def _mv_exists(self, view_name: str) -> bool:
        """Проверка существования материализованного представления"""
        try:
            # Проверяем в метаданных
            query = "SELECT 1 FROM mv_system_metadata WHERE (view_name = ? OR original_name = ?) AND is_materialized = TRUE"
            results = self.db_manager.execute_query(query, (view_name, view_name))
            
            if results:
                return True
            
            # Проверяем в системных таблицах
            actual_name = f"mv_{view_name}" if self.db_type == "sqlite" else view_name
            
            if self.db_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='view' AND name=?"
                results = self.db_manager.execute_query(query, (actual_name,))
            elif self.db_type == "postgresql":
                query = "SELECT matviewname FROM pg_matviews WHERE matviewname=?"
                results = self.db_manager.execute_query(query, (actual_name,))
            
            return bool(results)
            
        except:
            return False
    
    def _view_exists(self, view_name: str) -> bool:
        """Проверка существования обычного представления"""
        try:
            if self.db_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='view' AND name=?"
                results = self.db_manager.execute_query(query, (view_name,))
            elif self.db_type == "postgresql":
                query = "SELECT table_name FROM information_schema.views WHERE table_name=?"
                results = self.db_manager.execute_query(query, (view_name,))
            
            return bool(results)
        except:
            return False
    
    def _table_exists(self, table_name: str) -> bool:
        """Проверка существования таблицы"""
        try:
            if self.db_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
                results = self.db_manager.execute_query(query, (table_name,))
            elif self.db_type == "postgresql":
                query = "SELECT table_name FROM information_schema.tables WHERE table_name=?"
                results = self.db_manager.execute_query(query, (table_name,))
            
            return bool(results)
        except:
            return False
    
    def _estimate_mv_size(self, view_name: str) -> int:
        """Оценка размера материализованного представления"""
        try:
            count_query = f"SELECT COUNT(*) FROM {view_name}"
            result = self.db_manager.execute_query(count_query)
            
            if result:
                row_count = result[0][0]
                # Предполагаем ~100 байт на строку
                size_bytes = row_count * 100
                return size_bytes // 1024  # КБ
            
            return 0
        except:
            return 0
    
    def _get_mv_row_count(self, view_name: str) -> int:
        """Получение количества строк в материализованном представлении"""
        try:
            count_query = f"SELECT COUNT(*) FROM {view_name}"
            result = self.db_manager.execute_query(count_query)
            
            if result:
                return result[0][0]
            
            return 0
        except:
            return 0
    
    def _get_mv_status(self, view_name: str, last_refresh: Optional[str], next_refresh: Optional[str]) -> str:
        """Определение статуса материализованного представления"""
        try:
            if not self._mv_exists(view_name):
                return "NOT EXISTS"
            
            if last_refresh is None:
                return "NEVER REFRESHED"
            
            # Проверяем, не устарели ли данные
            if last_refresh:
                last_refresh_date = datetime.fromisoformat(last_refresh.replace('Z', '+00:00'))
                days_since_refresh = (datetime.now() - last_refresh_date).days
                
                if days_since_refresh > 30:
                    return "STALE"
                elif days_since_refresh > 7:
                    return "OUTDATED"
            
            return "ACTIVE"
        except:
            return "UNKNOWN"
    
    def _add_to_metadata(self, mv_info: Dict[str, Any]):
        """Добавление материализованного представления в метаданные"""
        try:
            query = """
            INSERT OR REPLACE INTO mv_system_metadata 
            (view_name, original_name, is_materialized, build_option, refresh_option, 
             last_full_refresh, estimated_size_kb, row_count, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.db_manager.execute_query(
                query,
                (
                    mv_info['name'],
                    mv_info['original_name'],
                    mv_info['is_materialized'],
                    mv_info['build_option'],
                    mv_info['refresh_option'],
                    now,
                    mv_info['size_kb'],
                    mv_info['row_count'],
                    mv_info['is_active']
                )
            )
        except Exception as e:
            print(f"Error adding to metadata: {e}")
    
    def _update_metadata(self, metadata: Dict[str, Any]):
        """Обновление метаданных материализованного представления"""
        try:
            view_name = metadata['view_name']
            
            # Строим динамический UPDATE запрос
            set_clauses = []
            params = []
            
            for key, value in metadata.items():
                if key != 'view_name':
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            
            params.append(view_name)
            
            query = f"UPDATE mv_system_metadata SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE view_name = ?"
            
            self.db_manager.execute_query(query, tuple(params))
        except Exception as e:
            print(f"Error updating metadata: {e}")
    
    def _update_refresh_stats(self, view_name: str, refresh_time_ms: int):
        """Обновление статистики обновления"""
        try:
            # Получаем текущую статистику
            query = """
            SELECT refresh_count, total_refresh_time_ms 
            FROM mv_system_metadata 
            WHERE view_name = ?
            """
            
            results = self.db_manager.execute_query(query, (view_name,))
            
            if results:
                current_count = results[0][0]
                current_total_time = results[0][1] or 0
                
                new_count = current_count + 1
                new_total_time = current_total_time + refresh_time_ms
                new_avg_time = new_total_time // new_count
                
                # Обновляем
                update_query = """
                UPDATE mv_system_metadata 
                SET refresh_count = ?, 
                    total_refresh_time_ms = ?,
                    avg_refresh_time_ms = ?,
                    last_full_refresh = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE view_name = ?
                """
                
                self.db_manager.execute_query(
                    update_query,
                    (new_count, new_total_time, new_avg_time, view_name)
                )
        except Exception as e:
            print(f"Error updating refresh stats: {e}")
    
    def _delete_metadata(self, view_name: str):
        """Удаление метаданных материализованного представления"""
        try:
            query = "DELETE FROM mv_system_metadata WHERE view_name = ?"
            self.db_manager.execute_query(query, (view_name,))
        except:
            pass
    
    def _delete_usage_stats(self, view_name: str):
        """Удаление статистики использования"""
        try:
            query = "DELETE FROM mv_usage_stats WHERE view_name = ?"
            self.db_manager.execute_query(query, (view_name,))
        except:
            pass
    
    def _delete_refresh_schedules(self, view_name: str):
        """Удаление расписаний обновления"""
        try:
            query = "DELETE FROM mv_refresh_schedules WHERE view_name = ?"
            self.db_manager.execute_query(query, (view_name,))
        except:
            pass
    
    def _build_postgresql_mv_sql(
        self,
        view_name: str,
        query: str,
        build_option: str,
        refresh_option: str
    ) -> str:
        """Построение SQL для создания материализованного представления в PostgreSQL"""
        sql = f"CREATE MATERIALIZED VIEW {view_name}"
        
        if build_option == BuildOption.DEFERRED.value:
            sql += " WITH NO DATA"
        else:
            sql += " AS"
        
        sql += f"\n{query}"
        
        if refresh_option:
            sql += f"\nWITH {refresh_option}"
        
        return sql + ";"
    
    def _refresh_postgresql_mv(
        self,
        view_name: str,
        refresh_type: str,
        with_data: bool,
        parallel: bool
    ) -> Tuple[bool, str]:
        """Обновление материализованного представления в PostgreSQL"""
        try:
            sql = "REFRESH MATERIALIZED VIEW "
            
            if refresh_type == RefreshType.CONCURRENTLY.value and parallel:
                sql += "CONCURRENTLY "
            
            sql += view_name
            
            if not with_data:
                sql += " WITH NO DATA"
            
            self.db_manager.execute_query(sql + ";")
            return True, "Refresh successful"
        except Exception as e:
            return False, str(e)
    
    def _refresh_generic_mv(
        self,
        view_name: str,
        refresh_type: str,
        mv_info: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Обновление материализованного представления (общий метод)"""
        try:
            # Получаем определение представления
            definition = self.get_mv_definition(view_name)
            
            if not definition:
                return False, "Cannot get view definition"
            
            # Извлекаем SELECT запрос
            if " AS " in definition.upper():
                select_query = definition.upper().split(" AS ", 1)[1].strip()
                if select_query.endswith(';'):
                    select_query = select_query[:-1]
            else:
                select_query = f"SELECT * FROM {view_name}"
            
            # Для инкрементального обновления
            if refresh_type == RefreshType.INCREMENTAL.value and mv_info.get('incremental_column'):
                incremental_col = mv_info['incremental_column']
                last_refresh = mv_info.get('last_full_refresh')
                
                if last_refresh:
                    # Добавляем условие для инкрементального обновления
                    if "WHERE" in select_query.upper():
                        select_query += f" AND {incremental_col} > '{last_refresh}'"
                    else:
                        select_query += f" WHERE {incremental_col} > '{last_refresh}'"
            
            # Пересоздаем представление
            drop_sql = f"DROP VIEW IF EXISTS {view_name}"
            create_sql = f"CREATE VIEW {view_name} AS {select_query}"
            
            self.db_manager.execute_query(drop_sql)
            self.db_manager.execute_query(create_sql)
            
            return True, "Refresh successful"
        except Exception as e:
            return False, str(e)
    
    def _save_index_metadata(
        self,
        view_name: str,
        index_name: str,
        columns: List[str],
        is_unique: bool,
        index_type: str
    ):
        """Сохранение информации об индексе в метаданные"""
        try:
            query = """
            INSERT OR REPLACE INTO mv_indexes 
            (index_name, view_name, columns, is_unique, index_type)
            VALUES (?, ?, ?, ?, ?)
            """
            
            columns_str = ",".join(columns)
            
            self.db_manager.execute_query(
                query,
                (index_name, view_name, columns_str, is_unique, index_type)
            )
        except Exception as e:
            print(f"Error saving index metadata: {e}")
    
    def _get_index_usage_stats(self, view_name: str, index_name: str) -> Dict[str, Any]:
        """Получение статистики использования индекса"""
        # В реальном приложении здесь была бы логика сбора статистики
        # Для демонстрации возвращаем заглушку
        return {
            'scans': 0,
            'reads': 0,
            'last_used': None
        }
    
    def _calculate_next_run(
        self,
        schedule_type: str,
        schedule_time: Optional[str],
        interval_minutes: Optional[int]
    ) -> str:
        """Вычисление времени следующего запуска"""
        now = datetime.now()
        
        if schedule_type == "HOURLY":
            if interval_minutes:
                next_run = now + timedelta(minutes=interval_minutes)
            else:
                next_run = now + timedelta(hours=1)
        
        elif schedule_type == "DAILY":
            if schedule_time:
                # Парсим время HH:MM
                hour, minute = map(int, schedule_time.split(':'))
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
            else:
                next_run = now + timedelta(days=1)
        
        elif schedule_type == "WEEKLY":
            next_run = now + timedelta(weeks=1)
            if schedule_time:
                hour, minute = map(int, schedule_time.split(':'))
                next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        elif schedule_type == "MONTHLY":
            # Первое число следующего месяца
            if now.month == 12:
                next_run = datetime(now.year + 1, 1, 1)
            else:
                next_run = datetime(now.year, now.month + 1, 1)
        
        else:  # CUSTOM
            if interval_minutes:
                next_run = now + timedelta(minutes=interval_minutes)
            else:
                next_run = now + timedelta(days=1)
        
        return next_run.strftime('%Y-%m-%d %H:%M:%S')
    
    def _update_next_scheduled_refresh(self, view_name: str):
        """Обновление информации о следующем запланированном обновлении"""
        try:
            # Находим ближайшее запланированное обновление
            query = """
            SELECT MIN(next_run) 
            FROM mv_refresh_schedules 
            WHERE view_name = ? AND is_active = TRUE
            """
            
            results = self.db_manager.execute_query(query, (view_name,))
            
            next_run = results[0][0] if results and results[0][0] else None
            
            # Обновляем метаданные
            update_query = """
            UPDATE mv_system_metadata 
            SET next_scheduled_refresh = ?
            WHERE view_name = ?
            """
            
            self.db_manager.execute_query(update_query, (next_run, view_name))
        except Exception as e:
            print(f"Error updating next scheduled refresh: {e}")
    
    def _update_schedule_after_run(self, schedule_id: int, success: bool):
        """Обновление расписания после выполнения"""
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Получаем информацию о расписании
            query = """
            SELECT schedule_type, schedule_interval, schedule_time 
            FROM mv_refresh_schedules 
            WHERE schedule_id = ?
            """
            
            results = self.db_manager.execute_query(query, (schedule_id,))
            
            if not results:
                return
            
            schedule_type, schedule_interval, schedule_time = results[0]
            
            # Рассчитываем следующее время запуска
            interval_minutes = None
            if schedule_interval:
                # Извлекаем минуты из строки "X minutes"
                match = re.search(r'(\d+)\s+minutes', schedule_interval)
                if match:
                    interval_minutes = int(match.group(1))
            
            next_run = self._calculate_next_run(schedule_type, schedule_time, interval_minutes)
            
            # Обновляем расписание
            update_query = """
            UPDATE mv_refresh_schedules 
            SET last_run = ?, 
                next_run = ?, 
                run_count = run_count + 1
            WHERE schedule_id = ?
            """
            
            self.db_manager.execute_query(update_query, (now, next_run, schedule_id))
        except Exception as e:
            print(f"Error updating schedule after run: {e}")
    
    def _schedule_deferred_build(self, view_name: str):
        """Планирование отложенного построения"""
        try:
            # Добавляем задание на ближайшее время
            self.add_refresh_schedule(
                view_name=view_name,
                schedule_type="CUSTOM",
                interval_minutes=1,  # Через 1 минуту
                start_date=datetime.now().strftime('%Y-%m-%d')
            )
        except Exception as e:
            print(f"Error scheduling deferred build: {e}")
    
    def _extract_table_references(self, sql: str) -> List[str]:
        """Извлечение ссылок на таблицы из SQL"""
        try:
            tables = set()
            
            patterns = [
                r'FROM\s+([\w]+)',
                r'JOIN\s+([\w]+)',
                r'UPDATE\s+([\w]+)',
                r'INTO\s+([\w]+)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, sql, re.IGNORECASE)
                for match in matches:
                    table_name = match.group(1).strip()
                    if table_name:
                        tables.add(table_name)
            
            return list(tables)
        except:
            return []
    
    def _get_generic_structure(self, view_name: str) -> List[Dict[str, Any]]:
        """Получение структуры представления (общий метод)"""
        try:
            # Получаем одну строку для анализа структуры
            query = f"SELECT * FROM {view_name} LIMIT 1"
            result = self.db_manager.execute_query(query)
            
            if not result:
                return []
            
            # Получаем информацию о столбцах из курсора
            columns = []
            cursor = self.db_manager.execute_query(query, return_cursor=True)
            
            if cursor and cursor.description:
                for i, desc in enumerate(cursor.description):
                    column_info = {
                        'cid': i,
                        'name': desc[0],
                        'type': desc[1] if len(desc) > 1 else 'TEXT',
                        'notnull': False,
                        'default_value': None,
                        'pk': False
                    }
                    columns.append(column_info)
            
            return columns
            
        except Exception as e:
            print(f"Error getting generic structure: {e}")
            return []


# Вспомогательные функции
def create_materialized_view_api(db_manager) -> MaterializedViewAPI:
    """
    Создание экземпляра MaterializedViewAPI
    
    Args:
        db_manager: Экземпляр DBManager
        
    Returns:
        Экземпляр MaterializedViewAPI
    """
    return MaterializedViewAPI(db_manager)


if __name__ == "__main__":
    # Демонстрация работы API
    print("=== Materialized View API Demo ===\n")
    
    # Пример использования
    try:
        from db_manager import DBManager
        
        # Создаем подключение к БД в памяти
        db_manager = DBManager(":memory:")
        
        # Создаем API
        mv_api = MaterializedViewAPI(db_manager)
        
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
        
        print("1. Creating materialized view...")
        success, message, mv_name = mv_api.create_materialized_view(
            view_name="attack_stats",
            query="SELECT attack_type, severity, COUNT(*) as count, AVG(danger) as avg_danger FROM attacks GROUP BY attack_type, severity",
            build_option=BuildOption.IMMEDIATE,
            refresh_option=MVRefreshOption.ON_DEMAND
        )
        print(f"   Result: {message}")
        if success:
            print(f"   Created as: {mv_name}")
        
        print("\n2. Getting all materialized views...")
        mvs = mv_api.get_all_materialized_views()
        print(f"   Found {len(mvs)} materialized views")
        for mv in mvs:
            print(f"   - {mv['name']}: {mv['row_count']} rows, last refresh: {mv['last_refresh'] or 'Never'}")
        
        print("\n3. Getting MV details...")
        if mvs:
            details = mv_api.get_mv_details(mvs[0]['name'])
            if details:
                print(f"   View: {details['name']}")
                print(f"   Columns: {len(details.get('structure', []))}")
                print(f"   Indexes: {len(details.get('indexes', []))}")
                print(f"   Refresh count: {details.get('refresh_count', 0)}")
        
        print("\n4. Adding refresh schedule...")
        success, message, schedule_id = mv_api.add_refresh_schedule(
            view_name="attack_stats",
            schedule_type="DAILY",
            schedule_time="02:00"
        )
        print(f"   Result: {message}")
        if success:
            print(f"   Schedule ID: {schedule_id}")
        
        print("\n5. Getting refresh schedules...")
        schedules = mv_api.get_refresh_schedule("attack_stats")
        print(f"   Found {len(schedules)} schedules")
        for schedule in schedules:
            print(f"   - {schedule['type']} at {schedule['time']}, next: {schedule['next_run']}")
        
        print("\n6. Creating index...")
        success, message = mv_api.create_mv_index(
            view_name="mv_attack_stats",
            index_config={
                'name': 'idx_attack_stats_type',
                'columns': ['attack_type', 'severity'],
                'unique': False
            }
        )
        print(f"   Result: {message}")
        
        print("\n7. Getting performance stats...")
        stats = mv_api.get_performance_stats("attack_stats")
        print(f"   Refresh count: {stats.get('refresh_count', 0)}")
        print(f"   Avg refresh time: {stats.get('avg_refresh_time_ms', 0)} ms")
        print(f"   Size: {stats.get('size_kb', 0)} KB")
        
        print("\n8. Exporting MV definition...")
        success, message, export_data = mv_api.export_materialized_view(
            view_name="attack_stats",
            format="sql",
            include_data=True,
            data_limit=3
        )
        if success:
            print(f"   Export successful ({len(export_data)} chars)")
            print(f"   First 200 chars: {export_data[:200]}...")
        
        print("\n9. Running scheduled refreshes...")
        refresh_stats = mv_api.run_scheduled_refreshes()
        print(f"   Scheduled: {refresh_stats.get('total_scheduled', 0)}")
        print(f"   Successful: {refresh_stats.get('successful', 0)}")
        print(f"   Failed: {refresh_stats.get('failed', 0)}")
        
        print("\n10. Dropping materialized view...")
        success, message = mv_api.drop_materialized_view("attack_stats")
        print(f"   Result: {message}")
        
        db_manager.close_connection()
        
        print("\n=== Demo completed ===")
        
    except ImportError:
        print("DBManager not available for demo")
    except Exception as e:
        print(f"Demo error: {e}")