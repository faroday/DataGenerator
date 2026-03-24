#!/usr/bin/env python3
"""Run DataGenerator from inside the package folder"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datagenerator.ui.main_window import MainWindow

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("DataGenerator")
    app.setOrganizationName("DataGenerator")

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
