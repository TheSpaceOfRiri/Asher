from core.tasks import get_completion_ratio, tasks_exist_today

HAPPY    = "happy"
PROUD    = "proud"
CONCERNED = "concerned"
ANGRY    = "angry"
FURIOUS  = "furious"

MOOD_ORDER = [FURIOUS, ANGRY, CONCERNED, HAPPY, PROUD]

def compute_mood(soothe_level: int = 0) -> str:
    """Derive mood from task completion ratio + soothe bonus."""
    if not tasks_exist_today():
        return HAPPY  

    ratio = get_completion_ratio()

    if ratio == 1.0:
        mood = PROUD
    elif ratio >= 0.67:
        mood = HAPPY
    elif ratio >= 0.34:
        mood = CONCERNED
    elif ratio > 0.0:
        mood = ANGRY
    else:
        mood = FURIOUS

    if soothe_level > 0:
        idx = MOOD_ORDER.index(mood)
        idx = min(len(MOOD_ORDER) - 1, idx + soothe_level)
        mood = MOOD_ORDER[idx]

    return mood

MOOD_DIALOGUE = {
    PROUD:    [
        "Every single one? You absolute legend. 🌟",
        "I knew you had it in you. Proud doesn't even cover it.",
        "Finished everything?! Okay I might cry a little.",
        "This is the best day. FOR ME. Because of YOU.",
    ],
    HAPPY:    [
        "Look at you, making progress~ Keep it up!",
        "Not bad at all. I'm watching… approvingly.",
        "You're doing great. Don't make me get emotional.",
        "Good job! Gold star. Several, actually.",
    ],
    CONCERNED: [
        "Mmmm. Some tasks still undone. I'm *concerned*.",
        "We're halfway there. The other half is judging you.",
        "I believe in you. Mostly. Get back to work.",
        "This is fine. It's fine. (It's not fine.)",
    ],
    ANGRY:    [
        "Excuse me? ONE task? ONE?",
        "I am disappointed and I want you to know that.",
        "The tasks are RIGHT THERE. I'm pointing at them.",
        "You and I are going to have a talk. Right now.",
    ],
    FURIOUS:  [
        "NOT. A. SINGLE. ONE.",
        "I have been sitting here ALL DAY.",
        "I'm not angry. I'm worse. I'm DISAPPOINTED.",
        "Do you want me to follow your cursor? Because I WILL.",
    ],
}

def get_dialogue(mood: str, index: int = 0) -> str:
    lines = MOOD_DIALOGUE.get(mood, ["..."])
    return lines[index % len(lines)]