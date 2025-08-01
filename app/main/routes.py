from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models import Challenge, UserProgress, db
from ..utils import select_daily_challenge_for

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("dashboard.html", user=None, challenge=None)

@main_bp.route("/dashboard")
@login_required
def dashboard():
    challenge = select_daily_challenge_for(current_user)
    return render_template(
        "dashboard.html",
        user=current_user,
        challenge=challenge,
    )

@main_bp.route("/complete/<int:challenge_id>", methods=["POST"])
@login_required
def complete(challenge_id):
    # mark as solved
    existing = UserProgress.query.filter_by(user_id=current_user.id, challenge_id=challenge_id).first()
    if not existing:
        progress = UserProgress(user_id=current_user.id, challenge_id=challenge_id)
        db.session.add(progress)
        db.session.commit()
    # Optionally update streak if this is first solve today
    return redirect(url_for("main.dashboard"))

@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        langs = request.form.get("languages", "")
        current_user.preferred_languages = langs
        db.session.commit()
        flash("Preferences updated.", "success")
        return redirect(url_for("main.profile"))
    return render_template("profile.html", user=current_user)
