import unittest
from app import app, db, Challenge, User

class AdminEditChallengeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a test user and log in
        self.admin = User(username='admin', password_hash='admin', is_admin=True)
        db.session.add(self.admin)
        db.session.commit()

        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = self.admin.id
                sess['_fresh'] = True

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_edit_challenge(self):
        # Create a challenge
        challenge = Challenge(title='Test Challenge', prompt='Test Prompt')
        db.session.add(challenge)
        db.session.commit()

        # Edit the challenge
        response = self.app.post(f'/admin/challenge/{challenge.id}/edit', data={
            'title': 'Updated Challenge',
            'prompt': 'Updated Prompt',
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Check that the challenge was updated in the database
        updated_challenge = db.session.get(Challenge, challenge.id)
        self.assertEqual(updated_challenge.title, 'Updated Challenge')
        self.assertEqual(updated_challenge.prompt, 'Updated Prompt')

if __name__ == '__main__':
    unittest.main()
