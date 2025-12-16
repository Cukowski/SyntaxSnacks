from flask import abort, render_template, request
from flask_login import current_user, login_required

from .data import (
    BIT_FLIPPER_LEVELS,
    DEFAULT_PUZZLE_XP,
    GIT_REBASE_RESCUE_LEVELS,
    REGEX_RESCUE_LEVELS,
    SELECTOR_SLEUTH_LEVELS,
)


def register_puzzle_routes(app, db, PuzzleCompletion):
    """Attach puzzle routes to the Flask app to keep app.py lean."""

    def _completed_set():
        return {
            pc.puzzle_name
            for pc in PuzzleCompletion.query.filter_by(user_id=current_user.id).all()
        }

    def _level_payload(levels, level_num, slug):
        if not (1 <= level_num <= len(levels)):
            abort(404)
        level_data = levels[level_num - 1].copy()
        puzzle_name = f"{slug}_lvl_{level_num}"
        is_completed = (
            PuzzleCompletion.query.filter_by(
                user_id=current_user.id, puzzle_name=puzzle_name
            ).first()
            is not None
        )
        level_data.update(
            {
                "puzzle_name": puzzle_name,
                "is_completed": is_completed,
                "xp_reward": DEFAULT_PUZZLE_XP,
                "total_levels": len(levels),
            }
        )
        return level_data

    @app.route("/puzzles")
    @login_required
    def puzzles_hub():
        """A hub page listing all available mini-game puzzles."""
        completed_puzzles = _completed_set()
        return render_template("puzzles_hub.html", completed_puzzles=completed_puzzles)

    @app.route("/puzzles/bit-flipper/<int:level_num>")
    @login_required
    def puzzle_bit_flipper(level_num):
        """The Bit Flipper mini-game."""
        level_data = _level_payload(BIT_FLIPPER_LEVELS, level_num, "bit_flipper")
        return render_template("puzzle_bit_flipper.html", **level_data)

    @app.route("/puzzles/selector-sleuth/<int:level_num>")
    @login_required
    def puzzle_selector_sleuth(level_num):
        """The Selector Sleuth mini-game for CSS selectors."""
        level_data = _level_payload(
            SELECTOR_SLEUTH_LEVELS, level_num, "selector_sleuth"
        )
        return render_template("puzzle_selector_sleuth.html", **level_data)

    @app.route("/puzzles/regex-rescue/<int:level_num>")
    @login_required
    def puzzle_regex_rescue(level_num):
        """The Regex Rescue mini-game."""
        level_data = _level_payload(REGEX_RESCUE_LEVELS, level_num, "regex_rescue")
        return render_template("puzzle_regex_rescue.html", **level_data)

    @app.route("/puzzles/git-rebase-rescue/<int:level_num>")
    @login_required
    def puzzle_git_rebase_rescue(level_num):
        """Commit ordering puzzle with dependency and squash/fixup mechanics."""
        level_data = _level_payload(
            GIT_REBASE_RESCUE_LEVELS, level_num, "git_rebase_rescue"
        )
        return render_template("puzzle_git_rebase_rescue.html", **level_data)

    @app.route("/puzzles/complete", methods=["POST"])
    @login_required
    def complete_puzzle():
        """Endpoint for mini-games to call upon completion to award XP."""
        data = request.get_json() or {}
        puzzle_name = data.get("puzzle_name")
        if not puzzle_name:
            return {"error": "Puzzle name is required."}, 400

        if PuzzleCompletion.query.filter_by(
            user_id=current_user.id, puzzle_name=puzzle_name
        ).first():
            return {"message": "Puzzle already completed."}, 200

        db.session.add(PuzzleCompletion(user_id=current_user.id, puzzle_name=puzzle_name))
        current_user.xp = (current_user.xp or 0) + DEFAULT_PUZZLE_XP
        db.session.commit()
        return {"message": "XP awarded!", "new_xp": current_user.xp}, 200
