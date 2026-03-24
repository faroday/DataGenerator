"""Pattern detection for columns based on existing data"""

import re
import uuid
import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from datetime import datetime

from faker import Faker

logger = logging.getLogger(__name__)


@dataclass
class ColumnPattern:
    PATTERN_AUTO = "auto"
    PATTERN_FAKER = "faker"
    PATTERN_ENUM = "enum"
    PATTERN_RANGE_INT = "range_int"
    PATTERN_RANGE_FLOAT = "range_float"
    PATTERN_SEQUENCE = "sequence"
    PATTERN_REFERENCE = "reference"
    PATTERN_TEXT = "text"
    PATTERN_REGEX = "regex"
    
    pattern_type: str = PATTERN_AUTO
    
    faker_method: str = "text"
    faker_locale: str = "en_US"
    
    enum_values: List[Any] = field(default_factory=list)
    enum_selected: List[Any] = field(default_factory=list)
    
    min_int: int = 0
    max_int: int = 100
    
    min_float: float = 0.0
    max_float: float = 100.0
    
    sequence_start: int = 1
    sequence_increment: int = 1
    
    ref_table: str = ""
    ref_column: str = ""
    
    text_min_length: int = 5
    text_max_length: int = 50
    
    date_min: str = ""  # YYYY-MM-DD
    date_max: str = ""  # YYYY-MM-DD
    
    regex_pattern: str = ""  # Custom regex pattern for generation
    
    def get_display_name(self) -> str:
        if self.pattern_type == self.PATTERN_AUTO:
            return "Auto-detect"
        elif self.pattern_type == self.PATTERN_FAKER:
            return f"Faker: {self.faker_method}"
        elif self.pattern_type == self.PATTERN_ENUM:
            values = self.enum_values[:3]
            suffix = "..." if len(self.enum_values) > 3 else ""
            return f"Enum: {values}{suffix}"
        elif self.pattern_type == self.PATTERN_RANGE_INT:
            return f"Int: {self.min_int}-{self.max_int}"
        elif self.pattern_type == self.PATTERN_RANGE_FLOAT:
            return f"Float: {self.min_float:.2f}-{self.max_float:.2f}"
        elif self.pattern_type == self.PATTERN_SEQUENCE:
            return f"Sequence: {self.sequence_start}+{self.sequence_increment}"
        elif self.pattern_type == self.PATTERN_REFERENCE:
            return f"FK: {self.ref_table}.{self.ref_column}"
        elif self.pattern_type == self.PATTERN_TEXT:
            return f"Text: {self.text_min_length}-{self.text_max_length} chars"
        elif self.pattern_type == self.PATTERN_REGEX:
            pattern_preview = self.regex_pattern[:20] + "..." if len(self.regex_pattern) > 20 else self.regex_pattern
            return f"Regex: {pattern_preview}"
        return self.pattern_type


