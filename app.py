import os
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
import csv, io, random
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

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(200))
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.Date)
    is_admin = db.Column(db.Boolean, default=False)

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    solution = db.Column(db.Text)
    hints = db.Column(db.Text)
    language = db.Column(db.String(40), default="General")
    difficulty = db.Column(db.String(30), default="Easy")
    topic = db.Column(db.String(60))
    added_by = db.Column(db.Integer, db.ForeignKey("user.id"))

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenge.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Joke(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

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

# -----------------------------------------------------------------------------
# CSV jokes/facts (Home page)
# -----------------------------------------------------------------------------
DATA_DIR = os.path.join(BASE_DIR, "data")
FUN_CSV = os.path.join(DATA_DIR, "fun_snacks.csv")
os.makedirs(DATA_DIR, exist_ok=True)

_fun_cache = {"items": [], "mtime": None}

def _load_fun_csv():
    """Load or hot-reload fun facts/jokes from CSV into a small cache."""
    try:
        mtime = os.path.getmtime(FUN_CSV)
    except FileNotFoundError:
        return []
    if _fun_cache["mtime"] != mtime:
        items = []
        try:
            with open(FUN_CSV, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    t = (row.get("type") or "fun").strip()
                    text = (row.get("text") or "").strip()
                    if text:
                        items.append({"type": t, "text": text})
            _fun_cache["items"] = items
            _fun_cache["mtime"] = mtime
        except Exception:
            _fun_cache["items"] = []
    return _fun_cache["items"]

def random_fun():
    items = _load_fun_csv()
    if not items:
        return {"type": "fun", "text": "Welcome to SyntaxSnacks!"}
    return random.choice(items)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def get_daily_challenge_for_user(user: User):
    """Return the first unsolved challenge for the user (simple baseline)."""
    solved_ids = {s.challenge_id for s in Submission.query.filter_by(user_id=user.id).all()}
    for ch in Challenge.query.order_by(Challenge.id.asc()):
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

    dungeon = Dungeon.query.filter_by(topic=challenge.topic).first()
    if not dungeon:
        return None # No dungeon for this topic

    # Check if user has already completed this dungeon
    if DungeonCompletion.query.filter_by(user_id=user.id, dungeon_id=dungeon.id).first():
        return None

    # Get all challenge IDs for this dungeon's topic
    dungeon_challenge_ids = {c.id for c in Challenge.query.filter_by(topic=dungeon.topic).all()}
    solved_challenge_ids = {s.challenge_id for s in Submission.query.filter_by(user_id=user.id).all()}

    if dungeon_challenge_ids.issubset(solved_challenge_ids):
        # User has solved all challenges in this dungeon!
        db.session.add(DungeonCompletion(user_id=user.id, dungeon_id=dungeon.id))
        user.xp = (user.xp or 0) + dungeon.reward_xp
        db.session.commit()
        return dungeon # Return the completed dungeon to flash a message

def admin_required():
    return current_user.is_authenticated and current_user.is_admin

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

    # Get total challenges per topic
    total_challenges_by_topic = dict(
        db.session.query(Challenge.topic, func.count(Challenge.id))
        .group_by(Challenge.topic)
        .all()
    )

    # Get user's solved challenges per topic
    solved_challenges_by_topic = dict(
        db.session.query(Challenge.topic, func.count(Submission.id))
        .join(Challenge, Challenge.id == Submission.challenge_id)
        .filter(Submission.user_id == current_user.id)
        .group_by(Challenge.topic)
        .all()
    )

    dungeon_data = []
    for d in all_dungeons:
        total = total_challenges_by_topic.get(d.topic, 0)
        solved = solved_challenges_by_topic.get(d.topic, 0)
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
    challenges = Challenge.query.filter_by(topic=dungeon.topic).order_by(Challenge.id).all()
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

# ---- Admin: add single challenge
@app.route("/admin/challenge/new", methods=["GET", "POST"])
@login_required
def admin_add_challenge():
    if not admin_required():
        flash("Admin only.")
        return redirect(url_for("index"))
    if request.method == "POST":
        ch = Challenge(
            title=request.form["title"].strip(),
            prompt=request.form["prompt"].strip(),
            solution=request.form.get("solution", "").strip(),
            hints=request.form.get("hints", "").strip(),
            language=request.form.get("language", "General").strip(),
            difficulty=request.form.get("difficulty", "Easy").strip(),
            topic=request.form.get("topic", "").strip(),
            added_by=current_user.id,
        )
        db.session.add(ch)
        db.session.commit()
        flash("Challenge added.")
        return redirect(url_for("admin_add_challenge"))
    return render_template("admin_add_challenge.html")

# ---- Admin: bulk import challenges from CSV
@app.route("/admin/challenges/import", methods=["GET", "POST"])
@login_required
def admin_import_challenges():
    if not admin_required():
        flash("Admin only.")
        return redirect(url_for("index"))
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.lower().endswith(".csv"):
            flash("Please upload a CSV file.")
            return redirect(url_for("admin_import_challenges"))
        try:
            stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
            reader = csv.DictReader(stream)
            count = 0
            for row in reader:
                title = (row.get("title") or "").strip()
                prompt = (row.get("prompt") or "").strip()
                if not title or not prompt:
                    continue
                ch = Challenge(
                    title=title,
                    prompt=prompt,
                    solution=(row.get("solution") or "").strip(),
                    hints=(row.get("hints") or "").strip(),
                    language=(row.get("language") or "General").strip(),
                    difficulty=(row.get("difficulty") or "Easy").strip(),
                    topic=(row.get("topic") or "").strip(),
                    added_by=current_user.id,
                )
                db.session.add(ch)
                count += 1
            db.session.commit()
            flash(f"Imported {count} challenges.")
        except Exception as e:
            db.session.rollback()
            flash(f"Import failed: {e}")
        return redirect(url_for("admin_import_challenges"))
    return render_template("admin_import_challenges.html")

@app.route("/admin/challenges/example.csv")
@login_required
def download_challenge_csv_example():
    if not admin_required():
        flash("Admin only.")
        return redirect(url_for("index"))
    csv_text = (
        "title,prompt,solution,hints,language,difficulty,topic\n"
        "Reverse String,Write a function that reverses a string.,"
        "Python: s[::-1]; JS: str.split('').reverse().join(''),"
        "Think about slicing or stacks.,General,Easy,strings\n"
    )
    return (
        csv_text,
        200,
        {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'attachment; filename="challenges_example.csv"',
        },
    )

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

# -----------------------------------------------------------------------------
# Seed
# -----------------------------------------------------------------------------
def seed_data():
    db.create_all()
    # Enable WAL for better concurrency (SQLite)
    with db.engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")

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
            )
        )
    # default joke
    if Joke.query.count() == 0:
        db.session.add(
            Joke(text="There are 10 kinds of people: those who understand binary and those who don't.")
        )
    # default dungeons
    if Dungeon.query.count() == 0:
        db.session.add(
            Dungeon(
                name="The String Sanctum",
                description="A series of challenges to test your string manipulation mastery.",
                topic="strings",
                unlock_xp=0,
                reward_xp=50
            )
        )
        db.session.add(
            Dungeon(name="The Logic Labyrinth", description="Puzzles that require algorithmic thinking and data structures.", topic="algorithms", unlock_xp=50, reward_xp=100)
        )

    db.session.commit()

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        seed_data()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
