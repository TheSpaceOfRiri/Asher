import os, random
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QFont, QCursor

from core.mood import compute_mood, PROUD, HAPPY, CONCERNED, ANGRY, FURIOUS
from core.tasks import (
    tasks_exist_today, get_completion_ratio,
    none_done, all_done, has_overdue_tasks
)
from core.reminders import get_reminder
from core.trust import get_trust, trust_greeting, record_day, get_trust_label

IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "images")

MOOD_IMAGES_DAY = {
    PROUD:     "neutral.png",
    HAPPY:     "happy.png",
    CONCERNED: "concerned.png",
    ANGRY:     "pissed.png",
    FURIOUS:   "frustrated.png",
}

MOOD_IMAGES_EVENING = {
    PROUD:     "neutral.png",
    HAPPY:     "thoughtful.png",
    CONCERNED: "concerned.png",
    ANGRY:     "frustrated.png",
    FURIOUS:   "frustrated.png",
}

OVERDUE_EXPRESSIONS = [
    "neutral.png"
]

OVERDUE_DIALOGUES = [
    "Hey! Your task is OVERDUE! 😤",
    "I'm watching you. The clock is ALSO watching you.",
    "Tick tock… that task won't finish itself!",
    "You were supposed to be done by now! 😠",
    "I followed your cursor here. Do the task.",
    "Running out of time… or have you already? 🤔",
    "The deadline passed. I noticed. Did YOU?",
    "I will haunt this cursor until you work.",
    "Task overdue. This is NOT a drill.",
]

EVENING_DIALOGUES = [
    "It's getting late… did you finish everything? 🌙",
    "Evening check-in. How are those tasks looking?",
    "The day's almost over. No pressure. (Lots of pressure.)",
    "Stars are out. Tasks still aren't done. Interesting.",
    "Nighttime Asher is sleepier but just as judgmental. 🌛",
]

SLEEP_IMAGE   = "sleep.png"
NEUTRAL_IMAGE = "neutral.png"

WALK_LEFT     = [f"walk {i}.png" for i in range(1, 10)]
WALK_RIGHT    = [f"walk {i}.png" for i in range(10, 19)]
DOLL_SIZE     = (180, 180)

