# Admin & Content Management

## Admin User & Seeding

On the first run, the application seeds the database with:

*   **Admin user**: `username=admin`, `password=admin123`
*   One starter challenge.
*   One starter programming joke.

You can log in with these credentials to access admin-only areas.

### Changing the Admin Password

For security, you should change the default admin password. You can run the following script in a Flask shell (`flask shell`):

```python
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    u = User.query.filter_by(username="admin").first()
    if u:
        u.password_hash = generate_password_hash("YOUR_NEW_STRONG_PASSWORD")
        db.session.commit()
        print("Admin password updated.")
    else:
        print("Admin user not found.")
```

## Admin Features

### Challenge Management

Admins can add challenges one by one or in bulk via CSV import.

*   **Add Single Challenge**: `/admin/challenge/new`
*   **Bulk Import Challenges**: `/admin/challenges/import`
    *   **CSV Headers**: `title,prompt,solution,hints,language,difficulty,topic`
    *   `title` and `prompt` are required.
    *   Download a sample CSV file at `/admin/challenges/example.csv`.

### Contact Message Inbox

Contact form submissions are saved to the database. Admins can manage them at `/admin/messages`.

*   Filter messages by status (all, read, unread) or search content.
*   Toggle the read/unread status of a single message.
*   Perform bulk actions (mark as read, mark as unread, delete).
*   Export the currently filtered list of messages to CSV via `/admin/messages/export.csv`.

## Home Page Content (Fun Snacks)

The fun facts and jokes displayed on the home page are loaded from `data/fun_snacks.csv`. The application will hot-reload this file if it changes, so you can edit it while the server is running.

**File:** `data/fun_snacks.csv`

**Headers:** `type,text`

**Example:**
```csv
type,text
joke,Why do programmers prefer dark mode? Because light attracts bugs.
fact,Python was named after 'Monty Python', not the snake.
```