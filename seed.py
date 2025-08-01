from app import create_app
from app.models import db, Challenge, Snack, User, UserProgress
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

    # sample snacks
    s1 = Snack(category="hint", text="Remember to keep functions small and focused.")
    s2 = Snack(category="joke", text="Why do programmers prefer dark mode? Because light attracts bugs!")
    s3 = Snack(category="fact", text="Python was named after Monty Python, not the snake.")
    db.session.add_all([s1, s2, s3])
    db.session.commit()
    print("Seeded snacks.")
