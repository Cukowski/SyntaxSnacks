import os
import tempfile
import unittest
import io

from werkzeug.security import generate_password_hash

from app import app, db, User, Joke


class AdminFunCardsTestCase(unittest.TestCase):
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

    def test_admin_can_add_and_delete_fun_card(self):
        self.login_admin()
        resp = self.client.post(
            "/admin/fun",
            data={"entry_type": "fact", "text": "Testing fun card"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        saved = Joke.query.first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.entry_type, "fact")

        del_resp = self.client.post(
            f"/admin/fun/{saved.id}/delete",
            follow_redirects=True,
        )
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(Joke.query.count(), 0)

    def test_admin_can_import_fun_cards_via_csv(self):
        self.login_admin()
        csv_text = "text,entry_type\nHello world,fun\nDid you know?,fact\nEmpty,,\n"
        resp = self.client.post(
            "/admin/fun",
            data={"file": (io.BytesIO(csv_text.encode("utf-8")), "fun.csv")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Joke.query.count(), 2)
        types = sorted({j.entry_type for j in Joke.query.all()})
        self.assertEqual(types, ["fact", "fun"])


if __name__ == "__main__":
    unittest.main()
