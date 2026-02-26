#!/usr/bin/env python3
import sqlite3
import os
from typing import List, Dict, Any
import logging
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class SQLiteClient:
    def __init__(self, db_path=None):
        if db_path is None:
            # Use data directory in Docker, current dir otherwise
            if os.path.exists('/app/data'):
                db_path = "/app/data/workout.db"
            else:
                db_path = "workout.db"

        self.db_path = db_path
        self.ensure_db_exists()
        
    def ensure_db_exists(self):
        """Create database file if it doesn't exist"""
        if not os.path.exists(self.db_path):
            logger.info(f"🔨 Creating database: {self.db_path}")
        
    def execute_query(self, query: str, params=None) -> List[Dict[str, Any]]:
        """Execute an arbitrary SQL query and return results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Return rows as dictionaries
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # For SELECT queries, fetch results
                if query.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                    logger.info(f"✅ Query returned {len(result)} rows")
                    return result
                else:
                    # For INSERT, UPDATE, DELETE
                    conn.commit()
                    affected = cursor.rowcount
                    logger.info(f"✅ Query affected {affected} rows")
                    return [{"affected_rows": affected, "lastrowid": cursor.lastrowid}]
                    
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            return []
    
    def create_table(self, table_name: str, columns: str) -> bool:
        """Helper to create a table"""
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
        result = self.execute_query(query)
        return len(result) > 0
    
    def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """Helper to insert data"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        result = self.execute_query(query, list(data.values()))
        return len(result) > 0
    
    def select(self, table: str, where: str = None, params=None) -> List[Dict[str, Any]]:
        """Helper to select data"""
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        return self.execute_query(query, params)
    
    def get_tables(self) -> List[str]:
        """Get list of all tables in database"""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        result = self.execute_query(query)
        return [row['name'] for row in result]
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
