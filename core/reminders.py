import random
from core.tasks import get_completion_ratio, tasks_exist_today, none_done

GENTLE = [
    "Psst. The tasks aren't going to do themselves~",
    "Hey. Hey you. Tasks.",
    "Just a friendly reminder that time is a flat circle and your tasks aren't done.",
    "I made a list. You have a list. The list wants attention.",
]

FIRM = [
    "Okay I'm going to need you to start on those tasks.",
    "The tasks. NOW. Please. I'm being very calm about this.",
    "We've been over this. Tasks. Today. You. Do them.",
    "I'm setting a timer. For my patience.",
]

AGGRESSIVE = [
    "DO THE TASKS.",
    "I will follow your cursor until you do at least ONE.",
    "I am RIGHT HERE. The tasks are RIGHT THERE. CONNECT THE DOTS.",
    "Fine. FINE. We're doing this the hard way.",
]


def get_reminder(ignore_count: int) -> str:
    if ignore_count <= 1:
        return random.choice(GENTLE)
    elif ignore_count <= 3:
        return random.choice(FIRM)
    else:
        return random.choice(AGGRESSIVE)


def should_follow_cursor(ignore_count: int) -> bool:
    """Start following cursor after 4+ ignores with 0% completion."""
    return ignore_count >= 4 and none_done()