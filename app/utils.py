import random
from datetime import date
from .models import Challenge, UserProgress, User, db

def select_daily_challenge_for(user: User):
    # get challenges in preferred languages that user hasn't done
    done_ids = {p.challenge_id for p in user.progress}
    langs = user.get_lang_list()
    query = Challenge.query.filter(Challenge.language.in_(langs))
    candidates = [c for c in query.all() if c.id not in done_ids]
    if not candidates:
        # fallback: any not done
        all_candidates = Challenge.query.all()
        candidates = [c for c in all_candidates if c.id not in done_ids]
    if not candidates:
        return None  # exhausted
    return random.choice(candidates)

def update_streak(user):
    today = date.today()
    if user.last_active:
        delta = (today - user.last_active).days
        if delta == 1:
            user.streak += 1
        elif delta > 1:
            user.streak = 1
    else:
        user.streak = 1
    user.last_active = today
    db.session.commit()
