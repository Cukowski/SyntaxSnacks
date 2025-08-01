from app import create_app
from app.models import db, Challenge, User, UserProgress
import json

app = create_app()

with app.app_context():
    # sample challenge
    c1 = Challenge(
        title="Reverse a String",
        prompt="Given a string, return it reversed.",
        solution="s[::-1]  # in Python",
        hints=json.dumps(["Think about slicing.", "What does s[::-1] do?"]),
        language="Python",
        topic="strings",
        difficulty="easy",
        reference_url="https://www.w3schools.com/python/python_strings.asp"
    )
    c2 = Challenge(
        title="Max of Array",
        prompt="Given an array of integers, return the maximum value.",
        solution="Use a simple loop or builtin function.",
        hints=json.dumps(["Iterate and track max.", "In Python: max(arr)"]),
        language="JavaScript",
        topic="arrays",
        difficulty="easy",
        reference_url="https://www.geeksforgeeks.org/javascript-array-max/"
    )
    db.session.add_all([c1, c2])
    db.session.commit()
    print("Seeded challenges.")
