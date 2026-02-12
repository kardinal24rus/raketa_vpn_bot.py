"""
Модуль для работы с базой данных SQLite
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = 'bot_database.db'):
        """Инициализация базы данных"""
        self.db_path = db_path
        self.create_tables()
    
    def get_connection(self) -> sqlite3.Connection:
        """Создание подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_tables(self) -> None:
        """Создание таблиц в БД"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица поисковых запросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                search_name TEXT NOT NULL,
                additional_info TEXT,
                results_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица найденных результатов (кэш)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                name TEXT,
                url TEXT,
                info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES search_queries (id)
            )
        ''')
        
        # Таблица статистики
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Таблицы созданы/проверены")
    
    def add_user(
        self, 
        user_id: int, 
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> None:
        """Добавление или обновление пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_activity = CURRENT_TIMESTAMP
        ''', (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
        logger.info(f"Пользователь {user_id} добавлен/обновлен")
    
    def add_search_query(
        self,
        user_id: int,
        search_name: str,
        additional_info: Optional[str] = None,
        results_count: int = 0
    ) -> int:
        """Добавление поискового запроса"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_queries (user_id, search_name, additional_info, results_count)
            VALUES (?, ?, ?, ?)
        ''', (user_id, search_name, additional_info, results_count))
        
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Запрос добавлен: {search_name} (ID: {query_id})")
        return query_id
    
    def add_search_result(
        self,
        query_id: int,
        source: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        info: Optional[str] = None
    ) -> None:
        """Добавление результата поиска"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_results (query_id, source, name, url, info)
            VALUES (?, ?, ?, ?, ?)
        ''', (query_id, source, name, url, info))
        
        conn.commit()
        conn.close()
    
    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получение истории поисков пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
                search_name,
                additional_info,
                results_count,
                datetime(created_at, 'localtime') as created_at
            FROM search_queries
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_search_results(self, query_id: int) -> List[Dict]:
        """Получение результатов по ID запроса"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT source, name, url, info
            FROM search_results
            WHERE query_id = ?
        ''', (query_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_statistics(
        self,
        user_id: int,
        action: str,
        details: Optional[str] = None
    ) -> None:
        """Добавление статистики действий"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO statistics (user_id, action, details)
            VALUES (?, ?, ?)
        ''', (user_id, action, details))
        
        conn.commit()
        conn.close()
    
    def get_total_searches(self) -> int:
        """Общее количество поисков"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM search_queries')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_total_users(self) -> int:
        """Общее количество пользователей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
