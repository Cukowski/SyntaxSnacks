import os
import tempfile
import unittest

from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app import app, db, Message, User


class AdminMessageTestCase(unittest.TestCase):
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
        db.session.add(admin)
        db.session.commit()

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

    def test_contact_creates_message(self):
        response = self.client.post(
            "/contact",
            data={
                "name": "Tester",
                "email": "tester@example.com",
                "message": "Hello there",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Message.query.count(), 1)
        stored = Message.query.first()
        self.assertEqual(stored.body, "Hello there")
        self.assertFalse(stored.is_read)

    def test_admin_can_mark_read_and_delete(self):
        msg = Message(name="User", email="user@example.com", body="Ping")
        db.session.add(msg)
        db.session.commit()

        self.login_admin()

        toggle_resp = self.client.post(
            f"/admin/messages/{msg.id}/toggle_read",
            data={"next": "/admin/messages"},
        )
        self.assertEqual(toggle_resp.status_code, 302)
        updated = db.session.get(Message, msg.id)
        self.assertTrue(updated.is_read)

        delete_resp = self.client.post(
            f"/admin/messages/{msg.id}/delete",
            data={"next": "/admin/messages"},
        )
        self.assertEqual(delete_resp.status_code, 302)
        deleted = db.session.get(Message, msg.id)
        self.assertIsNotNone(deleted.deleted_at)

    def test_export_respects_filters(self):
        unread = Message(name="One", email="one@example.com", body="Need help")
        read_msg = Message(
            name="Two",
            email="two@example.com",
            body="Thanks",
            is_read=True,
        )
        deleted = Message(
            name="Three",
            email="three@example.com",
            body="Ignore me",
            deleted_at=datetime.now(timezone.utc),
        )
        db.session.add_all([unread, read_msg, deleted])
        db.session.commit()

        self.login_admin()

        response = self.client.get("/admin/messages/export.csv?status=unread")
        self.assertEqual(response.status_code, 200)
        csv_text = response.data.decode("utf-8")
        self.assertIn("one@example.com", csv_text)
        self.assertNotIn("two@example.com", csv_text)
        self.assertNotIn("three@example.com", csv_text)


if __name__ == "__main__":
    unittest.main()
