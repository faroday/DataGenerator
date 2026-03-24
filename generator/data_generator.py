"""Data generator engine with batch processing"""

import logging
import time
from typing import Dict, List, Optional, Any

from core.models import (
    TableTemplate,
    GenerationProgress,
    GenerationResult,
    ProgressCallback,
    TableInfo,
)
from core.connection_manager import ConnectionManager
from core.schema_analyzer import SchemaAnalyzer
from generator.pattern_detector import PatternDetector, ColumnPattern
from config import config

logger = logging.getLogger(__name__)


class DataGenerator:
    def __init__(
        self,
        connection_manager: ConnectionManager,
        schema_analyzer: SchemaAnalyzer,
    ):
        self._conn = connection_manager
        self._schema = schema_analyzer
        self._detector = PatternDetector()
        self._cancel_requested = False
        self._progress_callback: Optional[ProgressCallback] = None
    
    def set_progress_callback(self, callback: ProgressCallback) -> None:
        self._progress_callback = callback
    
    def cancel(self) -> None:
        self._cancel_requested = True
        logger.info("Cancellation requested")
    
    def reset_cancel(self) -> None:
        self._cancel_requested = False
    
    def generate(
        self,
        templates: Dict[str, TableTemplate],
        patterns: Dict[str, Dict[str, ColumnPattern]] = None,
        batch_size: Optional[int] = None,
    ) -> GenerationResult:
        if batch_size is None:
            batch_size = config.database.default_batch_size
        
        start_time = time.time()
        total_rows = sum(t.row_count for t in templates.values())
        generated_rows = 0
        tables_updated = []
        
        generation_order = self._schema.get_generation_order(list(templates.keys()))
        
        self._detector.reset_sequences()
        self._reset_cancel()
        
        try:
            for table_name in generation_order:
                if self._cancel_requested:
                    logger.info("Generation cancelled by user")
                    break
                
                template = templates[table_name]
                logger.info(f"Generating {template.row_count} rows for table {table_name}")
                
                table_patterns = patterns.get(table_name) if patterns else None
                rows_generated = self._generate_table_with_patterns(
                    template, table_patterns, batch_size
                )
                generated_rows += rows_generated
                tables_updated.append(table_name)
                
                self._report_progress(generated_rows, total_rows, table_name)
            
            duration = time.time() - start_time
            logger.info(f"Generation completed: {generated_rows} rows in {duration:.2f}s")
            
            return GenerationResult(
                success=True,
                rows_generated=generated_rows,
                tables_updated=tables_updated,
                duration_seconds=duration,
            )
        
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return GenerationResult(
                success=False,
                rows_generated=generated_rows,
                tables_updated=tables_updated,
                error_message=str(e),
                duration_seconds=time.time() - start_time,
            )
    
    def _generate_table_with_patterns(
        self,
        template: TableTemplate,
        patterns: Optional[Dict[str, ColumnPattern]],
        batch_size: int,
    ) -> int:
        total_generated = 0
        table_name = template.table_name
        
        columns = [ct.column.name for ct in template.columns]
        
        while total_generated < template.row_count:
            if self._cancel_requested:
                break
            
            remaining = template.row_count - total_generated
            current_batch_size = min(batch_size, remaining)
            
            data = []
            for _ in range(current_batch_size):
                row = self._generate_row_with_patterns(template, patterns)
                data.append(tuple(row))
            
            try:
                inserted = self._conn.batch_insert(
                    table_name,
                    columns,
                    data,
                    batch_size=current_batch_size,
                )
                total_generated += inserted
                logger.debug(f"Inserted {inserted} rows into {table_name}")
            except Exception as e:
                logger.error(f"Batch insert failed for {table_name}: {e}")
                break
        
        return total_generated
    
    def _generate_row_with_patterns(
        self,
        template: TableTemplate,
        patterns: Optional[Dict[str, ColumnPattern]],
    ) -> List[Any]:
        row = []
        for ct in template.columns:
            if patterns and ct.column.name in patterns:
                pattern = patterns[ct.column.name]
            else:
                pattern = self._convert_strategy_to_pattern(ct.strategy)
            value = self._detector.generate_value(pattern)
            row.append(value)
        return row
    
    def _convert_strategy_to_pattern(self, strategy) -> ColumnPattern:
        from ..core.models import GenerationStrategyType
        pattern = ColumnPattern()
        
        if strategy.strategy_type == GenerationStrategyType.FAKER:
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = strategy.faker_method or "text"
        elif strategy.strategy_type == GenerationStrategyType.SEQUENCE:
            pattern.pattern_type = ColumnPattern.PATTERN_SEQUENCE
            pattern.sequence_start = strategy.start_value
            pattern.sequence_increment = strategy.increment
        elif strategy.strategy_type == GenerationStrategyType.RANDOM_INT:
            pattern.pattern_type = ColumnPattern.PATTERN_RANGE_INT
            pattern.min_int = strategy.min_value or 0
            pattern.max_int = strategy.max_value or 100
        elif strategy.strategy_type == GenerationStrategyType.RANDOM_FLOAT:
            pattern.pattern_type = ColumnPattern.PATTERN_RANGE_FLOAT
            pattern.min_float = strategy.min_value or 0.0
            pattern.max_float = strategy.max_value or 100.0
        elif strategy.strategy_type == GenerationStrategyType.RANDOM_CHOICE:
            pattern.pattern_type = ColumnPattern.PATTERN_ENUM
            pattern.enum_values = strategy.choices or [True, False]
        else:
            pattern.pattern_type = ColumnPattern.PATTERN_TEXT
        
        return pattern
    
    def _report_progress(
        self,
        current_rows: int,
        total_rows: int,
        current_table: str,
    ) -> None:
        if self._progress_callback:
            progress = GenerationProgress(
                total_rows=total_rows,
                generated_rows=current_rows,
                current_table=current_table,
            )
            self._progress_callback(progress)
    
    def _reset_cancel(self) -> None:
        self._cancel_requested = False
