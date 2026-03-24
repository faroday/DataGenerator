"""Dialog for editing column patterns"""

from typing import Dict, List, Any
import logging

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QFormLayout,
    QDialogButtonBox,
    QScrollArea,
    QWidget,
    QCheckBox,
)
from PyQt6.QtCore import Qt

from generator.pattern_detector import PatternDetector, ColumnPattern
from core.models import TableInfo, ColumnInfo

logger = logging.getLogger(__name__)


PATTERN_OPTIONS = [
    ("Auto-detect", ColumnPattern.PATTERN_AUTO),
    ("Faker: name", ColumnPattern.PATTERN_FAKER),
    ("Faker: first_name", ColumnPattern.PATTERN_FAKER),
    ("Faker: last_name", ColumnPattern.PATTERN_FAKER),
    ("Faker: email", ColumnPattern.PATTERN_FAKER),
    ("Faker: phone", ColumnPattern.PATTERN_FAKER),
    ("Faker: address", ColumnPattern.PATTERN_FAKER),
    ("Faker: city", ColumnPattern.PATTERN_FAKER),
    ("Faker: country", ColumnPattern.PATTERN_FAKER),
    ("Faker: date", ColumnPattern.PATTERN_FAKER),
    ("Faker: date_of_birth", ColumnPattern.PATTERN_FAKER),
    ("Faker: company", ColumnPattern.PATTERN_FAKER),
    ("Faker: job", ColumnPattern.PATTERN_FAKER),
    ("Faker: text", ColumnPattern.PATTERN_FAKER),
    ("Faker: url", ColumnPattern.PATTERN_FAKER),
    ("Faker: uuid", ColumnPattern.PATTERN_FAKER),
    ("Faker: postcode", ColumnPattern.PATTERN_FAKER),
    ("Enum (choose values)", ColumnPattern.PATTERN_ENUM),
    ("Sequence (auto-increment)", ColumnPattern.PATTERN_SEQUENCE),
    ("Random Integer", ColumnPattern.PATTERN_RANGE_INT),
    ("Random Float", ColumnPattern.PATTERN_RANGE_FLOAT),
    ("Text (random string)", ColumnPattern.PATTERN_TEXT),
    ("Custom Regex", ColumnPattern.PATTERN_REGEX),
    ("Reference (FK)", ColumnPattern.PATTERN_REFERENCE),
]

FAKER_METHODS_MAP = {
    "Faker: name": "name",
    "Faker: first_name": "first_name",
    "Faker: last_name": "last_name",
    "Faker: email": "email",
    "Faker: phone": "phone_number",
    "Faker: address": "address",
    "Faker: city": "city",
    "Faker: country": "country",
    "Faker: date": "date",
    "Faker: date_of_birth": "date_of_birth",
    "Faker: company": "company",
    "Faker: job": "job",
    "Faker: text": "text",
    "Faker: url": "url",
    "Faker: uuid": "uuid4",
    "Faker: postcode": "postcode",
}


