"""Configuration loader for DataGenerator"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class DatabaseConfig:
    default_batch_size: int = 5000
    worker_threads: int = 4
    connection_timeout: int = 30


@dataclass
class GenerationConfig:
    default_locale: str = "en_US"
    string_max_length: int = 255
    null_probability: float = 0.05
    max_retries: int = 3


@dataclass
class UIConfig:
    theme: str = "light"
    language: str = "en"
    window_width: int = 1000
    window_height: int = 700


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "datagenerator.log"
    max_size_mb: int = 10


@dataclass
class AppConfig:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AppConfig":
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        if not config_path.exists():
            return cls()
        
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
        
        return cls(
            database=DatabaseConfig(**data.get("database", {})),
            generation=GenerationConfig(**data.get("generation", {})),
            ui=UIConfig(**data.get("ui", {})),
            logging=LoggingConfig(**data.get("logging", {})),
        )
    
    def save(self, config_path: Optional[Path] = None) -> None:
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        data = {
            "database": self.database.__dict__,
            "generation": self.generation.__dict__,
            "ui": self.ui.__dict__,
            "logging": self.logging.__dict__,
        }
        
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)


config = AppConfig.load()
