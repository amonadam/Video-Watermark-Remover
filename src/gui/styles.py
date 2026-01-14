# src/gui/styles.py

MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #f0f0f0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}

QPushButton {
    background-color: #4CAF50;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #45a049;
}

QPushButton:pressed {
    background-color: #3d8b40;
}

QLineEdit {
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 3px;
}

QTextEdit {
    border: 1px solid #ccc;
    border-radius: 3px;
    background-color: white;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #cccccc;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
}

QProgressBar {
    border: 1px solid #ccc;
    border-radius: 3px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4CAF50;
    border-radius: 3px;
}
"""

PREVIEW_DIALOG_STYLE = """
QDialog {
    background-color: white;
}

QLabel {
    color: #333;
}

QPushButton {
    background-color: #2196F3;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #0b7dda;
}
"""

PROGRESS_DIALOG_STYLE = """
QDialog {
    background-color: white;
}

QLabel {
    color: #333;
    font-weight: bold;
}

QProgressBar {
    border: 1px solid #ccc;
    border-radius: 3px;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #4CAF50;
    border-radius: 3px;
}

QPushButton {
    background-color: #f44336;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #d32f2f;
}
"""

LOGIN_DIALOG_STYLE = """
QDialog {
    background-color: white;
    border-radius: 8px;
}

QLabel {
    color: #333333;
    font-weight: normal;
    line-height: 1.5;
    min-height: 20px;
}
"""

LINE_EDIT_STYLE = """
QLineEdit {
    padding: 10px 12px;
    border: 1px solid #cccccc;
    border-radius: 4px;
    font-size: 14px;
    background-color: white;
    min-height: 36px;
}

QLineEdit:focus {
    border: 2px solid #2196F3;
    outline: none;
}
"""

BUTTON_STYLE = """
QPushButton {
    background-color: #2196F3;
    border: none;
    color: white;
    padding: 10px 20px;
    border-radius: 4px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #0b7dda;
}

QPushButton:pressed {
    background-color: #0d6efd;
}

QPushButton:disabled {
    background-color: #cccccc;
}
"""

BUTTON_STYLE_CANCEL = """
QPushButton {
    background-color: #f44336;
    border: none;
    color: white;
    padding: 10px 20px;
    border-radius: 4px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #d32f2f;
}

QPushButton:pressed {
    background-color: #b91c1c;
}

QPushButton:disabled {
    background-color: #cccccc;
}
"""

BUTTON_STYLE_FLAT = """
QPushButton {
    background-color: transparent;
    border: none;
    color: #2196F3;
    font-size: 14px;
    padding: 0;
    text-decoration: underline;
}

QPushButton:hover {
    color: #0b7dda;
    background-color: transparent;
}

QPushButton:pressed {
    color: #0d6efd;
    background-color: transparent;
}
"""