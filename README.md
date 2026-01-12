# SyntaxSnacks — Daily Programming Practice (Flask)

A small, good-looking web app for bite-sized coding challenges. Users earn XP and streaks, view a leaderboard, and (as admin) add or bulk-import challenges. The Home page shows a public “Did you know? / Today’s joke” pulled from a CSV.

> Tech: **Flask**, **Flask-Login**, **Flask-SQLAlchemy**, **SQLite** (default), **Jinja2**, **Gunicorn** (cloud)

---

## Table of Contents
* [Features](#features)
* [Quick Start (Local)](#quick-start-local)
* [Documentation](#documentation)
* [Roadmap / Next Steps](#roadmap--next-steps)
* [License](#license)

---

## Features
* 🔐 **Auth** — Sign up, login, logout (Flask-Login).
* 🧠 **Daily Challenge Flow** — Shows the next unsolved challenge.
* 🗺️ **Dungeon Explorer** — Explore themed "islands" of challenges and earn bonus XP for clearing them.
* 🧩 **Puzzle Arcade** — Play interactive mini-games like "Bit Flipper" to test fundamental knowledge.
* ⭐ **Gamification** — “Mark as solved (+10 XP)” updates XP & streak logic.
* 🏆 **Leaderboard** — Sorted by XP, then streak.
* 🛠️ **Admin** — Add single challenge or **bulk-import via CSV**.
* 🎉 **Home “Did you know? / Today’s joke”** — Random item from CSV; “Show another” via `/api/fun`.
* 📬 **Contact** — Stores submissions, shows scoped success message, and surfaces entries in a sortable, filterable admin inbox with bulk actions and CSV export.
* 💅 **Nice UI** — Glassmorphism styling with a minimal theme; mobile-friendly.

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

## Documentation

For detailed information on specific topics, please see the documents below.
*   [**Features & Routes**](docs/features.md): A breakdown of all application features and their corresponding URL routes.
*   [**Configuration**](docs/configuration.md): How to configure the application using environment variables.
*   [**Admin & Content**](docs/admin.md): Guide to admin features, user seeding, and content management.
*   [**Customization**](docs/customization.md): How to modify the theme, layout, and application logic.
*   [**Deployment**](docs/deployment.md): Instructions for deploying the application to a cloud server.
*   [**Mac Server Script**](docs/deployment-script-mac-server.md): Automated runner script for Mac server deployment.
*   [**Data Model**](docs/data-model.md): An overview of the database schema.
*   [**API Reference**](docs/api.md): Details on the available API endpoints.

---

## Roadmap / Next Steps

* ✏️ **Answer box / sandbox** on Challenges (capture notes/solutions; optional code run in a safe service later).
* 🧑‍🤝‍🧑 **Community** (comments, reactions, challenge voting).
* 🧩 **Categories & filters** on challenges.
* 🤖 **LLM assist** (hint generation, explanation, solution review).
* 📊 **Analytics** (daily/weekly engagement, cohort stats).
* 🐳 **Docker** & **CI/CD**.

---

## License

MIT (or your preferred license). Replace this line with the one you use in your repo.
