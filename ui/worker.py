"""Background worker for data generation"""

import logging
from typing import Dict

from PyQt6.QtCore import QThread, pyqtSignal

from core.models import TableTemplate, GenerationResult
from generator.data_generator import DataGenerator

logger = logging.getLogger(__name__)


class GenerationWorker(QThread):
    progress = pyqtSignal(object)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, generator: DataGenerator, templates: Dict[str, TableTemplate]):
        super().__init__()
        self.generator = generator
        self.templates = templates
    
    def run(self):
        logger = logging.getLogger(__name__)
        logger.info(f"Worker started with templates: {list(self.templates.keys())}")
        try:
            self.generator.set_progress_callback(
                lambda p: self.progress.emit(p)
            )
            logger.info("Starting generation...")
            result = self.generator.generate(self.templates)
            logger.info(f"Generation complete: {result.rows_generated} rows")
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Worker error: {e}")
            self.error.emit(str(e))
