import csv
import html
import io
import os
import re
import tempfile
import unittest
from datetime import datetime

from werkzeug.security import generate_password_hash

from app import app, db, User, Challenge


class ChallengeImportTestCase(unittest.TestCase):
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

    def _build_csv(self, rows):
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["title", "prompt", "hints", "solution", "tags", "status", "published_at"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return buf.getvalue()

    def test_preview_then_import_skips_invalid_rows(self):
        self.login_admin()
        rows = [
            {"title": "FizzBuzz", "prompt": "Write fizzbuzz", "hints": "", "solution": "", "tags": "loops", "status": "published", "published_at": "2024-02-01"},
            {"title": "Array Sum", "prompt": "Sum items", "hints": "", "solution": "", "tags": "arrays", "status": "draft", "published_at": ""},
            {"title": "Bad Status", "prompt": "Should fail", "hints": "", "solution": "", "tags": "oops", "status": "invalid", "published_at": ""},
            {"title": "Auto Date", "prompt": "No date provided", "hints": "", "solution": "", "tags": "strings", "status": "published", "published_at": ""},
            {"title": "Tag Cleanup", "prompt": "Tags trimmed", "hints": "", "solution": "", "tags": " one , two ", "status": "draft", "published_at": ""},
        ]
        csv_payload = self._build_csv(rows).encode("utf-8")

        resp = self.client.post(
            "/admin/challenges/import",
            data={"file": (io.BytesIO(csv_payload), "bulk.csv")},
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode("utf-8")
        self.assertIn("Import Preview", body)
        self.assertIn("Status must be draft or published", body)

        match = re.search(r'<textarea name="payload" hidden>(.*?)</textarea>', body, re.S)
        self.assertIsNotNone(match)
        payload = html.unescape(match.group(1)).strip()

        confirm = self.client.post(
            "/admin/challenges/import",
            data={"payload": payload},
            follow_redirects=True,
        )
        self.assertEqual(confirm.status_code, 200)

        challenges = {c.title: c for c in Challenge.query.all()}
        self.assertEqual(len(challenges), 4)
        self.assertNotIn("Bad Status", challenges)

        fizz = challenges["FizzBuzz"]
        self.assertEqual(fizz.status, "published")
        self.assertEqual(fizz.published_at.date(), datetime(2024, 2, 1).date())

        auto = challenges["Auto Date"]
        self.assertEqual(auto.status, "published")
        self.assertIsNotNone(auto.published_at)

        draft = challenges["Array Sum"]
        self.assertEqual(draft.status, "draft")
        self.assertIsNone(draft.published_at)

        trimmed = challenges["Tag Cleanup"]
        self.assertEqual(trimmed.tags, "one,two")


if __name__ == "__main__":
    unittest.main()
