import os
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, date, timedelta, timezone
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required, logout_user,
    current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import csv, io, random, json
from sqlalchemy import or_, func
from werkzeug.exceptions import abort
from puzzles.routes import register_puzzle_routes

# -----------------------------------------------------------------------------
# App & DB setup
# -----------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv()


def _env_flag(name: str, default: bool = False) -> bool:
    """Interpret typical truthy strings from environment variables."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

def _parse_rate_limit(value: str) -> tuple[int, int]:
    """Parse a rate limit string like '10 per minute' into (count, seconds)."""
    parts = value.strip().lower().split()
    if len(parts) < 3 or parts[1] != "per":
        raise ValueError(f"Invalid rate limit format: {value!r}")
    count = int(parts[0])
    unit = parts[2]
    if unit.endswith("s"):
        unit = unit[:-1]
    seconds_map = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
    }
    if unit not in seconds_map:
        raise ValueError(f"Invalid rate limit unit: {unit!r}")
    return count, seconds_map[unit]

def _env_rate_limit(name: str, default: str) -> tuple[int, int]:
    value = os.environ.get(name, default)
    return _parse_rate_limit(value)

def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

rate_limits = {
    "auth": _env_rate_limit("RATE_LIMIT_AUTH", "10 per minute"),
    "contact": _env_rate_limit("RATE_LIMIT_CONTACT", "5 per minute"),
}
rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)

db = SQLAlchemy(app)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Default to secure cookies only when explicitly requested so local dev/tests keep working.
app.config['SESSION_COOKIE_SECURE'] = _env_flag("SESSION_COOKIE_SECURE", default=False)
app.config['PREFERRED_URL_SCHEME'] = 'https'

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Make now() available in templates (used by base.html footer)
@app.context_processor
def inject_now():
    return {"now": datetime.utcnow}


@app.before_request
def enforce_active_account():
    if current_user.is_authenticated and not current_user.active:
        logout_user()
        flash("Your account has been deactivated. Contact an admin to restore access.")
        return redirect(url_for("login"))

@app.before_request
def enforce_rate_limits():
    if request.endpoint in {"login", "signup"}:
        bucket = "auth"
    elif request.endpoint == "contact":
        bucket = "contact"
    else:
        return None

    max_requests, window_seconds = rate_limits[bucket]
    key = f"{bucket}:{_client_ip()}"
    now = time.time()
    window_start = now - window_seconds
    timestamps = rate_limit_buckets[key]
    while timestamps and timestamps[0] < window_start:
        timestamps.popleft()
    if len(timestamps) >= max_requests:
        retry_after = max(1, int(window_seconds - (now - timestamps[0])))
        response = render_template("rate_limited.html", retry_after=retry_after)
        return Response(response, status=429, headers={"Retry-After": str(retry_after)})
    timestamps.append(now)
    return None

@app.errorhandler(429)
def rate_limit_exceeded(error):
    retry_after = getattr(error, "retry_after", None)
    return render_template("rate_limited.html", retry_after=retry_after), 429

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=True, nullable=False)
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime, nullable=True)
    last_active_date = db.Column(db.Date)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    solution = db.Column(db.Text)
    hints = db.Column(db.Text)
    language = db.Column(db.String(40), default="General")
    difficulty = db.Column(db.String(30), default="Easy")
    topic = db.Column(db.String(60))
    tags = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="draft", nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    added_by = db.Column(db.Integer, db.ForeignKey("user.id"))

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenge.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Joke(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    entry_type = db.Column(db.String(20), default="fun", nullable=False)

# New models for Dungeons feature
class Dungeon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    topic = db.Column(db.String(60), nullable=False, index=True) # Links to Challenge.topic
    unlock_xp = db.Column(db.Integer, default=0) # XP required to see/enter
    reward_xp = db.Column(db.Integer, default=50) # Bonus XP for completion

class DungeonCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    dungeon_id = db.Column(db.Integer, db.ForeignKey("dungeon.id"), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'dungeon_id'),)

class PuzzleCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    puzzle_name = db.Column(db.String(80), nullable=False) # e.g., "bit_flipper_lvl_1"
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'puzzle_name'),)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(80), nullable=False)
    meta = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

# -----------------------------------------------------------------------------
# CSV jokes/facts (Home page)
# -----------------------------------------------------------------------------
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def random_fun():
    joke_row = Joke.query.order_by(db.func.random()).first()
    if joke_row:
        return {"type": joke_row.entry_type or "fun", "text": joke_row.text}
    return {"type": "fun", "text": "Welcome to SyntaxSnacks!"}

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def get_daily_challenge_for_user(user: User):
    """Return the first unsolved challenge for the user (simple baseline)."""
    solved_ids = {s.challenge_id for s in Submission.query.filter_by(user_id=user.id).all()}
    for ch in Challenge.query.filter_by(status="published").order_by(Challenge.id.asc()):
        if ch.id not in solved_ids:
            return ch
    return None

def update_streak_and_xp(user: User):
    """Add +10 XP and update streak based on last active date."""
    today = date.today()
    if user.last_active_date is None:
        user.streak = 1
    else:
        if user.last_active_date == today - timedelta(days=1):
            user.streak += 1
        elif user.last_active_date == today:
            pass
        else:
            user.streak = 1
    user.last_active_date = today
    user.xp = (user.xp or 0) + 10
    db.session.commit()

def check_and_complete_dungeon(user: User, challenge: Challenge):
    """After a challenge is solved, check if it completes a dungeon."""
    if not challenge.topic:
        return None # Challenge isn't part of a topic/dungeon

    dungeon = Dungeon.query.filter(func.lower(Dungeon.topic) == challenge.topic.lower()).first()
    if not dungeon:
        return None # No dungeon for this topic

    # Check if user has already completed this dungeon
    if DungeonCompletion.query.filter_by(user_id=user.id, dungeon_id=dungeon.id).first():
        return None

    # Get all challenge IDs for this dungeon's topic
    dungeon_challenge_ids = {
        c.id
        for c in Challenge.query.filter(
            func.lower(Challenge.topic) == dungeon.topic.lower(),
            Challenge.status == "published",
        ).all()
    }
    solved_challenge_ids = {s.challenge_id for s in Submission.query.filter_by(user_id=user.id).all()}

    if dungeon_challenge_ids.issubset(solved_challenge_ids):
        # User has solved all challenges in this dungeon!
        db.session.add(DungeonCompletion(user_id=user.id, dungeon_id=dungeon.id))
        user.xp = (user.xp or 0) + dungeon.reward_xp
        db.session.commit()
        return dungeon # Return the completed dungeon to flash a message

def admin_required():
    return current_user.is_authenticated and current_user.is_admin


def add_audit_log(actor_user_id: int, target_user_id: int, action: str, meta=None):
    """Queue an audit log row (commit at caller)."""
    log = AuditLog(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        action=action,
        meta=meta or {},
    )
    db.session.add(log)

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", fun=random_fun())

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        body = request.form.get("message", "").strip()

        if current_user.is_authenticated:
            if not name:
                name = current_user.username
            if not email:
                email = current_user.email
        
        if not (name and email and body):
            flash(("contact", "Please fill out all fields."))  # stays on contact page
            return redirect(url_for("contact"))

        # persist to DB
        msg = Message(name=name, email=email, body=body)
        db.session.add(msg)
        db.session.commit()

        # show success only on this page
        flash(("contact", "Message sent successfully! We'll get back to you soon."))
        return redirect(url_for("contact", sent=1))

    return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.active:
                flash("This account is deactivated. Contact an admin to restore access.")
                return redirect(url_for("login"))
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip() or None
        pw = request.form.get("password", "")
        cpw = request.form.get("confirm", "")
        if not u or not pw:
            flash("Username and password required.")
        elif pw != cpw:
            flash("Passwords do not match.")
        elif User.query.filter_by(username=u).first():
            flash("Username already taken.")
        else:
            user = User(username=u, email=email, password_hash=generate_password_hash(pw))
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    ch = get_daily_challenge_for_user(current_user)
    joke_row = Joke.query.order_by(db.func.random()).first()
    joke = joke_row.text if joke_row else None
    return render_template("dashboard.html", challenge=ch, joke=joke)

@app.route("/submit/<int:challenge_id>", methods=["POST"])
@login_required
def submit_challenge(challenge_id):
    ch = Challenge.query.get_or_404(challenge_id)
    existing = Submission.query.filter_by(user_id=current_user.id, challenge_id=ch.id).first()
    if not existing:
        db.session.add(Submission(user_id=current_user.id, challenge_id=ch.id))
        update_streak_and_xp(current_user)
        completed_dungeon = check_and_complete_dungeon(current_user, ch)
        if completed_dungeon:
            flash(f"Challenge solved! You cleared the {completed_dungeon.name} and earned a {completed_dungeon.reward_xp} XP bonus!")
        else:
            flash("Great! Challenge marked as solved. +10 XP")
    else:
        flash("You already solved this one.")
    return redirect(url_for("dashboard"))

@app.route("/leaderboard")
def leaderboard():
    users = User.query.order_by(User.xp.desc(), User.streak.desc()).limit(50).all()
    return render_template("leaderboard.html", users=users)

# ---- Dungeons & Exploration
@app.route("/dungeons")
@login_required
def dungeons_list():
    """Main exploration page listing all available dungeons."""
    # Get all dungeons, ordered by unlock XP
    all_dungeons = Dungeon.query.order_by(Dungeon.unlock_xp).all()

    # Get total published challenges per topic
    total_challenges_by_topic = dict(
        db.session.query(func.lower(Challenge.topic), func.count(Challenge.id))
        .filter(Challenge.status == "published")
        .group_by(func.lower(Challenge.topic))
        .all()
    )

    # Get user's solved published challenges per topic
    solved_challenges_by_topic = dict(
        db.session.query(func.lower(Challenge.topic), func.count(Submission.id))
        .join(Challenge, Challenge.id == Submission.challenge_id)
        .filter(Submission.user_id == current_user.id, Challenge.status == "published")
        .group_by(func.lower(Challenge.topic))
        .all()
    )

    dungeon_data = []
    for d in all_dungeons:
        topic_key = (d.topic or "").lower()
        total = total_challenges_by_topic.get(topic_key, 0)
        solved = solved_challenges_by_topic.get(topic_key, 0)
        progress = (solved / total * 100) if total > 0 else 0
        dungeon_data.append({
            "dungeon": d,
            "progress": round(progress),
            "is_locked": current_user.xp < d.unlock_xp
        })

    return render_template("dungeons_list.html", dungeon_data=dungeon_data)

@app.route("/dungeons/<int:dungeon_id>")
@login_required
def dungeon_view(dungeon_id):
    """View a single dungeon and its challenges."""
    dungeon = Dungeon.query.get_or_404(dungeon_id)

    if current_user.xp < dungeon.unlock_xp:
        flash("You need more XP to access this dungeon.")
        return redirect(url_for("dungeons_list"))

    # Get challenges for this dungeon's topic
    topic_key = (dungeon.topic or "").lower()
    challenges = (
        Challenge.query.filter(
            func.lower(Challenge.topic) == topic_key,
            Challenge.status == "published",
        )
        .order_by(Challenge.id)
        .all()
    )
    solved_challenge_ids = {s.challenge_id for s in Submission.query.filter_by(user_id=current_user.id).all()}

    # Check if all challenges in this dungeon are solved
    all_challenges_solved = all(ch.id in solved_challenge_ids for ch in challenges)

    return render_template(
        "dungeon_view.html", dungeon=dungeon, challenges=challenges,
        solved_ids=solved_challenge_ids, all_solved=all_challenges_solved
    )

# ---- Puzzles & Mini-Games
# Registered via puzzles.routes to keep app.py lean.
register_puzzle_routes(app, db, PuzzleCompletion)

# ---- Admin: Users
def _guard_admin():
    if not admin_required():
        abort(403)


def _parse_int_or_none(raw):
    if raw is None or str(raw).strip() == "":
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None

CHALLENGE_STATUSES = {"draft", "published"}


def _normalize_tags(raw: str) -> str:
    parts = [p.strip() for p in (raw or "").split(",") if p and p.strip()]
    return ",".join(parts)

def _normalize_topic(raw: str) -> str:
    cleaned = (raw or "").strip().lower()
    return cleaned or None

def _challenge_dedupe_key(cleaned: dict):
    return (cleaned["title"].strip().lower(), cleaned["prompt"].strip().lower())


def _admin_challenge_query(search: str, status_filter: str, tag_filter: str):
    query = Challenge.query
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(func.lower(Challenge.title).like(like))
    if status_filter in CHALLENGE_STATUSES:
        query = query.filter(Challenge.status == status_filter)
    if tag_filter:
        query = query.filter(func.lower(Challenge.tags).like(f"%{tag_filter.lower()}%"))
    return query


def _validate_challenge_row(row: dict):
    """Clean and validate a row coming from CSV/import payload."""
    def _clean(val):
        return (val or "").strip()

    title = _clean(row.get("title"))
    prompt = _clean(row.get("prompt"))
    hints = _clean(row.get("hints"))
    solution = _clean(row.get("solution"))
    language = _clean(row.get("language") or "General") or "General"
    difficulty = _clean(row.get("difficulty") or "Easy") or "Easy"
    topic = _normalize_topic(row.get("topic"))
    tags = _normalize_tags(row.get("tags", ""))
    status = (_clean(row.get("status")) or "draft").lower()
    pub_raw = _clean(row.get("published_at"))

    errors = []
    if not title:
        errors.append("Title is required.")
    if not prompt:
        errors.append("Prompt is required.")
    if len(title) > 200:
        errors.append("Title exceeds 200 characters.")
    if len(language) > 40:
        errors.append("Language exceeds 40 characters.")
    if len(difficulty) > 30:
        errors.append("Difficulty exceeds 30 characters.")
    if topic and len(topic) > 60:
        errors.append("Topic exceeds 60 characters.")
    if status not in CHALLENGE_STATUSES:
        errors.append("Status must be draft or published.")

    parsed_published_at = None
    if pub_raw:
        try:
            parsed_published_at = datetime.strptime(pub_raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            errors.append("published_at must be YYYY-MM-DD.")

    cleaned = {
        "title": title,
        "prompt": prompt,
        "hints": hints,
        "solution": solution,
        "language": language,
        "difficulty": difficulty,
        "topic": topic,
        "tags": tags,
        "status": status if status in CHALLENGE_STATUSES else "draft",
        "published_at": parsed_published_at,
        "published_at_raw": pub_raw,
    }
    return cleaned, errors


def _prepare_challenge_preview(rows):
    preview = []
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            row = {}
        cleaned, errors = _validate_challenge_row(row)
        preview.append(
            {
                "index": idx,
                "data": cleaned,
                "errors": errors,
                "is_valid": len(errors) == 0,
            }
        )
    return preview


@app.route("/admin/users")
@login_required
def admin_users():
    _guard_admin()
    search = request.args.get("search", "").strip()
    is_admin_filter = request.args.get("is_admin", "all")
    active_filter = request.args.get("active", "all")
    page = request.args.get("page", 1, type=int)

    query = User.query
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(User.username).like(like),
                func.lower(User.email).like(like),
            )
        )

    if is_admin_filter == "admins":
        query = query.filter(User.is_admin.is_(True))
    elif is_admin_filter == "users":
        query = query.filter(User.is_admin.is_(False))

    if active_filter == "active":
        query = query.filter(User.active.is_(True))
    elif active_filter == "inactive":
        query = query.filter(User.active.is_(False))

    pagination = query.order_by(User.created_at.desc(), User.id.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        search=search,
        is_admin_filter=is_admin_filter,
        active_filter=active_filter,
    )


@app.route("/admin/users/<int:user_id>")
@login_required
def admin_user_detail(user_id):
    _guard_admin()
    user = User.query.get_or_404(user_id)
    solves_count = Submission.query.filter_by(user_id=user.id).count()
    logs = (
        AuditLog.query.filter_by(target_user_id=user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "admin/user_detail.html",
        user=user,
        solves_count=solves_count,
        logs=logs,
    )


@app.post("/admin/users/<int:user_id>/toggle_active")
@login_required
def admin_toggle_user_active(user_id):
    _guard_admin()
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    add_audit_log(
        current_user.id,
        user.id,
        "toggle_active",
        {"active": user.active},
    )
    db.session.commit()
    flash(f"User {user.username} is now {'active' if user.active else 'deactivated'}.")
    return redirect(url_for("admin_user_detail", user_id=user.id))


@app.post("/admin/users/<int:user_id>/toggle_admin")
@login_required
def admin_toggle_user_admin(user_id):
    _guard_admin()
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    add_audit_log(
        current_user.id,
        user.id,
        "toggle_is_admin",
        {"is_admin": user.is_admin},
    )
    db.session.commit()
    flash(f"Updated admin status for {user.username}.")
    return redirect(url_for("admin_user_detail", user_id=user.id))


@app.post("/admin/users/<int:user_id>/reset_password")
@login_required
def admin_reset_user_password(user_id):
    _guard_admin()
    user = User.query.get_or_404(user_id)
    new_pw = secrets.token_urlsafe(8)
    user.password_hash = generate_password_hash(new_pw)
    add_audit_log(
        current_user.id,
        user.id,
        "reset_password",
        {"generated": True},
    )
    db.session.commit()
    flash(f"Temporary password for {user.username}: {new_pw}")
    return redirect(url_for("admin_user_detail", user_id=user.id))


@app.post("/admin/users/<int:user_id>/adjust_stats")
@login_required
def admin_adjust_user_stats(user_id):
    _guard_admin()
    user = User.query.get_or_404(user_id)
    dx = _parse_int_or_none(request.form.get("delta_xp"))
    ds = _parse_int_or_none(request.form.get("delta_streak"))
    reason = (request.form.get("reason") or "").strip()

    if dx is None or ds is None:
        flash("XP and streak adjustments must be numbers (use 0 for no change).")
        return redirect(url_for("admin_user_detail", user_id=user.id))

    user.xp = max(0, (user.xp or 0) + dx)
    user.streak = max(0, (user.streak or 0) + ds)
    add_audit_log(
        current_user.id,
        user.id,
        "adjust_stats",
        {"delta_xp": dx, "delta_streak": ds, "reason": reason},
    )
    db.session.commit()
    flash("Stats updated.")
    return redirect(url_for("admin_user_detail", user_id=user.id))


# ---- Admin: challenges
@app.route("/admin/challenges")
@login_required
def admin_challenges():
    _guard_admin()
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "all").lower()
    tag_filter = request.args.get("tag", "").strip()
    page = request.args.get("page", 1, type=int)

    query = _admin_challenge_query(search, status_filter, tag_filter)
    pagination = query.order_by(Challenge.id.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    status_counts = dict(
        db.session.query(Challenge.status, func.count(Challenge.id))
        .group_by(Challenge.status)
        .all()
    )
    export_url = url_for(
        "admin_challenges_export",
        search=search,
        status=status_filter,
        tag=tag_filter,
    )
    return render_template(
        "admin/challenges_list.html",
        challenges=pagination.items,
        pagination=pagination,
        search=search,
        status_filter=status_filter,
        tag_filter=tag_filter,
        status_counts=status_counts,
        export_url=export_url,
    )


@app.route("/admin/challenge/new", methods=["GET", "POST"])
@login_required
def admin_add_challenge():
    if not admin_required():
        flash("Admin only.")
        return redirect(url_for("index"))
    if request.method == "POST":
        status = (request.form.get("status") or "draft").strip().lower()
        if status not in CHALLENGE_STATUSES:
            status = "draft"
        tags = _normalize_tags(request.form.get("tags", ""))
        published_at = datetime.now(timezone.utc) if status == "published" else None
        ch = Challenge(
            title=request.form["title"].strip(),
            prompt=request.form["prompt"].strip(),
            solution=request.form.get("solution", "").strip(),
            hints=request.form.get("hints", "").strip(),
            language=request.form.get("language", "General").strip(),
            difficulty=request.form.get("difficulty", "Easy").strip(),
            topic=_normalize_topic(request.form.get("topic", "")),
            tags=tags,
            status=status,
            published_at=published_at,
            added_by=current_user.id,
        )
        db.session.add(ch)
        db.session.commit()
        flash("Challenge added.")
        return redirect(url_for("admin_add_challenge"))
    return render_template("admin_add_challenge.html")


@app.route("/admin/challenge/<int:challenge_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_challenge(challenge_id):
    if not admin_required():
        flash("Admin only.")
        return redirect(url_for("index"))
    ch = Challenge.query.get_or_404(challenge_id)
    if request.method == "POST":
        status = (request.form.get("status") or "draft").strip().lower()
        if status not in CHALLENGE_STATUSES:
            status = "draft"
        tags = _normalize_tags(request.form.get("tags", ""))
        
        # Only update published_at if status is changing to "published"
        if status == "published" and ch.status != "published":
            ch.published_at = datetime.now(timezone.utc)
        elif status == "draft":
            ch.published_at = None
        
        ch.title = request.form["title"].strip()
        ch.prompt = request.form["prompt"].strip()
        ch.solution = request.form.get("solution", "").strip()
        ch.hints = request.form.get("hints", "").strip()
        ch.language = request.form.get("language", "General").strip()
        ch.difficulty = request.form.get("difficulty", "Easy").strip()
        ch.topic = _normalize_topic(request.form.get("topic", ""))
        ch.tags = tags
        ch.status = status
        
        db.session.commit()
        flash("Challenge updated.")
        return redirect(url_for("admin_challenges"))
    return render_template("admin_edit_challenge.html", challenge=ch)



@app.route("/admin/challenges/import", methods=["GET", "POST"])
@login_required
def admin_import_challenges():
    if not admin_required():
        flash("Admin only.")
        return redirect(url_for("index"))
    if request.method == "POST":
        payload = request.form.get("payload")
        if payload:
            try:
                raw_rows = json.loads(payload)
            except json.JSONDecodeError:
                flash("Upload payload could not be read. Please re-upload the CSV.")
                return redirect(url_for("admin_import_challenges"))
            if not isinstance(raw_rows, list):
                flash("Upload payload was malformed. Please re-upload the CSV.")
                return redirect(url_for("admin_import_challenges"))

            preview_rows = _prepare_challenge_preview(raw_rows)
            valid_rows = [row for row in preview_rows if row["is_valid"]]
            invalid_count = len(preview_rows) - len(valid_rows)

            if not valid_rows:
                flash("No valid rows to import.")
                return render_template(
                    "admin/challenges_import_preview.html",
                    preview_rows=preview_rows,
                    payload=payload,
                    source_filename=request.form.get("source_filename"),
                )

            try:
                existing_map = {}
                title_map = defaultdict(list)
                for ch in Challenge.query.all():
                    key = ((ch.title or "").strip().lower(), (ch.prompt or "").strip().lower())
                    existing_map[key] = ch
                    title_key = (ch.title or "").strip().lower()
                    if title_key:
                        title_map[title_key].append(ch)

                seen = set()
                imported = 0
                updated = 0
                skipped_dupes = 0
                for row in valid_rows:
                    data = row["data"]
                    key = _challenge_dedupe_key(data)
                    if key in seen:
                        skipped_dupes += 1
                        continue
                    seen.add(key)

                    published_at = data["published_at"]
                    if data["status"] == "published" and not published_at:
                        published_at = datetime.now(timezone.utc)
                    if data["status"] == "draft":
                        published_at = None

                    existing_ch = existing_map.get(key)
                    if not existing_ch:
                        title_matches = title_map.get(data["title"].strip().lower(), [])
                        if len(title_matches) == 1:
                            existing_ch = title_matches[0]
                    if existing_ch and existing_ch.published_at and not data["published_at"] and data["status"] == "published":
                        published_at = existing_ch.published_at
                    if existing_ch:
                        existing_ch.title = data["title"]
                        existing_ch.prompt = data["prompt"]
                        existing_ch.solution = data["solution"]
                        existing_ch.hints = data["hints"]
                        existing_ch.language = data["language"]
                        existing_ch.difficulty = data["difficulty"]
                        existing_ch.topic = data["topic"]
                        existing_ch.tags = data["tags"]
                        existing_ch.status = data["status"]
                        existing_ch.published_at = published_at
                        updated += 1
                        continue

                    ch = Challenge(
                        title=data["title"],
                        prompt=data["prompt"],
                        solution=data["solution"],
                        hints=data["hints"],
                        language=data["language"],
                        difficulty=data["difficulty"],
                        topic=data["topic"],
                        tags=data["tags"],
                        status=data["status"],
                        published_at=published_at,
                        added_by=current_user.id,
                    )
                    db.session.add(ch)
                    imported += 1
                db.session.commit()
                flash(
                    "Imported {} challenges. Updated {} existing. Skipped {} duplicates. "
                    "Skipped {} invalid rows.".format(imported, updated, skipped_dupes, invalid_count)
                )
                return redirect(url_for("admin_challenges"))
            except Exception as e:
                db.session.rollback()
                flash(f"Import failed: {e}")
                return render_template(
                    "admin/challenges_import_preview.html",
                    preview_rows=preview_rows,
                    payload=payload,
                    source_filename=request.form.get("source_filename"),
                )

        file = request.files.get("file")
        if not file or not file.filename.lower().endswith(".csv"):
            flash("Please upload a CSV file.")
            return redirect(url_for("admin_import_challenges"))

        try:
            stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
            reader = csv.DictReader(stream)
            rows = []
            for row in reader:
                if not any((v or "").strip() for v in row.values()):
                    continue
                cleaned_row = {
                    (k or "").strip(): (v or "")
                    for k, v in row.items()
                    if k is not None
                }
                rows.append(cleaned_row)

            if not rows:
                flash("CSV contained no rows.")
                return redirect(url_for("admin_import_challenges"))

            preview_rows = _prepare_challenge_preview(rows)
            payload = json.dumps(rows)
            return render_template(
                "admin/challenges_import_preview.html",
                preview_rows=preview_rows,
                payload=payload,
                source_filename=file.filename,
            )
        except Exception as e:
            flash(f"Import failed: {e}")
            return redirect(url_for("admin_import_challenges"))

    return render_template("admin/challenges_import.html")


@app.route("/admin/challenges/example.csv")
@login_required
def download_challenge_csv_example():
    if not admin_required():
        flash("Admin only.")
        return redirect(url_for("index"))
    csv_text = (
        "title,prompt,hints,solution,language,difficulty,topic,tags,status,published_at\n"
        "Reverse String,Write a function that reverses a string.,"
        "Think about slicing or stacks.,Python: s[::-1]; JS: str.split('').reverse().join(''),"
        "Python,Easy,strings,strings,published,2024-01-01\n"
    )
    return (
        csv_text,
        200,
        {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'attachment; filename="challenges_example.csv"',
        },
    )


@app.route("/admin/challenges/export.csv")
@login_required
def admin_challenges_export():
    _guard_admin()
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "all").lower()
    tag_filter = request.args.get("tag", "").strip()

    challenges = (
        _admin_challenge_query(search, status_filter, tag_filter)
        .order_by(Challenge.id.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "title",
            "prompt",
            "hints",
            "solution",
            "language",
            "difficulty",
            "topic",
            "tags",
            "status",
            "published_at",
        ]
    )
    for ch in challenges:
        published_at = ch.published_at.strftime("%Y-%m-%d") if ch.published_at else ""
        writer.writerow(
            [
                ch.title,
                ch.prompt,
                ch.hints or "",
                ch.solution or "",
                ch.language or "General",
                ch.difficulty or "Easy",
                ch.topic or "",
                ch.tags or "",
                ch.status,
                published_at,
            ]
        )

    csv_data = output.getvalue()
    output.close()
    headers = {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": 'attachment; filename="challenges_export.csv"',
    }
    return Response(csv_data, headers=headers)


@app.post("/admin/challenges/<int:challenge_id>/publish")
@login_required
def admin_publish_challenge(challenge_id):
    _guard_admin()
    ch = Challenge.query.get_or_404(challenge_id)
    action = request.form.get("action", "publish")

    if action == "unpublish":
        ch.status = "draft"
        ch.published_at = None
        msg = f"Unpublished {ch.title}."
    else:
        ch.status = "published"
        ch.published_at = datetime.now(timezone.utc)
        msg = f"Published {ch.title}."

    db.session.commit()
    flash(msg)
    next_url = request.form.get("next") or url_for("admin_challenges")
    return redirect(next_url)

# ---- Admin: Fun cards editor
@app.route("/admin/fun", methods=["GET", "POST"])
@login_required
def admin_fun_cards():
    _guard_admin()
    if request.method == "POST":
        upload = request.files.get("file")
        if upload and upload.filename.lower().endswith(".csv"):
            try:
                stream = io.StringIO(upload.stream.read().decode("utf-8-sig"))
                reader = csv.DictReader(stream)
                count = 0
                skipped = 0
                existing = {
                    ((j.entry_type or "fun").strip().lower(), (j.text or "").strip().lower())
                    for j in Joke.query.all()
                }
                seen = set()
                for row in reader:
                    text = (row.get("text") or "").strip()
                    if not text:
                        continue
                    entry_type = (row.get("entry_type") or "fun").strip().lower()
                    if entry_type not in {"fun", "fact"}:
                        entry_type = "fun"
                    key = (entry_type, text.lower())
                    if key in seen or key in existing:
                        skipped += 1
                        continue
                    seen.add(key)
                    db.session.add(Joke(text=text, entry_type=entry_type))
                    count += 1
                db.session.commit()
                flash(f"Imported {count} fun cards. Skipped {skipped} duplicates.")
            except Exception as e:
                db.session.rollback()
                flash(f"Import failed: {e}")
            return redirect(url_for("admin_fun_cards"))

        text = (request.form.get("text") or "").strip()
        entry_type = (request.form.get("entry_type") or "fun").strip().lower()
        if entry_type not in {"fun", "fact"}:
            entry_type = "fun"
        if not text:
            flash("Text is required.")
        else:
            db.session.add(Joke(text=text, entry_type=entry_type))
            db.session.commit()
            flash("Fun card added.")
        return redirect(url_for("admin_fun_cards"))

    jokes = Joke.query.order_by(Joke.id.desc()).all()
    return render_template("admin/fun_cards.html", jokes=jokes)


@app.post("/admin/fun/<int:joke_id>/delete")
@login_required
def admin_delete_fun_card(joke_id):
    _guard_admin()
    joke = Joke.query.get_or_404(joke_id)
    db.session.delete(joke)
    db.session.commit()
    flash("Fun card deleted.")
    return redirect(url_for("admin_fun_cards"))


@app.route("/admin/fun/export.csv")
@login_required
def admin_fun_cards_export():
    _guard_admin()
    jokes = Joke.query.order_by(Joke.id.asc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "entry_type", "text"])
    for j in jokes:
        writer.writerow([j.id, j.entry_type or "fun", j.text])
    csv_data = output.getvalue()
    output.close()
    headers = {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": 'attachment; filename="fun_cards.csv"',
    }
    return Response(csv_data, headers=headers)

# ---- Admin: Contact
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)


def _admin_message_query(status: str, search: str):
    query = Message.query.filter(Message.deleted_at.is_(None))
    if status == "read":
        query = query.filter(Message.is_read.is_(True))
    elif status == "unread":
        query = query.filter(Message.is_read.is_(False))
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Message.email).like(like),
                func.lower(Message.body).like(like),
            )
        )
    return query


def _redirect_to_next(next_url: str):
    if next_url:
        return redirect(next_url)
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages")
@login_required
def admin_messages():
    if not admin_required():
        abort(403)

    status = request.args.get("status", "all").lower()
    if status not in {"all", "read", "unread"}:
        status = "all"
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)

    query = _admin_message_query(status, search)
    pagination = query.order_by(Message.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    export_url = url_for("admin_messages_export", status=status, search=search)
    current_url = request.full_path.rstrip("?")

    return render_template(
        "admin_messages.html",
        messages=pagination.items,
        pagination=pagination,
        status=status,
        search=search,
        export_url=export_url,
        current_url=current_url,
    )


@app.post("/admin/messages/<int:message_id>/toggle_read")
@login_required
def admin_toggle_message(message_id):
    if not admin_required():
        abort(403)
    msg = Message.query.get_or_404(message_id)
    if msg.deleted_at is None:
        msg.is_read = not msg.is_read
        db.session.commit()
    next_url = request.form.get("next")
    return _redirect_to_next(next_url)


@app.post("/admin/messages/<int:message_id>/delete")
@login_required
def admin_delete_message(message_id):
    if not admin_required():
        abort(403)
    msg = Message.query.get_or_404(message_id)
    if msg.deleted_at is None:
        msg.deleted_at = datetime.now(timezone.utc)
        db.session.commit()
    next_url = request.form.get("next")
    return _redirect_to_next(next_url)


@app.post("/admin/messages/bulk")
@login_required
def admin_bulk_messages():
    if not admin_required():
        abort(403)
    action = request.form.get("bulk_action")
    ids = [int(i) for i in request.form.getlist("message_ids") if i.isdigit()]
    next_url = request.form.get("next")

    if not ids or action not in {"mark_read", "mark_unread", "delete"}:
        flash("Select messages and an action before submitting.")
        return _redirect_to_next(next_url)

    messages = Message.query.filter(
        Message.id.in_(ids), Message.deleted_at.is_(None)
    ).all()

    if not messages:
        flash("No messages matched your selection.")
        return _redirect_to_next(next_url)

    if action == "mark_read":
        for msg in messages:
            msg.is_read = True
    elif action == "mark_unread":
        for msg in messages:
            msg.is_read = False
    elif action == "delete":
        now = datetime.now(timezone.utc)
        for msg in messages:
            msg.deleted_at = now

    db.session.commit()
    flash("Bulk action completed.")
    return _redirect_to_next(next_url)


@app.route("/admin/messages/export.csv")
@login_required
def admin_messages_export():
    if not admin_required():
        abort(403)

    status = request.args.get("status", "all").lower()
    if status not in {"all", "read", "unread"}:
        status = "all"
    search = request.args.get("search", "").strip()

    query = _admin_message_query(status, search)
    messages = query.order_by(Message.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Body", "Created At", "Status"])
    for msg in messages:
        writer.writerow(
            [
                msg.id,
                msg.name,
                msg.email,
                msg.body,
                msg.created_at.isoformat(),
                "Read" if msg.is_read else "Unread",
            ]
        )

    csv_data = output.getvalue()
    output.close()
    headers = {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": "attachment; filename=messages_export.csv",
    }
    return Response(csv_data, headers=headers)

# ---- Public API for Home page
@app.route("/api/fun")
def api_fun():
    return random_fun()


def _ensure_user_schema():
    """Lightweight, SQLite-friendly migration for newly added User columns."""
    with db.engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.exec_driver_sql("PRAGMA table_info(user);")
        }
        if "active" not in cols:
            conn.exec_driver_sql("ALTER TABLE user ADD COLUMN active BOOLEAN DEFAULT 1")
        if "last_login" not in cols:
            conn.exec_driver_sql("ALTER TABLE user ADD COLUMN last_login DATETIME")
        if "created_at" not in cols:
            conn.exec_driver_sql("ALTER TABLE user ADD COLUMN created_at DATETIME")
            conn.exec_driver_sql(
                "UPDATE user SET created_at = datetime('now') WHERE created_at IS NULL"
            )

def _ensure_joke_schema():
    """Ensure Joke has entry_type for fun/fact categorization."""
    with db.engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.exec_driver_sql("PRAGMA table_info(joke);")
        }
        if "entry_type" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE joke ADD COLUMN entry_type VARCHAR(20) NOT NULL DEFAULT 'fun'"
            )

def _ensure_challenge_schema():
    """Ensure recently added Challenge columns exist for older SQLite DBs."""
    with db.engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.exec_driver_sql("PRAGMA table_info(challenge);")
        }
        if "tags" not in cols:
            conn.exec_driver_sql("ALTER TABLE challenge ADD COLUMN tags TEXT DEFAULT ''")
        if "status" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE challenge ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'draft'"
            )
            conn.exec_driver_sql("UPDATE challenge SET status = 'published' WHERE status IS NULL")
        if "published_at" not in cols:
            conn.exec_driver_sql("ALTER TABLE challenge ADD COLUMN published_at DATETIME")
            conn.exec_driver_sql(
                "UPDATE challenge SET published_at = datetime('now') WHERE status = 'published' AND published_at IS NULL"
            )


# -----------------------------------------------------------------------------
# Seed
# -----------------------------------------------------------------------------
def seed_data():
    db.create_all()
    _ensure_user_schema()
    _ensure_joke_schema()
    _ensure_challenge_schema()
    # Enable WAL for better concurrency (SQLite)
    with db.engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
    # Normalize existing topic values to avoid case-sensitive mismatches.
    for dungeon in Dungeon.query.all():
        normalized_topic = _normalize_topic(dungeon.topic)
        if normalized_topic != dungeon.topic:
            dungeon.topic = normalized_topic
    for challenge in Challenge.query.all():
        normalized_topic = _normalize_topic(challenge.topic)
        if normalized_topic != challenge.topic:
            challenge.topic = normalized_topic

    # admin
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@example.com",
            is_admin=True,
            password_hash=generate_password_hash("admin123"),
        )
        db.session.add(admin)
    # default challenge
    if Challenge.query.count() == 0:
        db.session.add(
            Challenge(
                title="Reverse String",
                prompt="Write a function that reverses a string.\nExample: hello -> olleh",
                hints="Think about slicing or stacks.",
                solution="Python: s[::-1]\nJS: str.split('').reverse().join('')",
                language="General",
                difficulty="Easy",
                topic="strings",
                status="published",
                published_at=datetime.now(timezone.utc),
            )
        )
    # default joke
    if Joke.query.count() == 0:
        db.session.add(
            Joke(text="There are 10 kinds of people: those who understand binary and those who don't.", entry_type="fun")
        )
    # default dungeons
    dungeons_to_seed = [
        {
            "name": "The String Sanctum",
            "description": "A series of challenges to test your string manipulation mastery.",
            "topic": "strings", "unlock_xp": 0, "reward_xp": 50
        },
        {
            "name": "The Logic Labyrinth",
            "description": "Puzzles that require algorithmic thinking and data structures.",
            "topic": "algorithms", "unlock_xp": 50, "reward_xp": 100
        },
        {
            "name": "The Array Archipelago",
            "description": "Challenges focused on array manipulation and traversal.",
            "topic": "arrays", "unlock_xp": 20, "reward_xp": 75
        },
        {
            "name": "The Searching Spire",
            "description": "Tasks involving searching and sorting algorithms.",
            "topic": "search/sort", "unlock_xp": 30, "reward_xp": 75
        },
        {
            "name": "The Stack & Queue Station",
            "description": "Puzzles based on stack and queue data structures.",
            "topic": "stack/queue", "unlock_xp": 40, "reward_xp": 75
        },
        {
            "name": "The Mathematician's Maze",
            "description": "Problems that require mathematical insight and algorithms.",
            "topic": "math", "unlock_xp": 60, "reward_xp": 100
        },
        {
            "name": "The Dynamic Programming Dojo",
            "description": "A series of challenges on dynamic programming.",
            "topic": "dp", "unlock_xp": 100, "reward_xp": 150
        },
        {
            "name": "The SQL Summit",
            "description": "Test your database skills with these SQL challenges.",
            "topic": "sql", "unlock_xp": 80, "reward_xp": 120
        },
        {
            "name": "The Regex Reef",
            "description": "Master the art of regular expressions.",
            "topic": "regex", "unlock_xp": 70, "reward_xp": 100
        },
    ]

    for d_data in dungeons_to_seed:
        if not Dungeon.query.filter_by(name=d_data["name"]).first():
            db.session.add(Dungeon(**d_data))

    db.session.commit()


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        seed_data()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
else:
    # When running under a WSGI server (e.g., Gunicorn on Render/Heroku), ensure the
    # database schema exists and default seed data is present. This prevents runtime
    # errors on freshly deployed environments where create_all() hasn't been invoked
    # via the __main__ block above.
    with app.app_context():
        seed_data()
