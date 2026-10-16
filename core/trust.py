import json
import os
from datetime import date

TRUST_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trust.json")

MAX_TRUST = 100
MIN_TRUST = 0


def _load() -> dict:
    if not os.path.exists(TRUST_PATH):
        return {"score": 50, "history": []}
    with open(TRUST_PATH, "r") as f:
        return json.load(f)


def _save(data: dict):
    os.makedirs(os.path.dirname(TRUST_PATH), exist_ok=True)
    with open(TRUST_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_trust() -> int:
    return _load()["score"]


def record_day(completion_ratio: float):
    """Call at end of day or on app close to update trust."""
    data = _load()
    today = str(date.today())

    if completion_ratio == 1.0:
        delta = +10
    elif completion_ratio >= 0.67:
        delta = +5
    elif completion_ratio >= 0.34:
        delta = 0
    elif completion_ratio > 0.0:
        delta = -5
    else:
        delta = -10

    data["score"] = max(MIN_TRUST, min(MAX_TRUST, data["score"] + delta))
    data["history"].append({"date": today, "ratio": completion_ratio, "delta": delta})
    _save(data)


def get_trust_label() -> str:
    score = get_trust()
    if score >= 80:
        return "Devoted"
    elif score >= 60:
        return "Reliable"
    elif score >= 40:
        return "Neutral"
    elif score >= 20:
        return "Skeptical"
    else:
        return "Distrustful"


def trust_greeting() -> str:
    label = get_trust_label()
    score = get_trust()
    greetings = {
        "Devoted":     f"You're back! Trust level: {score}. I missed you~ ♡",
        "Reliable":    f"Good to see you. Trust: {score}. Let's have a good day.",
        "Neutral":     f"Oh. You're here. Trust: {score}. Don't disappoint me.",
        "Skeptical":   f"Hmm. Trust: {score}. I'm watching you. Carefully.",
        "Distrustful": f"...You. Trust: {score}. Prove me wrong today. Please.",
    }
    return greetings.get(label, f"Hello. Trust: {score}.")