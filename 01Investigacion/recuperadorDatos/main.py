#!/usr/bin/env python3
"""
Unitree Motor Monitor — Punto de entrada.
"""

import sys
from PyQt6.QtWidgets import QApplication
from unitree_monitor.ui_main import MotorMonitorWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MotorMonitorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

