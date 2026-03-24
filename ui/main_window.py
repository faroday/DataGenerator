"""Main application window for DataSynth"""

import logging
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QCheckBox,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.models import (
    ConnectionParams,
    DBType,
    Schema,
    TableInfo,
    TableTemplate,
    ColumnTemplate,
    GenerationProgress,
    GenerationStrategy,
    GenerationStrategyType,
)
from core.connection_manager import ConnectionManager
from core.schema_analyzer import SchemaAnalyzer
from generator.data_generator import DataGenerator
from generator.pattern_detector import PatternDetector, ColumnPattern
from ui.pattern_editor_dialog import PatternEditorDialog
from ui.worker import GenerationWorker

logger = logging.getLogger(__name__)


class MainWindow:
    def __init__(self):
        from PyQt6.QtWidgets import QMainWindow, QStatusBar
        
        self.window = QMainWindow()
        self.window.setWindowTitle("DataSynth - Synthetic Data Generator")
        self.window.setMinimumSize(1000, 700)
        
        self._conn = ConnectionManager()
        self._analyzer: Optional[SchemaAnalyzer] = None
        self._schema: Optional[Schema] = None
        self._generator: Optional[DataGenerator] = None
        self._pattern_detector = PatternDetector()
        self._templates: Dict[str, TableTemplate] = {}
        self._worker: Optional[GenerationWorker] = None
        
        self.status_bar = QStatusBar()
        self.window.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Not connected")
        
        self._setup_ui()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("DataSynth")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, 1)
        
        left_panel = self._create_connection_panel()
        content_layout.addWidget(left_panel, 1)
        
        right_panel = self._create_tables_panel()
        content_layout.addWidget(right_panel, 3)
        
        bottom_layout = QHBoxLayout()
        main_layout.addLayout(bottom_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        bottom_layout.addWidget(self.status_label, 1)
    
    def _create_connection_panel(self) -> QWidget:
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDragEnterEvent, QDropEvent
        
        group = QGroupBox("Database Connection")
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["SQLite", "PostgreSQL", "MySQL"])
        form_layout.addRow("Type:", self.db_type_combo)
        
        self.host_input = QLineEdit("localhost")
        self.host_label = QLabel("Host:")
        form_layout.addRow(self.host_label, self.host_input)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(5432)
        self.port_label = QLabel("Port:")
        form_layout.addRow(self.port_label, self.port_spin)
        
        db_layout = QHBoxLayout()
        self.db_name_input = QLineEdit()
        self.db_name_input.setPlaceholderText("/path/to/database.db")
        self.db_name_input.setMinimumWidth(200)
        self.db_name_input.setAcceptDrops(True)
        db_layout.addWidget(self.db_name_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse_file)
        self.browse_btn.setMaximumWidth(80)
        db_layout.addWidget(self.browse_btn)
        self.db_label = QLabel("Database:")
        form_layout.addRow(self.db_label, db_layout)
        
        self.username_input = QLineEdit()
        self.user_label = QLabel("Username:")
        form_layout.addRow(self.user_label, self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_label = QLabel("Password:")
        form_layout.addRow(self.pass_label, self.password_input)
        
        btn_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self.connect_btn)
        
        self.test_btn = QPushButton("Test")
        self.test_btn.clicked.connect(self._on_test)
        btn_layout.addWidget(self.test_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.disconnect_btn)
        
        form_layout.addRow(btn_layout)
        
        self.db_type_combo.currentTextChanged.connect(self._on_db_type_changed)
        
        self._on_db_type_changed("SQLite")
        
        main_layout.addLayout(form_layout)
        
        drop_label = QLabel("💡 Tip: Drag & drop a .sqlite file here")
        drop_label.setStyleSheet("color: #888; font-size: 11px;")
        main_layout.addWidget(drop_label)
        
        group.setLayout(main_layout)
        
        self.db_name_input.dragEnterEvent = self._on_drag_enter
        self.db_name_input.dropEvent = self._on_drop
        self.db_name_input.setDragEnabled(True)
        
        return group
    
    def _on_drag_enter(self, a0):
        from PyQt6.QtGui import QDragEnterEvent
        if a0.mimeData().hasUrls():
            a0.acceptProposedAction()
    
    def _on_drop(self, a0):
        from PyQt6.QtCore import QUrl
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0]
            file_path = url.toLocalFile()
            if file_path.endswith('.sqlite') or file_path.endswith('.db') or '.' in file_path:
                self.db_name_input.setText(file_path)
            a0.acceptProposedAction()
    
    def _on_browse_file(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Select SQLite Database",
            "",
            "SQLite Files (*.sqlite *.db *.sqlite3);;All Files (*)"
        )
        if file_path:
            self.db_name_input.setText(file_path)
    
    def _create_tables_panel(self) -> QWidget:
        self.tabs = QTabWidget()
        
        tables_tab = self._create_tables_tab()
        self.tabs.addTab(tables_tab, "Tables")
        
        settings_tab = self._create_settings_tab()
        self.tabs.addTab(settings_tab, "Settings")
        
        logs_tab = self._create_logs_tab()
        self.tabs.addTab(logs_tab, "Logs")
        
        return self.tabs
    
    def _create_tables_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Select tables to generate data:")
        layout.addWidget(label)
        
        self.tables_tree = QTreeWidget()
        self.tables_tree.setHeaderLabels(["Table", "Columns", "Rows"])
        self.tables_tree.setColumnWidth(0, 250)
        layout.addWidget(self.tables_tree, 1)
        
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.refresh_btn.setEnabled(False)
        btn_layout.addWidget(self.refresh_btn)
        
        self.generate_btn = QPushButton("Generate Data")
        self.generate_btn.clicked.connect(self._on_generate)
        self.generate_btn.setEnabled(False)
        btn_layout.addWidget(self.generate_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form = QFormLayout()
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(100, 50000)
        self.batch_size_spin.setValue(5000)
        self.batch_size_spin.setSuffix(" rows")
        form.addRow("Batch Size:", self.batch_size_spin)
        
        layout.addLayout(form)
        layout.addStretch()
        
        return widget
    
    def _create_logs_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)
        
        return widget
    
    def _log(self, message: str):
        self.logs_text.append(message)
        logger.info(message)
    
    def _on_db_type_changed(self, db_type: str):
        if db_type == "SQLite":
            self.host_label.setVisible(False)
            self.host_input.setVisible(False)
            self.port_label.setVisible(False)
            self.port_spin.setVisible(False)
            self.user_label.setVisible(False)
            self.username_input.setVisible(False)
            self.pass_label.setVisible(False)
            self.password_input.setVisible(False)
            self.db_label.setText("File:")
            self.db_name_input.setPlaceholderText("/path/to/database.db")
        elif db_type == "PostgreSQL":
            self.host_label.setVisible(True)
            self.host_input.setVisible(True)
            self.port_label.setVisible(True)
            self.port_spin.setVisible(True)
            self.user_label.setVisible(True)
            self.username_input.setVisible(True)
            self.pass_label.setVisible(True)
            self.password_input.setVisible(True)
            self.port_spin.setValue(5432)
            self.db_label.setText("Database:")
            self.db_name_input.setPlaceholderText("database_name")
        elif db_type == "MySQL":
            self.host_label.setVisible(True)
            self.host_input.setVisible(True)
            self.port_label.setVisible(True)
            self.port_spin.setVisible(True)
            self.user_label.setVisible(True)
            self.username_input.setVisible(True)
            self.pass_label.setVisible(True)
            self.password_input.setVisible(True)
            self.port_spin.setValue(3306)
            self.db_label.setText("Database:")
            self.db_name_input.setPlaceholderText("database_name")
    
    def _get_connection_params(self) -> ConnectionParams:
        db_type_map = {
            "PostgreSQL": DBType.POSTGRESQL,
            "MySQL": DBType.MYSQL,
            "SQLite": DBType.SQLITE,
        }
        
        return ConnectionParams(
            db_type=db_type_map[self.db_type_combo.currentText()],
            host=self.host_input.text(),
            port=self.port_spin.value(),
            database=self.db_name_input.text(),
            username=self.username_input.text(),
            password=self.password_input.text(),
        )
    
    def _on_connect(self):
        try:
            params = self._get_connection_params()
            self._conn.connect(params)
            self._analyzer = SchemaAnalyzer(self._conn)
            self._schema = self._analyzer.analyze()
            self._generator = DataGenerator(self._conn, self._analyzer)
            
            self._populate_tables()
            
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.generate_btn.setEnabled(True)
            
            self.status_bar.showMessage(f"Connected: {params.database} ({len(self._schema.get_tables())} tables)")
            self._log(f"Connected to {params.database}")
        
        except Exception as e:
            self.status_bar.showMessage(f"Connection failed: {e}", 5000)
            self._log(f"Connection failed: {e}")
    
    def _on_test(self):
        try:
            params = self._get_connection_params()
            temp_conn = ConnectionManager()
            temp_conn.connect(params)
            success = temp_conn.test_connection()
            temp_conn.disconnect()
            
            if success:
                self.status_bar.showMessage("Test successful: connection works!", 3000)
            else:
                self.status_bar.showMessage("Test failed: connection does not work", 5000)
        
        except Exception as e:
            self.status_bar.showMessage(f"Test failed: {e}", 5000)
    
    def _on_disconnect(self):
        self._conn.disconnect()
        self._schema = None
        self._analyzer = None
        self._generator = None
        self._templates.clear()
        self.tables_tree.clear()
        
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        
        self.status_bar.showMessage("Not connected")
        self._log("Disconnected")
    
    def _on_refresh(self):
        if self._analyzer:
            self._schema = self._analyzer.analyze()
            self._populate_tables()
            self._log("Schema refreshed")
    
    def _populate_tables(self):
        self.tables_tree.clear()
        self._templates.clear()
        
        if not self._schema:
            return
        
        for table_info in self._schema.get_tables():
            item = QTreeWidgetItem(self.tables_tree)
            item.setText(0, table_info.name)
            item.setText(1, str(len(table_info.columns)))
            item.setText(2, str(table_info.row_count))
            item.setCheckState(0, Qt.CheckState.Unchecked)
            
            template = TableTemplate(
                table_name=table_info.name,
                row_count=100,
            )
            for col in table_info.columns:
                strategy = GenerationStrategy(strategy_type=GenerationStrategyType.RANDOM_STRING)
                col_template = ColumnTemplate(column=col, strategy=strategy, enabled=True)
                template.columns.append(col_template)
            
            self._templates[table_info.name] = template
    
    def _on_generate(self):
        selected_tables = []
        
        for i in range(self.tables_tree.topLevelItemCount()):
            item = self.tables_tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                table_name = item.text(0)
                selected_tables.append(table_name)
        
        if not selected_tables:
            QMessageBox.warning(self.window, "Warning", "Please select at least one table")
            return
        
        templates = {}
        for name in selected_tables:
            if name in self._templates:
                templates[name] = self._templates[name]
            else:
                self._log(f"Warning: no template found for {name}")
        
        if not templates:
            QMessageBox.warning(self.window, "Warning", "No templates found for selected tables")
            return
        
        dialog_result = self._collect_sample_data_and_show_dialog(templates)
        if dialog_result is None:
            self._log("Pattern editing cancelled")
            return
        
        patterns, row_count, should_delete = dialog_result
        
        for template in templates.values():
            template.row_count = row_count
        
        if should_delete:
            reply = QMessageBox.question(
                self.window,
                "Confirm",
                f"This will delete all existing data in {len(selected_tables)} tables. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self._log(f"Generating {row_count} rows for: {list(templates.keys())}")
        
        if should_delete:
            for table_name in selected_tables:
                try:
                    self._conn.delete_from_table(table_name)
                    self._log(f"Deleted existing data from: {table_name}")
                except Exception as e:
                    self._log(f"Failed to delete from {table_name}: {e}")
        
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            self._log("Starting generation...")
            result = self._generator.generate(templates, patterns)
            self._log(f"Generated {result.rows_generated} rows")
            self._log("Generation complete!")
            self._on_finished(result)
        except Exception as e:
            self._log(f"Error: {e}")
            import traceback
            self._log(traceback.format_exc())
            self._on_error(str(e))
    
    def _collect_sample_data_and_show_dialog(self, templates: Dict[str, TableTemplate]) -> Optional[tuple]:
        detector = PatternDetector()
        all_patterns = {}
        row_count = 100
        should_delete = False
        
        for table_name, template in templates.items():
            table_info = self._conn.get_table_info(table_name)
            sample_data = self._get_sample_data(table_name, limit=100)
            
            dialog = PatternEditorDialog(table_info, sample_data, self.window)
            
            if dialog.exec() != PatternEditorDialog.DialogCode.Accepted:
                return None
            
            patterns = dialog.get_patterns()
            all_patterns[table_name] = patterns
            row_count = dialog.get_row_count()
            should_delete = dialog.should_delete_existing()
            
            self._log(f"Patterns for {table_name} ({row_count} rows, delete={should_delete}):")
            for col_name, pattern in patterns.items():
                self._log(f"  {col_name}: {pattern.get_display_name()}")
        
        return (all_patterns, row_count, should_delete)
    
    def _get_sample_data(self, table_name: str, limit: int = 100) -> Dict[str, List[Any]]:
        sample_data = {}
        try:
            table_info = self._conn.get_table_info(table_name)
            columns = [col.name for col in table_info.columns]
            
            result = self._conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            if not result:
                return sample_data
            
            for row in result:
                for i, col_name in enumerate(columns):
                    if col_name not in sample_data:
                        sample_data[col_name] = []
                    sample_data[col_name].append(row[i])
            
        except Exception as e:
            self._log(f"Failed to get sample data for {table_name}: {e}")
        
        return sample_data
    
    def _on_progress(self, progress: GenerationProgress):
        self.progress_bar.setValue(int(progress.percentage))
        self.status_label.setText(
            f"Generating: {progress.current_table} ({progress.generated_rows}/{progress.total_rows})"
        )
    
    def _on_finished(self, result):
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if result.success:
            self._log(f"Completed: {result.rows_generated} rows in {result.duration_seconds:.2f}s")
            self.status_bar.showMessage(f"Success: Generated {result.rows_generated} rows in {result.duration_seconds:.2f}s")
        else:
            self._log(f"Failed: {result.error_message}")
            self.status_bar.showMessage(f"Error: {result.error_message}", 10000)
        
        self.status_label.setText("Ready")
    
    def _on_error(self, error: str):
        self._log(f"Error: {error}")
        self.status_bar.showMessage(f"Error: {error}", 10000)
        
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")
    
    def _on_cancel(self):
        if self._worker and self._generator:
            self._generator.cancel()
            self._log("Cancellation requested...")
    
    def show(self):
        self.window.show()
