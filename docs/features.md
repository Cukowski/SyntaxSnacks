# Features & Routes

## Core Features
*   🔐 **Auth** — Sign up, login, logout (Flask-Login).
*   🧠 **Daily Challenge Flow** — Shows the next unsolved challenge based on a simple progression.
*   🧪 **Built-in Sandbox** — Try solutions in-browser (JavaScript or Python via Pyodide) before marking solved.
*   🗺️ **Dungeon Explorer** — Explore themed "islands" of challenges and earn bonus XP for clearing them.
*   🧩 **Puzzle Arcade** — Play interactive mini-games like "Bit Flipper" to test fundamental knowledge.
*   ⭐ **Gamification** — “Mark as solved (+10 XP)” updates XP & streak logic.
*   🏆 **Leaderboard** — Sorted by XP, then streak.
*   🛠️ **Admin** — Add single challenge or **bulk-import via CSV**.
*   🎉 **Home “Did you know? / Today’s joke”** — Random item from CSV; “Show another” via `/api/fun`.
*   📬 **Contact** — Stores submissions, shows scoped success message, and surfaces entries in a sortable, filterable admin inbox with bulk actions and CSV export.
*   💅 **Nice UI** — Glassmorphism styling with a minimal theme; mobile-friendly.

---

## Screens & Routes

| Page                      | Route                           | Notes                                                           |
| ------------------------- | ------------------------------- | --------------------------------------------------------------- |
| Home                      | `/`                             | Public; shows random fun fact/joke from CSV                     |
| About                     | `/about`                        | Public                                                          |
| Contact                   | `/contact`                      | Public; POST redirects to `/contact?sent=1`                     |
| Sign up                   | `/signup`                       | Public                                                          |
| Login                     | `/login`                        | Public                                                          |
| Dashboard                 | `/dashboard`                    | Requires login; daily challenge, hint, solution, mark-as-solved |
| Leaderboard               | `/leaderboard`                  | Public                                                          |
| Dungeon Explorer          | `/dungeons`                     | Requires login; lists available dungeons                        |
| Puzzle Arcade             | `/puzzles`                      | Requires login; lists available mini-games                      |
| Bit Flipper Puzzle        | `/puzzles/bit-flipper/<level>`  | Requires login; the binary number puzzle game                   |
| Selector Sleuth Puzzle    | `/puzzles/selector-sleuth/<level>` | Requires login; the CSS selector puzzle game                    |
| Admin: New Challenge      | `/admin/challenge/new`          | Requires admin                                                  |
| Admin: Import CSV         | `/admin/challenges/import`      | Requires admin                                                  |
| Admin: CSV Example        | `/admin/challenges/example.csv` | Download sample                                                 |
| Admin: Contact Messages   | `/admin/messages`               | Requires admin; review contact form submissions                 |
| Admin: Contact Export     | `/admin/messages/export.csv`    | Requires admin; CSV export honoring current filters             |
| API: Fun Item             | `/api/fun`                      | Returns `{type, text}` JSON                                     |