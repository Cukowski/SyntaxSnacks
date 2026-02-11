import os
import tempfile
import unittest

from app import app, db, User, Message
from werkzeug.security import generate_password_hash

class ContactFormTest(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI=f"sqlite:///{self.db_path}",
        )
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.session.remove()
        db.drop_all()
        db.create_all()

        # Create a user
        self.user = User(username='testuser', email='test@example.com', password_hash=generate_password_hash('password'))
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_contact_form_logged_in(self):
        # Log in the user
        self.login('testuser', 'password')

        # Navigate to the contact page
        response = self.app.get('/contact')
        self.assertEqual(response.status_code, 200)

        # Submit the form with an empty name and email
        response = self.app.post('/contact', data=dict(
            message='Test message'
        ), follow_redirects=True)
        self.assertIn(b'Message sent successfully!', response.data)

        # Submit the form with a name and email
        response = self.app.post('/contact', data=dict(
            name='Test User',
            email='test@example.com',
            message='Test message'
        ), follow_redirects=True)
        self.assertIn(b'Message sent successfully!', response.data)

    def test_contact_form_logged_out(self):
        # Log out the user
        self.logout()

        # Navigate to the contact page
        response = self.app.get('/contact')
        self.assertEqual(response.status_code, 200)

        # Submit the form with an empty name and email
        response = self.app.post('/contact', data=dict(
            message='Test message'
        ), follow_redirects=True)
        self.assertIn(b'Please fill out all fields.', response.data)

        # Submit the form with a name and email
        response = self.app.post('/contact', data=dict(
            name='Test User',
            email='test@example.com'
        ), follow_redirects=True)
        self.assertIn(b'Please fill out all fields.', response.data)

        # Submit the form with a name, email, and message
        response = self.app.post('/contact', data=dict(
            name='Test User',
            email='test@example.com',
            message='Test message'
        ), follow_redirects=True)
        self.assertIn(b'Message sent successfully!', response.data)

if __name__ == '__main__':
    unittest.main()
