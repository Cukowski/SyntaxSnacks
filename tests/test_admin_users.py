import os
import tempfile
import unittest

from werkzeug.security import generate_password_hash
from flask_login import current_user

from app import app, db, User, AuditLog


class AdminUserManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI=f"sqlite:///{self.db_path}",
        )
        self.app_context = app.app_context()
        self.app_context.push()
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.client = app.test_client()

        admin = User(
            username="admin",
            email="admin@example.com",
            is_admin=True,
            password_hash=generate_password_hash("password"),
        )
        user = User(
            username="player",
            email="player@example.com",
            password_hash=generate_password_hash("pw"),
        )
        db.session.add_all([admin, user])
        db.session.commit()
        self.user_id = user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def login_admin(self):
        return self.client.post(
            "/login",
            data={"username": "admin", "password": "password"},
            follow_redirects=True,
        )

    def test_inactive_user_cannot_login(self):
        user = db.session.get(User, self.user_id)
        user.active = False
        db.session.commit()

        with self.client as c:
            resp = c.post(
                "/login",
                data={"username": "player", "password": "pw"},
                follow_redirects=True,
            )
            self.assertIn(b"deactivated", resp.data)
            self.assertFalse(current_user.is_authenticated)

    def test_toggle_active_creates_audit_log(self):
        self.login_admin()
        resp = self.client.post(
            f"/admin/users/{self.user_id}/toggle_active", follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        user = db.session.get(User, self.user_id)
        self.assertFalse(user.active)
        log = AuditLog.query.filter_by(
            target_user_id=self.user_id, action="toggle_active"
        ).first()
        self.assertIsNotNone(log)

    def test_adjust_stats_updates_and_logs(self):
        self.login_admin()
        resp = self.client.post(
            f"/admin/users/{self.user_id}/adjust_stats",
            data={"delta_xp": "15", "delta_streak": "-2", "reason": "bonus fix"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        user = db.session.get(User, self.user_id)
        self.assertEqual(user.xp, 15)
        self.assertEqual(user.streak, 0)  # clamped at zero
        log = AuditLog.query.filter_by(
            target_user_id=self.user_id, action="adjust_stats"
        ).first()
        self.assertEqual(log.meta.get("reason"), "bonus fix")
        self.assertEqual(log.meta.get("delta_xp"), 15)

    def test_admin_can_update_username_and_hide_from_leaderboard(self):
        self.login_admin()
        resp = self.client.post(
            f"/admin/users/{self.user_id}/update_profile",
            data={"username": "player-renamed"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        user = db.session.get(User, self.user_id)
        self.assertEqual(user.username, "player-renamed")
        self.assertFalse(user.show_on_leaderboard)
        log = AuditLog.query.filter_by(
            target_user_id=self.user_id, action="update_profile"
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.meta.get("new_username"), "player-renamed")
        self.assertFalse(log.meta.get("new_show_on_leaderboard"))

    def test_leaderboard_hides_users_with_visibility_off(self):
        hidden_user = db.session.get(User, self.user_id)
        hidden_user.xp = 500
        hidden_user.show_on_leaderboard = False
        visible_user = User(
            username="visible",
            email="visible@example.com",
            password_hash=generate_password_hash("pw"),
            xp=100,
            show_on_leaderboard=True,
        )
        db.session.add(visible_user)
        db.session.commit()

        resp = self.client.get("/leaderboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"visible", resp.data)
        self.assertNotIn(b"player", resp.data)


if __name__ == "__main__":
    unittest.main()
