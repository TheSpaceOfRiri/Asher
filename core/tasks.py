import json
import os
from datetime import date, datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tasks.json")


def _load_raw() -> dict:
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def _save_raw(data: dict):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_today_key() -> str:
    return str(date.today())


def load_today_tasks() -> list[dict]:
    """Return today's tasks as list of {text, done, start_time, end_time}."""
    data = _load_raw()
    return data.get(get_today_key(), [])


def save_today_tasks(tasks: list[dict]):
    data = _load_raw()
    data[get_today_key()] = tasks
    _save_raw(data)


def tasks_exist_today() -> bool:
    return len(load_today_tasks()) > 0


def get_completion_ratio() -> float:
    tasks = load_today_tasks()
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks if t["done"])
    return done / len(tasks)


def all_done() -> bool:
    tasks = load_today_tasks()
    return bool(tasks) and all(t["done"] for t in tasks)


def none_done() -> bool:
    tasks = load_today_tasks()
    return bool(tasks) and not any(t["done"] for t in tasks)


def has_overdue_tasks() -> bool:
    """Return True if any incomplete task has passed its end_time (AM/PM format)."""
    tasks = load_today_tasks()
    if not tasks:
        return False
        
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    
    for task in tasks:
        if task.get("done", False):
            continue
        end_time = task.get("end_time", "")
        if end_time:
            try:
                # Parse "hh:mm AP" format
                dt = datetime.strptime(end_time, "%I:%M %p")
                if current_minutes > dt.hour * 60 + dt.minute:
                    return True
            except ValueError:
                pass
    return False