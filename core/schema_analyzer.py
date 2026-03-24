"""Schema analyzer for database introspection"""

import logging
from typing import Dict, List, Optional, Set, Tuple

from .connection_manager import ConnectionManager
from .models import (
    Schema,
    TableInfo,
    ColumnInfo,
    TableRelationship,
)

logger = logging.getLogger(__name__)


class SchemaAnalyzer:
    def __init__(self, connection_manager: ConnectionManager):
        self._conn = connection_manager
    
    def analyze(self) -> Schema:
        if not self._conn.is_connected:
            raise RuntimeError("Not connected to database")
        
        tables = self._conn.get_tables()
        schema = Schema()
        
        for table_name in tables:
            table_info = self._conn.get_table_info(table_name)
            schema.tables[table_name] = table_info
        
        logger.info(f"Analyzed {len(tables)} tables")
        return schema
    
    def get_relationships(self) -> List[TableRelationship]:
        relationships = []
        fk_map = self._conn.get_foreign_keys()
        
        for table_name, fks in fk_map.items():
            for fk in fks:
                for constrained_col in fk.get("constrained_columns", []):
                    referred_cols = fk.get("referred_columns", [])
                    if referred_cols:
                        relationship = TableRelationship(
                            from_table=table_name,
                            from_column=constrained_col,
                            to_table=fk["referred_table"],
                            to_column=referred_cols[0],
                            relationship_type="many-to-one",
                        )
                        relationships.append(relationship)
        
        return relationships
    
    def get_generation_order(self, selected_tables: List[str]) -> List[str]:
        relationships = self.get_relationships()
        fk_graph: Dict[str, Set[str]] = {}
        
        for table in selected_tables:
            fk_graph[table] = set()
        
        for rel in relationships:
            if rel.from_table in selected_tables and rel.to_table in selected_tables:
                fk_graph[rel.from_table].add(rel.to_table)
        
        visited = set()
        order = []
        
        def dfs(table: str):
            if table in visited:
                return
            visited.add(table)
            for dependency in fk_graph.get(table, set()):
                dfs(dependency)
            order.append(table)
        
        for table in selected_tables:
            dfs(table)
        
        return order
    
    def validate_foreign_keys(
        self,
        table_name: str,
        data: List[Tuple],
        column_indices: Dict[str, int],
    ) -> List[Tuple[int, str, str]]:
        errors = []
        
        table_info = self._conn.get_table_info(table_name)
        
        for col in table_info.columns:
            if col.is_foreign_key and col.foreign_key_ref:
                ref_table, ref_column = col.foreign_key_ref
                col_idx = column_indices.get(col.name)
                
                if col_idx is None:
                    continue
                
                col_values = set()
                for row in data:
                    val = row[col_idx]
                    if val is not None:
                        col_values.add(val)
                
                try:
                    result = self._conn.execute(
                        f"SELECT {ref_column} FROM {ref_table} WHERE {ref_column} IN :values",
                        {"values": tuple(col_values)}
                    )
                    existing_values = {row[0] for row in result}
                    
                    for i, row in enumerate(data):
                        val = row[col_idx]
                        if val is not None and val not in existing_values:
                            errors.append((i, col.name, f"FK value {val} not found in {ref_table}.{ref_column}"))
                
                except Exception as e:
                    logger.warning(f"FK validation skipped for {table_name}.{col.name}: {e}")
        
        return errors
