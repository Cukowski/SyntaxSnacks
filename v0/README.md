# 🧠 SyntaxSnacks  
*Snack-sized code challenges to sharpen your skills—one bite at a time.*

**SyntaxSnacks** is a free, open-source platform for daily programming practice, designed to make learning fun, fast, and consistent.  
Whether you're brushing up on Python, diving into C++, or just want a small challenge with your morning coffee—this is your daily dose of code.

## 🍪 What is SyntaxSnacks?

A lightweight web and desktop-friendly app that gives you:

- 🧩 **1–2 Daily Programming Challenges** (beginner to intermediate)  
- 💬 **Hints, jokes, and quick facts** to keep it engaging
- 🎉 **Random daily snacks** on the homepage
- 🛠️ Support for **Python, C++, JavaScript, Java, and C#** (more to come)  
- 📊 **Progress tracking** and personalized language preferences  
- 🤖 Future-proof with optional **LLM-generated content** (human-reviewed)  
- 🌐 Mobile-ready UI + optional desktop/PWA version  
- 🌱 Fully **open-source, ad-free**, and easy to host or contribute to  

## 📁 Repository Layout

```

syntaxsnacks/
├── .env.example
├── requirements.txt
├── manage.py
├── config.py
├── instance/
│   └── syntaxsnacks.sqlite   # (created at runtime)
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── utils.py
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── login.html
│       ├── signup.html
│       ├── dashboard.html
│       ├── profile.html
│       └── partials/
│           ├── _header.html
│           ├── _footer.html
│           └── _challenge_card.html
├── static/                  # Glossy Touch assets (css/, js/, images/)
├── seed.py                  # helper to seed initial challenges/jokes
└── README.md

```

## 🏗️ Current Status

✅ Basic backend (Python / Flask) with authentication and session management  
✅ Glossy Touch-inspired UI with modular Jinja templates  
✅ Visitor-friendly landing page for guests  
✅ Challenge engine with language preferences  
✅ Progress tracking (streaks, solved)  
🔜 LLM-assisted content pipeline (human-reviewed)  
🔜 Desktop/PWA packaging and deeper personalization  
🔜 Admin / content moderation tools  

## 📦 Tech Stack

- Backend: **Python (Flask)**  
- Frontend: **HTML, CSS, JavaScript** (no heavy frameworks)  
- Database: **SQLite** (easy to swap out)  
- Optional: **Open-source LLMs** (e.g., via `llama.cpp`) for content generation  
- Deployment: Self-hosted or low-cost VPS (e.g., Gunicorn + Nginx), custom domain `syntaxsnacks.site`  

## 🚀 Getting Started

### Prerequisites

- Python 3.10+  
- Git  

### Setup

```bash
git clone https://github.com/cukowski/syntaxsnacks.git
cd syntaxsnacks
````

Copy and customize environment:

```bash
cp .env.example .env
# edit .env: set a strong SECRET_KEY before running
```

Create and activate virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Seed initial content:

```bash
python seed.py
```

Run development server:

```bash
python manage.py
```

Open in browser: `http://localhost:5000`

## 🧠 Features to Contribute To

* Add new snack-sized challenges (multi-language)
* Improve UI/UX and responsiveness
* Enhance personalization / adaptive difficulty
* Build LLM-assisted draft content generation with approval workflow
* Extend to more languages or embed interactive execution
* Help with deployment, PWA support, or analytics

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🔒 Security Notes

* Passwords are hashed; no plaintext storage
* CSRF protection is enabled (via Flask-WTF or tokens)
* Session cookies are HTTP-only with sane defaults; production should enforce HTTPS
* Input is handled through SQLAlchemy to avoid injection risks

## 📚 License

MIT — do whatever you want, just don’t remove the cookies. See
[LICENSE](LICENSE) for the full text.

---

### Made with ☕, 💡, and a bit of `while(fun)`.