def _px(filename: str, size=DOLL_SIZE) -> QPixmap:
    path = os.path.join(IMG_DIR, filename)
    if os.path.exists(path):
        return QPixmap(path).scaled(
            size[0], size[1],
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    blank = QPixmap(size[0], size[1])
    blank.fill(Qt.GlobalColor.transparent)
    return blank

def _is_evening() -> bool:
    return datetime.now().hour >= 18

class DollWindow(QWidget):
    """Tiny transparent window — just the character PNG. Fully draggable."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(DOLL_SIZE[0], DOLL_SIZE[1])
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background: transparent;")
        self.label.setPixmap(_px("happy.png"))
        layout.addWidget(self.label)

        self._drag_offset = QPoint()
        self.is_dragging  = False

    def show_image(self, filename: str):
        self.label.setPixmap(_px(filename))

    def go_to(self, x: int, y: int):
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self._drag_offset = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(self.mapToGlobal(event.pos()) - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)

class FloatingDialogueBubble(QWidget):
    """Appears near the doll and moves with it. Now styled in cozy beige!"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(QFont("Segoe UI", 9))
        self._label.setStyleSheet("""
            QLabel {
                background: rgba(252, 248, 242, 230);
                color: #4a3b32;
                border: 2px solid #d4c5b9;
                border-radius: 12px;
                padding: 10px 14px;
                font-family: 'Segoe UI';
                font-size: 9pt;
            }
        """)
        layout.addWidget(self._label)

        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

        self.hide()

    def say(self, text: str, duration_ms: int = 4000):
        self._label.setText(text)
        self._label.adjustSize()
        self.adjustSize()
        self.show()
        self._hide_timer.stop()
        self._hide_timer.start(duration_ms)

    def follow_doll(self, doll_pos: QPoint):
        """Reposition near doll — try left first, fallback to right."""
        if not self.isVisible():
            return
        screen = QApplication.primaryScreen().availableGeometry()
        bx = doll_pos.x() - self.width() - 8
        by = doll_pos.y() - self.height() // 2 + DOLL_SIZE[1] // 4
        if bx < screen.left():
            bx = doll_pos.x() + DOLL_SIZE[0] + 8
        by = max(screen.top(), min(by, screen.bottom() - self.height()))
        bx = max(screen.left(), min(bx, screen.right() - self.width()))
        self.move(bx, by)

class CompanionWindow(QWidget):
    """Fixed panel at bottom-right; orchestrates doll + bubble."""

    def __init__(self):
        super().__init__()

        from ui.task_window import TaskInputWindow, TaskPanel
        self._TaskInputWindow = TaskInputWindow
        self._TaskPanel       = TaskPanel

        self._soothe_level      = 0
        self._ignore_count      = 0
        self._soothed_flash     = False
        self._is_sleeping       = False
        self._last_done_count   = 0
        self._expr_idx          = 0

        self._walk_frame   = 0
        self._is_walking   = False
        self._walk_frames  = WALK_LEFT
        self._follow_speed = 1.5   

        self.doll   = DollWindow()
        self.bubble = FloatingDialogueBubble()

        self._setup_window()
        self._build_ui()
        self._apply_style()

        screen = QApplication.primaryScreen().availableGeometry()
        self.doll.move(
            screen.width() - 170,
            screen.height() - DOLL_SIZE[1] - 270,
        )
        self.doll.show()

        self._walk_anim_timer = QTimer()
        self._walk_anim_timer.timeout.connect(self._tick_walk_frame)
        self._walk_anim_timer.start(140)      

        self._move_timer = QTimer()
        self._move_timer.timeout.connect(self._tick_movement)
        self._move_timer.start(16)

        self._expr_timer = QTimer()           
        self._expr_timer.timeout.connect(self._cycle_overdue_expr)
        self._expr_timer.start(2200)

        self._reminder_timer = QTimer()
        self._reminder_timer.timeout.connect(self._on_reminder_tick)
        self._reminder_timer.start(60_000)

        self._mood_timer = QTimer()
        self._mood_timer.timeout.connect(self._check_tasks_and_mood)
        self._mood_timer.start(10_000)

        self._overdue_timer = QTimer()        
        self._overdue_timer.timeout.connect(self._check_overdue)
        self._overdue_timer.start(30_000)

        self._wake_timer = QTimer()
        self._wake_timer.setSingleShot(True)
        self._wake_timer.timeout.connect(self._wake_up)

        self._evening_timer = QTimer()
        self._evening_timer.timeout.connect(self._evening_check)
        self._evening_timer.start(300_000)

        self._soothe_decay_timer = QTimer()
        self._soothe_decay_timer.setSingleShot(True)
        self._soothe_decay_timer.timeout.connect(self._decay_soothe_level)

        self._ask_user_mood_timer = QTimer()
        self._ask_user_mood_timer.timeout.connect(self._ask_about_user_mood)
        self._ask_user_mood_timer.start(180_000)

        QTimer.singleShot(600, self._on_boot)

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(240, 310)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.width()  - self.width()  - 10,
            screen.height() - self.height() - 50,
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.panel_frame = QFrame()
        panel = QVBoxLayout(self.panel_frame)
        panel.setContentsMargins(12, 10, 12, 10)
        panel.setSpacing(6)

        top_row = QHBoxLayout()
        self.mood_badge = QLabel("😊 Happy")
        self.mood_badge.setObjectName("mood_badge")
        self.mood_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mood_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        exit_btn = QPushButton("✕")
        exit_btn.setObjectName("exit_btn")
        exit_btn.setFixedSize(20, 20)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setToolTip("Quit Asher")
        exit_btn.clicked.connect(QApplication.quit)

        top_row.addWidget(self.mood_badge, stretch=1)
        top_row.addWidget(exit_btn)
        panel.addLayout(top_row)

        self.task_panel = self._TaskPanel()
        self.task_panel.task_toggled.connect(self._on_task_toggled)
        self.task_panel.setStyleSheet("""
            QCheckBox {
                color: #5c4d42;
                spacing: 6px;
                font-size: 8pt;
                font-family: 'Segoe UI';
            }
            QCheckBox::indicator {
                width: 14px; height: 14px;
                border-radius: 3px;
                border: 2px solid #bdae9f;
                background: rgba(255,255,255,180);
            }
            QCheckBox::indicator:checked { background: #9e8e7f; border-color: #9e8e7f; }
            QLabel {
                color: #7d6c5f;
                font-weight: bold;
                background: transparent;
            }
            QWidget { background: transparent; }
        """)
        panel.addWidget(self.task_panel)

        btn_row = QHBoxLayout()
        self.pet_btn     = QPushButton("🤗 Pet")
        self.promise_btn = QPushButton("📝 Promise")
        for btn in (self.pet_btn, self.promise_btn):
            btn.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(26)
        self.pet_btn.clicked.connect(self._on_pet)
        self.promise_btn.clicked.connect(self._on_promise)
        btn_row.addWidget(self.pet_btn)
        btn_row.addWidget(self.promise_btn)
        panel.addLayout(btn_row)

        self.tasks_btn = QPushButton("📋 Manage Tasks")
        self.tasks_btn.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        self.tasks_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tasks_btn.setFixedHeight(26)
        self.tasks_btn.clicked.connect(self._open_task_input)
        panel.addWidget(self.tasks_btn)

        self.trust_label = QLabel(self._trust_text())
        self.trust_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trust_label.setFont(QFont("Segoe UI", 7))
        self.trust_label.setStyleSheet("color: #7d6c5f; background: transparent;")
        panel.addWidget(self.trust_label)

        root.addWidget(self.panel_frame)

    def _apply_style(self):
        """Applied beautiful clean beige/cream theme styles"""
        self.setStyleSheet("""
            QWidget { background: transparent; }
            QPushButton {
                background: #bdae9f;
                color: #4a3b32; border: none;
                border-radius: 7px; padding: 3px 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #9e8e7f; color: white; }
            QPushButton#exit_btn {
                background: #d9a096;
                border-radius: 4px; font-size: 9px; padding: 0px;
                color: white;
            }
            QPushButton#exit_btn:hover { background: #c27b70; }
            QLabel#mood_badge {
                background: #ebe3d5;
                border-radius: 7px; padding: 2px 8px;
                color: #4a3b32; font-weight: bold;
            }
        """)
        self.panel_frame.setStyleSheet("""
            QFrame {
                background: rgba(252, 248, 242, 230);
                border-radius: 16px;
                border: 1px solid rgba(189, 174, 159, 140);
            }
        """)

    def _on_boot(self):
        self._say("Hi Riri!", 3000)
        if not tasks_exist_today():
            QTimer.singleShot(3200, lambda: self._say("Good morning~ How is your mood today? Set your tasks! 🌸", 5000))
            QTimer.singleShot(4500, self._open_task_input)
        else:
            QTimer.singleShot(3200, lambda: self._say(trust_greeting(), 5000))
            QTimer.singleShot(3500, self._check_tasks_and_mood)

    def _on_task_toggled(self):
        done_count = self._count_done()

        if all_done():
            self._go_to_sleep_all_done()
            return

        if done_count > self._last_done_count:
            self._last_done_count = done_count
            self._stop_walking()
            self._rest_on_panel()
        else:
            self._last_done_count = done_count
            self._check_tasks_and_mood()

    def _rest_on_panel(self):
        px, py = self.pos().x(), self.pos().y()
        tx = px + self.width() // 2 - DOLL_SIZE[0] // 2
        ty = py - DOLL_SIZE[1] + 12
        self.doll.go_to(tx, ty)
        self.doll.show_image(SLEEP_IMAGE)
        self._say(random.choice([
            "One down! Napping on the panel~ 💤",
            "Progress noted. *snoozes* 😴",
            "Nice work! A brief rest is deserved… zzz",
            "Task done! I'll just nap here. 💤",
        ]), 4000)
        QTimer.singleShot(5000, self._short_wake)

    def _short_wake(self):
        self._show_mood_image()
        QTimer.singleShot(500, self._check_tasks_and_mood)

    def _count_done(self) -> int:
        from core.tasks import load_today_tasks
        return sum(1 for t in load_today_tasks() if t["done"])

    def _check_tasks_and_mood(self):
        if self._is_sleeping:
            return
        self.task_panel.refresh()
        mood = compute_mood(self._soothe_level)
        self._update_mood_badge(mood)
        
        if not self._is_walking:
            self._show_mood_image()
            
        self.trust_label.setText(self._trust_text())
        self._check_overdue()

    def _check_overdue(self):
        if self._is_sleeping:
            return
        if has_overdue_tasks():
            if not self._is_walking:
                self._start_walking()
        else:
            if self._is_walking:
                self._stop_walking()
                self._show_mood_image()

    def _go_to_sleep_all_done(self):
        self._is_sleeping = True
        self._stop_walking()
        self.task_panel.refresh()
        self._move_doll_to_panel_top()
        self.doll.show_image(SLEEP_IMAGE)
        self._update_mood_badge(PROUD)
        self._say("All done?! Amazing. I'm going to sleep now. 💤", 6000)
        self._wake_timer.start(3_600_000)

    def _go_to_corner_sleep(self):
        self._is_sleeping = True
        self._stop_walking()
        screen = QApplication.primaryScreen().availableGeometry()
        tx = screen.width()  - DOLL_SIZE[0] - 15
        ty = screen.height() - DOLL_SIZE[1] - self.height() - 20
        self.doll.go_to(tx, ty)
        self.doll.show_image(SLEEP_IMAGE)
        self._say("Fine… I'll nap. But those tasks are still there! 💤", 5000)
        self._wake_timer.start(3_600_000)

    def _wake_up(self):
        self._is_sleeping = False
        self._show_mood_image()
        self._say(random.choice([
            "Wakey wakey~ Don't forget anything! 🌸",
            "I had a lovely nap. How are YOU doing?",
            "Back from dreamland. Everything okay?",
            "I'm awake. Just checking in~ 💕",
        ]), 5000)
        self._check_tasks_and_mood()

    def _move_doll_to_panel_top(self):
        px, py = self.pos().x(), self.pos().y()
        tx = px + self.width() // 2 - DOLL_SIZE[0] // 2
        ty = py - DOLL_SIZE[1] + 12
        self.doll.go_to(tx, ty)

    def _start_walking(self):
        self._is_walking = True

    def _stop_walking(self):
        self._is_walking = False

    def _tick_walk_frame(self):
        if not self._is_walking:
            return
        self._walk_frame = (self._walk_frame + 1) % len(self._walk_frames)
        self.doll.show_image(self._walk_frames[self._walk_frame])

    def _cycle_overdue_expr(self):
        if not self._is_walking or self._is_sleeping:
            return
            
        if self._ignore_count >= 30:
            escalated_exprs = ["pissed.png", "frustrated.png"]
            self._expr_idx = (self._expr_idx + 1) % len(escalated_exprs)
            self.doll.show_image(escalated_exprs[self._expr_idx])
        else:
            self._expr_idx = (self._expr_idx + 1) % len(OVERDUE_EXPRESSIONS)
            self.doll.show_image(OVERDUE_EXPRESSIONS[self._expr_idx])
            
        QTimer.singleShot(600, self._restore_walk_frame)
        if random.random() < 0.25:
            self._say(random.choice(OVERDUE_DIALOGUES), 3500)

    def _restore_walk_frame(self):
        if self._is_walking:
            self.doll.show_image(self._walk_frames[self._walk_frame])

    def _tick_movement(self):
        if self._is_sleeping or self.doll.is_dragging:
            return

        if self._is_walking:
            cursor = QCursor.pos()
            tx = cursor.x() - DOLL_SIZE[0] // 2
            ty = cursor.y() - DOLL_SIZE[1] // 2

            cur = self.doll.pos()
            dx = tx - cur.x()
            dy = ty - cur.y()
            dist = (dx**2 + dy**2) ** 0.5

            if dist > 5:
                if dx < 0 and self._walk_frames is not WALK_LEFT:
                    self._walk_frames = WALK_LEFT
                elif dx >= 0 and self._walk_frames is not WALK_RIGHT:
                    self._walk_frames = WALK_RIGHT
                nx = cur.x() + int(dx / dist * self._follow_speed)
                ny = cur.y() + int(dy / dist * self._follow_speed)
                self.doll.go_to(nx, ny)

            if self.bubble.isVisible():
                self.bubble.follow_doll(self.doll.pos())

    def _on_reminder_tick(self):
        if self._is_sleeping or not tasks_exist_today():
            return
        if get_completion_ratio() == 1.0:
            return
        self._ignore_count += 1
        self._say(get_reminder(self._ignore_count), 5000)

    def _evening_check(self):
        if not _is_evening() or self._is_sleeping:
            return
        self._say(random.choice(EVENING_DIALOGUES), 5000)
        self._check_tasks_and_mood()

    def _get_mood_images(self) -> dict:
        return MOOD_IMAGES_EVENING if _is_evening() else MOOD_IMAGES_DAY

    def _show_mood_image(self):
        if self._soothed_flash:
            self.doll.show_image("happy.png")
            return
        mood = compute_mood(self._soothe_level)
        self.doll.show_image(self._get_mood_images().get(mood, NEUTRAL_IMAGE))

    def _update_mood_badge(self, mood: str):
        icons = {PROUD:"🌟", HAPPY:"😊", CONCERNED:"😟", ANGRY:"😠", FURIOUS:"🤬"}
        suffix = " 🌙" if _is_evening() else ""
        self.mood_badge.setText(f"{icons.get(mood,'😊')} {mood.title()}{suffix}")

    def _decay_soothe_level(self):
        self._soothe_level = 0
        self._check_tasks_and_mood()

    def _ask_about_user_mood(self):
        if self._is_sleeping:
            return
        mood_questions = [
            "How are you feeling right now, Riri? 🌸",
            "Checking in on you! How is your mood today? 💕",
            "Are you doing alright? Don't push yourself too hard! 🥰",
            "Just wanted to ask: how is your mood looking? 🌸"
        ]
        self._say(random.choice(mood_questions), 5000)

    def _on_pet(self):
        if self._is_sleeping:
            self._say("Zzz… (shh, I'm sleeping) …zzz", 3000)
            return
        if self._is_walking:
            self._soothe_level = min(2, self._soothe_level + 1)
            self._go_to_corner_sleep()
            return
        self._soothe_level  = min(2, self._soothe_level + 1)
        self._ignore_count  = max(0, self._ignore_count - 2)
        self._soothed_flash = True
        self._say(random.choice([
            "…okay that was nice. But still. Tasks.",
            "Fine. I forgive you. Slightly.",
            "Ugh. Maybe I like you a little.",
            "One pet ≠ one task. But it helps.",
        ]), 4000)
        self._show_mood_image()
        
        self._soothe_decay_timer.stop()
        self._soothe_decay_timer.start(120_000)
        
        QTimer.singleShot(2500, self._clear_soothe)
        self._check_tasks_and_mood()

    def _on_promise(self):
        if self._is_sleeping:
            self._say("Mmph… promise noted… zzz", 3000)
            return
        self._soothe_level = min(2, self._soothe_level + 1)
        self._ignore_count = max(0, self._ignore_count - 1)
        self._say(random.choice([
            "Promise accepted. Delivery expected.",
            "I'm holding you to this.",
            "eh,you and your promises. But okay.",
            "Good. Now actually do it.",
        ]), 4000)
        
        self._soothe_decay_timer.stop()
        self._soothe_decay_timer.start(120_000)
        
        self._check_tasks_and_mood()

    def _clear_soothe(self):
        self._soothed_flash = False
        self._show_mood_image()

    def _open_task_input(self):
        self._task_input_win = self._TaskInputWindow()
        self._task_input_win.tasks_saved.connect(self._on_tasks_saved)
        self._task_input_win.show()

        self.doll.raise_()
        self.bubble.raise_()

    def _on_tasks_saved(self):
        self._last_done_count = 0
        self.task_panel.refresh()
        
        self._stop_walking() 
        self._show_mood_image()
        
        self._check_tasks_and_mood()
        self._say("Tasks updated. Now get to work~ 💪", 4000)

    def _say(self, text: str, duration_ms: int = 4000):
        self.bubble.say(text, duration_ms)
        self.bubble.follow_doll(self.doll.pos())

    def _trust_text(self):
        return f"Trust: {get_trust()} — {get_trust_label()}"

    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.addAction("📋 Manage Tasks", self._open_task_input)
        menu.addSeparator()
        menu.addAction("Quit Asher", QApplication.quit)
        menu.exec(event.globalPos())

    def closeEvent(self, event):
        if tasks_exist_today():
            record_day(get_completion_ratio())
        self.bubble.hide()
        self.doll.hide()
        event.accept()