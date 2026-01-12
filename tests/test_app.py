import unittest
from app import app, db, Joke

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_random_fun_with_jokes_in_db(self):
        # Add a joke to the database
        joke = Joke(text="This is a test joke", entry_type="fun")
        db.session.add(joke)
        db.session.commit()

        # Call the random_fun function
        with app.test_request_context():
            fun = app.view_functions['api_fun']()

        # Check that the returned fun fact is the one from the database
        self.assertEqual(fun['text'], "This is a test joke")
        self.assertEqual(fun['type'], "fun")

    def test_random_fun_without_jokes_in_db(self):
        # Call the random_fun function
        with app.test_request_context():
            fun = app.view_functions['api_fun']()

        # Check that the returned fun fact is the default one
        self.assertEqual(fun['text'], "Welcome to SyntaxSnacks!")
        self.assertEqual(fun['type'], "fun")

if __name__ == '__main__':
    unittest.main()