class PatternDetector:
    EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    PHONE_REGEX = re.compile(r'^[\+\d\s\-\(\)]{7,}$')
    UUID_REGEX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}', re.I)
    DATE_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}')
    
    FAKER_METHODS = {
        'email': 'email',
        'name': 'name',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'phone': 'phone_number',
        'address': 'address',
        'city': 'city',
        'country': 'country',
        'company': 'company',
        'job': 'job',
        'date': 'date',
        'text': 'text',
        'uuid': 'uuid4',
        'url': 'url',
        'postcode': 'postcode',
        'username': 'user_name',
    }
    
    def __init__(self):
        self._faker = Faker()
        self._faker.seed_instance(12345)
    
    def detect_pattern(
        self,
        column_name: str,
        column_type: str,
        sample_values: List[Any],
        is_primary_key: bool = False,
        is_foreign_key: bool = False,
        fk_reference: Optional[tuple] = None,
    ) -> ColumnPattern:
        pattern = ColumnPattern()
        col_lower = column_name.lower()
        type_lower = column_type.lower()
        
        if is_foreign_key and fk_reference:
            pattern.pattern_type = ColumnPattern.PATTERN_REFERENCE
            pattern.ref_table = fk_reference[0]
            pattern.ref_column = fk_reference[1]
            return pattern
        
        if is_primary_key:
            if 'uuid' in type_lower or 'uuid' in col_lower:
                pattern.pattern_type = ColumnPattern.PATTERN_FAKER
                pattern.faker_method = 'uuid4'
            elif any(x in type_lower for x in ['int', 'serial', 'integer']):
                pattern.pattern_type = ColumnPattern.PATTERN_SEQUENCE
                pattern.sequence_start = self._detect_sequence_start(sample_values)
                pattern.sequence_increment = 1
            else:
                pattern.pattern_type = ColumnPattern.PATTERN_FAKER
                pattern.faker_method = 'uuid4'
            return pattern
        
        if self._looks_like_email(sample_values):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'email'
            return pattern
        
        if self._looks_like_date(sample_values):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'date'
            return pattern
        
        if self._looks_like_phone(sample_values):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'phone_number'
            return pattern
        
        if any(x in col_lower for x in ['email']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'email'
            return pattern
        
        if any(x in col_lower for x in ['phone', 'tel']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'phone_number'
            return pattern
        
        if any(x in col_lower for x in ['name', 'firstname', 'first_name', 'lastname', 'last_name']):
            if 'first' in col_lower:
                pattern.pattern_type = ColumnPattern.PATTERN_FAKER
                pattern.faker_method = 'first_name'
            elif 'last' in col_lower:
                pattern.pattern_type = ColumnPattern.PATTERN_FAKER
                pattern.faker_method = 'last_name'
            else:
                pattern.pattern_type = ColumnPattern.PATTERN_FAKER
                pattern.faker_method = 'name'
            return pattern
        
        if any(x in col_lower for x in ['address', 'street']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'address'
            return pattern
        
        if any(x in col_lower for x in ['city']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'city'
            return pattern
        
        if any(x in col_lower for x in ['country']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'country'
            return pattern
        
        if any(x in col_lower for x in ['zip', 'postal']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'postcode'
            return pattern
        
        if any(x in col_lower for x in ['date', 'dob', 'birth']):
            if 'dob' in col_lower or 'birth' in col_lower:
                pattern.pattern_type = ColumnPattern.PATTERN_FAKER
                pattern.faker_method = 'date_of_birth'
            else:
                pattern.pattern_type = ColumnPattern.PATTERN_FAKER
                pattern.faker_method = 'date'
            return pattern
        
        if any(x in col_lower for x in ['time', 'timestamp', 'datetime']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'date_time'
            return pattern
        
        if any(x in col_lower for x in ['url', 'website', 'link']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'url'
            return pattern
        
        if any(x in col_lower for x in ['company', 'organization', 'org']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'company'
            return pattern
        
        if any(x in col_lower for x in ['job', 'position', 'title']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'job'
            return pattern
        
        if any(x in col_lower for x in ['sku']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'ean13'
            return pattern
        
        if any(x in col_lower for x in ['password']):
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = 'password'
            return pattern
        
        unique_values = self._get_unique_values(sample_values)
        
        if len(unique_values) <= 10 and len(unique_values) > 0:
            if all(isinstance(v, bool) or str(v).lower() in ['true', 'false', '0', '1', 'yes', 'no'] for v in unique_values):
                pattern.pattern_type = ColumnPattern.PATTERN_ENUM
                pattern.enum_values = list(unique_values)
                return pattern
            
            if all(isinstance(v, str) for v in unique_values):
                pattern.pattern_type = ColumnPattern.PATTERN_ENUM
                pattern.enum_values = list(unique_values)
                return pattern
        
        if any(x in type_lower for x in ['int', 'integer', 'smallint', 'bigint', 'numeric']):
            numeric_values = [v for v in sample_values if v is not None and str(v).replace('.', '').replace('-', '').isdigit()]
            if numeric_values:
                pattern.pattern_type = ColumnPattern.PATTERN_RANGE_INT
                pattern.min_int = int(min(numeric_values))
                pattern.max_int = int(max(numeric_values)) + 1
            else:
                pattern.pattern_type = ColumnPattern.PATTERN_RANGE_INT
            return pattern
        
        if any(x in type_lower for x in ['float', 'real', 'double', 'decimal']):
            numeric_values = [v for v in sample_values if v is not None]
            if numeric_values:
                pattern.pattern_type = ColumnPattern.PATTERN_RANGE_FLOAT
                pattern.min_float = float(min(numeric_values))
                pattern.max_float = float(max(numeric_values))
            else:
                pattern.pattern_type = ColumnPattern.PATTERN_RANGE_FLOAT
            return pattern
        
        if 'price' in col_lower or 'amount' in col_lower or 'cost' in col_lower or 'salary' in col_lower:
            pattern.pattern_type = ColumnPattern.PATTERN_RANGE_FLOAT
            pattern.min_float = 10.0
            pattern.max_float = 10000.0
            return pattern
        
        if 'count' in col_lower or 'qty' in col_lower or 'quantity' in col_lower or 'stock' in col_lower:
            pattern.pattern_type = ColumnPattern.PATTERN_RANGE_INT
            pattern.min_int = 0
            pattern.max_int = 1000
            return pattern
        
        if 'bool' in type_lower:
            pattern.pattern_type = ColumnPattern.PATTERN_ENUM
            pattern.enum_values = [True, False]
            return pattern
        
        text_values = [str(v) for v in sample_values if v is not None]
        if text_values:
            lengths = [len(v) for v in text_values]
            pattern.pattern_type = ColumnPattern.PATTERN_TEXT
            pattern.text_min_length = min(lengths)
            pattern.text_max_length = max(lengths)
        else:
            pattern.pattern_type = ColumnPattern.PATTERN_TEXT
            pattern.text_min_length = 5
            pattern.text_max_length = 50
        
        return pattern
    
    def _looks_like_email(self, values: List[Any]) -> bool:
        count = 0
        for v in values:
            if v and '@' in str(v) and '.' in str(v).split('@')[-1]:
                count += 1
        return count >= len(values) * 0.5 if values else False
    
    def _looks_like_phone(self, values: List[Any]) -> bool:
        count = 0
        for v in values:
            if v and self.PHONE_REGEX.match(str(v)):
                if not self._looks_like_date(values):
                    count += 1
        return count >= len(values) * 0.5 if values else False
    
    def _looks_like_date(self, values: List[Any]) -> bool:
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{2}/\d{2}/\d{4}$',
            r'^\d{2}-\d{2}-\d{4}$',
        ]
        count = 0
        for v in values:
            if v:
                v_str = str(v)
                for pattern in date_patterns:
                    import re
                    if re.match(pattern, v_str):
                        count += 1
                        break
        return count >= len(values) * 0.5 if values else False
    
    def _get_unique_values(self, values: List[Any]) -> set:
        unique = set()
        for v in values:
            if v is not None:
                unique.add(v)
        return unique
    
    def _detect_sequence_start(self, values: List[Any]) -> int:
        numeric = []
        for v in values:
            try:
                numeric.append(int(v))
            except (ValueError, TypeError):
                continue
        
        if not numeric:
            return 1
        
        return max(numeric) + 1
    
    def generate_value(self, pattern: ColumnPattern) -> Any:
        import random
        if pattern.pattern_type == ColumnPattern.PATTERN_FAKER:
            return self._generate_faker(pattern)
        elif pattern.pattern_type == ColumnPattern.PATTERN_ENUM:
            values = pattern.enum_selected if pattern.enum_selected else pattern.enum_values
            if values:
                return random.choice(values)
            return None
        elif pattern.pattern_type == ColumnPattern.PATTERN_RANGE_INT:
            return random.randint(pattern.min_int, pattern.max_int)
        elif pattern.pattern_type == ColumnPattern.PATTERN_RANGE_FLOAT:
            return round(random.uniform(pattern.min_float, pattern.max_float), 2)
        elif pattern.pattern_type == ColumnPattern.PATTERN_SEQUENCE:
            return self._generate_sequence_value(pattern)
        elif pattern.pattern_type == ColumnPattern.PATTERN_TEXT:
            return self._generate_text(pattern)
        elif pattern.pattern_type == ColumnPattern.PATTERN_REFERENCE:
            return random.randint(1, 10)
        elif pattern.pattern_type == ColumnPattern.PATTERN_REGEX:
            return self._generate_from_regex(pattern)
        else:
            return None
    
    def _generate_faker(self, pattern: ColumnPattern) -> str:
        import random
        from datetime import datetime, timedelta
        
        method_name = pattern.faker_method
        method = getattr(self._faker, method_name, None)
        
        if pattern.faker_method in ["date", "date_of_birth"] and pattern.date_min and pattern.date_max:
            try:
                start_date = datetime.strptime(pattern.date_min, "%Y-%m-%d")
                end_date = datetime.strptime(pattern.date_max, "%Y-%m-%d")
                random_days = random.randint(0, (end_date - start_date).days)
                return (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")
            except Exception:
                pass
        
        if method:
            try:
                result = method()
                if pattern.faker_method == 'ean13':
                    return str(result)[:13]
                return result
            except Exception:
                return self._faker.text(max_nb_chars=30)
        return self._faker.text(max_nb_chars=30)
    
    def _generate_sequence_value(self, pattern: ColumnPattern) -> int:
        key = f"{pattern.sequence_start}_{pattern.sequence_increment}"
        if not hasattr(self, '_sequence_cache'):
            self._sequence_cache = {}
        
        if key not in self._sequence_cache:
            self._sequence_cache[key] = pattern.sequence_start
        else:
            self._sequence_cache[key] += pattern.sequence_increment
        
        return self._sequence_cache[key]
    
    def _generate_text(self, pattern: ColumnPattern) -> str:
        import random
        import string
        length = random.randint(pattern.text_min_length, pattern.text_max_length)
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _generate_from_regex(self, pattern: ColumnPattern) -> str:
        import random
        if not pattern.regex_pattern:
            return self._faker.text(max_nb_chars=10)
        
        try:
            import rstr
            return rstr.xeger(pattern.regex_pattern)
        except ImportError:
            logger.warning("rstr library not installed, falling back to random text")
            return self._generate_text(ColumnPattern(
                pattern_type=ColumnPattern.PATTERN_TEXT,
                text_min_length=5,
                text_max_length=20
            ))
        except Exception as e:
            logger.warning(f"Regex generation failed: {e}, falling back to random text")
            return self._generate_text(ColumnPattern(
                pattern_type=ColumnPattern.PATTERN_TEXT,
                text_min_length=5,
                text_max_length=20
            ))
    
    def reset_sequences(self) -> None:
        if hasattr(self, '_sequence_cache'):
            self._sequence_cache = {}
