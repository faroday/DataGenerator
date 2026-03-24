"""Data models for DataGenerator"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable


class DBType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    ORACLE = "oracle"


class GenerationStrategyType(Enum):
    FAKER = "faker"
    SEQUENCE = "sequence"
    RANDOM_INT = "random_int"
    RANDOM_FLOAT = "random_float"
    RANDOM_STRING = "random_string"
    RANDOM_CHOICE = "random_choice"
    CONSTANT = "constant"
    REFERENCE = "reference"
    CUSTOM = "custom"


@dataclass
class ConnectionParams:
    db_type: DBType
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    charset: str = "utf8mb4"

    def get_connection_url(self) -> str:
        if self.db_type == DBType.POSTGRESQL:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DBType.MYSQL:
            return f"mysql+mysqlconnector://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == DBType.SQLITE:
            return f"sqlite:///{self.database}"
        elif self.db_type == DBType.ORACLE:
            return f"oracle+cx_oracle://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        raise ValueError(f"Unsupported database type: {self.db_type}")


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool = True
    default_value: Any = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    max_length: Optional[int] = None
    foreign_key_ref: Optional[tuple] = None  # (table, column)


@dataclass
class TableInfo:
    name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_key: Optional[str] = None
    row_count: int = 0


@dataclass
class TableRelationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str = "many-to-one"


@dataclass
class Schema:
    tables: Dict[str, TableInfo] = field(default_factory=dict)
    
    def get_table(self, name: str) -> Optional[TableInfo]:
        return self.tables.get(name)
    
    def get_tables(self) -> List[TableInfo]:
        return list(self.tables.values())


@dataclass
class GenerationStrategy:
    strategy_type: GenerationStrategyType
    faker_method: Optional[str] = None
    faker_locale: str = "en_US"
    start_value: int = 1
    increment: int = 1
    min_value: Any = None
    max_value: Any = None
    choices: List[Any] = field(default_factory=list)
    constant_value: Any = None
    reference_table: Optional[str] = None
    reference_column: Optional[str] = None
    custom_code: Optional[str] = None


@dataclass 
class ColumnTemplate:
    column: ColumnInfo
    strategy: GenerationStrategy
    enabled: bool = True


@dataclass
class TableTemplate:
    table_name: str
    columns: List[ColumnTemplate] = field(default_factory=list)
    row_count: int = 100


@dataclass
class GenerationProgress:
    total_rows: int = 0
    generated_rows: int = 0
    current_table: str = ""
    
    @property
    def percentage(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return (self.generated_rows / self.total_rows) * 100


@dataclass
class GenerationResult:
    success: bool
    rows_generated: int = 0
    tables_updated: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    duration_seconds: float = 0.0


ProgressCallback = Callable[[GenerationProgress], None]
