"""Database connection manager"""

from typing import Any, Dict, List, Optional, Tuple
import logging

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.engine.row import Row

from .models import (
    ConnectionParams,
    DBType,
    TableInfo,
    ColumnInfo,
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._engine: Optional[Engine] = None
        self._connection = None
    
    @property
    def is_connected(self) -> bool:
        return self._engine is not None and self._connection is not None
    
    def connect(self, params: ConnectionParams) -> bool:
        try:
            self._engine = create_engine(
                params.get_connection_url(),
                pool_pre_ping=True,
                echo=False,
            )
            self._connection = self._engine.connect()
            logger.info(f"Connected to {params.db_type.value}: {params.host}/{params.database}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._engine = None
            self._connection = None
            raise
    
    def disconnect(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None
        if self._engine:
            self._engine.dispose()
            self._engine = None
        logger.info("Disconnected from database")
    
    def test_connection(self) -> bool:
        try:
            if not self._connection:
                return False
            self._connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_tables(self) -> List[str]:
        if not self._engine:
            return []
        
        inspector = inspect(self._engine)
        return inspector.get_table_names()
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        if not self._engine:
            return []
        
        inspector = inspect(self._engine)
        columns_raw = inspector.get_columns(table_name)
        
        pk_columns = inspector.get_pk_constraint(table_name)
        fk_columns = inspector.get_foreign_keys(table_name)
        
        pk_set = set(pk_columns.get("constrained_columns", []))
        fk_dict = {}
        for fk in fk_columns:
            for col in fk.get("constrained_columns", []):
                fk_dict[col] = (fk["referred_table"], fk["referred_columns"][0])
        
        columns = []
        for col in columns_raw:
            column_info = ColumnInfo(
                name=col["name"],
                data_type=str(col["type"]),
                nullable=col["nullable"],
                default_value=col.get("default"),
                is_primary_key=col["name"] in pk_set,
                is_foreign_key=col["name"] in fk_dict,
                foreign_key_ref=fk_dict.get(col["name"]),
                max_length=self._get_max_length(col["type"]),
            )
            columns.append(column_info)
        
        return columns
    
    def _get_max_length(self, col_type) -> Optional[int]:
        type_str = str(col_type).lower()
        if "varchar" in type_str or "char" in type_str:
            import re
            match = re.search(r'\((\d+)\)', str(col_type))
            if match:
                return int(match.group(1))
        return None
    
    def get_table_info(self, table_name: str) -> TableInfo:
        columns = self.get_columns(table_name)
        primary_key = None
        for col in columns:
            if col.is_primary_key:
                primary_key = col.name
                break
        
        row_count = self.get_row_count(table_name)
        
        return TableInfo(
            name=table_name,
            columns=columns,
            primary_key=primary_key,
            row_count=row_count,
        )
    
    def get_row_count(self, table_name: str) -> int:
        try:
            result = self._connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar() or 0
        except Exception:
            return 0
    
    def execute(self, query: str, params: tuple = None) -> List[Row]:
        if not self._connection:
            raise RuntimeError("Not connected to database")
        
        result = self._connection.execute(text(query), params or {})
        return result.fetchall()
    
    def batch_insert(
        self,
        table_name: str,
        columns: List[str],
        data: List[Tuple],
        batch_size: int = 1000,
    ) -> int:
        if not self._connection:
            raise RuntimeError("Not connected to database")
        
        if not data:
            return 0
        
        cols_str = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])
        
        query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
        
        total_inserted = 0
        with self._engine.begin() as conn:
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                for row in batch:
                    params = {columns[j]: row[j] for j in range(len(columns))}
                    conn.execute(text(query), params)
                total_inserted += len(batch)
        
        return total_inserted
    
    def truncate_table(self, table_name: str) -> None:
        if not self._connection:
            raise RuntimeError("Not connected to database")
        
        with self._engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
    
    def delete_from_table(self, table_name: str) -> int:
        if not self._connection:
            raise RuntimeError("Not connected to database")
        
        result = self._connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar() or 0
        
        with self._engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {table_name}"))
            conn.commit()
        
        return count
    
    def get_foreign_keys(self) -> Dict[str, List[Dict]]:
        if not self._engine:
            return {}
        
        inspector = inspect(self._engine)
        tables = inspector.get_table_names()
        fk_map = {}
        
        for table in tables:
            fks = inspector.get_foreign_keys(table)
            if fks:
                fk_map[table] = fks
        
        return fk_map
    
    def begin_transaction(self):
        if self._connection:
            self._connection.begin()
    
    def commit_transaction(self):
        if self._connection:
            self._connection.commit()
    
    def rollback_transaction(self):
        if self._connection:
            self._connection.rollback()
