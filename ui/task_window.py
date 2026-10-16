from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTime
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTimeEdit
from core.tasks import load_today_tasks, save_today_tasks


class TaskRow(QWidget):
    remove_requested = pyqtSignal(object)

    def __init__(self, task_data=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._build_ui(task_data or {})

    def _build_ui(self, task_data):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Task description…")
        self.task_input.setText(task_data.get("text", ""))
        self.task_input.setFont(QFont("Segoe UI", 9))

        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("hh:mm AP") 
        self.start_time.setFixedWidth(80)
        start = task_data.get("start_time", "09:00 AM")
        try:
            dt = datetime.strptime(start, "%I:%M %p")
            h, m = dt.hour, dt.minute
        except Exception:
            h, m = 9, 0
        self.start_time.setTime(QTime(h, m))

        arrow = QLabel("→")
        arrow.setFixedWidth(14)
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setStyleSheet("color: #6373a8; background: transparent;")

        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("hh:mm AP")
        self.end_time.setFixedWidth(80)
        end = task_data.get("end_time", "10:00 AM")
        try:
            dt2 = datetime.strptime(end, "%I:%M %p")
            h2, m2 = dt2.hour, dt2.minute
        except Exception:
            h2, m2 = 10, 0
        self.end_time.setTime(QTime(h2, m2))

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        remove_btn.setStyleSheet("""
            QPushButton {
                background: rgba(200,70,90,200);
                color: white; border: none; border-radius: 5px;
                font-size: 9px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(230,50,70,240); }
        """)

        layout.addWidget(self.task_input, stretch=1)
        layout.addWidget(self.start_time)
        layout.addWidget(arrow)
        layout.addWidget(self.end_time)
        layout.addWidget(remove_btn)

    def get_data(self):
        return {
            "text": self.task_input.text().strip(),
            "start_time": self.start_time.time().toString("hh:mm AP"), 
            "end_time": self.end_time.time().toString("hh:mm AP"),     
            "done": False,
        }


class TaskInputWindow(QWidget):
    tasks_saved = pyqtSignal()

    def __init__(self, theme_mood="Happy", parent=None):
        super().__init__(parent)
        self.theme_mood = theme_mood
        self.setWindowTitle("Asher — Manage Tasks")
        self.setMinimumWidth(500)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self._task_rows: list[TaskRow] = []
        self._build_ui()
        self._apply_style()
        self._load_existing()
        self.adjustSize()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("📋 Manage Today's Tasks")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Set tasks with time windows. Asher follows your cursor when they're overdue!")
        sub.setFont(QFont("Segoe UI", 8))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #888;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        hdr = QHBoxLayout()
        for txt, stretch, w in [("Task", 1, None), ("From", 0, 80), ("", 0, 14), ("To", 0, 80), ("", 0, 24)]:
            l = QLabel(txt)
            l.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            l.setStyleSheet("color: #6373a8;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if w:
                l.setFixedWidth(w)
            hdr.addWidget(l, stretch=stretch)
        layout.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(280)
        scroll.setMinimumHeight(80)

        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(4)
        self._rows_layout.addStretch()
        scroll.setWidget(self._rows_container)
        layout.addWidget(scroll)

        add_btn = QPushButton("＋ Add Task")
        add_btn.setFont(QFont("Segoe UI", 9))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setObjectName("add_btn")
        add_btn.clicked.connect(lambda: self._add_row())
        layout.addWidget(add_btn)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e05070; background: transparent;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        close_btn = QPushButton("✕ Close")
        close_btn.setFont(QFont("Segoe UI", 9))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(self.close)

        save_btn = QPushButton("Save Tasks 🌸")
        save_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(close_btn)
        btn_row.addWidget(save_btn, stretch=1)
        layout.addLayout(btn_row)

    def _load_existing(self):
        tasks = load_today_tasks()
        if tasks:
            for t in tasks:
                self._add_row(t)
        else:
            self._add_row()   

    def _add_row(self, task_data=None):
        row = TaskRow(task_data)
        row.remove_requested.connect(self._remove_row)
        insert_pos = self._rows_layout.count() - 1  # before stretch
        self._rows_layout.insertWidget(insert_pos, row)
        self._task_rows.append(row)

    def _remove_row(self, row: TaskRow):
        self._rows_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()
        self._task_rows.remove(row)
        self.error_label.setText("")

    def _save(self):
        tasks = []
        for row in self._task_rows:
            data = row.get_data()
            if not data["text"]:
                self.error_label.setText("Task description can't be empty!")
                return
            tasks.append(data)
        existing = {t["text"]: t.get("done", False) for t in load_today_tasks()}
        for t in tasks:
            t["done"] = existing.get(t["text"], False)
        save_today_tasks(tasks)
        self.tasks_saved.emit()
        self.close()

    def _apply_style(self):
        themes = {
            "Happy": {"bg": "#fff0f5", "border": "#e0b0c8", "btn": "#c47ea0", "text": "#3a1a2e"},
            "Calm": {"bg": "#f0f8ff", "border": "#b0c4de", "btn": "#6495ed", "text": "#191970"},
            "Gloomy": {"bg": "#2f4f4f", "border": "#556b2f", "btn": "#8fbc8f", "text": "#f8f8ff"},
            "Energetic": {"bg": "#ffebcd", "border": "#ffd700", "btn": "#ff8c00", "text": "#8b4500"}
        }
        colors = themes.get(self.theme_mood, themes["Happy"])
        
        self.setStyleSheet(f"""
            QWidget {{ background: {colors['bg']}; color: {colors['text']}; }}
            QLineEdit {{
                background: white; border: 2px solid {colors['border']}; border-radius: 8px; padding: 5px 8px; color: black;
            }}
            QLineEdit:focus {{ border-color: {colors['btn']}; }}
            QTimeEdit {{
                background: white; border: 2px solid {colors['border']}; border-radius: 6px; padding: 2px 4px; color: black;
            }}
            QTimeEdit:focus {{ border-color: {colors['btn']}; }}
            QPushButton {{
                background: {colors['btn']}; color: white; border: none; border-radius: 10px; padding: 8px 16px;
            }}
            QPushButton:hover {{ filter: brightness(0.9); }}
            QPushButton#close_btn {{
                background: rgba(0,0,0,0.1); color: {colors['text']};
            }}
            QPushButton#close_btn:hover {{ background: rgba(0,0,0,0.2); }}
            QPushButton#add_btn {{
                background: transparent;
                border: 2px dashed {colors['border']};
                color: {colors['text']};
            }}
            QPushButton#add_btn:hover {{ background: {colors['btn']}; color: white; border-color: {colors['btn']}; }}
            QScrollArea {{ background: transparent; }}
        """)


class TaskPanel(QWidget):
    task_toggled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.checkboxes: list[QCheckBox] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(5)

        header = QLabel("📋 Today's Tasks")
        header.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffaad4; background: transparent;")
        layout.addWidget(header)

        self._tasks_layout = QVBoxLayout()
        self._tasks_layout.setSpacing(4)
        self._tasks_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._tasks_layout)

        self.refresh()

    def refresh(self):
        while self._tasks_layout.count():
            item = self._tasks_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self.checkboxes.clear()

        tasks = load_today_tasks()
        for idx, task in enumerate(tasks):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)

            cb = QCheckBox()
            cb.setChecked(task["done"])
            cb.setFixedWidth(18)
            cb.stateChanged.connect(lambda state, i=idx: self._toggle(i, state))

            label_txt = task["text"]
            et = task.get("end_time", "")
            st = task.get("start_time", "")
            if et:
                label_txt += f"\n⏰ {st}–{et}"

            text = QLabel(label_txt)
            text.setWordWrap(True)
            text.setFont(QFont("Segoe UI", 7))
            if task["done"]:
                text.setStyleSheet("color: #906080; background: transparent; text-decoration: line-through;")
            else:
                text.setStyleSheet("color: #567896; background: transparent;")

            row.addWidget(cb)
            row.addWidget(text, stretch=1)

            container = QWidget()
            container.setStyleSheet("background: transparent;")
            container.setLayout(row)
            self._tasks_layout.addWidget(container)
            self.checkboxes.append(cb)

    def _toggle(self, idx: int, state: int):
        tasks = load_today_tasks()
        if idx < len(tasks):
            tasks[idx]["done"] = (state == 2)
        save_today_tasks(tasks)
        self.task_toggled.emit()