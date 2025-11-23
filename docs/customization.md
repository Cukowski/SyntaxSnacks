# Customization

You can customize several aspects of the application to fit your needs.

*   **Theme/Styling**: Edit `static/css/custom.css` to override or add your own styles. This is the primary file for changing the look and feel.

*   **Layout & Navigation**: The base HTML structure, including the navigation bar and footer, is located in `templates/base.html`.

*   **Home Page Content**: Modify the "fun snacks" (jokes and facts) by editing the `data/fun_snacks.csv` file.

*   **Gamification Rules**: The logic for awarding XP and calculating streaks is in the `update_streak_and_xp()` function in `app.py`. You can adjust the values and conditions here.

*   **Daily Challenge Logic**: The `get_daily_challenge_for_user()` function in `app.py` currently returns the first unsolved challenge for a user. This can be replaced with more complex logic, such as being date-based, random, or following a specific curriculum path.

*   **In-browser Runner**: The sandbox UI is in `templates/dashboard.html`. The JavaScript wiring for the sandbox (including the Pyodide and JS runners) is in `templates/base.html`.