class PatternEditorDialog(QDialog):
    def __init__(
        self,
        table_info: TableInfo,
        sample_data: Dict[str, List[Any]],
        parent=None,
    ):
        super().__init__(parent)
        self.table_info = table_info
        self.sample_data = sample_data
        self.detector = PatternDetector()
        self.detected_patterns: Dict[str, ColumnPattern] = {}
        self.edited_patterns: Dict[str, ColumnPattern] = {}
        
        self.setWindowTitle(f"Edit Patterns: {table_info.name}")
        self.setMinimumSize(800, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        table_label = QLabel(f"Table: <b>{self.table_info.name}</b>")
        table_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(table_label)
        
        options_layout = QHBoxLayout()
        
        options_layout.addWidget(QLabel("Rows to generate:"))
        self.row_count_spin = QSpinBox()
        self.row_count_spin.setRange(1, 10000000)
        self.row_count_spin.setValue(100)
        self.row_count_spin.setSuffix(" rows")
        options_layout.addWidget(self.row_count_spin)
        
        options_layout.addSpacing(20)
        self.delete_existing_check = QCheckBox("Delete existing data")
        self.delete_existing_check.setChecked(False)
        options_layout.addWidget(self.delete_existing_check)
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        instructions = QLabel("Review and adjust the pattern for each column. Click on a pattern to change it.")
        layout.addWidget(instructions)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Column</b>"), 2)
        header_layout.addWidget(QLabel("<b>Type</b>"), 1)
        header_layout.addWidget(QLabel("<b>Sample Values</b>"), 2)
        header_layout.addWidget(QLabel("<b>Pattern</b>"), 2)
        scroll_layout.addLayout(header_layout)
        
        for column in self.table_info.columns:
            self._add_column_row(scroll_layout, column)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _add_column_row(self, layout: QVBoxLayout, column: ColumnInfo):
        row_layout = QHBoxLayout()
        
        col_label = QLabel(column.name)
        if column.is_primary_key:
            col_label.setText(f"🔑 {column.name}")
        elif column.is_foreign_key:
            col_label.setText(f"🔗 {column.name}")
        row_layout.addWidget(col_label, 2)
        
        type_label = QLabel(column.data_type)
        type_label.setStyleSheet("color: #666;")
        row_layout.addWidget(type_label, 1)
        
        sample_values = self.sample_data.get(column.name, [])[:3]
        sample_text = ", ".join(str(v) for v in sample_values)
        if len(sample_values) > 3:
            sample_text += "..."
        sample_label = QLabel(sample_text if sample_text else "(empty)")
        sample_label.setStyleSheet("color: #888; font-size: 11px;")
        sample_label.setWordWrap(True)
        row_layout.addWidget(sample_label, 2)
        
        config_layout = QHBoxLayout()
        config_layout.setSpacing(5)
        
        self._add_pattern_combo(column, config_layout)
        self._add_config_button(column, config_layout)
        
        row_layout.addLayout(config_layout, 3)
        
        layout.addLayout(row_layout)
    
    def _add_pattern_combo(self, column: ColumnInfo, config_layout: QHBoxLayout):
        combo = QComboBox()
        combo.setObjectName(f"pattern_{column.name}")
        combo.currentIndexChanged.connect(
            lambda idx, c=column: self._on_pattern_changed(c.name, idx)
        )
        
        for display, value in PATTERN_OPTIONS:
            combo.addItem(display, value)
        
        sample_values = self.sample_data.get(column.name, [])
        pattern = self.detector.detect_pattern(
            column_name=column.name,
            column_type=column.data_type,
            sample_values=sample_values,
            is_primary_key=column.is_primary_key,
            is_foreign_key=column.is_foreign_key,
            fk_reference=column.foreign_key_ref,
        )
        
        if pattern.pattern_type == ColumnPattern.PATTERN_REFERENCE and column.foreign_key_ref:
            pattern.ref_table = column.foreign_key_ref[0]
            pattern.ref_column = column.foreign_key_ref[1]
        
        self.detected_patterns[column.name] = pattern
        self.edited_patterns[column.name] = pattern
        
        self._set_combo_selection(combo, pattern)
        combo.setMinimumWidth(150)
        config_layout.addWidget(combo)
        
        setattr(self, f"_combo_{column.name}", combo)
    
    def _set_combo_selection(self, combo: QComboBox, pattern: ColumnPattern):
        if pattern.pattern_type == ColumnPattern.PATTERN_FAKER:
            for display, method in FAKER_METHODS_MAP.items():
                if method == pattern.faker_method:
                    for i in range(combo.count()):
                        if combo.itemText(i) == display:
                            combo.setCurrentIndex(i)
                            return
        else:
            for i in range(combo.count()):
                if combo.itemData(i) == pattern.pattern_type:
                    combo.setCurrentIndex(i)
                    return
    
    def _add_config_button(self, column: ColumnInfo, config_layout: QHBoxLayout):
        btn = QPushButton("⚙")
        btn.setObjectName(f"config_{column.name}")
        btn.setMaximumWidth(30)
        btn.setToolTip("Configure pattern settings")
        btn.clicked.connect(lambda _, c=column: self._open_config_dialog(c))
        config_layout.addWidget(btn)
        
        info_label = QLabel()
        info_label.setObjectName(f"info_{column.name}")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        self._update_config_info(column, info_label)
        config_layout.addWidget(info_label, 1)
    
    def _update_config_info(self, column: ColumnInfo, label: QLabel):
        pattern = self.edited_patterns.get(column.name)
        if not pattern:
            return
        
        if pattern.pattern_type == ColumnPattern.PATTERN_REFERENCE:
            label.setText(f"→ {pattern.ref_table}.{pattern.ref_column}")
            label.setStyleSheet("color: #0066cc; font-size: 10px;")
        elif pattern.pattern_type == ColumnPattern.PATTERN_RANGE_INT:
            label.setText(f"min: {pattern.min_int}, max: {pattern.max_int}")
        elif pattern.pattern_type == ColumnPattern.PATTERN_RANGE_FLOAT:
            label.setText(f"min: {pattern.min_float:.2f}, max: {pattern.max_float:.2f}")
        elif pattern.pattern_type == ColumnPattern.PATTERN_TEXT:
            label.setText(f"len: {pattern.text_min_length}-{pattern.text_max_length} chars")
        elif pattern.pattern_type == ColumnPattern.PATTERN_ENUM:
            count = len(pattern.enum_values)
            label.setText(f"{count} values")
        elif pattern.pattern_type == ColumnPattern.PATTERN_FAKER and pattern.faker_method in ["date", "date_of_birth"]:
            label.setText(f"range: {pattern.date_min or '1970-01-01'} - {pattern.date_max or '2030-12-31'}")
        elif pattern.pattern_type == ColumnPattern.PATTERN_REGEX:
            preview = pattern.regex_pattern[:15] + "..." if len(pattern.regex_pattern) > 15 else pattern.regex_pattern or "(not set)"
            label.setText(preview)
        else:
            label.setText("")
    
    def _open_config_dialog(self, column: ColumnInfo):
        pattern = self.edited_patterns.get(column.name)
        if not pattern:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Configure: {column.name}")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        pattern_label = QLabel(f"<b>{pattern.pattern_type}</b> - {pattern.get_display_name()}")
        layout.addWidget(pattern_label)
        
        if pattern.pattern_type in [ColumnPattern.PATTERN_RANGE_INT, ColumnPattern.PATTERN_RANGE_FLOAT]:
            form = QFormLayout()
            
            if pattern.pattern_type == ColumnPattern.PATTERN_RANGE_INT:
                min_spin = QSpinBox()
                min_spin.setRange(-999999999, 999999999)
                min_spin.setValue(pattern.min_int)
                min_spin.valueChanged.connect(lambda v, p=pattern: setattr(p, 'min_int', v))
                form.addRow("Min:", min_spin)
                
                max_spin = QSpinBox()
                max_spin.setRange(-999999999, 999999999)
                max_spin.setValue(pattern.max_int)
                max_spin.valueChanged.connect(lambda v, p=pattern: setattr(p, 'max_int', v))
                form.addRow("Max:", max_spin)
            
            elif pattern.pattern_type == ColumnPattern.PATTERN_RANGE_FLOAT:
                min_spin = QDoubleSpinBox()
                min_spin.setRange(-999999999, 999999999)
                min_spin.setDecimals(2)
                min_spin.setValue(pattern.min_float)
                min_spin.valueChanged.connect(lambda v, p=pattern: setattr(p, 'min_float', v))
                form.addRow("Min:", min_spin)
                
                max_spin = QDoubleSpinBox()
                max_spin.setRange(-999999999, 999999999)
                max_spin.setDecimals(2)
                max_spin.setValue(pattern.max_float)
                max_spin.valueChanged.connect(lambda v, p=pattern: setattr(p, 'max_float', v))
                form.addRow("Max:", max_spin)
            
            layout.addLayout(form)
        
        elif pattern.pattern_type == ColumnPattern.PATTERN_TEXT:
            form = QFormLayout()
            
            min_spin = QSpinBox()
            min_spin.setRange(1, 1000)
            min_spin.setValue(pattern.text_min_length)
            min_spin.valueChanged.connect(lambda v, p=pattern: setattr(p, 'text_min_length', v))
            form.addRow("Min length:", min_spin)
            
            max_spin = QSpinBox()
            max_spin.setRange(1, 10000)
            max_spin.setValue(pattern.text_max_length)
            max_spin.valueChanged.connect(lambda v, p=pattern: setattr(p, 'text_max_length', v))
            form.addRow("Max length:", max_spin)
            
            layout.addLayout(form)
        
        elif pattern.pattern_type == ColumnPattern.PATTERN_ENUM:
            info_label = QLabel(f"Found {len(pattern.enum_values)} unique values:")
            layout.addWidget(info_label)
            
            if not pattern.enum_selected:
                pattern.enum_selected = list(pattern.enum_values)
            
            selected_text = ", ".join(str(v) for v in pattern.enum_selected)
            values_edit = QLineEdit(selected_text)
            values_edit.setPlaceholderText("value1, value2, value3, ...")
            values_edit.textChanged.connect(
                lambda v, p=pattern: setattr(p, 'enum_selected', [x.strip() for x in v.split(',') if x.strip()])
            )
            layout.addWidget(values_edit)
        
        elif pattern.pattern_type == ColumnPattern.PATTERN_FAKER and pattern.faker_method in ["date", "date_of_birth"]:
            form = QFormLayout()
            
            min_edit = QLineEdit(pattern.date_min or "1970-01-01")
            min_edit.setPlaceholderText("YYYY-MM-DD")
            min_edit.textChanged.connect(lambda v, p=pattern: setattr(p, 'date_min', v))
            form.addRow("From:", min_edit)
            
            max_edit = QLineEdit(pattern.date_max or "2030-12-31")
            max_edit.setPlaceholderText("YYYY-MM-DD")
            max_edit.textChanged.connect(lambda v, p=pattern: setattr(p, 'date_max', v))
            form.addRow("To:", max_edit)
            
            layout.addLayout(form)
        
        elif pattern.pattern_type == ColumnPattern.PATTERN_SEQUENCE:
            form = QFormLayout()
            
            start_spin = QSpinBox()
            start_spin.setRange(0, 999999999)
            start_spin.setValue(pattern.sequence_start)
            start_spin.valueChanged.connect(lambda v, p=pattern: setattr(p, 'sequence_start', v))
            form.addRow("Start from:", start_spin)
            
            increment_spin = QSpinBox()
            increment_spin.setRange(1, 1000)
            increment_spin.setValue(pattern.sequence_increment)
            increment_spin.valueChanged.connect(lambda v, p=pattern: setattr(p, 'sequence_increment', v))
            form.addRow("Increment:", increment_spin)
            
            layout.addLayout(form)
        
        elif pattern.pattern_type == ColumnPattern.PATTERN_REFERENCE:
            ref_label = QLabel(f"References: {pattern.ref_table}.{pattern.ref_column}")
            layout.addWidget(ref_label)
            
            info_label = QLabel("Values will be random IDs from the referenced table")
            info_label.setStyleSheet("color: #666;")
            layout.addWidget(info_label)
        
        elif pattern.pattern_type == ColumnPattern.PATTERN_REGEX:
            regex_label = QLabel("<b>Enter a regex pattern:</b>")
            layout.addWidget(regex_label)
            
            regex_edit = QLineEdit(pattern.regex_pattern or "")
            regex_edit.setPlaceholderText("e.g., [A-Z]{3}[0-9]{4}")
            regex_edit.textChanged.connect(
                lambda v, p=pattern: setattr(p, 'regex_pattern', v)
            )
            layout.addWidget(regex_edit)
            
            examples_label = QLabel(
                "<b>Examples:</b><br>"
                "- <code>[A-Z]{3}[0-9]{4}</code> → ABC1234<br>"
                "- <code>user[0-9]{3}@example\\.com</code> → user123@example.com<br>"
                "- <code>\\d{3}-\\d{3}-\\d{4}</code> → 555-123-4567"
            )
            examples_label.setStyleSheet("color: #666; font-size: 11px;")
            layout.addWidget(examples_label)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.exec()
        
        self.edited_patterns[column.name] = pattern
        
        info_label_widget = self.findChild(QLabel, f"info_{column.name}")
        if info_label_widget:
            self._update_config_info(column, info_label_widget)
    
    def _on_pattern_changed(self, column_name: str, combo_index: int):
        combo = self.sender()
        if not combo:
            return
        
        if column_name not in self.edited_patterns:
            return
        
        pattern = self.edited_patterns[column_name]
        new_type = combo.currentData()
        
        if new_type == ColumnPattern.PATTERN_FAKER:
            display_text = combo.currentText()
            method = FAKER_METHODS_MAP.get(display_text, "text")
            pattern.pattern_type = ColumnPattern.PATTERN_FAKER
            pattern.faker_method = method
        elif new_type == ColumnPattern.PATTERN_ENUM:
            pattern.pattern_type = ColumnPattern.PATTERN_ENUM
            pattern.enum_values = self._get_enum_values_from_sample(column_name)
        elif new_type == ColumnPattern.PATTERN_RANGE_INT:
            pattern.pattern_type = ColumnPattern.PATTERN_RANGE_INT
        elif new_type == ColumnPattern.PATTERN_RANGE_FLOAT:
            pattern.pattern_type = ColumnPattern.PATTERN_RANGE_FLOAT
        elif new_type == ColumnPattern.PATTERN_SEQUENCE:
            pattern.pattern_type = ColumnPattern.PATTERN_SEQUENCE
            pattern.sequence_start = self._detect_next_sequence(column_name)
        elif new_type == ColumnPattern.PATTERN_TEXT:
            pattern.pattern_type = ColumnPattern.PATTERN_TEXT
        elif new_type == ColumnPattern.PATTERN_REGEX:
            pattern.pattern_type = ColumnPattern.PATTERN_REGEX
            pattern.regex_pattern = "[A-Z]{3}[0-9]{3}"
        elif new_type == ColumnPattern.PATTERN_REFERENCE:
            pattern.pattern_type = ColumnPattern.PATTERN_REFERENCE
        else:
            pattern.pattern_type = new_type
        
        self.edited_patterns[column_name] = pattern
        
        col_info = next((c for c in self.table_info.columns if c.name == column_name), None)
        if col_info:
            info_label = self.findChild(QLabel, f"info_{column_name}")
            if info_label:
                self._update_config_info(col_info, info_label)
    
    def _get_enum_values_from_sample(self, column_name: str) -> List[Any]:
        values = self.sample_data.get(column_name, [])
        return list(set(values))
    
    def _detect_next_sequence(self, column_name: str) -> int:
        values = self.sample_data.get(column_name, [])
        numeric = []
        for v in values:
            try:
                numeric.append(int(v))
            except (ValueError, TypeError):
                continue
        return max(numeric) + 1 if numeric else 1
    
    def _on_config_changed(self, column_name: str, config_key: str, value: Any):
        if column_name not in self.edited_patterns:
            return
        
        pattern = self.edited_patterns[column_name]
        
        if config_key == "min_int":
            pattern.min_int = int(value)
        elif config_key == "max_int":
            pattern.max_int = int(value)
        elif config_key == "min_float":
            pattern.min_float = float(value)
        elif config_key == "max_float":
            pattern.max_float = float(value)
        elif config_key == "text_min":
            pattern.text_min_length = int(value)
        elif config_key == "text_max":
            pattern.text_max_length = int(value)
        elif config_key == "date_min":
            pattern.date_min = str(value)
        elif config_key == "date_max":
            pattern.date_max = str(value)
        
        self.edited_patterns[column_name] = pattern
    
    def get_patterns(self) -> Dict[str, ColumnPattern]:
        return self.edited_patterns.copy()
    
    def get_row_count(self) -> int:
        return self.row_count_spin.value()
    
    def should_delete_existing(self) -> bool:
        return self.delete_existing_check.isChecked()
