import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required, logout_user,
    current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import csv, io, random

# -----------------------------------------------------------------------------
# App & DB setup
# -----------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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
    return User.query.get(int(user_id))

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
    # Use query param to signal success; no flash, so no leak to other pages.
    if request.method == "POST":
        return redirect(url_for("contact", sent=1))
    return render_template("contact.html", sent=request.args.get("sent"))

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
        flash("Great! Challenge marked as solved. +10 XP")
    else:
        flash("You already solved this one.")
    return redirect(url_for("dashboard"))

@app.route("/leaderboard")
def leaderboard():
    users = User.query.order_by(User.xp.desc(), User.streak.desc()).limit(50).all()
    return render_template("leaderboard.html", users=users)

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

# ---- Public API for Home page
@app.route("/api/fun")
def api_fun():
    return random_fun()

# -----------------------------------------------------------------------------
# Seed
# -----------------------------------------------------------------------------
def seed_data():
    db.create_all()
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
    db.session.commit()

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        seed_data()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
