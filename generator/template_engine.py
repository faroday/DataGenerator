"""Template engine for auto-generating data templates"""

import logging
import random
import re
import uuid
from typing import Dict, List, Optional

from faker import Faker

from core.models import (
    GenerationStrategy,
    GenerationStrategyType,
    TableTemplate,
    ColumnTemplate,
    ColumnInfo,
    TableInfo,
)
from config import config

logger = logging.getLogger(__name__)


class TemplateEngine:
    def __init__(self):
        self._faker = Faker(config.generation.default_locale)
        self._sequence_counters: Dict[str, int] = {}
    
    def create_template(self, table_info: TableInfo, row_count: int = 100) -> TableTemplate:
        template = TableTemplate(
            table_name=table_info.name,
            row_count=row_count,
        )
        
        for column in table_info.columns:
            strategy = self._detect_strategy(column)
            
            if column.is_foreign_key and column.foreign_key_ref:
                ref_table, ref_column = column.foreign_key_ref
                strategy = GenerationStrategy(
                    strategy_type=GenerationStrategyType.RANDOM_INT,
                    min_value=1,
                    max_value=10,
                )
            
            column_template = ColumnTemplate(
                column=column,
                strategy=strategy,
                enabled=True,
            )
            template.columns.append(column_template)
        
        return template
    
    def _detect_strategy(self, column: ColumnInfo) -> GenerationStrategy:
        col_name_lower = column.name.lower()
        data_type = column.data_type.lower()
        
        if column.is_primary_key:
            if "int" in data_type or "serial" in data_type or "identity" in data_type:
                return GenerationStrategy(
                    strategy_type=GenerationStrategyType.RANDOM_INT,
                    min_value=1,
                    max_value=999999999,
                )
            elif "uuid" in data_type:
                return GenerationStrategy(
                    strategy_type=GenerationStrategyType.CUSTOM,
                    custom_code="lambda: str(uuid.uuid4())",
                )
        
        if "uuid" in col_name_lower:
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.CUSTOM,
                custom_code="lambda: str(uuid.uuid4())",
            )
        
        if "email" in col_name_lower:
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.FAKER,
                faker_method="unique.email",
            )
        
        if "name" in col_name_lower or "fullname" in col_name_lower or "full_name" in col_name_lower:
            if "first" in col_name_lower:
                return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="first_name")
            elif "last" in col_name_lower:
                return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="last_name")
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="name")
        
        if "phone" in col_name_lower or "tel" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="phone_number")
        
        if "address" in col_name_lower or "street" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="address")
        
        if "city" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="city")
        
        if "country" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="country")
        
        if "zip" in col_name_lower or "postal" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="postcode")
        
        if "date" in col_name_lower:
            if "birth" in col_name_lower or "dob" in col_name_lower:
                return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="date_of_birth")
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="date")
        
        if "time" in col_name_lower or "timestamp" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="date_time")
        
        if "url" in col_name_lower or "website" in col_name_lower or "link" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="url")
        
        if "sku" in col_name_lower:
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.CUSTOM,
                custom_code="__generate_sku__",
            )
        
        if "company" in col_name_lower or "organization" in col_name_lower or "org" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="company")
        
        if "job" in col_name_lower or "position" in col_name_lower or "title" in col_name_lower:
            return GenerationStrategy(strategy_type=GenerationStrategyType.FAKER, faker_method="job")
        
        if "description" in col_name_lower or "text" in col_name_lower or "note" in col_name_lower:
            max_len = column.max_length or 255
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.FAKER,
                faker_method="text",
            )
        
        if "price" in col_name_lower or "amount" in col_name_lower or "cost" in col_name_lower or "salary" in col_name_lower:
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.RANDOM_FLOAT,
                min_value=0.01,
                max_value=10000.0,
            )
        
        if "count" in col_name_lower or "quantity" in col_name_lower or "qty" in col_name_lower:
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.RANDOM_INT,
                min_value=0,
                max_value=1000,
            )
        
        if "bool" in data_type or column.data_type.lower() in ("boolean",):
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.RANDOM_CHOICE,
                choices=[True, False],
            )
        
        if "int" in data_type or "numeric" in data_type or "decimal" in data_type:
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.RANDOM_INT,
                min_value=0,
                max_value=10000,
            )
        
        if "float" in data_type or "real" in data_type or "double" in data_type:
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.RANDOM_FLOAT,
                min_value=0.0,
                max_value=1000.0,
            )
        
        if "varchar" in data_type or "text" in data_type or "char" in data_type:
            max_len = column.max_length or 50
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.RANDOM_STRING,
                min_value=1,
                max_value=min(max_len, 50),
            )
        
        if "json" in data_type:
            return GenerationStrategy(
                strategy_type=GenerationStrategyType.FAKER,
                faker_method="json",
            )
        
        return GenerationStrategy(
            strategy_type=GenerationStrategyType.RANDOM_STRING,
            min_value=1,
            max_value=20,
        )
    
    def reset_sequences(self) -> None:
        self._sequence_counters.clear()
    
    def generate_value(self, strategy: GenerationStrategy) -> any:
        try:
            if strategy.strategy_type == GenerationStrategyType.FAKER:
                return self._generate_faker(strategy)
            elif strategy.strategy_type == GenerationStrategyType.SEQUENCE:
                return self._generate_sequence(strategy)
            elif strategy.strategy_type == GenerationStrategyType.RANDOM_INT:
                return random.randint(strategy.min_value, strategy.max_value)
            elif strategy.strategy_type == GenerationStrategyType.RANDOM_FLOAT:
                return random.uniform(strategy.min_value, strategy.max_value)
            elif strategy.strategy_type == GenerationStrategyType.RANDOM_STRING:
                return self._generate_random_string(strategy)
            elif strategy.strategy_type == GenerationStrategyType.RANDOM_CHOICE:
                return random.choice(strategy.choices)
            elif strategy.strategy_type == GenerationStrategyType.CONSTANT:
                return strategy.constant_value
            elif strategy.strategy_type == GenerationStrategyType.CUSTOM:
                return self._generate_custom(strategy)
            else:
                return None
        except Exception as e:
            logger.warning(f"Generation error for strategy {strategy.strategy_type}: {e}")
            return None
    
    def _generate_faker(self, strategy: GenerationStrategy) -> any:
        if not strategy.faker_method:
            return self._faker.text(max_nb_chars=50)
        
        method = getattr(self._faker, strategy.faker_method, None)
        if method:
            try:
                return method()
            except TypeError:
                return self._faker.text(max_nb_chars=50)
        return self._faker.text(max_nb_chars=50)
    
    def _generate_sequence(self, strategy: GenerationStrategy) -> int:
        key = f"{strategy.start_value}_{strategy.increment}"
        if key not in self._sequence_counters:
            self._sequence_counters[key] = strategy.start_value
        
        value = self._sequence_counters[key]
        self._sequence_counters[key] += strategy.increment
        return value
    
    def _generate_random_string(self, strategy: GenerationStrategy) -> str:
        length = random.randint(strategy.min_value, strategy.max_value)
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(random.choice(chars) for _ in range(length))
    
    def _generate_custom(self, strategy: GenerationStrategy) -> any:
        if strategy.custom_code:
            try:
                import uuid
                if strategy.custom_code == "__generate_sku__":
                    return uuid.uuid4().hex[:8].upper()
                if strategy.custom_code == "__generate_uuid__":
                    return str(uuid.uuid4())
            except Exception as e:
                logger.warning(f"Custom code execution failed: {e}")
        return self._generate_random_string(strategy)
    
    def generate_row(self, template: TableTemplate) -> List[any]:
        row = []
        for col_template in template.columns:
            value = self.generate_value(col_template.strategy)
            row.append(value)
        return row
