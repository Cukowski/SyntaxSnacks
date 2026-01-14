# Features & Routes

## Core Features
*   🔐 **Auth** — Sign up, login, logout (Flask-Login).
*   🧠 **Daily Challenge Flow** — Shows the next unsolved challenge based on a simple progression.
*   🗺️ **Dungeon Explorer** — Explore themed "islands" of challenges and earn bonus XP for clearing them.
*   🧩 **Puzzle Arcade** — Play interactive mini-games like "Bit Flipper" to test fundamental knowledge.
*   ⭐ **Gamification** — “Mark as solved (+10 XP)” updates XP & streak logic.
*   🏆 **Leaderboard** — Sorted by XP, then streak.
*   🛠️ **Comprehensive Admin Panel** — Manage users, challenges, and site content.
*   🎉 **Home “Did you know? / Today’s joke”** — Random item from the database, managed via the admin panel.
*   📬 **Contact Form** — Stores submissions in a full-featured admin inbox with filtering, bulk actions, and CSV export.
*   💅 **Nice UI** — Glassmorphism styling with a minimal theme; mobile-friendly.

---

## Screens & Routes

| Page                      | Route                           | Notes                                                           |
| ------------------------- | ------------------------------- | --------------------------------------------------------------- |
| Home                      | `/`                             | Public; shows random fun fact/joke from the database            |
| About                     | `/about`                        | Public                                                          |
| Contact                   | `/contact`                      | Public; POST redirects to `/contact?sent=1`                     |
| Sign up                   | `/signup`                       | Public                                                          |
| Login                     | `/login`                        | Public                                                          |
| Challenges                | `/dashboard`                    | Requires login; daily challenge, hint, solution, mark-as-solved |
| Leaderboard               | `/leaderboard`                  | Public                                                          |
| Dungeon Explorer          | `/dungeons`                     | Requires login; lists available dungeons                        |
| Dungeon View              | `/dungeons/<int:dungeon_id>`    | Requires login; shows challenges for a specific dungeon         |
| Puzzle Arcade             | `/puzzles`                      | Requires login; lists available mini-games                      |
| Bit Flipper Puzzle        | `/puzzles/bit-flipper/<level>`  | Requires login; the binary number puzzle game                   |
| Selector Sleuth Puzzle    | `/puzzles/selector-sleuth/<level>` | Requires login; the CSS selector puzzle game                   |
| **Admin: Users**              | `/admin/users`                  | Requires admin; manage users                                    |
| **Admin: User Detail**        | `/admin/users/<int:user_id>`    | Requires admin; view user details and audit log                 |
| **Admin: Challenges**         | `/admin/challenges`             | Requires admin; manage challenges                               |
| **Admin: New Challenge**      | `/admin/challenge/new`          | Requires admin                                                  |
| **Admin: Edit Challenge**     | `/admin/challenge/<challenge_id>/edit` | Requires admin                                                 |
| **Admin: Import CSV**         | `/admin/challenges/import`      | Requires admin                                                  |
| **Admin: Export CSV**         | `/admin/challenges/export.csv`  | Requires admin                                                  |
| **Admin: Fun Cards**          | `/admin/fun`                    | Requires admin; manage home page jokes/facts                    |
| **Admin: Contact Messages**   | `/admin/messages`               | Requires admin; review contact form submissions                 |
| API: Fun Item             | `/api/fun`                      | Returns `{type, text}` JSON                                     |
