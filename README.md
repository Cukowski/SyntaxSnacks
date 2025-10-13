# SyntaxSnacks — Daily Programming Practice (Flask)

A small, good-looking web app for bite-sized coding challenges. Users earn XP and streaks, view a leaderboard, and (as admin) add or bulk-import challenges. The Home page shows a public “Did you know? / Today’s joke” pulled from a CSV.

> Tech: **Flask**, **Flask-Login**, **Flask-SQLAlchemy**, **SQLite** (default), **Jinja2**, **Gunicorn** (cloud)

---

## Table of Contents

* [Features](#features)
* [Screens & Routes](#screens--routes)
* [Quick Start (Local)](#quick-start-local)
* [Configuration](#configuration)
* [Folder Structure](#folder-structure)
* [Data Model](#data-model)
* [Admin & Seeding](#admin--seeding)
* [Challenges: Bulk CSV Import](#challenges-bulk-csv-import)
* [Home CSV (Fun Facts / Jokes)](#home-csv-fun-facts--jokes)
* [API](#api)
* [Deploying to the Cloud](#deploying-to-the-cloud)
* [Customization](#customization)
* [Roadmap / Next Steps](#roadmap--next-steps)
* [License](#license)

---

## Features

* 🔐 **Auth** — Sign up, login, logout (Flask-Login).
* 🧠 **Daily Challenge Flow** — Shows the next unsolved challenge.
* ⭐ **Gamification** — “Mark as solved (+10 XP)” updates XP & streak logic.
* 🏆 **Leaderboard** — Sorted by XP, then streak.
* 🛠️ **Admin** — Add single challenge or **bulk-import via CSV**.
* 🎉 **Home “Did you know? / Today’s joke”** — Random item from CSV; “Show another” via `/api/fun`.
* 📬 **Contact** — Success message scoped to the page (no global flash leaks).
* 💅 **Nice UI** — Glassmorphism styling with a minimal theme; mobile-friendly.

---

## Screens & Routes

| Page                 | Route                           | Notes                                                           |
| -------------------- | ------------------------------- | --------------------------------------------------------------- |
| Home                 | `/`                             | Public; shows random fun fact/joke from CSV                     |
| About                | `/about`                        | Public                                                          |
| Contact              | `/contact`                      | Public; POST redirects to `/contact?sent=1`                     |
| Sign up              | `/signup`                       | Public                                                          |
| Login                | `/login`                        | Public                                                          |
| Dashboard            | `/dashboard`                    | Requires login; daily challenge, hint, solution, mark-as-solved |
| Leaderboard          | `/leaderboard`                  | Public                                                          |
| Admin: New Challenge | `/admin/challenge/new`          | Requires admin                                                  |
| Admin: Import CSV    | `/admin/challenges/import`      | Requires admin                                                  |
| Admin: CSV Example   | `/admin/challenges/example.csv` | Download sample                                                 |
| Admin: Contact Messages   | `/admin/messages` | Requires admin                                                  |
| API: Fun Item        | `/api/fun`                      | Returns `{type, text}` JSON                                     |

---

## Quick Start (Local)

### 1) Clone & create a virtualenv

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

```bash
cp .env.example .env
# then edit .env to set a strong FLASK_SECRET_KEY
```

### 4) Run

```bash
python app.py
# http://localhost:5000
```

> On first run, the app seeds an **admin** user and a starter challenge.

---

## Configuration

Environment variables (via `.env`):

| Key                | Default            | Description                            |
| ------------------ | ------------------ | -------------------------------------- |
| `FLASK_SECRET_KEY` | `dev-secret`       | Set a strong secret in production      |
| `DATABASE_URL`     | `sqlite:///app.db` | SQLAlchemy URL (Postgres, MySQL, etc.) |

Examples:

```
# SQLite (default)
DATABASE_URL=sqlite:///app.db

# Postgres
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
```

---

## Folder Structure

```
.
├── app.py
├── requirements.txt
├── Procfile
├── .env.example
├── data/
│   └── fun_snacks.csv           # public facts/jokes CSV
├── static/
│   ├── css/
│   │   ├── templatemo-glossy-touch.css
│   │   └── custom.css           # project styles (edit me)
│   ├── images/
│   │   ├── logo.png
│   │   └── hero.jpg
│   └── js/
│       └── templatemo-glossy-touch.js
└── templates/
    ├── base.html
    ├── index.html
    ├── about.html
    ├── contact.html
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    ├── leaderboard.html
    ├── admin_add_challenge.html
    └── admin_import_challenges.html
```

---

## Data Model

**User**

* `id`, `username` (unique), `email` (unique), `password_hash`
* `xp` (int), `streak` (int), `last_active_date` (date)
* `is_admin` (bool)

**Challenge**

* `id`, `title`, `prompt`, `solution`, `hints`
* `language`, `difficulty`, `topic`
* `added_by` (User.id)

**Submission**

* `id`, `user_id`, `challenge_id`, `timestamp`

**Joke**

* `id`, `text`

---

## Admin & Seeding

On the first run the app seeds:

* **Admin user** — `username=admin`, `password=admin123`
* One starter challenge and one starter joke.

To change the admin password later:

```python
from app import app, db, User
from werkzeug.security import generate_password_hash
with app.app_context():
    u = User.query.filter_by(username="admin").first()
    u.password_hash = generate_password_hash("NEW_PASSWORD")
    db.session.commit()
```

---

## Challenges: Bulk CSV Import

**Route:** `/admin/challenges/import` (admin only)

**Accepted CSV headers:**

```
title,prompt,solution,hints,language,difficulty,topic
```

**Notes**

* `title` and `prompt` are required; others are optional.
* Encoding: UTF-8 (BOM accepted).
* Try the sample: `/admin/challenges/example.csv`.

---

## Home CSV (Fun Facts / Jokes)

**File:** `data/fun_snacks.csv`

**Headers:**

```
type,text
```

**Example rows:**

```
joke,Why do programmers prefer dark mode? Because light attracts bugs.
fact,Python was named after 'Monty Python', not the snake.
joke,A SQL query walks into a bar and asks: 'Can I join you?'
```

The Home page shows a random row and a **Show another** button that calls the `/api/fun` endpoint.

---

## API

### `GET /api/fun`

Returns a random fun item from `data/fun_snacks.csv`.

**Response**

```json
{ "type": "joke", "text": "There are 10 kinds of people..." }
```

---

## Deploying to the Cloud

The repo includes a `Procfile`:

```
web: gunicorn app:app
```

**General steps (Render/Railway/Fly/Heroku-like):**

1. Set environment variables:

   * `FLASK_SECRET_KEY`
   * `DATABASE_URL` (use a managed Postgres in production)
2. Use the `web` process: `gunicorn app:app`
3. Ensure `python-version` and `build` step install `requirements.txt`.

**Static files** are served by Flask; for high traffic consider a CDN.

---

## Customization

* **Theme/Styling:** Edit `static/css/custom.css`.
* **Nav & layout:** Edit `templates/base.html`.
* **Home Fun Section:** `templates/index.html` + `data/fun_snacks.csv`.
* **Gamification Rules:** See `update_streak_and_xp()` in `app.py`.
* **Daily Logic:** `get_daily_challenge_for_user()` currently returns the first unsolved challenge; swap for schedule/rotation when ready.

---

## Roadmap / Next Steps

* ✏️ **Answer box / sandbox** on Dashboard (capture notes/solutions; optional code run in a safe service later).
* 🧑‍🤝‍🧑 **Community** (comments, reactions, challenge voting).
* 🧩 **Categories & filters** on challenges.
* 🤖 **LLM assist** (hint generation, explanation, solution review).
* 📊 **Analytics** (daily/weekly engagement, cohort stats).
* 🐳 **Docker** & **CI/CD**.

---

## License

MIT (or your preferred license). Replace this line with the one you use in your repo.

