from PyQt6.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont


class DialogueBubble(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(220)
        self.setMinimumHeight(50)
        self.setFont(QFont("Segoe UI", 9))
        self.setStyleSheet("""
            QLabel {
                background: rgba(30, 10, 25, 210);
                color: #ffe0f4;
                border: 2px solid #c47ea0;
                border-radius: 12px;
                padding: 10px 12px;
                font-family: 'Segoe UI';
                font-size: 9pt;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)

        self.hide()

        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def say(self, text: str, duration_ms: int = 4000):
        self.setText(text)
        self.adjustSize()
        self.setFixedWidth(220)
        self.show()
        self._hide_timer.stop()
        self._hide_timer.start(duration_ms)